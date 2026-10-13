"""Fixed T18 ART actuator/setting-record vertical slice, not general tracing.

GNU provides decoding. These are static structural contracts with opaque
callee, runtime registry and UDF qualifications; no OEM instruction execution.
"""
import struct
try:
    from .inspect_olympus_oe import FormatError
    from .mn103_analysis import operands,memory
    from .t18_art_linkage import direct_candidates
except ImportError:
    from inspect_olympus_oe import FormatError
    from mn103_analysis import operands,memory
    from t18_art_linkage import direct_candidates


def bundle_layout(writeback,handoff):
    """Only nominated common-tail stores and adjacent key/value call arguments.

    No field names, arbitrary SSA, helper evaluation or image ownership inferred.
    Caller current-SP+4 is the156-byte buffer; callee's own SP is a different base.
    """
    fields=[]
    for i,row in enumerate(writeback):
        p=operands(row.operands)
        if len(p)!=2:continue
        try:dst=memory(p[1])
        except ValueError:continue
        if dst is None or dst.get('base')!='a0':continue
        if row.mnemonic!='mov' or set(dst)!={'base','displacement'}:
            raise FormatError('bundle word-store shape changed')
        previous=writeback[max(0,i-2):i]
        if not any(r.mnemonic=='mov' and r.operands=='(28,sp),a0' for r in previous):
            raise FormatError('bundle destination lacks nominated pointer reload')
        fields.append(dst['displacement'])
    if sorted(fields)!=list(range(0,156,4)):
        raise FormatError('bundle is not39 distinct word fields')
    result=[]
    for i,row in enumerate(handoff):
        if row.mnemonic!='call' or row.direct_target()!=0x292230:continue
        context=handoff[max(0,i-4):i];key=offset=None
        if any(r.mnemonic in ('call','calls') for r in context):
            raise FormatError('argument context crosses an opaque call')
        if not all(any(r.mnemonic=='mov' and r.operands==o for r in context)
                   for o in ('2,d1','d2,d0')):
            raise FormatError('bank/type argument contract drifted')
        for r in context:
            p=operands(r.operands)
            if r.mnemonic!='mov' or len(p)!=2:continue
            if p[1]=='a1':
                try:src=memory(p[0])
                except ValueError:src=None
                offset=src.get('displacement') if src and src.get('base')=='sp' else None
            if p[1]=='a0':
                try:key=int(p[0],0)
                except ValueError:key=None
        if key is None or offset is None or not 0<=key<=65535:
            raise FormatError('bundle argument origin unproved')
        result.append({'record_offset':offset-4,'setting_key':key,'call':hex(row.address)})
    if sorted(r['record_offset'] for r in result)!=sorted(fields) or len(result)!=39:
        raise FormatError('bundle handoff does not cover the same39 fields')
    return result


def evidence(data,decoded,guard):
    count=0;edges=[]
    def g(w,a,m,o):
        nonlocal count
        guard(decoded[w][a],m,o);count+=1
    def e(kind,source,target,origin,note,confidence='verified'):
        edges.append(dict(kind=kind,source=source,target=target,
                          origins=[hex(a) for a in origin],confidence=confidence,
                          coordinate='decoded #0 offsets/scoped static values',note=note))
    for w,a,m,o in [
      ('art_component_factory',0xdb5142,'mov',str(0x611401f4)+',a0'),
      ('art_component_factory',0xdb5151,'calls','(a1)'),
      ('art_actuator_ctor',0xd422ee,'mov',str(0x60fd2880)+',d0'),
      ('art_actuator_ctor',0xd422f4,'mov','d0,(a0)'),
      ('art_actuator_ctor',0xd42347,'add',str(0x60fd1b14)+',d2'),
      ('art_actuator_ctor',0xd42362,'mov','d1,(d0,a0)'),
      ('art_actuator_ctor',0xd4236c,'cmp','12,d2'),
      ('art_actuator_destructor',0xd423e7,'mov','1000,d0'),
      ('art_actuator_destructor',0xd423eb,'mov','d1,mdr'),
      ('art_actuator_destructor',0xd423ed,'divu','d0,d3'),
      ('art_actuator_destructor',0xd4240e,'add','164,a1'),
      ('art_actuator_destructor',0xd42413,'mov','(d2,a1),a1'),
      ('art_actuator_destructor',0xd42419,'calls','(a2)'),
      ('art_actuator_reset',0xd42496,'mov',str(0x61fb4274)+',a1'),
      ('art_actuator_slot0_wrapper',0xd424bb,'mov','(48,a2),a1'),
      ('art_actuator_slot0_wrapper',0xd424be,'calls','(a1)'),
      ('art_actuator_slot0',0xd42529,'call','0xd434f8,[d2,a2,a3],24'),
      ('art_actuator_snapshot',0xd43527,'mov','280,d0'),
      ('art_actuator_snapshot',0xd43556,'mov','(a2),d0'),
      ('art_actuator_snapshot',0xd43572,'add','164,a3'),
      ('art_setting_interface_ctor',0x7d90a8,'mov',str(0x60acb0dc)+',d0'),
      ('art_setting_getter',0x7d959b,'call','0x806c62,[d2],16'),
      ('art_setting_getter',0x7d95a2,'mov','d0,(a2)'),
      ('art_setting_setter',0x7da335,'call','0x807420,[d2,d3,a2],16'),
      ('art_setting_set_backend',0x80746b,'call','0x28f870,[],4'),
      ('art_callback_registry_init',0x2916e6,'mov',str(0x604317ac)+',a3'),
      ('art_callback_registry_init',0x2916f2,'movhu','(a3),d0'),
      ('art_callback_registry_init',0x291721,'add','60,a3'),
      ('art_callback_registry_init',0x291723,'cmp','439,d1'),
      ('art_callback_registry_lookup',0x29172d,'mov','63,d1'),
      ('art_callback_registry_lookup',0x291733,'mov',str(0x62245f48)+',a1'),
      ('art_setting_notification',0x291479,'add','24,a3'),
      ('art_setting_notification',0x291482,'calls','(a0)'),
      ('art_variant_hook8',0x295ce4,'mov','111,d0'),
      ('art_variant_hook8',0x295cec,'cmp','8,d1'),
      ('art_variant_hook8',0x295cf1,'call','0x2988f6,[d2],164'),
      ('art_variant_hook12',0x295d05,'cmp','12,d1'),
      ('art_variant_parallel_hook8',0x298c37,'mov','1,d0'),
      ('art_bundle_producer',0x297b53,'mov','d1,d2'),
      ('art_bundle_producer',0x297bce,'mov','(d2,a0),a0'),
      ('art_bundle_producer',0x297dfe,'mov','363,a0'),
      ('art_bundle_producer',0x297e06,'mov','d0,(36,sp)'),
      ('art_bundle_producer',0x297e8d,'mov','364,a0'),
      ('art_bundle_producer',0x29881a,'mov','d0,(32,a0)'),
      ('art_bundle_producer',0x298865,'mov','a3,(76,a0)'),
      ('art_bundle_producer',0x2988f3,'ret','[d2,d3,a2,a3],172'),
      ('art_bundle_handoff',0x2988fb,'call','0x297b51,[d2,d3,a2,a3],172'),
      ('art_bundle_handoff',0x298967,'mov','362,a0'),
      ('art_bundle_handoff',0x2989f6,'mov','872,a0'),
      ('art_bank_dispatch',0x292233,'udfu01','12,d0'),
      ('art_bank_dispatch',0x292243,'mov','a1,d1'),
      ('art_bank_dispatch',0x292246,'calls','(a2)')]:
        g(w,a,m,o)
    u32=lambda a:struct.unpack_from('<I',data,a)[0]
    if u32(0x112031c)!=49 or u32(0x1120320)!=0x60d622b4:
        raise FormatError('actual component49 keyed record drifted')
    if u32(0xaab0bc)!=0x607fa129 or u32(0xaab0c4)!=0x607f9549:
        raise FormatError('consumed SettingController slots drifted')
    if u32(0x22c514)!=0x60d624ff:
        raise FormatError('consumed object48 callback drifted')
    count+=3
    selected=[];start=0x41178c
    for i in range(12):
        gui_key,setting=struct.unpack_from('<II',data,0xfb1af4+8*i)
        matches=[start+60*j for j in range(439)
                 if struct.unpack_from('<H',data,start+60*j)[0]==setting]
        if len(matches)!=1:raise FormatError('ART setting descriptor not uniquely bound')
        record=matches[0]
        selected.append({'gui_selector_key':gui_key,'setting_key':setting,'record':hex(record),
                         'callback24':hex(u32(record+24)-0x60020020),
                         'candidate48':hex(u32(record+48)-0x60020020)})
    if selected[0]['setting_key']!=363 or selected[0]['callback24']!='0x295ce1' or selected[2]['setting_key']!=364 or selected[2]['callback24']!='0x295cfa':
        raise FormatError('nominated ART variant callbacks drifted')
    if any(u32(int(r['record'],16)+20)!=0 for r in selected):
        raise FormatError('selected scalar optional-value callback drifted')
    count+=13
    for key,record,label in [(0x010202,0x21fa78,'SettingController::setSetting'),
                              (0x010203,0x21fa7c,'SettingController::getSetting')]:
        # Independently checked root/group/name geometry, not handler ordinals.
        bank=u32(0x2211a0)-0x61d87d60
        names=u32(bank+4)-0x61d87d60
        if names+4*((key&255)-1)!=record:raise FormatError('setting metadata geometry drifted')
        p=u32(record)-0x60020020
        if data[p:p+len(label)+1]!=label.encode()+b'\0':raise FormatError('setting method label drifted')
        count+=1
    label_row=decoded['art_actuator_destructor'][0xd423a8]
    p=int(operands(label_row.operands)[0])-0x60020020
    z=data.find(b'\0',p,p+180)
    if z<0 or b'Art_Select_Menu_Actuator' not in data[p:z]:raise FormatError('actual actuator label drifted')
    count+=1
    producer=list(decoded['art_bundle_producer'].values())
    layout=bundle_layout([r for r in producer if r.address>=0x2987e0],
                         list(decoded['art_bundle_handoff'].values()))
    if {r['record_offset']:r['setting_key'] for r in layout}[32]!=362 or {r['record_offset']:r['setting_key'] for r in layout}[76]!=872:
        raise FormatError('selected bundle field/key mapping drifted')
    targets=[u32(0x440438+4*i)-0x60020020 for i in range(66)]
    if targets[8]!=0x297dfb or targets[12]!=0x297e8a or not all(t in decoded['art_bundle_producer'] for t in targets):
        raise FormatError('bounded selector jump table drifted')
    count+=3
    # Only this new, independently grounded target; old source caller search
    # is never repeated. One known call does not exclude indirect/other modules.
    if direct_candidates(data,0x297b51,16)!=[0x2988fb]:
        raise FormatError('new bundle direct-reference observation drifted')
    e('conditional_component_record','ART GUI candidate417/component49','Art_Select_Menu_Actuator',
      [0x117a56c,0x112031c,0xd42294,0xd422ee,0xd423a8],
      'actual keyed factory/constructor/label; outer GUI lookup UDF and runtime type remain qualified','hypothesized')
    e('native_setting_cache','12 ART-associated setting keys','actuator+164 twelve word values',
      [0xfb1af4,0xd42359,0xd42362,0xd4236c],
      'constructor-path getter output/cache; later helper mutations and actual values unobserved')
    e('conditional_setting_restore','actuator cached selected value','SettingController::setSetting',
      [0xd42413,0xd42419,0xaab0bc,0x7da335],
      'temporary editing lifecycle, not named saved looks, nonvolatile persistence or firmware recovery')
    e('registered_art_callback','setting363/record0x414900+24','0x295ce1',
      [0x2916e6,0x291721,0x414918,0x291479,0x291482],
      'actual per-key descriptor/callback consumer; initialization/runtime registry and normal-callee assumptions')
    e('selector_bound_update','setting111==8 in callback363','0x2988f6 -> 0x297b51 selector8',
      [0x295ce4,0x295cec,0x295cf1,0x2988fb,0x297b53],
      'ART-associated registered setting update; numeric selector is not an assigned stock filter name')
    e('configuration_record','selector8 / setting363','156-byte39-word bundle',
      [0x440458,0x297dfe,0x297e06,0x29881a,0x2988f3],
      'typed local record writes; opaque getters/UDF bank semantics/value lifetimes remain conditional; not old35-byte source')
    e('typed_scalar_handoff','bundle+32/+76','outgoing settings362/872',
      [0x29881a,0x298865,0x298967,0x2989f6,0x292246],
      '39 matching key/value arguments, not identified ISP/JPEG consumer; variant/extra semantic names remain unassigned')
    e('parallel_context_candidate','descriptor363+48','bank-byte1 hook0x298c24',
      [0x414930,0x298c37,0x298c39],
      'pointer/body coherence only; exact+48 dispatcher and RAW/capture ownership not proved','hypothesized')
    return edges,count,{'setting_map':selected,'bundle_bytes':156,'bundle_words':39,
                        'bundle_handoffs':layout,'selected_style_cases':[8,12],
                        'source35_alias':'unknown','pixel_consumer':'unknown',
                        'raw_shared_record':'unknown; new direct-target probe found known caller only',
                        'result':'new ART-associated configuration-record graph; G2 still incomplete'}
