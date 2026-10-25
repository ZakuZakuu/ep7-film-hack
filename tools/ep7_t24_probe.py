#!/usr/bin/env python3
"""Finite E142/1100 T24 experiments; no package output, settings I/O or devices.

Original harness, reusing the separately pinned GNU engine and this repository's
Experiment. Reference method: fishcu/oly_fw_analysis@539fcf1, read/run only.
All OEM windows, memory and traces stay in a private /tmp directory. Caller
objects are declared fixtures, not captured camera RAM. Unknown accesses stop.
"""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import struct
import sys

from ep7_color_min import Experiment, BASE, CAVE, STACK, SP, digest, require

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/hsl-profiles/e-p7'
SITE, RESUME = 0x603b14f3, 0x603b14f8
J, C, O, F, W = 0x19400000, 0x19200000, 0x19100000, 0x19600000, 0x19700000
Q = J + 11364
SYMBOLS = dict(ep7_selector=0x603b0252, ep7_resume=RESUME,
               ep7_request_callback=0x60355fd4, ep7_owner_callback=0x603e7b83,
               ep7_alternate_owner_callback=0x603e9631)
# Physical record order, paired native H/L values (96 constants, not OEM bytes).
ROWS = [[0]*24 for _ in range(4)]
ROWS[0][0] = -3000
ROWS[1][7] = -200
ROWS[2][2], ROWS[2][11] = 3000, 100
WINDOWS = [
    (0x603af871, 0x603b0345), (0x603b551d, 0x603b559f), (0x603b1466, 0x603b1517),
    (0x603e611e, 0x603e61b8), (0x603537eb, 0x60353cb7),
    (0x60354b8c, 0x60354c4c), (0x60354cb9, 0x60355098),
    (0x603e8a87, 0x603e8af1), (0x6029b9d1, 0x6029ba1e),
    (0x60343b23, 0x60343ebe), (0x60339c27,0x60339c9b), (0x60345ebe, 0x60345fc2),
    (0x603eaa04, 0x603eab39), (0x603f2102, 0x603f2190),
    (0x602a859c, 0x602a86c7), (0x6005c5be, 0x6005c919),
    (0x602cbd00, 0x602ccb20), (0x6005c326,0x6005c583),
    (0x6005dc19,0x6005dc87),
]


class Probe(Experiment):
    def prepare(self):
        self.mapping()
        self.windows = []
        for a, b in WINDOWS:
            self.disassemble(f'w_{a:x}', a, b)
            self.windows.append(dict(start=hex(a), end_exclusive=hex(b), sha256=digest(self.read(a,b-a))))
        self.extension = self.assemble('v2_extension', (PATCH/'hook.s').read_text(), CAVE, SYMBOLS)
        self.jump = self.assemble('v2_jump', 'jmp ep7_extension\n', SITE, {'ep7_extension':CAVE})
        require(len(self.jump)==5 and len(self.extension)<=464, 'Unqualified code extent')
        require(self.read(CAVE,len(self.extension))==b'\xff'*len(self.extension), 'Padding mismatch')
        value = bytearray(self.data)
        value[SITE-BASE:SITE-BASE+5] = self.jump
        value[CAVE-BASE:CAVE-BASE+len(self.extension)] = self.extension
        self.candidate = bytes(value)  # Private execution fixture; never packaged/written as firmware.

    def fixture(self, profile, *, saturation=None, record=0, key=11, flags=0,
                special=False, custom=False, poison=None, callback=0x603e7b83):
        req = bytearray(1884)
        struct.pack_into('<II',req,0,0x60355fd4,J+14576+56*record)
        req[8:12] = bytes((key>>24 & 255,key>>16 & 255,key & 255,key>>8 & 255))
        struct.pack_into('<H',req,12,0xf00d if special else 0)
        struct.pack_into('<12b',req,1816,*(saturation or [0]*12))
        job = bytearray(15488)
        struct.pack_into('<2I',job,4,callback,W)
        struct.pack_into('<I',job,14576+56*record,J)
        if custom: struct.pack_into('<I',req,1524,F+0x9000)
        job[11364:11364+1884] = req
        cfg = bytearray(0x8000)
        cfg[24053],cfg[24776],cfg[24083] = 11,11,profile
        owner = bytearray(512)
        struct.pack_into('<I',owner,28,F)
        struct.pack_into('<I',owner,36,J)
        struct.pack_into('<I',owner,116,1)
        struct.pack_into('<H',owner,194,0x1001)
        ctx = bytearray(208)
        struct.pack_into('<I',ctx,4,Q)
        struct.pack_into('<I',ctx,12,O)
        struct.pack_into('<I',ctx,52,key)
        struct.pack_into('<I',ctx,60,flags)
        struct.pack_into('<I',ctx,108,0x40000000)
        r=self.provider.Region
        regions=[r('job',J,bytes(job)),r('context',C,bytes(ctx),'rw',True),
                 r('output',O,poison if poison is not None else bytes(3164),'rw',True),
                 r('image_owner',W,bytes(owner)),r('snapshot',F,bytes(cfg))]
        if custom:
            regions += [r('custom_descriptor',F+0x9000,bytes(16)+struct.pack('<I',0x6051de2c))]
        return regions

    def select(self, name, regions, patched):
        r=self.provider.Region
        # Execute the original MOV D3,A0, CALL and return breakpoint. It is a
        # caller window, not a synthetic substitute for selector behavior.
        registers={'pc':SITE-2,'sp':SP,'d3':C,'d2':0x11223344,'a2':0x55667788,
                   'a3':0xabcdef88,'mdr':0x1234,'psw':0}
        result=self.provider.execute([
            r('rom',BASE,self.candidate if patched else self.data,'rx'),
            r('stack',STACK,bytes(0x2000),'rw',True),*regions],
            registers,RESUME,limit=20000,trace_limit=20000)
        (self.out/(name+'.json')).write_text(json.dumps(result)+'\n')
        require(result['status']=='returned',f'{name}: {result["status"]} {result.get("fault")}')
        require(result['registers']['sp']==SP,'Unbalanced stack')
        result['aligned']=self.audit_alignment(result)
        return result

    def pair(self, name, profile, *, eligible=True, **kwargs):
        fixture=self.fixture(profile,**kwargs)
        a=self.select(name+'_stock',fixture,False)
        b=self.select(name+'_candidate',fixture,True)
        require(a['registers']==b['registers'],name+': register/PSW/MDR/LAR/LIR mismatch')
        require(self.captured(a,'stack')[SP-STACK:]==self.captured(b,'stack')[SP-STACK:],
                name+': live stack mismatch')
        old,new=(self.captured(v,'output') for v in (a,b))
        expected=bytearray(old)
        if eligible:
            for i in range(12):
                struct.pack_into('<h',expected,706+24*i,ROWS[profile-1][2*i])
                struct.pack_into('<h',expected,710+24*i,ROWS[profile-1][2*i+1])
        require(new==bytes(expected),name+': unexpected output field')
        ca,cb=(bytearray(self.captured(v,'context')) for v in (a,b))
        # No dirty/cache flags are changed by this candidate.
        require(ca==cb,name+': context differs outside HSL upload bit')
        return dict(case=name,profile=profile,eligible=eligible,registers_equal=True,
                    live_stack_equal=True,aligned=a['aligned']+b['aligned'],
                    changed_offsets=[i for i in range(len(new)) if old[i]!=new[i]],
                    H=[struct.unpack_from('<h',new,706+24*i)[0] for i in range(12)],
                    L=[struct.unpack_from('<h',new,710+24*i)[0] for i in range(12)],
                    upload_bit=bool(struct.unpack_from('<I',cb,108)[0]&2)),new,bytes(cb)

    def matrix(self):
        result=[]
        for profile in range(1,5):
            for flags in (0,2):
                row,_,_=self.pair(f'equal_S_p{profile}_dirty{flags}',profile,flags=flags)
                result.append(row)
        for item in self.profiles():
            row,_,_=self.pair(f'factory_S_p{item["profile"]}',item['profile'],saturation=item['default_saturation'])
            result.append(row)
        for profile,saturation in [(1,[-5]*12),(2,[5]*12),(3,[-5,5]*6)]:
            row,_,_=self.pair(f'edge_S_p{profile}',profile,saturation=saturation)
            result.append(row)
        row,_,_=self.pair('alternate_header_owner',2,callback=0x603e9631)
        result.append(row)
        for record in (1,7,15):
            row,_,_=self.pair(f'operation_record_{record}',3,record=record)
            result.append(row)
        for name,p,kw in [('Natural',1,dict(key=2)),('MONO',1,dict(key=12)),
                          ('invalid_profile_0',0,{}),('invalid_profile_5',5,{}),
                          ('unknown_owner',1,dict(callback=0)),('non_record_slot',1,dict(record=-1)),('f00d',1,dict(special=True)),
                          ('custom_clean',1,dict(custom=True)),
                          ('custom_dirty',1,dict(custom=True,flags=0x10000000))]:
            row,_,_=self.pair(name,p,eligible=False,**kw)
            result.append(row)
        sequence=[]
        previous=None
        for turn,profile in enumerate((1,2,3,4,3,2,1,4)):
            row,previous,ctx=self.pair(f'switch_{turn}_p{profile}',profile,poison=previous)
            sequence.append(row)
        return dict(cases=result,same_S_switch_sequence=sequence)


    def reentry_gate(self):
        # The actual upstream caller tests this predicate before entering the
        # mother builder. Families 1/2 are admitted by format, not S equality.
        r=self.provider.Region
        out=[]
        for fmt in (0x0105,0x0205,0x0000):
            for profile in range(1,5):
                regions=self.fixture(profile)
                changed=[]
                for v in regions:
                    blob=bytearray(v.data)
                    if v.name=='job':struct.pack_into('<H',blob,11364+28,fmt)
                    if v.name=='context':struct.pack_into('<I',blob,24,Q+20)
                    changed.append(replace(v,data=bytes(blob)))
                v=self.call(f'reentry_{fmt:x}_{profile}',0x60339c27,4,
                            [r('rom',BASE,self.data,'rx'),*changed],{'a0':C},mask='a2')
                expected=int(fmt!=0)
                require(v['registers']['d0']==expected,'Upstream entry predicate changed')
                out.append(dict(input_format=hex(fmt),profile=profile,all_S_zero=True,
                                original_dirty_flag=0,admitted=bool(expected),instructions=v['completed']))
        return out

    def new_state(self):
        # Reuse the existing state container, not a second CPU interpreter.
        from penf_boot_emulator import BootState, HOOK_RETURN
        import ep7_t23_probe as existing
        existing.x=self
        existing.R=existing.r=self.provider.Region
        return existing.state_type(BootState,HOOK_RETURN)()

    def prefix(self, name, start, stop, regions, regs, frame=0, mask='d2,d3,a2,a3', limit=20000):
        r=self.provider.Region
        caller=0x18020000
        code=self.assemble(name+'_caller',f'call target,[{mask}],{frame}\nnop\n',symbols={'target':start})
        result=self.provider.execute([r('rom',BASE,self.data,'rx'),
            r('stack',STACK,bytes(0x2000),'rw',True),r('caller',caller,code,'rx'),*regions],
            {'pc':caller,'sp':SP,**regs},stop,limit=limit,trace_limit=limit)
        (self.out/(name+'.json')).write_text(json.dumps(result)+'\n')
        require(result['status']=='returned',name+': '+str(result.get('fault')))
        self.audit_alignment(result)
        return result

    def owners(self):
        r=self.provider.Region
        cases=[]
        for profile in range(1,5):
            s=self.new_state()
            fixtures=self.fixture(profile)
            for v in fixtures:
                if v.name not in ('context','output'):
                    s.regions.append(replace(v,permissions='rw',capture=True) if v.name=='job' else v)
            # Actual native handle lookup reads this one registered input row.
            handle_base=0x6223d178
            s.ram('handle1',handle_base+24,struct.pack('<6I',4,0,0,F,0,0),aliases=False)
            s.execute_call(0x6029b9d1,'',24,{'d0':1})
            require(s.regs['a0']==F,'Native image-handle pointer mismatch')
            # Native header creator supplies [callback, image owner]. Stop
            # before unrelated mode/geometry helpers, not at a fabricated RET.
            H=0x19800000
            s.ram('header',H,bytes(32),aliases=False)
            s.enter(0x603e611e,'d2,d3,a2,a3',24,{'a0':W,'a1':H})
            step=s.run({0x603e2c0d,0x603e6152},limit=1000)
            require(s.regs['pc']==0x603e2c0d,'Header diagnostic boundary changed')
            s.return_from_model(0)  # Diagnostics only; no settings or hardware response.
            step=s.run({0x603e6152},limit=1000)
            require(s.regs['pc']==0x603e6152,'Header prefix did not complete')
            require(struct.unpack('<2I',s.read(H,8))==(0x603e7b83,W),'Header parent link')
            # Execute the real 32-byte job header copy with retained inputs.
            s.regs.update(pc=0x60353915,sp=SP,a3=J,a2=H)
            step=s.run({0x60353922},limit=1000)
            require(s.regs['pc']==0x60353922,'Native job header copy stopped: '+str(step.get('fault')))
            require(struct.unpack('<2I',s.read(J+4,8))==(0x603e7b83,W),'Job parent link')
            cases.append(dict(profile=profile,handle=1,lookup='0x6029b9d1',
                              header_owner='header+4',job_owner='job+8',
                              snapshot='*(job.owner+28)',profile_offset=24083,
                              public_mode=(54,55,56,64)[profile-1],
                              source_model='Own registered handle row and snapshot; native lookup/header/copy executed',
                              diagnostic_boundary='0x603e2c0d',instructions=s.steps))
        record_cases=[]
        for index in (0,1,7,15):
            job=bytearray(15488)
            for i in range(index):struct.pack_into('<I',job,14576+56*i,J)
            req=bytearray(1884)
            token=0x19900000
            v=self.prefix('enqueue_'+str(index),0x60354bb0,0x60354bfe,[
                r('job',J,bytes(job),'rw',True),r('request',F,bytes(req),'rw',True),
                r('token',token,bytes(4),'rw',True)],
                {'a0':J,'a1':F,'d1':token,'d0':0},frame=24)
            j=self.captured(v,'job');q=self.captured(v,'request')
            parent,back=struct.unpack_from('<I',j,14576+56*index)[0],struct.unpack_from('<I',q,4)[0]
            require(parent==J and back==J+14576+56*index,'Native operation parent/backlink')
            record_cases.append(dict(record=index,parent_valid=True,request_backlink_valid=True,
                                     instructions=v['completed']))
        return dict(native_owner_cases=cases,native_enqueue_prefix=record_cases,
                    capture_creator='0x603e611e ->0x603537eb; direct caller0x603e6d34/3e',
                    second_creator='0x603e8a87 ->0x603537eb at0x603f2bb9; callback603e9631 (workflow not named)',
                    limits=['The original scheduler/acquisition/slot lifetime is not replayed.',
                            'Compact constructor60321ea8 uses another callback/owner layout: candidate returns stock.',
                            'Record and callback checks establish layout, not general memory-corruption resistance.',
                            'Constant values need stable per-image identity; future mutable recipes need copied values.'])

    def pack_and_upload(self, name, params, bank):
        r=self.provider.Region
        allocation=O-0x20c
        ctx=bytearray(208)
        struct.pack_into('<I',ctx,8,allocation)
        root=struct.pack('<2I',C,bank)
        # The first native upload-packer basic blocks OR the coefficient flag
        # unconditionally; they do not read context+60 or context+108.
        v=self.prefix(name+'_pack',0x60343b23,0x60343b72,[
            r('root',F,root),r('context',C,bytes(ctx)),
            r('allocation',allocation,bytes(12288),'rw',True)],{'a0':F},frame=20)
        flag=struct.unpack_from('<I',self.captured(v,'allocation'))[0]
        expected=8 if bank==0 else 0x40000
        require(flag==expected,'Native HSL upload flag missing')
        u=self.upload(name+'_writer',params,0x9f001000 if bank==0 else 0x9f805000)
        got=self.captured(u,'mmio')
        require(got[752:1040]==params[688:976],'ISP coefficient transfer differs')
        return dict(bank=bank,flag=hex(flag),packer_prefix='60343b23..60343b72',
                    writer='0x6034667e',all_288_coefficient_bytes_match=True,
                    H=[struct.unpack_from('<h',got,770+24*i)[0] for i in range(12)],
                    L=[struct.unpack_from('<h',got,774+24*i)[0] for i in range(12)],
                    instructions=v['completed']+u['completed'])

    def upload_sequences(self):
        previous=None
        out=[]
        for turn,p in enumerate((1,2,3,4,3,2,1,4)):
            _,params,_=self.pair('upload_sequence_'+str(turn),p,poison=previous)
            previous=params
            out.append(dict(profile=p,uploads=[self.pack_and_upload(f'up_{turn}_{b}',params,b) for b in (0,1)]))
        return out

    def placement(self):
        from ep7_hsl_install_checks import load, initializer
        from penf_code_space_audit import pointer_candidates, branch_candidates
        import subprocess
        for a,b in [(0x60045786,0x6004586c),(0x60067102,0x60067146),
                    (0x6018e19e,0x6018e214),(0x603d9f9e,0x603de100)]:
            self.disassemble(f'placement_{a:x}',a,b)
        helper=self.out/'relocated_helper.bin'
        helper.write_bytes(self.read(BASE+0x141c9e0,0x1800))
        text=subprocess.check_output([str(self.tools/'binutils/objdump'),'-D','-z','-b','binary',
            '-m','mn10300','--no-show-raw-insn','--adjust-vma=0x47000800',str(helper)],text=True)
        (self.out/'relocated_helper.asm').write_text(text)
        self.remember_instructions(text)
        _,loaded=load(self,self.candidate,'v2_load',0xa5)
        _,reload=load(self,self.candidate,'v2_reload',0x55)
        init=initializer(self)
        positive=initializer(self,True)
        refs=[]
        for address in (CAVE,CAVE+0x40000000,CAVE-0x1f980000,CAVE+0x20680000):
            for block in self.blocks:
                refs += [dict(component=block.index,alias_base=hex(address),**v) for v in pointer_candidates(block.payload,address,address+len(self.extension))]
        branches=branch_candidates(self.data,BASE,[(CAVE,CAVE+len(self.extension))])[0]
        classified=self.classify_resource_references(refs)
        require(len(classified)==6 and not branches,'Unresolved references into code cave')
        return dict(section=2,loaded_start='0x60280800',loaded_end_exclusive='0x6055e800',
                    extension_start=hex(CAVE),bytes=len(self.extension),
                    prefix_margin=64,suffix_margin=0x6055e800-CAVE-len(self.extension),
                    native_load=loaded,native_reload=reload,initializers=init,positive_control=positive,
                    raw_pointer_candidates=len(refs),classified_encoded_data=classified,branch_candidates=0,
                    limits='No computed-access/DMA/cache-concurrency or physical recovery proof')

    def classify_resource_references(self, refs):
        # Classify just the six candidates from the enlarged code span. This is
        # placement validation, not another image/resource/ART search.
        from io import BytesIO
        from PIL import Image
        import zlib
        result=[]
        for row in refs:
            data=self.blocks[row['component']].payload
            off=int(row['offset'],0)
            if row['component']==4:
                start=data.rfind(b'\xff\xd8\xff',0,off)
                end=data.find(b'\xff\xd9',start)+2
                require(start>=0 and start<off<end,'Candidate outside JPEG extent')
                stream=BytesIO(data[start:end])
                image=Image.open(stream)
                entropy_start=start+stream.tell()  # Pillow stops its header parser after SOS.
                require(entropy_start<=off and off+4<=end-2,'Candidate is not in JPEG entropy data')
                image.load()
                require(image.format=='JPEG','Resource format mismatch')
                result.append(dict(**row,classification='encoded JPEG data, Pillow full decode passed',
                                   containing_start=hex(start),containing_end=hex(end),entropy_start=hex(entropy_start),size=list(image.size)))
            elif row['component']==2:
                start=data.rfind(b'\x1f\x8b\x08',0,off)
                require(start>=0,'Compressed candidate start missing')
                decoder=zlib.decompressobj(31)
                decoded=decoder.decompress(data[start:])
                end=len(data)-len(decoder.unused_data)
                require(decoder.eof and start<off<end,'Candidate outside CRC-validated gzip stream')
                result.append(dict(**row,classification='encoded gzip data, zlib EOF/CRC validation passed',
                                   containing_start=hex(start),containing_end=hex(end),decoded_bytes=len(decoded)))
            else:raise ValueError('Unqualified pointer candidate in another component')
        return result

    def storage(self):
        r=self.provider.Region
        keys=[*range(927,963),*range(1655,1667)]
        resets=[]
        for key in keys:
            s=self.new_state()
            s.enter(0x602b9c4f,'d2,d3,a2',16,{'d0':0,'d1':key})
            observed=[]
            for _ in range(12):
                v=s.run({s.finish,0x602cbc0a,0x602b2250,0x602cc0d0},limit=10000)
                require(v['status']=='breakpoint','Reset reached unmodeled boundary: '+str(v.get('fault')))
                if s.regs['pc']==s.finish:break
                pc=s.regs['pc']
                if pc==0x602cbc0a:
                    require(s.regs['d0']==4508,'Unexpected reset environment key')
                elif pc==0x602b2250:
                    require(s.regs['a0']==key,'Reset callback key')
                else:
                    require(s.regs['d0']==key,'Reset ACTIVE key')
                    observed.append(dict(part=s.regs['d1'],value=s.regs['a0']))
                # Boundary records requested writes; no real settings are changed.
                s.return_from_model(0)
            require(s.regs['pc']==s.finish and s.regs['sp']==SP,'Reset did not return')
            require([v['part'] for v in observed]==[0,1],'Reset must target both parts')
            require(observed[0]['value']==observed[1]['value'],'Part defaults differ')
            resets.append(dict(key=key,requested_ACTIVE_writes=observed,instructions=s.steps))
        checks=[]
        size=0x40000
        for profile,key in enumerate((927,939,951,1655),1):
            data=bytearray(size)
            struct.pack_into('<H',data,0,7)
            offset=0x6250ba00-0x624ea400+4*(1769+key)
            struct.pack_into('<I',data,offset,0x4831f00f)
            caller=0x18020000
            code=self.assemble(f'checksum_{profile}_caller','call target,[a2],8\nnop\n',
                               symbols={'target':0x6005c7e7})
            v=self.provider.execute([r('rom',BASE,self.data,'rx'),r('caller',caller,code,'rx'),
                r('stack',STACK,bytes(0x2000),'rw',True),r('mode_record',F,bytes(data),'rw',True)],
                {'pc':caller,'sp':SP,'a0':F,'d0':size},caller+len(code),limit=2000000,
                trace_limit=32,trace_tail=True)
            require(v['status']=='returned','Mode checksum did not return')
            got=self.captured(v,'mode_record')
            require(sum(struct.unpack('<'+str(size//2)+'H',got))%65536==0,'Native Mode checksum mismatch')
            require(got[offset:offset+4]==data[offset:offset+4],'Checksum modified candidate cell')
            (self.out/f'mode_checksum_{profile}.json').write_text(json.dumps(v)+'\n')
            checks.append(dict(profile=profile,key=key,part=1,record_relative=offset,
                               native_checksum=struct.unpack_from('<H',got,2)[0],
                               all_halfwords_zero_sum=True,instructions=v['completed'],
                               model='Own full-sized Mode record; native checksum only, no backend write'))
        compare_cases=[]
        for key in (None,927,939,951,1655):
            baseline=bytearray(size)
            working=bytearray(baseline)
            if key is not None:
                off=0x6250ba00-0x624ea400+4*(1769+key)
                struct.pack_into('<I',working,off,0x4831f00f)
            descriptor=bytearray(24)
            struct.pack_into('<H',descriptor,0,7)
            struct.pack_into('<I',descriptor,4,F)
            struct.pack_into('<I',descriptor,16,F+size)
            struct.pack_into('<I',descriptor,20,size)
            caller=0x18020000
            code=self.assemble('compare_mode_'+str(key),'call backend,[d2,d3,a2,a3],24\nnop\n',
                               symbols={'backend':0x6005c5be})
            v=self.provider.execute([r('rom',BASE,self.data,'rx'),r('caller',caller,code,'rx'),
                r('stack',STACK,bytes(0x2000),'rw',True),r('descriptor',C,bytes(descriptor)),
                r('backing',F,bytes(baseline)),r('working',F+size,bytes(working))],
                {'pc':caller,'sp':SP,'a0':C},caller+len(code),breakpoints=[0x6005c5ff],
                limit=5000000,trace_limit=32,trace_tail=True)
            (self.out/f'mode_compare_{key}.json').write_text(json.dumps(v)+'\n')
            require(v['status']==('returned' if key is None else 'breakpoint'),
                    'Mode compare stopped: '+str((v['status'],v['registers']['pc'],v.get('fault'),v['completed'])))
            if key is not None:require(v['registers']['pc']==0x6005c5ff,'Storage boundary crossed')
            (self.out/f'mode_compare_{key}.json').write_text(json.dumps(v)+'\n')
            compare_cases.append(dict(key=key,only_part1_changed=key is not None,
                                      outcome='no write needed' if key is None else 'change detected before slot selection',
                                      instructions=v['completed'],native_stop=hex(v['registers']['pc'])))
        slot_cases=[]
        for second in (0,0xa2ab8000):  # Second nonzero address is a synthetic positive control.
            for index in (0,1):
                descriptor=bytearray(28)
                struct.pack_into('<H',descriptor,0,7)
                descriptor[2]=index
                struct.pack_into('<2I',descriptor,4,0xa2a78000,second)
                struct.pack_into('<I',descriptor,16,0x624ea400)
                struct.pack_into('<I',descriptor,20,0x40000)
                v=self.call(f'mode_slot_{second:x}_{index}',0x6005c4b2,16,[
                    r('rom',BASE,self.data,'rx'),r('descriptor',C,bytes(descriptor),'rw',True)],
                    {'a0':C},mask='d2,a2,a3')
                expected=0 if second==0 else 1-index
                require(v['registers']['d0']==expected and self.captured(v,'descriptor')[2]==expected,
                        'Native storage slot selection changed')
                slot_cases.append(dict(second_backing=hex(second),initial_index=index,selected=expected,
                                       actual_mode_layout=second==0,instructions=v['completed']))
        return dict(reset_cases=resets,checksum_cases=checks,backend_compare=compare_cases,slot_selection=slot_cases,
                    candidate_A='conditional',
                    actual_mode_backings=['0xa2a78000','0x0'],
                    power_loss_counterevidence='6005dc3a/4d configure one nonzero Mode backing;6005c4b2 keeps slot0. Generic two-slot code is not evidence of Mode redundancy.',
                    whole_reset='602b962f iterates keys0..1768, resets parts0/1;602b969e saves all9 banks',
                    mode_backend='6005f1fa ->6005c5be: compares payload+8..size-4; increments generation; checksums full record excluding checksum cell; stops before storage6005bc79',
                    reset_fixture='Declared environment key4508=0; native default lookup executed. Registered setters and ACTIVE setters record write intent and return0; no persistence modeled.',
                    reset_warning='Part1 is allocated alternate storage, not unused zero padding. Reset replaces it with the stock setting default.',
                    unproved=['Exhaustive computed/raw pointer consumers','E-P7 named backup import/export',
                              'Physical power-loss atomicity and recovery after torn settings writes'],
                    stock_revert='No new stock H/L interpretation established; native reset overwrites alternate cells; raw getters/debug can expose them. Not a proof of harmlessness for all stock consumers.',
                    candidate_B='Independent SD file avoids part1 ownership, but native parser, atomic replacement and image snapshot remain unverified; not implemented')


def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--upstream',required=True,type=Path)
    p.add_argument('--stock',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    x=Probe(a.upstream,a.stock,a.out)
    x.prepare()
    results=dict(schema_version=1,issue=58,baseline_main='fba762f87c5160d16fdefdab53701269c528e372',
                 stock_sha256=digest(a.stock.read_bytes()),main_sha256=digest(x.data),
                 extension_bytes=len(x.extension),extension_sha256=digest(x.extension),
                 decoded_candidate_sha256=digest(x.candidate),native_windows=x.windows)
    for name,method in [('matrix',x.matrix),('reentry_gate',x.reentry_gate),('owners',x.owners),('uploads',x.upload_sequences),
                        ('placement',x.placement),('storage',x.storage)]:
        results[name]=method()
        (x.out/'checkpoint.json').write_text(json.dumps(results,indent=2)+'\n')
    (x.out/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(dict(result='pass',cases=len(results['matrix']['cases']),
                         switches=len(results['matrix']['same_S_switch_sequence']))))


if __name__=='__main__': main()
