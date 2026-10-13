"""T19 fixed ART scalar/record contracts, backed by external GNU decoding.

No OEM execution, general alias solver, UDF semantics or rendering inference.
Physical descriptors are not observations of initialized runtime registries.
"""
import struct

try:
    from .inspect_olympus_oe import FormatError
    from .mn103_analysis import operands, memory
except ImportError:
    from inspect_olympus_oe import FormatError
    from mn103_analysis import operands, memory


def descriptor(data, start, count, stride, key):
    """An explicitly nominated physical table; reject ambiguity/out-of-bounds."""
    if stride != 20 or count <= 0 or start < 0 or start + count * stride > len(data):
        raise FormatError('nominated twenty-byte descriptor bounds changed')
    hits = [start + stride * i for i in range(count)
            if struct.unpack_from('<H', data, start + stride * i)[0] == key]
    if len(hits) > 1:
        raise FormatError('selected descriptor key is ambiguous')
    return hits[0] if hits else None


def scalar_format(record_id):
    """Only the nominated native reader's admitted 1/2/4 width contracts.

    This is field geometry, not a general record-ID/processor specification.
    Bit8 affects byte/halfword extension; the word branch ignores that bit.
    """
    width = record_id & 7
    if not 0 <= record_id <= 0xffff or width not in (1, 2, 4):
        raise FormatError('native scalar format outside admitted contract')
    return {'bytes': width, 'signed_read': bool(record_id & 0x100) and width != 4}


def adjacent_transfer(rows, source_base, source_offset, destination_base,
                      destination_offset, width):
    """One adjacent scalar load/store, not propagation across calls or loops."""
    mnemonic = {1: 'movbu', 2: 'movhu', 4: 'mov'}.get(width)
    if mnemonic is None:
        raise FormatError('transfer width outside contract')
    for a, b in zip(rows, rows[1:]):
        pa, pb = operands(a.operands), operands(b.operands)
        if a.mnemonic != mnemonic or b.mnemonic != mnemonic or len(pa) != 2 or len(pb) != 2:
            continue
        if pa[1] not in ('d0', 'd1', 'd2', 'd3') or pb[0] != pa[1]:
            continue
        try:
            src, dst = memory(pa[0]), memory(pb[1])
        except ValueError:
            continue
        if src == {'base': source_base, 'displacement': source_offset} and dst == {
                'base': destination_base, 'displacement': destination_offset}:
            return [hex(a.address), hex(b.address)]
    raise FormatError('nominated adjacent field transfer is not proved')


def evidence(data, decoded, guard):
    """Selected roots/fields only; opaque bank/UDF/runtime ownership retained."""
    count = 0
    def g(window, at, mnemonic, operand):
        nonlocal count
        guard(decoded[window][at], mnemonic, operand)
        count += 1
    checks = [
        ('t19_key_registry_init', 0x29a4bd, 'mov', '1615645068,a3'),
        ('t19_key_registry_init', 0x29a4f8, 'add', '20,a3'),
        ('t19_key_registry_init', 0x29a4fa, 'cmp', '1333,d1'),
        ('t19_key_registry_lookup', 0x29a509, 'asl2', 'd1'),
        ('t19_key_registry_lookup', 0x29a50a, 'mov', '1646560552,a1'),
        ('t19_key_classifier', 0x29a105, 'movbu', '(17,a0),d1'),
        ('t19_key_classifier', 0x29a10a, 'cmp', '6,d1'),
        ('t19_key_classifier', 0x29a10e, 'mov', '2,d0'),
        ('t19_enum_normalize', 0x299dd9, 'mov', '(8,a2),a1'),
        ('t19_enum_normalize', 0x299de0, 'mov', 'd3,d0'),
        ('art_setting_notification', 0x29146a, 'call', '0x290b00,[d2,d3],12'),
        ('t19_scalar_notify', 0x290b0d, 'call', '0x2abc3d,[d2,d3],12'),
        ('t19_scalar_record_set', 0x2abc3f, 'call', '0x2ac6af,[],0'),
        ('t19_scalar_record_set', 0x2abc47, 'beq', '0x2abc51'),
        ('t19_scalar_record_set', 0x2abc78, 'call', '0x2abd1b,[d2,d3,a2,a3],28'),
        ('t19_scalar_record_set', 0x2abc7f, 'call', '0x2abf6b,[],0'),
        ('t19_scalar_record_set', 0x2abc95, 'call', '0x3ea02,[d2,d3,a2,a3],40'),
        ('t19_record_mapping', 0x2abd24, 'cmp', '1768,d2'),
        ('t19_record_mapping', 0x2abd2b, 'mov', '1615686676,a0'),
        ('t19_record_mapping', 0x2abd31, 'movhu', '(d2,a0),d0'),
        ('t19_record_mapping_index', 0x2abf7f, 'movhu', '(2,a0),d0'),
        ('t19_scalar_record_get', 0x2abc30, 'call', '0x2aca60,[],4'),
        ('t19_native_read_api', 0x3e96b, 'call', '0x3ef9d,[d2,d3],12'),
        ('t19_native_read_codec', 0x3efa7, 'btst', '8,d3'),
        ('t19_native_read_codec', 0x3efc1, 'movbu', '(d2,a0),d0'),
        ('t19_native_read_codec', 0x3efc3, 'extb', 'd0'),
        ('t19_native_read_codec', 0x3efe0, 'movbu', '(d2,a0),d0'),
        ('t19_native_write_api', 0x3ea6b, 'call', '0x3e63a,[],0'),
        ('t19_native_write_api', 0x3ea73, 'bne', '0x3ea90'),
        ('t19_native_write_api', 0x3eaaa, 'call', '0x3e6c9,[d2,d3,a2,a3],48'),
        ('t19_native_write_api', 0x3eab7, 'call', '0x3eabf,[d2,d3,a2,a3],20'),
        ('t19_native_write_codec', 0x3eac6, 'call', '0x470e2,[d2],4'),
        ('t19_native_write_codec', 0x3eaee, 'movbu', 'd0,(d3,a3)'),
        ('t19_native_write_codec', 0x3eaf0, 'movbu', 'd0,(d3,a0)'),
        ('t19_native_lookup', 0x3d90c, 'asr', '4,d2'),
        ('t19_native_lookup', 0x3d92d, 'add', '-1569719672,a0'),
        ('t19_primary_snapshot', 0x288511, 'mov', '62929,d0'),
        ('t19_primary_snapshot', 0x28851a, 'call', '0x3e951,[d2,d3],12'),
        ('t19_primary_snapshot', 0x288523, 'movbu', 'd0,(24785,a0)'),
        ('t19_primary_snapshot', 0x288536, 'movbu', 'd0,(24784,a0)'),
        ('t19_alternate_snapshot', 0xc470b9, 'call', '0x3e951,[d2,d3],12'),
        ('t19_alternate_snapshot', 0xc470c0, 'movbu', 'd0,(24785,a3)'),
        ('t19_effect_diagnostic', 0x13d94da, 'movbu', '(24785,a3),d0'),
        ('t19_effect_diagnostic', 0x13d94de, 'mov', '1631805671,a0'),
        ('t19_effect_diagnostic', 0x13d94cd, 'mov', '1631805648,a0'),
        ('t19_parallel_notify', 0x291088, 'add', '48,a3'),
        ('t19_parallel_notify', 0x291091, 'calls', '(a0)'),
        ('t19_parallel_scalar_notify', 0x291147, 'call', '0x2ac1d2,[d2],4'),
        ('t19_shadow_set', 0x2ac1e1, 'mov', '1646605724,a0'),
        ('t19_shadow_set', 0x2ac1e7, 'mov', 'd1,(d0,a0)'),
        ('t19_bracket_builder', 0x3d1ec6, 'call', '0x3d20e2,[d2,a2,a3],12'),
        ('t19_bracket_builder', 0x3d1f16, 'call', '0x3d2182,[d2,a2,a3],16'),
        ('t19_bracket_builder', 0x3d1f48, 'bcs', '0x3d1ed5'),
        ('t19_bracket_builder', 0x3d20cc, 'udfu01', '46,d3'),
        ('t19_bracket_builder', 0x3d20d4, 'movbu', 'd0,(d3,a1)'),
        ('t19_bracket_restore', 0x3c1ff7, 'cmp', '48,d3'),
        ('t19_bracket_restore', 0x3c200f, 'udfu01', '46,d2'),
        ('t19_bracket_restore', 0x3c206b, 'movbu', 'd0,(24785,a2)'),
        ('t19_bracket_projection', 0x3d2136, 'movbu', 'd0,(12,a2)'),
        ('t19_bracket_diagnostic', 0x13c667a, 'mov', '1631722056,a0'),
        ('t19_bracket_diagnostic', 0x13c668f, 'movbu', '(24808,a2),d0'),
        ('t19_effect_predicate', 0x3c0b7e, 'movbu', '(24785,a2),d1'),
        ('t19_apply_caller', 0x3c162d, 'call', '0x3c1fc1,[d2,d3,a2],24'),
        ('t19_apply_caller', 0x3c1641, 'call', '0x3c20ce,[d2,d3,a2,a3],32'),
        ('t19_apply_control', 0x3c2231, 'movhu', 'd1,(3184,a3)'),
        ('t19_apply_control', 0x3c23de, 'ret', '[d2,d3,a2,a3],32'),
        ('t19_composite_keys', 0x2915d2, 'mov', '1615004708,a0'),
        ('t19_composite_keys', 0x2915d9, 'mov', '147,d3'),
        ('t19_composite_keys', 0x2915e3, 'add', '34,a0'),
        ('t19_composite_collect', 0x290d82, 'mov', '64,d1'),
        ('t19_composite_collect', 0x290da7, 'call', '0x2abbea,[],4'),
        ('t19_composite_collect', 0x290dc1, 'call', '0x290d1b,[],0'),
        ('t19_composite_collect', 0x290dd3, 'ret', '[d2,d3,a2,a3],88'),
        ('t19_composite_owner', 0x290d1b, 'movbu', '(0x62245f44),d0'),
        ('t19_composite_owner', 0x290d30, 'mov', '20,d1'),
        ('t19_composite_owner', 0x290d32, 'div', 'd1,d0'),
        ('t19_composite_owner', 0x290d37, 'asl', '6,d0'),
        ('t19_composite_owner', 0x290d3c, 'add', '1646549572,a0'),
        ('t19_enum_record_index', 0x299eec, 'movhu', '(12,a0),d2'),
        ('t19_enum_record_index', 0x299eef, 'movhu', '(14,a0),d1'),
        ('t19_enum_record_compare', 0x299e8d, 'call', '0x2f69,[d2,d3],8'),
        ('t19_enum_record_compare', 0x299e9f, 'add', 'd1,a2'),
        ('t19_bracket_metadata_builder', 0x3d2183, 'movbu', '(4,a2),d0'),
        ('t19_bracket_metadata_builder', 0x3d21eb, 'movhu', '(a2),d0'),
        ('t19_bracket_metadata_builder', 0x3d21ed, 'movhu', '(2,a2),d1'),
        ('t19_bracket_metadata_builder', 0x3d21f2, 'call', '0x3e951,[d2,d3],12'),
        ('t19_bracket_metadata_builder', 0x3d21f9, 'movbu', 'd0,(12,a3)'),
        ('t19_effect_gate_caller', 0x3d27c8, 'call', '0x3c0b64,[d2,a2],16'),
        ('t19_effect_gate_caller', 0x3d27d2, 'bne', '0x3d27d8'),
        ('t19_record_overlay', 0x3d24c0, 'movbu', 'd0,(38,a2)'),
        ('t19_record_overlay', 0x3d24e6, 'movbu', 'd0,(39,a2)'),
        ('t19_write_gate', 0x2ac6a6, 'movbu', 'd0,(0x62257b04)'),
        ('t19_write_gate', 0x2ac6af, 'movbu', '(0x62257b04),d0'),
        ('t19_active_mirror_init', 0x2abbb9, 'mov', '35668,d0'),
        ('t19_active_mirror_init', 0x2abbc6, 'mov', 'a0,(0x62253598)'),
        ('t19_active_mirror_set', 0x2ac102, 'mov', 'd1,a1'),
        ('t19_active_mirror_set', 0x2ac11c, 'call', '0x3ea02,[d2,d3,a2,a3],40'),
        ('t19_mirror_backup', 0x2ac3cc, 'mov', '1646614608,d2'),
        ('t19_mirror_backup', 0x2ac435, 'mov', '(0x62253598),a1'),
        ('t19_mirror_backup', 0x2ac43b, 'mov', '7076,d0'),
        ('t19_mirror_backup', 0x2ac43e, 'call', '0xe6fe1032,[d2,d3,a2,a3],28'),
        ('t19_mirror_restore', 0x2ac5f8, 'mov', '(0x62253598),a0'),
        ('t19_mirror_restore', 0x2ac607, 'call', '0xe6fe1032,[d2,d3,a2,a3],28'),
        ('t19_mirror_refresh', 0x2ac615, 'call', '0x2abbf3,[d2,d3,a2],20'),
        ('t19_mirror_refresh', 0x2ac627, 'cmp', '1769,d3'),
        ('t19_gate_begin', 0x293a42, 'mov', '1,d0'),
        ('t19_gate_begin', 0x293a44, 'call', '0x2ac6a6,[],0'),
        ('t19_gate_begin', 0x293a4b, 'call', '0x2ac3cc,[d2,d3,a2,a3],20'),
        ('t19_gate_begin', 0x293a52, 'call', '0x2ac611,[d2,d3],12'),
        ('t19_gate_end', 0x293a21, 'call', '0x2ac5f8,[],4'),
        ('t19_gate_end', 0x293a28, 'clr', 'd0'),
        ('t19_gate_end', 0x293a29, 'call', '0x2ac6a6,[],0'),
    ]
    for check in checks:
        g(*check)
    r = descriptor(data, 0x4ac96c, 1333, 20, 872)
    if r != 0x4b0c88 or data[r+17] != 1 or struct.unpack_from('<I', data, r+8)[0] != 0:
        raise FormatError('872 scalar descriptor identity drifted')
    if descriptor(data, 0x4ac96c, 1333, 20, 362) is not None:
        raise FormatError('362 comparison observation drifted')
    if any(struct.unpack_from('<H', data, 0x41178c+60*i)[0] in (872, 362) for i in range(439)):
        raise FormatError('selected keys unexpectedly have static update descriptors')
    p = struct.unpack_from('<I', data, r+4)[0] - 0x60020020
    if struct.unpack_from('<H', data, r+12)[0] != 10 or sorted(data[p:p+10]) != list(range(10)):
        raise FormatError('872 scalar domain drifted')
    mapping = []
    for key, wanted in [(872, (0xf5d1, 0)), (362, (0x44c1, 0)), (363, (0x44c1, 1)),
                        (370, (0x44d1, 0)), (873, (0xf5e1, 0)),
                        (371, (0x44d1, 4)), (875, (0xf5e1, 4))]:
        value = struct.unpack_from('<HH', data, 0x4b6bf4 + 4*key)
        if value != wanted:
            raise FormatError('selected native record/index mapping drifted')
        mapping.append({'key': key, 'record_id': hex(value[0]), 'index': value[1],
                        **scalar_format(value[0])})
    count += 9
    for p, label in [(0x14160c7, b' mode_art_effect '),
                     (0x14160b0, b' mode_art_effect_type '),
                     (0x1401a28, b'--rec_set_exif_artbkt--\n')]:
        if data[p:p+len(label)+1] != label + b'\0':
            raise FormatError('directly referenced diagnostic identity drifted')
        count += 1
    transfer = []
    for src, dst in [(24784, 11), (24785, 12)]:
        transfer.append({'config_offset': src, 'record_offset': dst, 'bytes': 1,
                         'projection': adjacent_transfer(list(decoded['t19_bracket_projection'].values()),
                                                       'a1', src, 'a2', dst, 1),
                         'restore': adjacent_transfer(list(decoded['t19_bracket_restore'].values()),
                                                    'a0', dst, 'a2', src, 1)})
        count += 2
    # Selector111 is a composite enum, not its identically keyed native leaf.
    composite = descriptor(data, 0x4ac96c, 1333, 20, 111)
    if composite != 0x4accf0 or data[composite+17] != 6:
        raise FormatError('composite111 descriptor type drifted')
    size, stride = struct.unpack_from('<HH', data, composite+12)
    values = struct.unpack_from('<I', data, composite+4)[0]-0x60020020
    selectors = struct.unpack_from('<I', data, composite+8)[0]-0x60020020
    if (size, stride, values, selectors) != (2112, 64, 0x49a8dc, 0x48dda8):
        raise FormatError('composite111 enum geometry drifted')
    group_hits = [0x410404+34*i for i in range(147)
                  if struct.unpack_from('<H', data, 0x410404+34*i)[0] == 111]
    if group_hits != [0x4108ee] or struct.unpack_from('<4H', data, 0x4108f0) != (111, 908, 973, 3200):
        raise FormatError('composite111 active-key/sentinel declaration drifted')
    selected_enum = []
    for selector, ordinal, raw_mode in [(8, 17, 100), (12, 21, 104)]:
        if struct.unpack_from('<I', data, selectors+4*ordinal)[0] != selector or struct.unpack_from('<I', data, values+64*ordinal)[0] != raw_mode:
            raise FormatError('selected composite enum identity drifted')
        selected_enum.append({'selector': selector, 'ordinal': ordinal,
                              'candidate': hex(values+64*ordinal), 'native_mode': raw_mode})
    shared = []
    for row, mode, variant, record_id in [(0x51e250, 100, 1, 0x44d1),
                                         (0x51e262, 100, 2, 0xf5e1),
                                         (0x51e2bc, 104, 1, 0x44d1),
                                         (0x51e2ce, 104, 2, 0xf5e1)]:
        index = 0 if mode == 100 else 4
        if data[row+4:row+6] != bytes((mode, variant)) or struct.unpack_from('<HH', data, row+10) != (record_id, index):
            raise FormatError('selected ART bracket source-record relation drifted')
        shared.append({'candidate': hex(row), 'native_mode': mode,
                       'variant': variant, 'effect_record_id': hex(record_id), 'index': index})
    count += 11
    def edge(kind, source, target, origins, note):
        return dict(kind=kind, source=source, target=target,
                    origins=[hex(a) for a in origins], confidence='verified',
                    coordinate='decoded#0 offsets/scoped static values', note=note)
    edges = [
        edge('native_scalar_identity', 'setting872', 'native record0xf5d1/index0',
             [0x4b0c88, 0x4b7994, 0x2abd31, 0x2abf7f],
             'physical key maps and signed byte reader; bank UDF/registration/value assumptions not discharged'),
        edge('native_scalar_write', 'key/value scalar notification', 'typed native byte record write',
             [0x29146a, 0x290b0d, 0x2abc95, 0x3eab7, 0x3eaee],
             'gate-dependent, normal-return/pointer assumptions; no flash durability or accepted arbitrary values'),
        edge('independent_scalar_snapshot', 'native record0xf5d1/index0', 'config+24785 mode_art_effect',
             [0x28851a, 0x288523, 0xc470b9, 0xc470c0, 0x13d94da],
             'two independently located reads/byte stores and direct diagnostic; not pixel/effect-bit interpretation'),
        edge('native_scalar_comparison', 'setting362/363', 'native record0x44c1/index0/1',
             [0x4b719c, 0x4b71a0, 0x28852d, 0x13d94c9],
             'shared group/different indices;362 current diagnostic field differs from old source Type+24'),
        edge('bracket_snapshot', 'config+24784/+24785', 'bracket record+11/+12 bytes',
             [0x3d2132, 0x3d2136, 0x3c205d, 0x3c206b, 0x13c667a],
             '46-byte-shaped transient bracketing records; selected-slot UDF46/owner/lifetime qualified; not named presets'),
        edge('parallel_registered_hook', 'setting descriptor+48', '0x291091 indirect hook consumer',
             [0x291088, 0x291091, 0x414930],
             'consumed slot now independently located; context1 is not identified as RAW/capture'),
        edge('shadow_scalar_store', 'parallel scalar notification', 'word slots at static0x6225359c',
             [0x291147, 0x2ac1e1, 0x2ac1e7],
             'numeric key-indexed RAM word mirror, not nonvolatile storage or native byte buffer'),
        edge('non_pixel_apply_boundary', 'bracket-selected config', '0x3c20ce scalar shaping',
             [0x3c162d, 0x3c1641, 0x3c2231],
             'control/data transformation; no alias to old35-byte source, pixel work or typed ISP/JPEG interface'),
        edge('composite_selector_record', 'SettingController selector111=8/12', 'native mode100/104',
             [0x4accf0, 0x4108ee, 0x290da7, 0x49ad1c, 0x49ae1c, 0x299e8d],
             '33 physical64-byte candidates, three active native leaf values; compare/helper/runtime qualifications; not33 complete saved looks'),
        edge('transient_composite_owner', '64-byte composite getter snapshot', 'static pool0x62245a44',
             [0x290dc1, 0x290dcc, 0x290d30, 0x290d3c],
             '20-slot-shaped scratch pool/byte counter, normal returns and finite64-byte copy; not permanent ownership or thread safety'),
        edge('shared_art_effect_source', 'selector8 effect sources370/873', 'mode100 variants1/2 bracket record+12',
             [0x4b71bc, 0x4b7998, 0x51e250, 0x51e262, 0x3d21f2, 0x3d21f9],
             'same native record IDs44d1/f5e1,index0; static metadata registration/index UDF remains qualified; not proven RAW/capture or pixel sharing'),
        edge('boolean_effect_control', 'config+24785 mode_art_effect', '0x3d27d2 nonzero gate',
             [0x3c0b7e, 0x3c0b87, 0x3d27c8, 0x3d27d2],
             'effect identity collapses to Boolean control here; not an effect operator or accepted combination'),
        edge('gated_scalar_views', 'scalar key/value notification', 'active word mirror and conditional native byte',
             [0x2ac102, 0x2ac11c, 0x2ac6af, 0x2abc47, 0x2abc95],
             '2ac102 preservesD2/D3 through explicit nested saves;gate==1 suppresses backing byte path,not mirror update;other validation can reject'),
        edge('temporary_mirror_lifecycle', 'gate1 / backup / shadow refresh', '7076-byte active mirror restore / gate0',
             [0x2abbc6, 0x293a44, 0x2ac43e, 0x2ac607, 0x293a29],
             'native record0x8b54 pointer/1769-word active,shadow,backup views;begin/end operation pairing,ART caller and NV commit are not proved'),
    ]
    return edges, count, {'descriptor872': hex(r), 'enum872_count': 10,
                           'native_mapping': mapping, 'bracket_transfer': transfer,
                           'negative_keys_in_439_callback_table': [872, 362],
                           'old_effect_source_alias': 'unknown', 'pixel_consumer': 'unknown',
                           'named_preset_or_nonvolatile_save': 'not established',
                           'bank_udf12': 'unadmitted', 'pool_udf46': 'unadmitted',
                           'composite111': {'records': 33, 'stride': 64, 'active_fields': 3,
                                            'selected': selected_enum, 'scratch_slots': 20},
                           'shared_bracket_sources': shared}
