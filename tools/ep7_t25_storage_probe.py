#!/usr/bin/env python3
"""Finite T25 native storage/admission checks; not a v4 implementation.

Owned Mode RAM fixtures, strict pinned GNU execution, explicit service cuts.
No raw record/device I/O, network request, firmware edit or install package.
Reference method: fishcu/oly_fw_analysis@539fcf1 (read/run only).
"""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import struct

from ep7_color_min import BASE, SP, digest, require
from ep7_t24_probe import Probe as ExistingProbe

MODE, SIZE = 0x624ea400, 0x40000
BANKS, ACTIVE, LIVE = 0x624ea8dc, 0x6250ba00, 0x62509e30
KEYS = [*range(927,963),*range(1655,1667)]
MARK = 0xe7410000  # Proposed format, never installed; differs from PEN-F.
WINDOWS = [(0x602cbffe,0x602cc122),(0x6005e947,0x6005eb15),
           (0x6005efbd,0x6005f005),(0x602cca80,0x602cca8c),
           (0x6005c8cc,0x6005c8e2),(0x6005e65a,0x6005e676),
           (0x60067102,0x60067146),(0x602b9bad,0x602b9c90),
           (0x602b3330,0x602b3444),(0x602b38a7,0x602b392d),
           (0x602afa11,0x602afa30),(0x602cc6c6,0x602cc6d8),
           (0x60bd408d,0x60bd4150),(0x602b97c5,0x602b98a0)]


def encode(h,l):
    if any(type(x) is not int or not -7<=x<=7 for x in (h,l)):
        raise ValueError('H/L must be integer -7..7')
    v=(h&15)|((l&15)<<4)
    return MARK|((v^255)<<8)|v


def decode(word):
    if type(word) is not int or not 0<=word<=0xffffffff or word&0xffff0000!=MARK:
        return 0,0
    v=word&255
    if (word>>8&255)!=(v^255):return 0,0
    h,l=(v&15),(v>>4)
    h=h-16 if h>=8 else h
    l=l-16 if l>=8 else l
    return (h,l) if -7<=h<=7 and -7<=l<=7 else (0,0)


class Probe(ExistingProbe):
    def prepare(self):
        self.mapping()
        self.windows=[]
        for a,b in WINDOWS:
            self.disassemble(f'native_{a:x}',a,b)
            self.windows.append(dict(start=hex(a),end_exclusive=hex(b),sha256=digest(self.read(a,b-a))))

    def state(self):
        s=self.new_state()
        data=bytearray(SIZE)
        struct.pack_into('<H',data,0,7)
        s.ram('owned_mode_record',MODE,data)
        s.ram('bank_active_live_pointers',0x62253590,struct.pack('<3I',BANKS,ACTIVE,LIVE))
        s.ram('native_inhibit',0x62257b04,b'\0')
        # Explicit protected record range outside the owned Mode fixture. This
        # is a permission-guard input, not a claimed captured camera value.
        s.ram('protected_record_base',0xa2711a88,struct.pack('<I',0x10000000))
        return s

    def native(self,s,target,mask,frame,args,limit=1000000):
        s.enter(target,mask,frame,args)
        v=s.run({s.finish},limit=limit)
        require(v['status']=='breakpoint' and s.regs['pc']==s.finish,
                'Unknown native boundary: '+str((hex(target),v['status'],v.get('fault'))))
        require(s.regs['sp']==SP,'Native stack not restored')
        return s.regs['d0']

    def part_write(self,s,key,word):
        self.native(s,0x602cc0d0,'d2',8,{'d0':key,'d1':1,'a0':word})

    def part_read(self,s,key):
        return self.native(s,0x602cc0a7,'d2',8,{'d0':key,'d1':1})

    def arrays(self):
        s=self.state()
        results=[]
        for bank in range(9):
            before_part0=s.read(ACTIVE,1769*4)
            expected=[]
            for i,key in enumerate(KEYS):
                pair=((i+bank)%15-7,(2*i+bank)%15-7)
                word=encode(*pair)
                self.part_write(s,key,word)
                require(decode(self.part_read(s,key))==pair,'Part API roundtrip')
                expected.append(word)
            require(s.read(ACTIVE,1769*4)==before_part0,'H/L part writes modified part0')
            self.native(s,0x602cc03a,'d2,d3',12,{'d0':bank})
            results.append(expected)
        for bank,expected in enumerate(results):
            self.native(s,0x602cbffe,'d2,d3',12,{'d0':bank})
            actual=[self.part_read(s,key) for key in KEYS]
            require(actual==expected,'Native bank copy lost part1')
        # An exact caller window loads ACTIVE before invoking its subsequent
        # filter. Current typed config is deliberately retained at old value.
        s.write(0x6250f836,b'\x01')
        before=[self.part_read(s,k) for k in KEYS]
        # Execute the original caller's selected-bank MOV/CALL, stopping at
        # its return before later recall publication and inhibit-setting.
        s.regs={'pc':0x602b3406,'sp':SP,'a2':2,'psw':0}
        v=s.run({0x602b340f},limit=1000000)
        require(v['status']=='breakpoint' and s.regs['pc']==0x602b340f,'Native recall load window')
        after=[self.part_read(s,k) for k in KEYS]
        require(before!=after and s.read(0x6250f836,1)==b'\x01' and s.read(0x62257b04,1)==b'\0',
                'Recall staging observation changed')
        (self.out/'arrays-private.json').write_text(json.dumps(dict(events=s.events))+'\n')
        self.state_with_values=s
        return dict(native_part_roundtrips=9*48,native_bank_saves=9,native_bank_loads=10,
                    all_48_candidate_cells_preserved=True,part0_unchanged_by_HL_API=True,
                    internal_banks_not_user_presets=True,
                    native_part_api='0x602cc0d0 /0x602cc0a7',
                    native_bank_api='0x602cc03a /0x602cbffe',
                    staging_counterexample=dict(active_part1_changed=True,current_profile_unchanged=True,
                        native_inhibit_still_zero=True,native_window='0x602b3406..0x602b340f',
                        native_caller_order='0x602b33ec bank_load precedes0x602b33f7 filter;0x602b3408 loads selected bank',
                        actual_concurrent_image_admission='NOT established; a quiescent/publication join is required',
                        not_claimed='Does not prove a physical mixed frame; disproves treating ACTIVE pointer as intrinsically committed'),
                    fixture='Owned full-sized Mode RAM, CPU0, coherent aliases; exact ROM routines; no NVS backend or complete Myset transaction')

    def reset_cells(self):
        s=self.state_with_values
        rows=[]
        for key in KEYS:
            self.part_write(s,key,encode(3,-5))
            s.enter(0x602b9c4f,'d2,d3,a2',16,{'d0':0,'d1':key})
            services=[]
            for _ in range(12):
                v=s.run({s.finish,0x602cbc0a,0x602b2250},limit=100000)
                require(v['status']=='breakpoint','Reset unknown boundary')
                pc=s.regs['pc']
                if pc==s.finish:break
                if pc==0x602cbc0a:
                    require(s.regs['d0']==4508,'Reset environment key changed')
                else:
                    require(s.regs['a0']==key,'Unexpected reset setter key')
                services.append(hex(pc))
                # Only environment query and higher registered setter are
                # modeled; ACTIVE part writes and default lookup execute.
                s.return_from_model(0)
            require(s.regs['pc']==s.finish,'Reset did not complete')
            value=self.part_read(s,key)
            require(decode(value)==(0,0) and value!=encode(3,-5),'Reset not neutral')
            rows.append(dict(key=key,part1_decodes_neutral=True,modeled_services=services))
        (self.out/'reset-private.json').write_text(json.dumps(dict(events=s.events))+'\n')
        return dict(cases=rows,native_part1_write=True,native_default_lookup=True,
                    full_registered_reset_lifecycle=False,
                    limits='Registered typed setters modeled, so not a full UI reset/save/restart proof')

    def admission(self):
        r=self.provider.Region
        cases=[]
        for flag in (0,1,2,255):
            s=self.new_state()
            s.ram('native_inhibit',0x62257b04,bytes([flag]))
            s.enter(0x602afa11,'d2,d3',16,{'d0':927,'d1':3})
            v=s.run({s.finish,0x602b0bc9},limit=1000)
            admitted=s.regs['pc']==0x602b0bc9
            require(v['status']=='breakpoint' and admitted==(flag!=1),'Native inhibit predicate changed')
            (self.out/f'admission_{flag}.json').write_text(json.dumps(v)+'\n')
            cases.append(dict(inhibit=flag,reaches_registered_edit=admitted,
                              stopped_before_edit=True,capture_or_menu_state_checked=False))
        return dict(cases=cases,native='0x602afa11 ->0x602cc6cf ->0x602b0bc9',
                    meaning='One inhibit byte blocks only value1; this entry does not establish shooting/menu idle or acquire a 40-value transaction',
                    next_boundary='Wi-Fi application state selection precedes this function and remains unqualified')

    def wifi_pending(self):
        s=self.new_state()
        address=0xa26a4524
        s.ram('native_pending',address,b'\xa5'*12)
        messages=[]
        for key,value in ((927,3),(939,-2)):
            s.regs={'pc':0x60bd40e7,'sp':SP,'d0':key,'d2':value&0xffffffff,'psw':0}
            v=s.run({0x60bd40fb},limit=100)
            require(v['status']=='breakpoint','Pending record prefix failed')
            data=struct.unpack('<3I',s.read(address,12))
            require(data==(key,0,value&0xffffffff),'Pending fields differ')
            messages.append(dict(key=key,type=0,value=value))
        (self.out/'pending-private.json').write_text(json.dumps(dict(events=s.events))+'\n')
        return dict(native_prefix='0x60bd40e7..0x60bd40fb',pending_address=hex(address),
                    bytes=12,messages=messages,second_replaces_first=True,
                    stopped_before_event_post='0x60bd548d',
                    limits='Native prefix only; no claim that stock worker races. A new bulk receiver needs owned immutable payload and timeout lifetime, not40 scalar posts.')

    def secondary_core(self):
        s=self.state()
        s.regions=[replace(q,data=struct.pack('<I',1)) if q.name=='cpu' else q for q in s.regions]
        before=s.read(ACTIVE,3538*4)
        s.enter(0x602cc0d0,'d2',8,{'d0':927,'d1':1,'a0':encode(3,-5)})
        v=s.run({s.finish,0x60061808},limit=1000)
        require(v['status']=='breakpoint' and s.regs['pc']==0x60061808,
                'Secondary core must reach declared diagnostic boundary')
        require(before==s.read(ACTIVE,3538*4),'Secondary core wrote before admission')
        (self.out/'secondary-core-private.json').write_text(json.dumps(dict(events=s.events))+'\n')
        return dict(cpu=1,native_cached_pointer=hex(ACTIVE),
                    guard='0x6005ea4a..0x6005ea71',stop='0x60061808',
                    storage_unchanged_before_stop=True,
                    continuation_not_modeled='Native code then resolves its global record and can use cross-core6005e6e9; complete transport/ack not replayed',
                    conclusion='CPU0 part tests do not qualify direct execution from an arbitrary HTTP/app worker')


def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--upstream',required=True,type=Path)
    p.add_argument('--stock',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    x=Probe(a.upstream,a.stock,a.out)
    x.prepare()
    result=dict(issue=65,stock_sha256=digest(a.stock.read_bytes()),main_sha256=digest(x.data),
                native_windows=x.windows,firmware_modified=False)
    for name,method in [('arrays',x.arrays),('reset',x.reset_cells),('admission',x.admission),
                        ('wifi_pending',x.wifi_pending),('secondary_core',x.secondary_core)]:
        result[name]=method()
        (x.out/'checkpoint.json').write_text(json.dumps(result,indent=2)+'\n')
    (x.out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(native_checks='pass',v4_ready=False)))


if __name__=='__main__':main()
