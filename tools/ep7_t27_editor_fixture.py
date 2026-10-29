#!/usr/bin/env python3
"""Bounded E142 GUI services; original code, no camera I/O or boot claim.

Method reference: fishcu/oly_fw_analysis@539fcf1, penf_color_edit_probe.py
(read/run only). Addresses/layouts below were re-established on E142/1100.
Mutex success means an explicitly uncontended, single-thread owned fixture;
status reads, admission branches, setting conversions and writes stay native.
"""
import struct

from ep7_color_min import require
from ep7_t27_ui_flow_probe import Probe as Flow
from ep7_t25_v4_probe import SERVICE_CUTS

RESOURCE_TABLE, STATUS_MUTEX = 0x1C060000, 0x1C061000
COMMON, BACKGROUND = 0x1C070000, 0x1C071000
LOCATOR, COORDINATOR = 0x1C072000, 0x1C073000
OPTIONAL_PROVIDER = 0x1C074000
MUTEX_VTABLE = 0x60a66390
MUTEX_ENTER, MUTEX_LEAVE = 0x607684F9, 0x60768509
DIAGNOSTICS = {0x60768038, 0x60767FDE, 0x60767FF8, 0x60768016}


class Fixture(Flow):
    def warm(self, s, flags=(0, 0, 0, 0), application_state=0):
        require(len(flags) == 4, 'Four explicit capture status inputs required')
        self.held_mutexes, self.sync_events = [], []
        self.peer_events = []
        self.active_peer = False
        # All other resources point to UNMAPPED witnesses. They cannot silently
        # acquire a successful mutex using this model.
        pointers = [0x1BFF0000 + 8 * i for i in range(14)]
        pointers[5] = STATUS_MUTEX
        s.ram('owned_ComResource_table', RESOURCE_TABLE,
              struct.pack('<14I', *pointers), aliases=False)
        s.ram('owned_resource5', STATUS_MUTEX,
              struct.pack('<2I', MUTEX_VTABLE, 0xDEAD0005), aliases=False)
        s.write(0x61FA71B4, struct.pack('<I', RESOURCE_TABLE))
        s.ram('explicit_capture_status', 0x622CB16C, struct.pack('<4I', *flags))
        # Only reached method contracts are mapped. In particular the opaque
        # background backend stays unmapped; its reached predicate ignores it.
        s.ram('owned_common_header', COMMON,
              struct.pack('<I', 0x60a95cb4), aliases=False)
        s.write(0x61FA90F0, struct.pack('<I', COMMON))
        s.ram('owned_background_header', BACKGROUND,
              struct.pack('<2I', 0x60a9d1fc, 0x1BFF1000), aliases=False)
        s.write(0x61FA9440, struct.pack('<I', BACKGROUND))
        s.ram('diagnostic_mask', 0x622CC164, bytes(4))  # bit 16 only adds logging
        s.write(0x61FA7334, bytes(4))  # explicit no-modal-overlay input
        s.ram('owned_application_locator_header', LOCATOR,
              struct.pack('<2I', 0x60adc020, application_state), aliases=False)
        s.ram('owned_application_state_mutex', LOCATOR + 24,
              struct.pack('<2I', MUTEX_VTABLE, 0xDEAD0100), aliases=False)
        s.write(0x61FA9950, struct.pack('<I', LOCATOR))
        s.ram('owned_empty_coordinator', COORDINATOR, bytes(16), aliases=False)
        # Native 16-byte coordinator constructor; empty is an explicit input,
        # not a claim that live application coordination always takes no work.
        self.ui_call(s, 0x60813EA9, 'a2', 8, {'a0': COORDINATOR})
        s.write(0x61FA9878, struct.pack('<I', COORDINATOR))
        s.ram('owned_optional_provider', OPTIONAL_PROVIDER, bytes(8), aliases=False)
        self.ui_call(s, 0x607FAB30, '', 0, {'a0': OPTIONAL_PROVIDER})
        s.write(0x61FA96B4, struct.pack('<I', OPTIONAL_PROVIDER))
        s.ram('owned_edit_diagnostic_interface', 0x1C075000,
              struct.pack('<I', 0x60AC9FF4), aliases=False)
        s.write(0x61FA9578, struct.pack('<I', 0x1C075000))
        # Reached copy getter ignores its context pointer; do not fabricate
        # the large unrelated C3d backend or infer this is the wheel producer.
        s.write(0x61FA90D8, struct.pack('<I', 0x1BFF3000))
        s.ram('explicit_twelve_byte_diagnostic_input', 0x622CB528, bytes(12))
        # Queue lock handle is explicit. Native matching/clearing loops run.
        s.write(0x61FB2A28, struct.pack('<I', 0xDEAD0200))
        s.ram('owned_empty_gui_queue_indices', 0x6246A6F0, bytes(4))
        self.queue_locked = False
        # Separate native 15000..15273 lazy pointer-cache family, not settings
        # values. The native metadata resolver fills reached entries.
        s.ram('empty_special_property_pointer_cache', 0xA269BB20, bytes(274 * 4))
        s.ram('empty_default_policy_pointer_cache', 0xA269B90C, bytes(22 * 4))
        # Short OK queries key 15272 through the C9A2 native record family.
        # Register exactly that two-u16 initializer, with its stock defaults;
        # the rest of the secondary UI records remain absent and fail closed.
        for i, (source, key, count) in enumerate(((0x60090CE0, 0xC9A2, 2),
                                                 (0x60090FAC, 0x0AA2, 1))):
            # AA2 is the native default-policy input used by key 4508.
            descriptor = self.read(source, 8)
            require(struct.unpack('<HH', descriptor[:4]) == (key, count),
                    'E142 GUI descriptor changed')
            desc, data = 0x1C076000 + i * 512, 0x1C076100 + i * 512
            s.ram(f'owned_descriptor_{key:x}', desc, descriptor + bytes(4), aliases=False)
            s.ram(f'owned_native_defaults_{key:x}', data, descriptor[4:], aliases=False)
            self.ui_call(s, 0x6005D987, 'd2,d3,a2,a3', 48,
                         {'a0': desc, 'a1': data, 'd0': 0xA26FFA88})

    def active_application(self, s):
        """Witness for the native state-range branch, NOT a live app/task ID.

        The unchanged request and record producers execute. The external
        synchronous message service and UI notification delivery are explicit
        successful peer inputs. No kernel scheduling or camera state is inferred.
        """
        self.active_peer = True
        s.write(LOCATOR + 4, struct.pack('<I', 0x10001))
        s.write(COORDINATOR + 4, struct.pack('<I3H', 1, 14, 15, 16))

    def run_ui(self, s, stops):
        peer = ({0x607AAD76, 0x607AABFC, 0x602F8873}
                if getattr(self, 'active_peer', False) else set())
        queue = {0x6082C122, 0x6082C0F6}
        extra = {MUTEX_ENTER, MUTEX_LEAVE} | SERVICE_CUTS | DIAGNOSTICS | peer | queue
        # Twelve ALL commits each traverse the native per-setting status reads.
        for _ in range(4096):
            super().run_ui(s, set(stops) | extra)
            pc = s.regs['pc']
            if pc in stops:
                return
            if pc in queue:
                require(s.regs['d0'] == 0xDEAD0200,
                        'Unmodeled GUI queue synchronization handle')
                if pc == 0x6082C122:
                    require(not self.queue_locked and s.regs['d1'] == 0xFFFFFFFF,
                            'Queue lock contract')
                    self.queue_locked = True
                else:
                    require(self.queue_locked, 'Queue unlock without lock')
                    self.queue_locked = False
                s.return_from_model(0)
            elif pc in peer:
                from penf_boot_emulator import HOOK_RETURN
                if pc == 0x607AAD76:
                    require(s.regs['mdr'] == 0x607AABF4,
                            'Unreviewed request connection factory')
                    # Opaque connection carried by the native 995 constructor;
                    # no backend storage is mapped or guessed.
                    s.write(HOOK_RETURN, self.rets + b'\xcb' * 6)
                    s.regs.update(pc=HOOK_RETURN, a0=0x1BFF2000)
                    continue
                if pc == 0x607AABFC:
                    require(s.regs['mdr'] == 0x60828128,
                            'Unreviewed synchronous message producer')
                    message = s.regs['a1']
                    require(struct.unpack('<H', s.read(message + 4, 2))[0] == 995
                            and struct.unpack('<I', s.read(message + 28, 4))[0]
                            == 0x1BFF2000, 'Native message/connection contract')
                    self.peer_events.append(dict(service='sync', message_id=995,
                                                 response=0))
                else:
                    require(s.regs['mdr'] == 0x60814078,
                            'Unreviewed setting notification producer')
                    p = s.regs['a0']
                    self.peer_events.append(dict(service='setting_notice',
                        key=struct.unpack('<H', s.read(p, 2))[0],
                        value=struct.unpack('<i', s.read(p + 4, 4))[0],
                        witnesses=list(struct.unpack('<3H', s.read(p + 8, 6)))))
                s.return_from_model(0)
            elif pc in (MUTEX_ENTER, MUTEX_LEAVE):
                pointer = s.regs['a0']
                require(pointer in (STATUS_MUTEX, LOCATOR + 24),
                        f'Unmodeled GUI synchronization object {pointer:#x}')
                held = getattr(self, 'held_mutexes', [])
                if pc == MUTEX_ENTER:
                    require(pointer not in held, 'Recursive modeled GUI mutex')
                    held.append(pointer)
                else:
                    require(held and held.pop() == pointer, 'Unbalanced GUI mutex')
                self.held_mutexes = held
                self.sync_events.append(dict(entry=hex(pc), object=hex(pointer),
                                             return_pc=hex(s.regs['mdr'])))
                s.return_from_model(0)
            elif pc in SERVICE_CUTS:
                self.model(s, pc)  # existing qualified v4 side-consumer cuts
            else:
                # Structured diagnostics only, whose result is discarded by
                # the reviewed callers. No admission or setter is replaced.
                s.return_from_model(0)
        raise ValueError('Finite GUI service budget exhausted')
