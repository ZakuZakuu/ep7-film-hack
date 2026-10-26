#!/usr/bin/env python3
"""Original finite E142/1100 v3 checks; OEM outputs stay in private /tmp.

Reuse T24 fixtures and the pinned strict GNU engine. No device/settings writes,
no new simulator, and no installable firmware output. fishcu@539fcf1 is a
separately obtained read/run method reference, never copied implementation.
"""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from ep7_color_min import BASE, CAVE, STACK, SP, digest, require
from ep7_t24_probe import Probe as V2Probe, PATCH as V2PATCH, SYMBOLS as V2SYMBOLS
from ep7_t24_probe import SITE, RESUME, J, C, O, Q, ROWS, W

PATCH = Path(__file__).resolve().parents[1] / 'patches/hsl-profiles-preview/e-p7'
CURRENT = 0x6250f836
COMPACT = (0x60306ad5, 0x6031b4de, 0)
SYMBOLS = dict(V2SYMBOLS, ep7_compact_callback=COMPACT[0],
               ep7_compact_secondary_callback=COMPACT[1], ep7_current_profile=CURRENT)
WINDOWS = [
    (0x6031151e,0x6031155b), (0x6031b1e5,0x6031b211),
    (0x6030fe2b,0x6030fe81), (0x603132ca,0x6031335b),
    (0x60321d3b,0x60321eaf), (0x60353915,0x60353940),
    (0x603aaced,0x603aad5d), (0x603b17e6,0x603b1843),
    (0x603b1466,0x603b1517), (0x603af7b7,0x603af806),
    (0x603aade3,0x603aae13), (0x6005efbd,0x6005f005),
    (0x602cbd3b,0x602cbd97),
]


class Probe(V2Probe):
    def prepare(self):
        super().prepare()
        self.v2_extension, self.v2_candidate = self.extension, self.candidate
        self.v2_instructions = dict(self.instructions)
        self.instructions={pc:entry for pc,entry in self.instructions.items()
                           if not CAVE<=pc<CAVE+len(self.v2_extension)}
        self.extension = self.assemble('v3_extension',(PATCH/'hook.s').read_text(),CAVE,SYMBOLS)
        for pc,(op,args) in list(self.instructions.items()):
            # GNU's ELF listing annotates resolved absolute-memory symbols;
            # normalize only that syntax before the existing numeric audit.
            args=re.sub(r'\b([0-9a-f]+) <ep7_current_profile>',r'0x\1',args)
            self.instructions[pc]=(op,args)
        require(len(self.extension)<=464,'v3 exceeds qualified loaded suffix')
        changed=bytearray(self.data)
        changed[SITE-BASE:RESUME-BASE]=self.jump
        changed[CAVE-BASE:CAVE-BASE+len(self.extension)]=self.extension
        self.candidate=bytes(changed)
        # v2/v3 share addresses but have distinct instruction boundaries.
        self.v3_instructions = dict(self.instructions)
        self.windows=[]
        for start,end in WINDOWS:
            self.disassemble(f'native_{start:x}',start,end)
            self.windows.append(dict(start=hex(start),end_exclusive=hex(end),sha256=digest(self.read(start,end-start))))
        self.helper=self.read(BASE+0x141c9e0,0x1800)
        helper=self.out/'prepare_helper.bin'
        helper.write_bytes(self.helper)
        listing=subprocess.check_output([str(self.tools/'binutils/objdump'),'-D','-z','-b','binary',
            '-m','mn10300','--no-show-raw-insn','--adjust-vma=0x47000800',str(helper)],text=True)
        (self.out/'prepare_helper.asm').write_text(listing)
        self.remember_instructions(listing)
        self.v3_instructions=dict(self.instructions)

    def fixture(self, profile, *, compact=None, current=None, **kwargs):
        regions=super().fixture(profile,**kwargs)
        if compact is None:
            return regions  # Global current settings deliberately unmapped.
        result=[]
        for region in regions:
            if region.name in ('image_owner','snapshot'):
                continue  # A compact owner must never be interpreted as a snapshot.
            if region.name=='job':
                data=bytearray(region.data)
                struct.pack_into('<2I',data,4,compact,0 if compact==0 else W)
                region=replace(region,data=bytes(data))
            result.append(region)
        r=self.provider.Region
        result.append(r('current_profile',CURRENT,bytes([profile if current is None else current])))
        return result

    def compact_matrix(self):
        cases=[]
        for callback in COMPACT:
            for profile in range(1,5):
                row,_,_=self.pair(f'compact_{callback:x}_p{profile}',profile,compact=callback)
                cases.append(row)
        for callback in COMPACT[:2]:
            for record in range(16):
                row,_,_=self.pair(f'compact_slot_{callback:x}_{record}',3,compact=callback,record=record)
                cases.append(row)
        for name,kw in [('Natural',dict(key=2)),('MONO',dict(key=12)),
                        ('custom_clean',dict(custom=True)),
                        ('custom_dirty',dict(custom=True,flags=0x10000000)),('f00d',dict(special=True))]:
            row,_,_=self.pair('compact_exclusion_'+name,1,compact=COMPACT[0],eligible=False,**kw)
            cases.append(row)
        for current in (0,5,255):
            row,_,_=self.pair('compact_invalid_'+str(current),1,compact=COMPACT[0],current=current,eligible=False)
            cases.append(row)
        sequences=[]
        for callback in COMPACT:
            previous=None
            for turn,profile in enumerate((1,2,3,4,3,2,1,4)):
                row,previous,_=self.pair(f'compact_switch_{callback:x}_{turn}',profile,
                                       compact=callback,poison=previous)
                row['uploads']=[self.pack_and_upload(f'compact_isp_{callback:x}_{turn}_{bank}',previous,bank)
                                for bank in (0,1)]
                sequences.append(row)
        return dict(cases=cases,sequences=sequences)

    def owners_unchanged(self):
        result=[]
        image=self.candidate
        instruction_map=dict(self.instructions)
        for callback in (0x603e7b83,0x603e9631):
            for profile in range(1,5):
                fixture=self.fixture(profile,callback=callback)
                self.candidate=self.v2_candidate
                self.instructions=self.v2_instructions
                old=self.select(f'v2_owner_{callback:x}_{profile}',fixture,True)
                self.candidate=image
                self.instructions=instruction_map
                new=self.select(f'v3_owner_{callback:x}_{profile}',fixture,True)
                require(old['registers']==new['registers'],'v2/v3 owner ABI changed')
                for name in ('output','context'):
                    require(self.captured(old,name)==self.captured(new,name),'v2/v3 owner '+name)
                require(self.captured(old,'stack')[SP-STACK:]==self.captured(new,'stack')[SP-STACK:],
                        'v2/v3 owner live stack changed')
                result.append(dict(callback=hex(callback),profile=profile,all_registers_equal=True,
                                   output_context_and_live_stack_equal=True,global_settings_unmapped=True))
        return result

    def native_window(self,name,start,stop,regions,registers,image=None):
        r=self.provider.Region
        v=self.provider.execute([r('rom',BASE,self.data if image is None else image,'rx'),*regions],
                               {'pc':start,'sp':SP,**registers},stop,limit=30000,trace_limit=30000)
        (self.out/(name+'.json')).write_text(json.dumps(v)+'\n')
        require(v['status']=='returned',name+': '+str(v.get('fault')))
        self.audit_alignment(v)
        return v

    def native_paths(self):
        r=self.provider.Region
        result=[]
        descriptor=0x19800000
        for callback,entry in zip(COMPACT,(0x60311541,0x6031b1f8,0x6030fe2b)):
            stack=bytearray(0x2000)
            struct.pack_into('<I',stack,SP-STACK+8,descriptor+8)
            if callback:
                end=0x6031154a if entry==0x60311541 else 0x6031b201
                produced=self.native_window(f'header_literal_{callback:x}',entry,end,
                    [r('stack',STACK,bytes(stack),'rw',True),r('descriptor',descriptor,bytes(36),'rw',True)],
                    {'a0':descriptor+8,'d3':descriptor+8})
                input_data=self.captured(produced,'descriptor')
            else:
                produced=self.native_window('header_zero',entry,0x6030fe3a,
                    [r('stack',STACK,b'\xa5'*0x2000,'rw',True),
                     r('copied_helper',0x47000800,self.helper,'rx')],{})
                input_data=self.captured(produced,'stack')[SP-STACK+44:SP-STACK+80]
                require(input_data==bytes(36),'Native zero compact input initialization')
            require(struct.unpack_from('<I',input_data,8)[0]==callback,'Native compact callback producer')
            struct.pack_into('<I',stack,SP-STACK+28,descriptor)
            converted=self.native_window(f'header_convert_{callback:x}',0x60321d69,0x60321e9b,
                [r('stack',STACK,bytes(stack),'rw',True),r('descriptor',descriptor,input_data)],{'d2':0})
            header=self.captured(converted,'stack')[SP-STACK+40:SP-STACK+72]
            require(struct.unpack_from('<I',header)[0]==callback,'Native converted header callback')
            copied=self.native_window(f'header_to_job_{callback:x}',0x60353915,0x60353922,
                [r('stack',STACK,bytes(stack),'rw',True),r('header',descriptor,header),
                 r('job',J,bytes(15488),'rw',True)],{'a3':J,'a2':descriptor})
            require(self.captured(copied,'job')[4:36]==header,'Native header-to-job copy')
            result.append(dict(callback=hex(callback),literal_producer=hex(entry),
                               native_header_conversion='0x60321d69..0x60321e9b',
                               native_job_copy='0x60353915..0x60353922',
                               job_callback_offset=4,job_compact_owner_offset=8))
        dispatch=[]
        for fmt,stop in ((0x0105,0x603b17e6),(0x0205,0x603b1466)):
            regions=self.fixture(1,compact=COMPACT[0])
            regions=[replace(q,data=q.data[:11364+28]+struct.pack('<H',fmt)+q.data[11364+30:])
                     if q.name=='job' else q for q in regions]
            v=self.native_window(f'dispatch_{fmt:x}',0x603aaced,stop,
                [r('stack',STACK,bytes(0x2000),'rw',True),*regions],{'a0':C})
            dispatch.append(dict(format=hex(fmt),native_start='0x603aaced',native_stop=hex(stop),
                                 instructions=v['completed']))
        routes=[]
        for callback in COMPACT:
            for profile in range(1,5):
                regions=self.fixture(profile,compact=callback)
                value=self.native_window(f'parent_path_{callback:x}_{profile}',0x603b14b2,RESUME,
                    [r('stack',STACK,bytes(0x2000),'rw',True),*regions],{'d3':C},image=self.candidate)
                pcs={row['pc'] for row in value['trace']}
                require({SITE,0x603b0252,0x603b02d9,0x603b0068}<=pcs,'Actual selector/builder path missed')
                data=self.captured(value,'output')
                require([struct.unpack_from('<h',data,706+24*i)[0] for i in range(12)]==ROWS[profile-1][::2],
                        'Parent path H mismatch')
                routes.append(dict(callback=hex(callback),profile=profile,start='0x603b14b2',
                                   reached_hook_selector_builder=True,instructions=value['completed']))
        # The native typed scalar reader for key908's RDI63153 uses MOVBU.
        require(struct.unpack('<H',self.read(0x604d6c14+908*4,2))[0]==63153,'Leaf908 RDI changed')
        leaf=[]
        for profile in range(1,5):
            value=self.native_window(f'current_byte_{profile}',0x6005efc4,0x6005f002,
                [r('stack',STACK,bytes(0x2000),'rw',True),r('current',CURRENT,bytes([profile]))],
                {'d0':CURRENT,'d3':63153,'d2':0})
            require(value['registers']['d0']==profile,'Native profile byte width/value')
            leaf.append(dict(profile=profile,rdi=63153,bytes=1,native_load='0x6005f000'))
        return dict(header_producers=result,dispatch=dispatch,common_selector_routes=routes,current_leaf=leaf,
                    static_dispatch='603aaced ->603b17e6/603b1819 ->603b1466 ->603b14f3 ->603b0252 ->603b02d9',
                    limits='Segmented native producers and downstream path; complete RTOS/menu/frame acquisition not replayed')

    def current_interleaving(self):
        r=self.provider.Region
        load_pc=next(pc for pc,(op,args) in self.instructions.items()
                     if op=='movbu' and args=='(0x6250f836),d0')
        next_pc=min(pc for pc in self.instructions if pc>load_pc)
        cases=[]
        for when,cut,expected in (('before_byte_read',load_pc,2),('after_byte_read',next_pc,1)):
            regions=[r('rom',BASE,self.candidate,'rx'),r('stack',STACK,bytes(0x2000),'rw',True),
                     *self.fixture(1,compact=COMPACT[0])]
            first=self.provider.execute(regions,{'pc':SITE-2,'sp':SP,'d3':C},RESUME,
                                        breakpoints=[cut],limit=20000,trace_limit=20000)
            (self.out/('interleave_cut_'+when+'.json')).write_text(json.dumps(first)+'\n')
            require(first['status']=='breakpoint','Interleaving cut not reached: '+str((hex(cut),first['status'],first.get('fault'))))
            self.audit_alignment(first)
            saved={v['name']:bytes.fromhex(v['hex']) for v in first['memory']}
            resumed=[replace(v,data=bytes([2]) if v.name=='current_profile' else saved.get(v.name,v.data))
                     for v in regions]
            last=self.provider.execute(resumed,first['registers'],RESUME,limit=20000,trace_limit=20000)
            require(last['status']=='returned','Interleaving continuation failed')
            self.audit_alignment(last)
            data=self.captured(last,'output')
            values=[struct.unpack_from('<h',data,706+24*i+j)[0] for i in range(12) for j in (0,4)]
            require(values==ROWS[expected-1],'Torn/mixed profile row')
            (self.out/('interleave_'+when+'.json')).write_text(json.dumps(dict(before=first,after=last))+'\n')
            cases.append(dict(commit=when,selected_profile=expected,complete_row_only=True,
                              write_to_current_settings=False))
        return dict(cases=cases,current_load=hex(load_pc),width=1,
                    limit='Current-profile byte may select an old/new preview frame; no lock or end-to-end scheduling guarantee')

    def placement(self):
        # v3 is strictly inside the original v2 span. Reuse native loading,
        # initializer counterfactual and bounded reference classification.
        from ep7_hsl_install_checks import load, initializer
        from penf_code_space_audit import pointer_candidates, branch_candidates
        for a,b in [(0x60045786,0x6004586c),(0x60067102,0x60067146),
                    (0x6018e19e,0x6018e214),(0x603d9f9e,0x603de100)]:
            self.disassemble(f'placement_{a:x}',a,b)
        helper=self.out/'helper.bin'
        helper.write_bytes(self.read(BASE+0x141c9e0,0x1800))
        listing=subprocess.check_output([str(self.tools/'binutils/objdump'),'-D','-z','-b','binary',
            '-m','mn10300','--no-show-raw-insn','--adjust-vma=0x47000800',str(helper)],text=True)
        (self.out/'helper.asm').write_text(listing)
        self.remember_instructions(listing)
        _,first=load(self,self.candidate,'v3_load',0xa5)
        _,second=load(self,self.candidate,'v3_reload',0x55)
        init,negative=initializer(self),initializer(self,True)
        refs=[]
        for address in (CAVE,CAVE+0x40000000,CAVE-0x1f980000,CAVE+0x20680000):
            for block in self.blocks:
                refs += [dict(component=block.index,alias_base=hex(address),**v)
                         for v in pointer_candidates(block.payload,address,address+len(self.extension))]
        branches=branch_candidates(self.data,BASE,[(CAVE,CAVE+len(self.extension))])[0]
        require(not branches,'Unresolved transfer to v3 cave')
        classified=self.classify_resource_references(refs)
        require(len(classified)==len(refs),'Unclassified cave references')
        return dict(section=2,start=hex(CAVE),end_exclusive=hex(CAVE+len(self.extension)),
                    bytes=len(self.extension),prefix_margin=64,suffix_margin=0x6055e800-CAVE-len(self.extension),
                    native_load=first,native_reload=second,initializers=init,
                    initializer_counterfactual=negative,classified_references=classified,
                    direct_branch_candidates=0,
                    limits='No physical DMA/cache/concurrency/recovery guarantee')


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream',required=True,type=Path)
    parser.add_argument('--stock',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    x=Probe(args.upstream,args.stock,args.out)
    x.prepare()
    result=dict(issue=63,stock_sha256=digest(args.stock.read_bytes()),main_sha256=digest(x.data),
                extension_bytes=len(x.extension),extension_sha256=digest(x.extension),
                decoded_candidate_sha256=digest(x.candidate),native_windows=x.windows)
    for name,method in [('long_matrix',x.matrix),('owners_unchanged',x.owners_unchanged),
                        ('long_uploads',x.upload_sequences),
                        ('compact_matrix',x.compact_matrix),('native_paths',x.native_paths),
                        ('current_interleaving',x.current_interleaving),
                        ('reentry_gate',x.reentry_gate),('placement',x.placement)]:
        result[name]=method()
        (x.out/'checkpoint.json').write_text(json.dumps(result,indent=2)+'\n')
    (x.out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(result='pass',extension_bytes=len(x.extension),
                          owner_cases=len(result['owners_unchanged']),
                          compact_cases=len(result['compact_matrix']['cases']))))


if __name__=='__main__':main()
