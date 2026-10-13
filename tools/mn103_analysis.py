"""Original non-executing MN103 contracts and narrow counted-copy proof.

GNU remains the decoder AND external synthetic execution reference. This is
not a CPU interpreter, raw decoder, compiler ABI, SSA engine or P-code language.
Manual 13250-040E + pinned GNU simulator sources/fixtures are cited in docs21.
"""
from __future__ import annotations
import re


class SemanticGap(ValueError):
    pass


PREDICATES = {'beq':'Z=1','bne':'Z=0','bgt':'Z=0 and N=V','bge':'N=V',
              'ble':'Z=1 or N!=V','blt':'N!=V','bhi':'C=0 and Z=0',
              'bls':'C=1 or Z=1','bcc':'C=0','bcs':'C=1'}
REGISTER = re.compile(r'(?:[da][0-3]|sp|mdr|lir|lar)$')


def operands(text):
    """Split GNU operands without splitting memory/register-list commas."""
    parts,level,begin = [],0,0
    for i,c in enumerate(text):
        if c in '([': level += 1
        if c in ')]': level -= 1
        if level < 0: raise SemanticGap('unbalanced operands')
        if c == ',' and level == 0:
            parts.append(text[begin:i].strip());begin = i+1
    if level: raise SemanticGap('unbalanced operands')
    parts.append(text[begin:].strip())
    return parts


def memory(text):
    if not text.startswith('(') or not text.endswith(')'):
        return None
    parts = operands(text[1:-1])
    if len(parts) == 1:
        if REGISTER.fullmatch(parts[0]):
            return {'base':parts[0],'displacement':0}
        return {'absolute':int(parts[0],0)}
    if len(parts) == 2 and REGISTER.fullmatch(parts[1]):
        if REGISTER.fullmatch(parts[0]):
            return {'base':parts[1],'index':parts[0]}
        return {'base':parts[1],'displacement':int(parts[0],0)}
    raise SemanticGap('unadmitted addressing form')


def effect(row, size):
    """Typed architectural facts; no register/memory values are evaluated."""
    r = {'address':row.address,'status':'unmodeled','basis':'manual + synthetic GNU admission'}
    m,p = row.mnemonic,operands(row.operands)
    try:
        if m in ('call','calls'):
            expected = {5,7} if m == 'call' else {2,4,6}
            if size not in expected: raise SemanticGap('call encoding length')
            target = memory(p[0])
            if target is not None:
                if m != 'calls' or size != 2 or set(target) != {'base','displacement'} or target['displacement'] != 0:
                    raise SemanticGap('unadmitted indirect call form')
                # CALLS (An) uses An itself, not a data load from *An.
                target = {'register':target['base']}
            else:
                target = {'decoded_direct':row.direct_target()}
            r.update(status='modeled',link_offset=size,sp_delta=0,flags='preserved',
                     target=target,memory_writes=[{'base':'sp_before_call','offset':0,'width':4,'value':'next_pc'}],
                     register_writes=['mdr','pc'])
            if m == 'call':
                if len(p) != 3: raise SemanticGap('call operands')
                frame = int(p[2],0)
                if not 0 <= frame <= 255: raise SemanticGap('frame range')
                saved = p[1].strip('[]').split(',') if p[1] != '[]' else []
                if any(x not in ('d2','d3','a2','a3') for x in saved):
                    raise SemanticGap('other/EX register save groups not admitted')
                saved = [x for x in ('d2','d3','a2','a3') if x in saved]
                r['memory_writes'] += [{'base':'sp_before_call','offset':-4*(i+1),'width':4,'value':reg} for i,reg in enumerate(saved)]
                r.update(sp_delta=-frame,saved_registers=saved)
                r['register_writes'].append('sp')
        elif m in ('ret','retf','rets'):
            if size != (2 if m=='rets' else 3): raise SemanticGap('return encoding length')
            frame = 0 if m=='rets' else int(p[1],0)
            if not 0 <= frame <= 255: raise SemanticGap('return frame range')
            r.update(status='modeled',sp_delta=frame,flags='preserved',
                     target={'memory':'restored_sp','width':4} if m!='retf' else {'register':'mdr_before_restore'},
                     note='RETS does not add four to SP; RETF target precedes register restore')
            if m != 'rets':
                saved = p[0].strip('[]').split(',') if p[0] != '[]' else []
                if any(x not in ('d2','d3','a2','a3') for x in saved):
                    raise SemanticGap('unadmitted restore group')
                saved = [x for x in ('d2','d3','a2','a3') if x in saved]
                r['restores'] = [{'base':'restored_sp','offset':-4*(i+1),'width':4,'register':reg} for i,reg in enumerate(saved)]
        elif m == 'movm' and p == ['[a2]','(sp)'] and size == 2:
            # T17 admits this ONE common save form, not OTHER/EX or an ABI.
            r.update(status='modeled',sp_delta=-4,flags='preserved',
                     memory_writes=[{'base':'sp_before','offset':-4,'width':4,'value':'a2'}],
                     register_writes=['sp'])
        elif m in ('mov','movbu','movhu') and len(p)==2:
            width = {'mov':4,'movbu':1,'movhu':2}[m]
            src,dst = memory(p[0]),memory(p[1])
            if src is not None and dst is not None: raise SemanticGap('memory-memory move')
            r.update(status='modeled',flags='preserved',width=width)
            if src is not None:
                r.update(memory_read=src,destination=p[1],load_extension='zero' if width<4 else 'none')
            elif dst is not None:
                r.update(memory_write=dst,source=p[0],stored_low_bits=width*8)
            else:
                if m!='mov' or not REGISTER.fullmatch(p[1]): raise SemanticGap('move form')
                r.update(source=p[0],destination=p[1],width=4)
        elif m in ('extb','extbu','exth','exthu'):
            if not re.fullmatch(r'd[0-3]',p[0]): raise SemanticGap('extension register')
            r.update(status='modeled',width=4,source_bits=8 if m.startswith('extb') else 16,
                     extension='zero' if m.endswith('u') else 'sign',flags='preserved')
        elif m in ('and','or') and len(p)==2 and re.fullmatch(r'd[0-3]',p[1]):
            r.update(status='modeled',width=4,flags='V=0,C=0,N=result[31],Z=(result=0)')
        elif m in ('inc','inc4'):
            if not re.fullmatch(r'[da][0-3]',p[0]): raise SemanticGap('increment register')
            if m=='inc4' and p[0][0]!='a': raise SemanticGap('INC4 register')
            r.update(status='modeled',register=p[0],increment=4 if m=='inc4' else 1,width=4,
                     flags='add32 condition codes' if p[0][0]=='d' else 'preserved')
        elif m == 'cmp':
            r.update(status='modeled',width=4,flags='sub32: borrow C, signed overflow V, N=result[31], Z=(result=0)')
        elif m in PREDICATES:
            r.update(status='modeled',predicate=PREDICATES[m],target=row.direct_target(),
                     fallthrough=row.address+size,flags='preserved',flag_source='forwarded; raw PSW timing not modeled')
        elif m == 'setlb' and size == 1:
            r.update(status='modeled',logical_cached_bytes=4,cache_origin=row.address+1,
                     lar=row.address+5,flags='preserved',physical_lir_packing='unknown CPU-dependent')
        elif m == 'lne' and size == 1:
            r.update(status='modeled',predicate='Z=0',target='LAR-4 with cached prefix replay',
                     fallthrough=row.address+1,flags='preserved')
    except (ValueError,IndexError):
        # Do not retain apparently complete partial facts after a failed gate.
        return {'address':row.address,'status':'unmodeled','basis':'unsupported form/size'}
    return r


def prove_copy_loop(rows, at):
    """Closed-form proof of a very narrow counted word-copy shape.

    No memory contents/CPU are executed. Only loop-local structural semantics
    are established. Arbitrary SETLB, unknown entry LIR or dynamic bounds stop.
    """
    by = {r.address:r for r in rows}
    previous = next((a for a,b in zip(rows,rows[1:]) if b.address==at),None)
    if previous is None or previous.mnemonic!='mov':
        raise SemanticGap('no immediate local counter setup')
    p = operands(previous.operands)
    if len(p)!=2 or not re.fullmatch(r'd[0-3]',p[1]):
        raise SemanticGap('unadmitted counter')
    count = -int(p[0],0)
    if not 1 <= count <= 4096: raise SemanticGap('nonfinite/unbounded count')
    sequence = [by.get(at+i) for i in range(7)]
    if any(r is None for r in sequence): raise SemanticGap('prefix crosses instruction boundary')
    if [r.mnemonic for r in sequence] != ['setlb','mov','inc4','mov','inc4','inc','lne']:
        raise SemanticGap('unsupported copy shape')
    if sequence[0].operands or sequence[6].operands:
        raise SemanticGap('malformed operandless loop instruction')
    load,store = operands(sequence[1].operands),operands(sequence[3].operands)
    src,dst = memory(load[0]),memory(store[1])
    if src is None or dst is None or set(src)!= {'base','displacement'} or set(dst)!= {'base','displacement'}:
        raise SemanticGap('not direct pointer copy')
    if src['displacement'] or dst['displacement'] or src['base']==dst['base']:
        raise SemanticGap('noncanonical pointer copy')
    if not re.fullmatch(r'a[0-3]',src['base']) or not re.fullmatch(r'a[0-3]',dst['base']):
        raise SemanticGap('unadmitted pointer registers')
    if load[1] != store[0] or not re.fullmatch(r'd[0-3]',load[1]) or load[1]==p[1]:
        raise SemanticGap('counter clobbered or transfer register mismatch')
    if sequence[2].operands!=src['base'] or sequence[4].operands!=dst['base'] or sequence[5].operands!=p[1]:
        raise SemanticGap('increments do not match memory/counter')
    if by.get(at+7) is None: raise SemanticGap('missing exit boundary')
    for row in rows:
        target = row.direct_target()
        if target is not None and at <= target <= at+6 and not at <= row.address <= at+6:
            raise SemanticGap('external direct entry bypasses local loop setup')
    return {'setup':at,'counter_setup':previous.address,'cached_origin':at+1,
            'cached_bytes':4,'lar':at+5,'condition_site':at+6,'exit':at+7,
            'iterations':count,'width':4,'bytes_transferred':count*4,
            'source_register':src['base'],'destination_register':dst['base'],
            'pointer_delta':count*4,'counter_register':p[1],'counter_exit':0,
            'exit_condition_codes':{'Z':1,'N':0,'V':0,'C':1},
            'confidence':'verified','claim':'conditional static loop contract',
            'conditions':['entry executes immediate counter setup and SETLB',
                          'valid aligned nonvolatile buffers; no fault/interrupt changes',
                          'cached loop code remains unchanged; no intervening LIR/LAR rewrite',
                          'value-preserving field copy requires nonoverlap'],
            'note':'logical cached-prefix edge, not a new ordinary PC-relative branch or OEM execution'}
