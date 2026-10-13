"""Small T18 reference filters; GNU supplies decoding and synthetic encodings.

Byte hits are candidates, not code/type/GUI identities. No OEM execution,
general alias analysis, ISA implementation, or inferred method ordinals.
"""
import struct
import subprocess
import tempfile
from pathlib import Path
try:
    from .inspect_olympus_oe import FormatError
    from .probe_oe_executable import disassemble
    from .mn103_analysis import operands
except ImportError:
    from inspect_olympus_oe import FormatError
    from probe_oe_executable import disassemble
    from mn103_analysis import operands


def direct_candidates(data, target, limit=32):
    """GNU2.44's four audited PC-relative forms, before boundary qualification.

    Displacement is relative to instruction START. Embedded data deliberately
    remains a candidate; only independent context can establish a real call.
    """
    if not 0 <= target <= 0xffffffff:
        raise FormatError('target outside u32')
    hits=[]
    for opcode,offset,size,width in [(b'\xcd',1,5,2),(b'\xdd',1,7,4),
                                     (b'\xfa\xff',2,4,2),(b'\xfc\xff',2,6,4)]:
        cursor=0
        while (cursor:=data.find(opcode,cursor))>=0:
            if cursor+size<=len(data):
                delta=int.from_bytes(data[cursor+offset:cursor+offset+width],
                                     'little',signed=True)
                if (cursor+delta)&0xffffffff==target:
                    hits.append(cursor)
                    if len(hits)>limit:
                        raise FormatError('reference bound exceeded')
            cursor+=1
    return sorted(set(hits))


def qualify_virtual(rows, slot, producers, scalar=False):
    """A nominated return-A0 -> vptr -> slot -> CALLS fragment only.

    Producer identity/return contract is curated separately. This filter does
    not prove the runtime vptr, reachability, ABI or absence of later mutation.
    A setter may have one immediate/CLR D0 between vptr and slot loads.
    """
    if len(rows)<4 or rows[0].mnemonic!='call' or rows[0].direct_target() not in producers:
        return None
    p=operands(rows[1].operands)
    if rows[1].mnemonic!='mov' or len(p)!=2 or p[0]!='(a0)' or p[1] not in ('a0','a1','a2','a3'):
        return None
    index=2;value=None
    if scalar and index<len(rows):
        r=rows[index];q=operands(r.operands)
        if r.mnemonic=='clr' and q==['d0']:
            value=0;index+=1
        elif r.mnemonic=='mov' and len(q)==2 and q[1]=='d0':
            try:value=int(q[0],0)&0xffffffff
            except ValueError:return None
            index+=1
    if len(rows)<index+2:return None
    r,c=rows[index:index+2];q=operands(r.operands)
    if r.mnemonic!='mov' or len(q)!=2 or q[0]!=f'({slot},{p[1]})' or q[1] not in ('a0','a1','a2','a3'):
        return None
    if c.mnemonic!='calls' or c.operands!=f'({q[1]})':return None
    return {'producer_call':hex(rows[0].address),'slot_load':hex(r.address),
            'indirect_call':hex(c.address),'scalar':value,
            'qualification':'curated producer/type contract required; conditional runtime target'}


def panel_reference_probe(data,objdump):
    """Fixed two getters/two slots; no recursive expansion or new keys."""
    refs=[]
    for target in (0x74a27f,0x775b02):
        hits=direct_candidates(data,target,4)
        for at in hits:
            r=disassemble(objdump,data[at:at+10],at)[0]
            if r.direct_target()!=target:raise FormatError('GNU call sieve drift')
        refs.append({'target':hex(target),'candidates':[hex(h) for h in hits]})
    literal=struct.pack('<I',0x61fa729c);cursor=0;absolute=[]
    while (cursor:=data.find(literal,cursor))>=0:
        absolute.append(hex(cursor));cursor+=1
        if len(absolute)>4:raise FormatError('absolute field bound exceeded')
    root=Path(objdump).resolve().parents[1]
    assembler=root/'gas/as-new';objcopy=root/'binutils/objcopy'
    fixture=Path(__file__).resolve().parents[1]/'tests/fixtures/mn103_virtual_access.s'
    result=[]
    with tempfile.TemporaryDirectory(prefix='ep7-t18-original-',dir='/tmp') as tmp:
        tmp=Path(tmp)
        for slot in (816,820):
            obj,raw=tmp/'original.o',tmp/'original.bin'
            for argv in ([str(assembler),'--defsym',f'panel_slot={slot}','-o',str(obj),str(fixture)],
                         [str(objcopy),'-O','binary','-j','.text',str(obj),str(raw)]):
                subprocess.run(argv,capture_output=True,check=True,timeout=30)
            synthetic=raw.read_bytes();rows=disassemble(objdump,synthetic,0)
            if len(rows)!=32:raise FormatError('original fixture shape drift')
            ends=[r.address for r in rows[::2]]+[len(synthetic)];hits=[]
            for lo,hi in zip(ends,ends[1:]):
                pattern=synthetic[lo:hi];cursor=0
                while (cursor:=data.find(pattern,cursor))>=0:
                    hits.append(cursor);cursor+=1
                    if len(hits)>64:raise FormatError('slot-reference bound exceeded')
            result.append({'slot':slot,'raw_pattern_hits':len(hits)})
    return {'absolute_u32_candidates':absolute,'direct_getter_candidates':refs,
            'virtual_pattern_counts':result,
            'limits':'#0 only; four direct forms/adjacent slot-load CALLS; no completeness or type proof'}


def evidence(data,decoded,objdump,guard):
    """Fixed, manually nominated edges; never auto-close a style/pixel chain."""
    count=0;edges=[]
    def g(w,a,m,o):
        nonlocal count
        guard(decoded[w][a],m,o);count+=1
    def edge(kind,source,target,origins,note):
        edges.append(dict(kind=kind,source=source,target=target,
                          origins=[hex(a) for a in origins],confidence='verified',
                          coordinate='decoded #0 offsets/scoped static values',note=note))
    for w,a,m,o in [
        ('panel_interface_getter',0x7daae6,'call','0x7dab10,[],0'),
        ('panel_interface_getter',0x7daaf1,'mov','d0,(0x61fa96b4)'),
        ('panel_interface_ctor',0x7dab10,'mov',str(0x60acb270)+',d0'),
        ('panel_interface_ctor',0x7dab16,'mov','d0,(a0)'),
        ('panel_interface_ctor',0x7dab1b,'retf','[],0'),
        ('panel_field_getter',0x74a27f,'movhu','(0x61fa729c),d0'),
        ('panel_backend_getter',0x775b02,'call','0x74a27f,[],0'),
        ('panel_get_entry',0x7dfbeb,'call','0x775b02,[],4'),
        ('panel_get_entry',0x7dfc09,'mov','d2,d0'),
        ('panel_get_entry',0x7dfc0a,'exthu','d0'),
        ('panel_get_entry',0x7dfc0b,'ret','[d2,a2],16'),
        ('panel_ui_bridge',0xcdd289,'call','0x7daaab,[],4'),
        ('panel_ui_bridge',0xcdd290,'ret','[a2],12'),
        ('panel_state_consumer_a',0xcbffbb,'cmp','1,d0'),
        ('panel_state_consumer_a',0xcbffbd,'bne','0xcbffd3'),
        ('panel_state_consumer_a',0xcbffc6,'mov','d0,(a0)'),
        ('panel_state_consumer_a',0xcbffcf,'mov','d0,(192,a2)'),
        ('panel_state_consumer_b',0xccb343,'cmp','1,d0'),
        ('panel_state_consumer_b',0xccb345,'bne','0xccb35b'),
        ('panel_state_consumer_b',0xccb357,'mov','d0,(192,a3)'),
        ('raw_art_request_fields',0x764d44,'mov','d2,(228,a3)'),
        ('raw_art_request_fields',0x764d48,'mov','d3,(224,a3)'),
        ('raw_art_request_fields',0x764d3a,'mov','6836,d1'),
        ('raw_art_request_fields',0x764d74,'mov','(4,sp),d0'),
        ('raw_art_request_fields',0x764d76,'mov','d0,(a0)'),
        ('raw_art_request_fields',0x764d79,'mov',str(0x60785263)+',d0'),
        ('raw_art_request_fields',0x764d7f,'mov','d0,(4,a0)'),
        ('raw_art_request_fields',0x764d86,'mov','a3,(8,a0)'),
        ('raw_art_request_fields',0x764d95,'movhu','d0,(12,a0)'),
        ('raw_art_request_fields',0x764da6,'movhu','d0,(14,a0)'),
        ('raw_art_result_callback',0x76524a,'cmp','1,d1'),
        ('raw_art_result_callback',0x765269,'mov','6836,d0'),
        ('raw_art_result_callback',0x765296,'mov','(a0),d2'),
        ('raw_art_result_callback',0x7652a4,'mov','d2,a2'),
        ('raw_art_result_callback',0x7652a6,'calls','(a2)'),
        ('raw_art_operation_callback',0x7e97ab,'cmp','456,d2'),
        ('raw_art_operation_callback',0x7e97e8,'cmp','456,d2'),
        ('gui_candidate_factory',0xe2ce94,'udfu01','12,d1'),
        ('gui_candidate_factory',0xe2ce99,'add',str(0x6119fadc)+',a1'),
        ('gui_candidate_factory',0xe2cebf,'udfu01','24,d0'),
        ('gui_candidate_factory',0xe2cef9,'call','0xe2cb3a,[d3,a2,a3],52'),
        ('gui_record_ctor',0xe2cba0,'mov','(20,a0),a0'),
        ('gui_record_ctor',0xe2cbad,'mov','sp,a0'),
        ('gui_record_ctor',0xe2cbae,'mov','a2,(24,a3)'),
        ('gui_record_ctor',0xe2cbc2,'calls','(a2)')]:
        g(w,a,m,o)
    u32=lambda a:struct.unpack_from('<I',data,a)[0]
    if u32(0xaab580)!=0x607ffb5e or u32(0xaab584)!=0x607ffbcb:
        raise FormatError('Shooting constructor-path slots drifted')
    count+=2
    # Fragment qualification does not prove opaque nested callees preserve
    # scalar registers, nor that the runtime object retains its constructor vptr.
    qualified=[]
    nominations=[('panel_debug_get',0x7c6033,820,False),
                 ('panel_state_consumer_a',0xcbffab,820,False),
                 ('panel_state_consumer_b',0xccb315,820,False),
                 ('panel_state_consumer_b',0xccb333,820,False),
                 ('panel_gui_start_fragment',0xe3b7e9,816,True),
                 ('panel_gui_mode_change',0xe3b90a,816,True),
                 ('panel_gui_exit_fragment',0xe3ba7f,816,True)]
    for w,at,slot,scalar in nominations:
        rows=list(decoded[w].values());index=next(i for i,r in enumerate(rows) if r.address==at)
        q=qualify_virtual(rows[index:index+5],slot,{0x7daaab,0xcdd277},scalar)
        if q is None:raise FormatError('curated virtual fragment drifted')
        qualified.append(q);count+=1
    if [q['scalar'] for q in qualified[-3:]]!=[1,1,0]:
        raise FormatError('ART entry/exit input drifted')
    # Direct code-referenced short labels, not global string discovery.
    for w,at,label in [('panel_gui_start_fragment',0xe3b7cd,'SsMenuLv_ArtSelect_ModeStart_Entry'),
                       ('panel_gui_mode_change',0xe3b8f6,'SsMenuLv_ArtSelect_ModeChange_Entry'),
                       ('panel_gui_exit_fragment',0xe3ba6b,'SsMenuLv_ArtSelect_Exit'),
                       ('scene_neighbor_counterexample',0xe3b96d,'SsMenuLv_ScnSelect_ModeChange_Entry')]:
        row=decoded[w][at]
        if row.mnemonic!='mov':raise FormatError('label pointer is not MOV')
        ptr=(int(operands(row.operands)[0],0)&0xffffffff)-0x60020020
        if not 0<=ptr<len(data):raise FormatError('label pointer outside view')
        end=data.find(b'\0',ptr,min(ptr+180,len(data)))
        if end<ptr or label.encode() not in data[ptr:end]:raise FormatError('direct label drifted')
        count+=1
    # Independent physical adjacency/count agreement, NOT UDF admission.
    header=0x117fabc;start=u32(header+4)-0x60020020
    end=u32(header+16)-0x60020020;number=struct.unpack_from('<H',data,header+8)[0]
    if u32(header)!=8 or (start,end,number)!=(0x117a2fc,0x117cb34,429) or end-start!=24*number:
        raise FormatError('physical catalog candidate drifted')
    if u32(0x117a56c)!=417 or u32(0x117a56c+20)!=0:
        raise FormatError('selected candidate GUI record drifted')
    count+=2
    probe=panel_reference_probe(data,objdump)
    if probe['absolute_u32_candidates']!=['0x74a278','0x74a281'] or [r['raw_pattern_hits'] for r in probe['virtual_pattern_counts']]!=[6,7]:
        raise FormatError('fixed panel-reference observation drifted')
    if [r['candidates'] for r in probe['direct_getter_candidates']]!=[['0x775b02'],['0x7dfbeb']]:
        raise FormatError('fixed direct-getter observation drifted')
    edge('conditional_virtual','constructor-path Shooting slots816/820','set/get ArtPanelFlag',
         [0x7dab16,0xaab580,0xaab584],
         'actual consumed offsets, not method ordinals; later mutation/runtime type unobserved')
    edge('gui_state_input','ART selection entry/change/exit','panel setter inputs1/1/0',
         [0xe3b7f2,0xe3b913,0xe3ba88],
         'direct GUI labels and literal arguments; complete setter value join requires opaque-callee register preservation')
    edge('control_word_read','u16 at 0x61fa729c','Shooting getArtPanelFlag',
         [0x74a27f,0x775b02,0x7dfbeb],
         'getter return path subject to normal nested returns/state assumptions; no universal-reader claim')
    edge('state_gate','getArtPanelFlag==1 and setting280==3','output fields32/36/192',
         [0xcbffbb,0xcbffc6,0xcbffcf,0xccb343,0xccb357],
         'state/control output, not independently bound style source or pixel buffer; other predicate semantics unknown')
    edge('unused_scalar','0xccb322 getter result','overwritten by following setting query',
         [0xccb322,0xccb327],
         'do not count the first call in this function as a value-dependent consumer')
    edge('callback_record','RAW actor+228/+224','callback7e9761 and context',
         [0x7e9225,0x764d44,0x764d48,0x7652a4,0x7652a6],
         'actual request/context fields; not evidence of capture-time shared effects')
    edge('typed_request_header','RAW actor+236 request','operation/callback/self/u16 routes',
         [0x764d76,0x764d7f,0x764d86,0x764d95,0x764da6],
         '1644-size-shaped allocation; offsets12/14 are halfwords, distinct from copied effect word+12')
    edge('result_copy','RAW callback event1/input','actor+252 region,6836-byte argument',
         [0x76524a,0x765269,0x76526c],
         'generic relocated copy identity reused; size/contents/ownership not established as style record')
    edge('conditional_catalog','GUI factory D0=8,D1=417','physical candidate record0x117a56c',
         [0xe3b91b,0xe3b91d,0xe2ce99,0x117fabc,0x117a56c],
         'physical adjacency/count fits24-byte grouping; UDF12/24 semantics remain unadmitted, runtime selection unproved')
    edges[-1]['confidence']='hypothesized'
    edge('nullable_callback','GUI metadata word+20','constructed object+24/CALLS target',
         [0xe2cba0,0xe2cbae,0xe2cbc2],
         'six caller words are distinct from >=35-byte effect source; selected417 candidate has0 callback')
    edge('conditional_record_copy','selected pointer/current caller SP+4','six ctor words/current callee SP+56',
         [0xe2cee8,0xe2ceec,0xe2ceee,0xe2cef4,0xe2cef9,0xe2cb74],
         '24-byte local copy contract reused; CALL frame52 joins SP+4 to SP+56; upstream UDF lookup remains stopped')
    edge('negative_identity','nearby six-case1431..1436->438..443','SCN-labelled controller selection',
         [0xe3b96d,0xe3b9c9,0xe3b9e2],
         'direct referenced SCN labels prevent relabeling nearby cases as ART presets')
    return edges,count,{'reference_probe':probe,'qualified_virtual_fragments':qualified,
                        'physical_catalog_candidate':{'domain':8,'count':429,'stride_bytes':24,
                            'runtime_lookup':'unadmitted UDF12/24; no semantic upgrade'},
                        'source_effect_writer':'unknown','processing_consumer':'unknown',
                        'result':'ART GUI state linkage and distinct control records, no closed style pipeline'}
