"""Fixed T19 native-effect -> existing32-byte receiver proof annotations.

Symbolic mask composition is non-executing static analysis. No interpreter,
OEM simulation, arbitrary tracing, UDF admission or rendering inference.
"""
import struct
try:
    from .inspect_olympus_oe import FormatError
except ImportError:
    from inspect_olympus_oe import FormatError


def summarize_flag_block(rows, entry, join):
    """One acyclic nominated word update: (input & keep) | set.

    Only exact a2/d0 load/store, immediate AND/OR and direct BRA are admitted.
    Never evaluates a runtime value, helper, conditional or machine state.
    """
    by = {r.address: r for r in rows}
    nxt = {a.address: b.address for a, b in zip(rows, rows[1:])}
    keep, bits, loaded, stored = 0xffffffff, 0, False, False
    visited = set()
    at = entry
    while at != join:
        if at in visited or len(visited) >= 12 or at not in by:
            raise FormatError('flag block escaped nominated acyclic bounds')
        visited.add(at)
        r = by[at]
        if r.mnemonic == 'bra' and r.direct_target() is not None:
            at = r.direct_target()
            continue
        if r.mnemonic == 'mov' and r.operands == '(a2),d0' and not loaded:
            loaded = True
        elif r.mnemonic in ('and', 'or') and loaded and not stored:
            p = r.operands.split(',')
            if len(p) != 2 or p[1] != 'd0':
                raise FormatError('flag arithmetic register drifted')
            try:
                value = int(p[0], 0) & 0xffffffff
            except ValueError as e:
                raise FormatError('flag mask is not an immediate') from e
            if r.mnemonic == 'and':
                keep &= value
                bits &= value
            else:
                bits |= value
        elif r.mnemonic == 'mov' and r.operands == 'd0,(a2)' and loaded and not stored:
            stored = True
        else:
            raise FormatError('flag block contains an opaque/unsupported effect')
        if at not in nxt:
            raise FormatError('flag block ends before join')
        at = nxt[at]
    if loaded != stored:
        raise FormatError('flag load/store contract incomplete')
    return {'keep_mask': hex(keep), 'set_mask': hex(bits)}


def evidence(data, decoded, guard):
    n = 0
    def g(w, a, m, o):
        nonlocal n
        guard(decoded[w][a], m, o)
        n += 1
    for check in [
        ('t19_effect_flags', 0x3cab19, 'mov', '(28,a0),a3'),
        ('t19_effect_flags', 0x3cab1c, 'mov', 'a1,a2'),
        ('t19_effect_flags', 0x3cab1d, 'mov', '24785,a1'),
        ('t19_effect_flags', 0x3cab22, 'movbu', '(a1),d0'),
        ('t19_effect_flags', 0x3cab28, 'cmp', '9,d0'),
        ('t19_effect_flags', 0x3cab2d, 'mov', '1616108800,a0'),
        ('t19_effect_flags', 0x3caba9, 'and', '-16385,d0'),
        ('t19_effect_flags', 0x3cabaf, 'mov', 'd0,(a2)'),
        ('t19_effect_flags', 0x3cabb0, 'and', '-65537,d0'),
        ('t19_effect_flags', 0x3cabc8, 'or', '8388608,d0'),
        ('t19_effect_flags', 0x3cabd1, 'and', '-8388609,d0'),
        ('t19_effect_flags', 0x3cabd8, 'ret', '[a2,a3],20'),
        ('t19_packet_A', 0x3c6138, 'mov', '12,a1'),
        ('t19_packet_A', 0x3c613c, 'call', '0x3cab19,[a2,a3],20'),
        ('t19_packet_A', 0x3c617f, 'movhu', 'd0,(16,a2)'),
        ('t19_packet_B', 0x3c8a67, 'mov', 'a0,a3'),
        ('t19_packet_B', 0x3c8a6c, 'mov', 'a1,a2'),
        ('t19_packet_B', 0x3c8a84, 'mov', '1614714417,d0'),
        ('t19_packet_B', 0x3c8a8a, 'mov', 'd0,(a2)'),
        ('t19_packet_B', 0x3c8a99, 'mov', '12,a1'),
        ('t19_packet_B', 0x3c8a9d, 'call', '0x3cab19,[a2,a3],20'),
        ('t19_packet_B', 0x3c8ac2, 'call', '0x3ca8e9,[d2,a2],12'),
        ('t19_packet_B', 0x3c8ac7, 'movhu', 'd0,(16,a2)'),
        ('t19_packet_B', 0x3c8ace, 'ret', '[a2,a3],16'),
        ('t19_packet_A_handoff', 0x3d27f0, 'add', '16,a2'),
        ('t19_packet_A_handoff', 0x3d2807, 'mov', '32,d1'),
        ('t19_packet_A_handoff', 0x3d2812, 'call', '0x3c60fe,[d2,d3,a2,a3],24'),
        ('t19_packet_A_handoff', 0x3d281c, 'mov', 'a2,a0'),
        ('t19_packet_A_handoff', 0x3d281e, 'call', '0x3337cb,[d2,d3,a2,a3],44'),
        ('t19_packet_A_handoff', 0x3d2825, 'mov', 'd0,(36,a3)'),
        ('t19_packet_B_handoff', 0x3d2b01, 'add', '-356,sp'),
        ('t19_packet_B_handoff', 0x3d2b0e, 'add', '324,a0'),
        ('t19_packet_B_handoff', 0x3d2b12, 'mov', 'a0,(12,sp)'),
        ('t19_packet_B_handoff', 0x3d2b7f, 'mov', '(12,sp),a0'),
        ('t19_packet_B_handoff', 0x3d2b82, 'mov', '32,d1'),
        ('t19_packet_B_handoff', 0x3d2b8c, 'mov', '(12,sp),a1'),
        ('t19_packet_B_handoff', 0x3d2b8e, 'call', '0x3c8a67,[a2,a3],16'),
        ('t19_packet_B_handoff', 0x3d2b95, 'mov', '(12,sp),a0'),
        ('t19_packet_B_handoff', 0x3d2b99, 'call', '0x3337cb,[d2,d3,a2,a3],44'),
        ('t19_packet_B_handoff', 0x3d2ba0, 'mov', 'd0,(60,sp)'),
        ('t19_type_origin', 0x3ca915, 'movhu', '(206,a2),d1'),
        ('t19_type_origin', 0x3ca919, 'mov', '32,d0'),
        ('t19_type_origin', 0x3ca91f, 'mov', '16,d0'),
        ('t19_type_origin', 0x3ca921, 'mov', '256,d2'),
        ('t19_type_origin', 0x3ca92e, 'mov', '4096,d1'),
        ('t19_type_origin', 0x3ca931, 'and', '240,d0'),
        ('t19_tuple_origin', 0x3caa50, 'mov', 'a2,a0'),
        ('t19_tuple_origin', 0x3caa51, 'call', '0x329277,[a2,a3],8'),
        ('t19_tuple_head', 0x3292b4, 'mov', '1,d0'),
        ('t19_tuple_head', 0x3292b6, 'movbu', 'd0,(a0)'),
        ('t19_tuple_join', 0x3294ac, 'movbu', 'd0,(1,a0)'),
        ('t19_tuple_join', 0x3294b1, 'movhu', 'd0,(2,a0)'),
        ('t19_effect_program', 0x3c10b0, 'mov', '24785,a1'),
        ('t19_effect_program', 0x3c0c5b, 'mov', '3264,a3'),
        ('t19_effect_program', 0x3c0c62, 'mov', '40,d1'),
        ('t19_effect_program', 0x3c0c85, 'mov', '1616097560,a0'),
        ('t19_effect_program', 0x3c0cb4, 'mov', '2,d1'),
        ('t19_effect_program', 0x3c0cd9, 'movhu', 'd1,(a3)'),
        ('t19_effect_program', 0x3c0cdd, 'mov', '16,d0'),
        ('t19_effect_program', 0x3c0d99, 'mov', '6,d2'),
        ('t19_effect_program', 0x3c0dc0, 'movhu', 'd2,(a3)'),
        ('t19_effect_program', 0x3c0dc7, 'mov', '19,d0'),
        ('t19_effect_program', 0x3c10b3, 'add', 'd3,a1'),
        ('t19_effect_program', 0x3c10b5, 'movbu', '(a1),d0'),
        ('t19_effect_program', 0x3c10c6, 'mov', '1616097520,a0'),
        ('t19_effect_program', 0x3c10d5, 'mov', '32832,d0'),
        ('t19_effect_program', 0x3c1116, 'mov', '32896,d0'),
        ('t19_effect_program', 0x3c1123, 'mov', '32897,d0'),
        ('t19_effect_program', 0x3c1136, 'movhu', 'd0,(8,a0)'),
        ('t19_effect_program', 0x3c1139, 'mov', '4352,d0'),
        ('t19_effect_program', 0x3c12d6, 'ret', '[d2,d3,a2,a3],48'),
        ('t19_onehot_effect', 0x2df074, 'mov', '24785,a1'),
        ('t19_onehot_effect', 0x2df0d0, 'movbu', '(a1),d1'),
        ('t19_onehot_effect', 0x2df0da, 'add', '-1,d0'),
        ('t19_onehot_effect', 0x2df0dc, 'asl', 'd0,d1'),
        ('t19_onehot_effect', 0x2df0df, 'and', '511,d0'),
        ('t19_onehot_effect', 0x2df0e3, 'movhu', 'd0,(72,sp)'),
        ('t19_mirror_commit', 0x2ac547, 'movhu', 'd3,(d0,a0)'),
        ('t19_mirror_commit', 0x2ac551, 'call', '0x2abc54,[d2,d3,a2],20'),
        ('t19_mirror_commit', 0x2ac55a, 'cmp', '1769,d2'),
        ('t19_mirror_commit', 0x2ac5f5, 'ret', '[d2,d3,a2,a3],36'),
    ]:
        g(*check)
    flags = list(decoded['t19_effect_flags'].values())
    targets = [struct.unpack_from('<I', data, 0x51dce0+4*i)[0]-0x60020020 for i in range(10)]
    result = [dict(effect=i, **summarize_flag_block(flags, target, 0x3caba8))
              for i, target in enumerate(targets)]
    expected = [(0xffffffff,0),(0xffffffff,128),(0xffffffff,1024),
                (0xffffffff,32768),(0xffffffff,8192),(0xffffffff,64),
                (0xfffffcff,256),(0xfffffcff,512),(0xffffe7ff,2048),(0xffffe7ff,4096)]
    if [(int(r['keep_mask'],16),int(r['set_mask'],16)) for r in result] != expected:
        raise FormatError('selected effect mask cases drifted')
    program = [struct.unpack_from('<I',data,0x51b0d0+4*i)[0]-0x60020020 for i in range(10)]
    if (program[1],program[6],program[7]) != (0x3c10d0,0x3c1111,0x3c111e):
        raise FormatError('selected halfword representation drifted')
    if [struct.unpack_from('<I',data,0x51b0f8+4*i)[0]-0x60020020 for i in (0,4)] != [0x3c0cb2,0x3c0d97]:
        raise FormatError('selected base-filter metadata mapping drifted')
    n += 12
    def e(kind, source, target, origins, note):
        return dict(kind=kind,source=source,target=target,origins=[hex(a) for a in origins],
                    coordinate='decoded#0 offsets/scoped static values',confidence='verified',note=note)
    edges = [
        e('actual_effect_flag_writer','config+24785 mode_art_effect','constructed32-byte parameter+12',
          [0x3cab1d,0x3cab22,0x51dce0,0x3cabaf,0x3c8a99,0x3c8a9d],
          'valid0..9 static flag cases;all reach common bit14/16 clearing;MonoEnable23 derived from separate native fields'),
        e('native_parameter_to_known_receiver','native constructed32-byte parameter','0x3337cb known effects receiver',
          [0x3d2812,0x3d281e,0x3d2b8e,0x3d2b99],
          'two actual matching buffer/constructor/call paths;frames and normal-return/nonalias assumptions;not old35-byte source writer or renderer'),
        e('typed_parameter_origin','actor opcode/field206','parameter Type+16 input domain',
          [0x3ca8e9,0x3ca915,0x3ca931,0x3c8ac7],
          'local possible outputs0/1000/110/120hex;no RAW/JPEG/color semantic names;later receiver helper mutation not excluded'),
        e('alternative_effect_representation','config+24785 mode_art_effect','native halfword descriptors at config+3264',
          [0x3c10b0,0x3c10ce,0x3c1136],
          '40-byte/20-halfword record and tags match independentExifTool CameraSettings52f;metadata-compatible,not an identified ISP ABI/pixel consumer'),
        e('bulk_native_apply','wordshadow selected values','raw native setters and changed-u16-key list',
          [0x2ac531,0x2ac547,0x2ac551],
          'bypasses wrapper bytegate using2abc54;active/shadow alias,ART operation pairing and NV commit remain unknown'),
    ]
    return edges,n,{'effect_flag_cases':result,'common_clear_mask':'0x14000',
                    'common_clear_bit14':'FilmNoise in the independently joined receiver representation',
                    'mono_bit23':'conditional on config24054/24055,not effect872 alone',
                    'parameter_bytes':32,'flags_offset':12,'type_offset':16,
                    'receiver':'0x3337cb','constructor_calls':['0x3d2812','0x3d2b8e'],
                    'receiver_calls':['0x3d281e','0x3d2b99'],
                    'type_input_domain':['0x0','0x1000','0x110','0x120'],
                    'old_source35_alias':'unknown;this independent construction bypasses that missing provenance',
                    'auxiliary30':'zero immediately after32-byte fill;no promoted unconditional value across opaque callees',
                    'rendering':'unknown;knownreceiver normalizes parameters,not proven pixel processing',
                    'bank_udf12':'still unadmitted;native-record reads and constructor join do not require its admission',
                    'metadata_record':{'offset':3264,'bytes':40,'external_tag':'Olympus CameraSettings0x52f',
                                       'selected_base_ids':{'mode100':[2,16],'mode104':[6,19]},
                                       'qualification':'numericE-P7 mapping verified;external tag labels community definitions,not rendering/firmware compatibility'}}
