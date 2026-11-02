#!/usr/bin/env python3
"""Original editor-only split sizing. No OEM input, package or release writer.

The old simulator layout and hypothetical adjacent link are analysis views,
never qualification of additional firmware space. All products require /tmp.
"""
import argparse
import json
import os
from pathlib import Path

from ep7_color_min import require
from ep7_t27_editor_only_source import materialize, V4
from ep7_t27_size_study import run, labels, groups, V4_GROUPS, CAPACITY, MIRROR_BYTES
from ep7_t27_candidate import LAYOUT


def build(upstream, out):
    upstream, out = Path(upstream).resolve(), Path(out).resolve()
    require(Path('/tmp') in out.parents and not out.exists(), 'Fresh private /tmp output required')
    require(run(['git','-C',upstream,'rev-parse','HEAD']).strip() ==
            '539fcf1fa9eda5fdef8ede4deeab94a4691d94c3', 'Wrong reference revision')
    require(not run(['git','-C',upstream,'status','--porcelain']).strip(),
            'External tracked tools are modified')
    out.mkdir(mode=0o700)
    source = materialize(out/'source')
    tool = upstream/'toolchains/mn103-patch-build'
    assembler, linker, copy, nm = (tool/'gas/as-new', tool/'ld/ld-new',
                                 tool/'binutils/objcopy', tool/'binutils/nm-new')
    versions = {str(p.relative_to(tool)):run([p,'--version']).splitlines()[0]
                for p in (assembler, linker, copy, nm)}
    require(all(v.endswith(' 2.45') for v in versions.values()), 'Qualified GNU 2.45 required')
    symbols = json.loads((source/'symbols.json').read_text())
    objects = []
    for name in ('core','api','editor'):
        obj = out/(name+'.o')
        run([assembler,'-o',obj,source/(name+'.s')]);objects.append(obj)
    oldobj, oldelf, oldbin = out/'v4.o', out/'v4.elf', out/'v4.bin'
    run([assembler,'-o',oldobj,V4/'hook.s'])
    oldsyms = json.loads((V4/'symbols.json').read_text())
    run([linker,'-Ttext','0x60210940','-e','_start',
         *[f'--defsym={k}={v:#x}' for k,v in oldsyms.items()],'-o',oldelf,oldobj])
    run([copy,'-O','binary','-j','.text',oldelf,oldbin])
    require(oldbin.stat().st_size==1276,'Frozen v4 changed')
    oldlabels=labels(nm,oldelf)
    oldgroups=groups(V4_GROUPS,oldlabels,0x60210940+1276)
    pure_a={'_start','cell_index','decode_cell','publish','lightness_steps','hue_steps'}
    pure_b={'wifi_write','wifi_read','id_parse','value_parse','canonical_hex'}
    result=dict(versions=versions,old_v4_groups=oldgroups,
        split=dict(A_unchanged_functions=sum(r['bytes'] for r in oldgroups if r['function'] in pure_a),
                   B_only_functions=sum(r['bytes'] for r in oldgroups if r['function'] in pure_b),
                   shared_app_and_validation=sum(r['bytes'] for r in oldgroups if r['function'] not in pure_a|pure_b),
                   mirror=MIRROR_BYTES),layouts=[])
    lab_symbols = None
    for layout, relax in (('lab',False),('adjacent',False),('adjacent',True)):
        tag=layout+('-relax' if relax else '')
        script, elf = out/(tag+'.ld'), out/(tag+'.elf')
        chunks=['.text 0x60210940 : { *(.text) } :code']
        for name,address,_ in LAYOUT:
            where=hex(address) if layout=='lab' else 'ALIGN(4)'
            chunks.append(f'.ep7_{name} {where} : {{ *(.ep7_{name}) }} '
                          f':{"state" if name=="state" else "code"}')
        script.write_text('PHDRS { code PT_LOAD FLAGS(5); state PT_LOAD FLAGS(6); }\nSECTIONS {\n'+
                          '\n'.join(chunks)+'\n}\n')
        run([linker,'-T',script,'-e','_start',*(['--relax'] if relax else []),
             *[f'--defsym={k}={v:#x}' for k,v in symbols.items()],'-o',elf,*objects])
        syms=labels(nm,elf);sizes={}
        for name in ('core',*[r[0] for r in LAYOUT]):
            section='.text' if name=='core' else '.ep7_'+name
            target=out/(tag+'-'+name+'.bin')
            run([copy,'-O','binary','-j',section,elf,target]);sizes[name]=target.stat().st_size
        raw=sum(sizes.values());span=raw if layout=='lab' else syms['v5_state_ram']+sizes['state']-0x60210940
        row=dict(layout=layout,relax=relax,sections=sizes,raw_bytes=raw,
            padded_span=None if layout=='lab' else span,total_with_mirror=span+MIRROR_BYTES,
            capacity=CAPACITY,deficit=span+MIRROR_BYTES-CAPACITY,
            fits=span+MIRROR_BYTES<=CAPACITY,placement_qualified=False,
            limit='Lab mapping is prior simulation only; adjacent link ignores fixed mirror/guards and is unexecuted')
        if layout=='lab':
            lab_symbols = syms
            row['A_functions']=groups(('_start','cell_index','a_apply','validate_gui','decode_cell',
                'publish','lightness_steps','hue_steps'),syms,0x60210940+sizes['core'])
            require(syms['hue_steps']%2==syms['lightness_steps']%2==0,'Halfword table alignment')
            # The decoder contains only local branches and constants; it must
            # remain byte-identical despite relinking its callers.
            a,b=syms['decode_cell']-0x60210940,oldlabels['decode_cell']-0x60210940
            code=(out/(tag+'-core.bin')).read_bytes()
            require(code[a:a+53]==oldbin.read_bytes()[b:b+53],'Persistent decoder changed')
            row['persistent_decoder_bytes_identical']=True
        result['layouts'].append(row)
    # These are identified exclusive pieces, not implemented deletions or
    # proven net savings. INFO/S-ALL entry and native reset need safe handling.
    optional = dict(ALL=lab_symbols['v5_numeric_detour']-lab_symbols['v5_upper_detour'],
        held_OK_stub=lab_symbols['v5_set']-lab_symbols['v5_default'],
        held_OK_scope=lab_symbols['scope_set']-lab_symbols['scope_default'],
        held_OK_table_entry=4)
    gross = sum(optional.values())
    result['optional_features'] = dict(exclusive_gross_bytes=optional,
        gross_total=gross,implemented=False,net_saved_bytes=None,
        deficit_even_if_gross_removed_free=result['layouts'][0]['deficit']-gross,
        limitation='Disabling INFO/ALL and preventing native S reset need protective code; no safe net saving proved')
    result.update(release_manifest_generated=False,installer_created=False,
        storage_format='0xe741CCVV; same 48 part-1 cells; same native typed publication',
        removed_hooks=[hex(a) for a in (0x60bd2a60,0x60bd2a8f,0x60bd2aba,0x60bd2785,0x60888b35)],
        retained_hooks=[hex(a) for a in (0x603b14f3,0x602cbcb5)],
        required_removal='All network parser/read/write and application marker hooks revert to exact stock bytes')
    (out/'study.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--upstream',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();r=build(a.upstream,a.out)
    print(json.dumps(dict(split=r['split'],layouts=r['layouts']),indent=2))


if __name__=='__main__':main()
