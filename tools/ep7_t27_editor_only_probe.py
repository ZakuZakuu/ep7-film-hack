#!/usr/bin/env python3
"""Finite native A/storage/stock-HTTP checks, not an editor release.

Source method reference: fishcu@539fcf1, read/run only. No network/camera or
package writer. Original firmware, native traces and generated code stay /tmp.
Program switches preserve an OWNED Mode RAM fixture, not physical flashing.
"""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import struct

from ep7_color_min import BASE, SP, digest, require
from ep7_t25_v4_probe import Probe as V4
from ep7_t25_storage_probe import MODE, SIZE, KEYS, encode, decode
from ep7_t27_editor_only_study import build
from ep7_t27_size_study import labels


class CoreProbe(V4):
    def prepare(self):
        super().prepare()
        self.v4_program, self.v4_labels = self.candidate, dict(self.labels)
        require(digest(self.v4_program) ==
                '670c4cffe6876bd7a2aa27162b53aab56a36e48ec1894ca8463d1ad568ba1f2b',
                'Frozen v4 decoded program changed')
        self.study = build(self.root, self.out/'source-build')
        directory = self.out/'source-build'
        self.a_labels = labels(self.tools/'binutils/nm-new', directory/'lab.elf')
        code = (directory/'lab-core.bin').read_bytes()
        require(len(code) <= 1276 and self.read(0x60210940,len(code))==b'\xff'*len(code),
                'A would extend outside the frozen v4 code footprint')
        image = bytearray(self.data)
        edits = [(0x60210940,code),(0x60210EC0,bytes(192)),
                 (0x603B14F3,self.assemble('A-image-site','jmp target\n',0x603B14F3,
                                         {'target':0x60210940})),
                 (0x602CBCB5,self.assemble('A-publish-site',
                    'call target,[d2,d3,a2,a3],40\n',0x602CBCB5,{'target':self.a_labels['publish']}))]
        for a,b in edits:image[a-BASE:a-BASE+len(b)]=b
        self.a_program = bytes(image)
        self.a_edits=[dict(address=hex(a),length=len(b),replacement_sha256=digest(b)) for a,b in edits]
        self.use('A')
        for a,z in ((0x60210940,0x60210940+len(code)),(0x603B14F3,0x603B14F8),
                    (0x602CBCB5,0x602CBCBC),(0x60888B35,0x60888B3C),
                    (0x60BD2A60,0x60BD2AE4),(0x60BD2785,0x60BD278C)):
            self.disassemble('A-native-'+hex(a),a,z)
        self.restore_checks=[]
        for a,n in ((0x60BD2A60,7),(0x60BD2A8F,7),(0x60BD2ABA,10),
                    (0x60BD2785,7),(0x60888B35,7)):
            expected=self.read(a,n)
            require(self.a_program[a-BASE:a-BASE+n]==expected,'Half EP71 hook retained')
            self.restore_checks.append(dict(address=hex(a),bytes=n,stock_sha256=digest(expected),
                                           exact_stock=True))

    def use(self, version, s=None):
        self.candidate={'A':self.a_program,'v4':self.v4_program,'stock':self.data}[version]
        self.labels=self.v4_labels if version=='v4' else self.a_labels
        self.image.write_bytes(self.candidate)
        if s is not None:
            s.regions=[replace(q,data=self.candidate[q.address-BASE:q.address-BASE+len(q.data)])
                if 'x' in q.permissions and BASE<=q.address<BASE+len(self.data) else q
                for q in s.regions]

    def local(self,s,key,axis,value):
        tag={'H':0x4751,'L':0x4752}[axis]
        s.enter(self.a_labels['a_apply'],'d2,d3',16,
                dict(d0=key,d1=(tag<<16)|(value&0xFFFF)))
        self.run_native(s,{s.finish})
        require(s.regs['sp']==SP,'A local commit stack')
        return s.regs['d0']

    def interoperation(self):
        self.use('v4');s=self.state();rows=[]
        # Same owned bank contents and original APIs across program changes.
        # No bank migration, erase or firmware update is simulated here.
        for key in (927,938,939,962,1655,1666):
            require(self.app(s,key,0x45510003)==0 and
                    self.app(s,key,0x4552FFFE)==0,'v4 seed through native app path')
            before=self.part_read(s,key)
            require(decode(before)==(3,-2),'v4 encoded pair')
            self.use('A',s)
            require(self.part_read(s,key)==before,'Program switch changed stored word')
            original_S=self.native(s,0x602CBC0A,'',4,dict(d0=key))
            require(self.local(s,key,'H',-7)==0,'A H native commit')
            require(self.part_read(s,key)==encode(-7,-2),'A failed to preserve L/format')
            require(self.local(s,key,'L',7)==0,'A L native commit')
            after=self.part_read(s,key)
            require(after==encode(-7,7),'A encoded word')
            require(self.native(s,0x602CBC0A,'',4,dict(d0=key))==original_S,'A changed S')
            pair=s.read(0x60210EC0+KEYS.index(key)*4,4)
            require(struct.unpack('<2h',pair)==(-7,7),'A publication mismatch')
            self.use('v4',s)
            require(self.part_read(s,key)==after,'Return to v4 lost pair')
            h=self.native(s,self.v4_labels['wifi_read'],'',4,dict(d0=0x8000|key))
            l=self.native(s,self.v4_labels['wifi_read'],'',4,dict(d0=0xC000|key))
            require((h,l)==(0xFFFFFFF9,7),'v4 interprets A data differently')
            rows.append(dict(key=key,v4_word=hex(before),A_word=hex(after),
                pair_after_A=[-7,7],v4_readback=[-7,7],S_unchanged=True,
                native_part_normal_edit_publication=True))
        self.use('A',s)
        before=s.read(MODE,SIZE),s.read(0x60210EC0,192)
        rejected=[]
        for key,axis,value in ((926,'H',1),(927,'H',8),(1655,'L',-8),(1667,'L',0)):
            require(self.local(s,key,axis,value)!=0,'Invalid local edit admitted')
            require(before==(s.read(MODE,SIZE),s.read(0x60210EC0,192)),'Rejected edit wrote')
            rejected.append(dict(key=key,axis=axis,value=value,no_write=True))
        s.write(0x62257B04,b'\1')
        require(self.local(s,927,'H',0)!=0,'Inhibited local edit admitted')
        require(before==(s.read(MODE,SIZE),s.read(0x60210EC0,192)),'Inhibited edit wrote')
        return dict(cases=rows,invalid=rejected,inhibit_no_write=True,
            limitation='Same owned bank RAM across native programs, NOT a physical cross-version firmware/reboot test')

    def stock_http(self):
        rows=[]
        for key,value in ((927,3),(1655,0xFFFFFFFB),(927,0x45510003),(927,0x4552FFFE)):
            outputs=[]
            for version in ('stock','A'):
                self.use(version);s=self.state()
                code,events=self.http(s,key,value)
                outputs.append((code,events,s.read(MODE,SIZE)))
            require(outputs[0]==outputs[1],'Original set_mcon behavior differs')
            rows.append(dict(key=key,value=hex(value),same_status_events_Mode=True))
        reads=[]
        for key in (927,1655,0xFFFF,0x839F,0xC39F):
            values=[]
            for version in ('stock','A'):
                self.use(version);s=self.state();values.append(self.query(s,key))
            require(values[0]==values[1],'Original get_mcon behavior differs')
            reads.append(dict(key=hex(key),value=hex(values[0]),stock_equal=True))
        self.use('A')
        return dict(set_mcon=rows,get_mcon=reads,stock_capability=True,
                    exact_stock_network_patch_sites=self.restore_checks,
                    limitation='Finite native HTTP parser/response fixtures; no radio connection')


def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('upstream','stock','out'):p.add_argument('--'+arg,required=True)
    a=p.parse_args();x=CoreProbe(a.upstream,a.stock,a.out);x.prepare()
    result=dict(passed=False,core_only=True,code_sha256=digest(x.a_program),
                installation_qualified=False,installer_created=False,camera_connected=False,
                A_edits=x.a_edits)
    def save(): (x.out/'A-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    try:
        result['interop']=x.interoperation();save()
        result['http']=x.stock_http();save()
        result['image_matrix']=x.image_matrix();save()
        result['boot_and_staging']=x.boot_and_staging();save()
        result['passed']=True;save()
    except Exception as e:
        result['error']=f'{type(e).__name__}: {e}';save();raise
    print(json.dumps(dict(passed=True,core_only=True,firmware_fit=False)))


if __name__=='__main__':main()
