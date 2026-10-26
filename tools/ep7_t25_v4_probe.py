#!/usr/bin/env python3
"""Original T25 v4 finite native experiment; OEM bytes/traces remain under /tmp.

Uses pinned upstream GNU engine, not copied upstream code. Explicit RTOS, HTTP
response, UI side-consumer and allocation models; unknown accesses fail closed.
No camera/network I/O or installable package generation.
"""
import argparse,os,sys,json,struct,re,subprocess
from dataclasses import replace
from pathlib import Path
from ep7_t25_storage_probe import Probe as Storage,MODE,SIZE,ACTIVE,KEYS,encode
from ep7_color_min import BASE,SP,STACK,require,digest
from ep7_t24_1_probe import Probe as Preview,COMPACT
from ep7_t24_probe import O,C,SITE,RESUME
PATCH=Path(__file__).resolve().parents[1]/'patches/hsl-recipes/e-p7'
EXTENSION,MIRROR=0x60210940,0x60210ec0
SERVICE_CUTS={0x602f3f17,0x602b5f59,0x60827954}
L_STEPS=[-300,-250,-200,-150,-100,-50,-25,0,25,50,100,150,200,250,300]
class Probe(Storage):
 def prepare(self):
  super().prepare()
  self.symbols=json.loads((PATCH/'symbols.json').read_text())
  self.extension=self.assemble('v4',(PATCH/'hook.s').read_text(),0x60210940,self.symbols)
  nm=subprocess.check_output([str(self.tools/'binutils/nm-new'),str(self.out/'v4.elf')],text=True)
  self.labels={b:int(a,16) for a,t,b in [s.split() for s in nm.splitlines() if len(s.split())==3]}
  value=bytearray(self.data)
  for a,b in [(0x603b14f3,self.assemble('imagejump','jmp ep7_extension\n',0x603b14f3,{'ep7_extension':0x60210940})),(0x60210940,self.extension),(0x60210ec0,bytes(192))]:value[a-BASE:a-BASE+len(b)]=b
  for a,label,mask,frame in [(0x60bd2a60,'id_parse','d2,d3,a2,a3',16),(0x60bd2a8f,'value_parse','d2,d3,a2,a3',16),(0x60bd2aba,'wifi_write','d2,d3',12),(0x60bd2785,'wifi_read','',4),(0x60888b35,'app_edit','d2,d3',16),(0x602cbcb5,'publish','d2,d3,a2,a3',40)]:
   b=self.assemble(label+'_jump',f'call target,[{mask}],{frame}\n',a,{'target':self.labels[label]});assert len(b)==7
   value[a-BASE:a-BASE+7]=b
  value[0x60bd2ac1-BASE:0x60bd2ac4-BASE]=self.assemble('nops','nop\nnop\nnop\n',0x60bd2ac1)
  self.candidate=bytes(value)
  self.edits=[(0x603b14f3,5),(EXTENSION,len(self.extension)),(MIRROR,192),
              (0x60bd2a60,7),(0x60bd2a8f,7),(0x60bd2aba,10),(0x60bd2785,7),(0x60888b35,7),(0x602cbcb5,7)]
  for a,b in [(0x602cbc58,0x602cbd98),(0x602cc540,0x602cc580),
              (0x60bd2709,0x60bd2866),(0x60bd2a18,0x60bd2ae4),
              (0x60bd2044,0x60bd20a8),(0x60bd548d,0x60bd5570),
              (0x60888552,0x6088859b),(0x60888b11,0x60888b45),
              (0x60e083d5,0x60e0844d),(0x60343b23,0x60343b72),
              (0x602b8916,0x602b8b18),(0x603b1466,0x603b1517),(0x603af871,0x603b0345)]:
   self.disassemble('native_'+hex(a),a,b)
   self.windows.append(dict(start=hex(a),end_exclusive=hex(b),sha256=digest(self.read(a,b-a))))
  for pc,(op,args) in list(self.instructions.items()):
   args=re.sub(r'\b([0-9a-f]+) <[^>]+>',r'0x\1',args)
   self.instructions[pc]=(op,args)
  self.boundaries=[]
  self.rets=self.assemble('service_rets','rets\n')
 def new_state(self):
  s=super().new_state();from dataclasses import replace
  s.regions=[replace(q,data=self.candidate) if q.name=='rom' else q for q in s.regions]
  s.ram('mirror',0x60210ec0,bytes(192))
  return s
 def state(self):
  s=super().state()
  for name,a,n in [('attr',1646550856,64*4+439*8),('conversion',1646560552,128*4+1333*8)]:s.ram(name,a,bytes(n))
  self.native(s,0x602b16f7,'d2,a2,a3',12,{})
  self.native(s,0x602ba4cc,'d2,a2,a3',12,{})
  # Native per-key fast pointer cache. Only qualified COLOR / tone cells need pointers.
  s.ram('record_index',0xa26ffa88,bytes(4096*8))
  self.native(s,0x6005d987,'d2,d3,a2,a3',48,{'a0':0x60096f98,'a1':MODE+8,'d0':0xa26ffa88})
  s.ram('secondary_index_enable',0xa26ffa84,bytes(2))
  s.ram('pointer_enable',0xa269bf68,b'\1')
  ptrs=bytearray(1769*4)
  # Native metadata index is built above; an empty fast cache fills lazily.
  s.ram('current_pointer_cache',(-1570136908)&0xffffffff,ptrs)
  s.ram('event_diagnostics_disabled',0x6224bd3c,bytes(2))
  s.ram('native_notifications',0x61f9ec18,struct.pack('<2I',0x608276d2,0x60bd93cb))
  s.ram('notification_state',0x61fa72b8,bytes(4))
  s.ram('event_log_channels',0x61f9ec34,bytes(8))
  s.ram('composite_ring',1646549572,bytes(20*64+1))
  s.write(0x6250f836,b'\1')
  s.write(0x6250f278,b'\x00')
  return s
 def model(self,s,pc):
  # These are unrelated UI consistency/side-consumer/notification cuts. The
  # registered setting conversion, typed write and COLOR callbacks execute.
  self.boundaries.append(dict(pc=hex(pc),key=s.regs['d0']))
  if pc==0x602b5f59:
   from penf_boot_emulator import HOOK_RETURN
   require(s.regs['mdr']==0x602b14a4,'Unreviewed indirect callback return')
   s.write(HOOK_RETURN,self.rets+b'\xcb'*6)
   s.regs.update(pc=HOOK_RETURN,d0=0)
  else:s.return_from_model(0)

 def run_native(self,s,stops,limit=500000):
  for _ in range(200):
   v=s.run(set(stops)|SERVICE_CUTS,limit=limit)
   if v['status']=='breakpoint' and s.regs['pc'] in SERVICE_CUTS:
    self.model(s,s.regs['pc']);continue
   require(v['status']=='breakpoint' and s.regs['pc'] in stops,
           'Unmodeled native boundary: '+str((hex(s.regs['pc']),v['status'],v.get('fault'))))
   return v
  raise ValueError('Finite service cut budget exhausted')

 def app(self,s,key,word):
  s.enter(self.labels['app_edit'],'d2,d3',16,{'d0':key,'d1':word})
  self.run_native(s,{s.finish})
  require(s.regs['sp']==SP,'App ABI stack')
  return s.regs['d0']

 def http(self,s,key,word,raw_id=None,raw_value=None):
  params=bytearray(122)
  struct.pack_into('<H',params,0,2)
  for n,(name,value) in enumerate((('mode',key),('value',word))):
   off=2+n*60
   params[off:off+len(name)]=name.encode()
   text=((raw_id if name=='mode' else raw_value) or f'{value&0xffffffff:X}').encode()
   params[off+30:off+30+len(text)]=text
  s.ram('parsed_http_query',0x1b000000,params,aliases=False)
  s.ram('native_pending',0xa26a4524,bytes(12))
  s.ram('app_received',0x1b000080,bytes(8),aliases=False)
  s.ram('wifi_diagnostics',0xa26a40e0,bytes(4))
  s.ram('remote_property_cache_absent',0xa26a4108,bytes(4))
  s.enter(0x60bd2a18,'',0,{'a0':0x1b100000,'a1':0x1b000000})
  posts=[]
  for _ in range(4):
   self.run_native(s,{0x60bd548d,0x60bc43a3})
   if s.regs['pc']==0x60bc43a3:
    code=s.regs['d0'];s.return_from_model(0)
    self.run_native(s,{s.finish});return code,posts
   require(s.regs['d0']==0x041b0011,'Unexpected event ID')
   posts.append(struct.unpack('<3I',s.read(0xa26a4524,12)))
   # HTTP service is suspended while the same native pending record is read
   # on an explicitly selected, serialized application worker. RTOS transport,
   # rec admission, scheduling and timeout are not fabricated CPU execution.
   saved=dict(s.regs);finish=s.finish;http_stack=s.read(STACK,0x3000)
   self.native(s,0x60bd2044,'d2,a2,a3',16,
               {'a0':0x1b000080,'a1':0x1b000082,'d0':0x1b000084})
   k,t,val=struct.unpack('<HHI',s.read(0x1b000080,8))
   require((k,t,val)==posts[-1],'Native pending receiver changed value')
   # Native application front dispatch, including its call to 60888b11 and
   # the actual patched 60888b35 CALL. Stop after this normal-edit return.
   s.enter(0x60888552,'d2,d3,a2',24,{'d0':k,'a0':0,'a1':val})
   # The wrapper stores A1's scalar on its stack and passes its address onward.
   s.run({0x608886ff},limit=500)
   require(s.regs['pc']==0x608886ff,'Application logging boundary')
   s.return_from_model(0)
   self.run_native(s,{0x60888b3c})
   app_result=s.regs['d0']
   s.write(STACK,http_stack);s.regs=saved;s.finish=finish
   # Stock event completion is modeled separately from actual application
   # effect. HTTP success is explicitly NOT a durable commit receipt.
   s.return_from_model(0 if app_result==0 else 1)
  raise ValueError('Unexpected repeated HTTP event')

 def protocol_matrix(self):
  s=self.state();out=[]
  # The two registered native notification callbacks remain installed; their
  # unrelated application queue is an explicit model boundary.
  for slot,key in enumerate((927,939,951,1655),1):
   for tag,value in [(0x4551,-7),(0x4551,7),(0x4552,-7),(0x4552,7),
                     (0x4550,-5),(0x4550,5)]:
    code,posts=self.http(s,key,(tag<<16)|(value&65535))
    require(code==200 and len(posts)==1,'Valid marked scalar rejected')
    read=self.native(s,self.labels['wifi_read'],'',4,
                     {'d0':key|(0x8000 if tag==0x4551 else 0xc000 if tag==0x4552 else 0)})
    require(read==value&0xffffffff,'Marked write/read mismatch '+str((slot,tag,value,hex(read),s.read(MIRROR+48*(slot-1),4).hex(),s.read(0x6250f860,8).hex())))
    out.append(dict(slot=slot,tag=hex(tag),value=value,http=code,event_count=1))
  scalar=[]
  for key in [963,964,965,966,967,968,969,970,971,1672,1673,1674,1667,1668,1669,1670]:
   maximum=5 if 1667<=key<=1670 else 7
   for value in (-maximum,maximum):
    code,posts=self.http(s,key,(0x4550<<16)|(value&65535))
    got=self.native(s,self.labels['wifi_read'],'',4,{'d0':key})
    require(code==200 and got==value&0xffffffff,'Native tone/shading unit conversion')
    scalar.append(dict(key=key,value=value,native_readback_signed=value))
  invalid=[]
  for key,tag,value in [(926,0x4551,0),(927,0x4553,0),(927,0x455f,0),
                        (927,0x4551,8),(927,0x4552,-8),(927,0x4550,6),
                        (1667,0x4550,6),(963,0x4551,1),(972,0x4550,0),(65535,0x4550,0),(0x1039f,0x4551,0)]:
   before=s.read(MODE,SIZE),s.read(MIRROR,192)
   code,posts=self.http(s,key,(tag<<16)|(value&65535))
   require(code==520 and not posts and before==(s.read(MODE,SIZE),s.read(MIRROR,192)),
           'Invalid family escaped to raw setter or modified settings')
   invalid.append(dict(key=key,tag=hex(tag),value=value,status=code,no_event_or_settings_write=True))
  for raw_id,raw_value in [('1039F','45510003'),('10000039F','45510003'),('039F','455100003'),('039F','4551000G'),('0039F','45510003')]:
   before=s.read(MODE,SIZE),s.read(MIRROR,192)
   code,posts=self.http(s,927,0,raw_id=raw_id,raw_value=raw_value)
   require(code==520 and not posts and before==(s.read(MODE,SIZE),s.read(MIRROR,192)),'Malformed marked parser bypass')
   invalid.append(dict(raw_id=raw_id,raw_value=raw_value,status=code,no_event_or_settings_write=True))
  s.write(0x62257b04,b'\x01')
  before=s.read(MODE,SIZE),s.read(MIRROR,192)
  code,posts=self.http(s,927,0x45510003)
  require(code==520 and len(posts)==1 and before==(s.read(MODE,SIZE),s.read(MIRROR,192)),'Native inhibit guard bypass')
  s.write(0x62257b04,b'\0')
  capability=self.native(s,self.labels['wifi_read'],'',4,{'d0':65535})
  require(capability==0x45503731,'Capability identity')
  return dict(native_inhibit_rejects_without_write=True,marked=out,scalar_units=scalar,invalid=invalid,capability=hex(capability)),s

 def imaging(self,s):
  # One complete marked H/L chain with COLOR actually active. Native COLOR
  # callback builds/publishes its effective 12 S values, then original builder
  # and upload functions run on those values and the new mirror.
  s.write(0x6250f278,b'\x0b')
  s.write(0x6250f836,b'\x01')
  self.http(s,927,0x45510003)
  self.http(s,927,0x4552fffe)
  row=struct.unpack('<24h',s.read(MIRROR,48))
  require(row[:2]==(3,-2),'Expected published H/L row')
  view=Preview.__new__(Preview);view.__dict__.update(self.__dict__)
  saturation=list(struct.unpack('<12h',s.read(0x6250f848,24)))
  result=[]
  for compact in (None,COMPACT[0],COMPACT[1],0):
   regions=view.fixture(1,compact=compact,saturation=saturation)
   regions.append(self.provider.Region('mirror',MIRROR+0x40000000,s.read(MIRROR,192)))
   stock=self.select('v4_image_stock_'+str(compact),regions,False)
   new=self.select('v4_image_'+str(compact),regions,True)
   require(stock['registers']==new['registers'],'Image ABI changed')
   a=self.captured(stock,'output');b=self.captured(new,'output')
   expected=bytearray(a)
   for i in range(12):
    struct.pack_into('<h',expected,706+i*24,-1000*row[i*2])
    struct.pack_into('<h',expected,710+i*24,L_STEPS[row[i*2+1]+7])
   require(b==expected,'Unexpected native parameter output')
   result.append(dict(compact=None if compact is None else hex(compact),registers_equal=True,
                      H0=struct.unpack_from('<h',b,706)[0],L0=struct.unpack_from('<h',b,710)[0],
                      uploads=[self.pack_and_upload('v4_isp_'+str(compact)+'_'+str(bank),b,bank) for bank in (0,1)]))
  return dict(chain='native query parser -> pending -> modeled RTOS delivery -> native app dispatcher/registered setter -> part API -> typed COLOR publication -> mirror -> native constructor -> ISP writer',
              cases=result,physical_pixels_not_emulated=True)

 def boot_and_staging(self):
  s=self.state()
  # Execute the exact current-record update used by native key loop 602cc540.
  for i,key in enumerate(KEYS):self.part_write(s,key,encode(i%15-7,(i*2)%15-7))
  require(s.read(MIRROR,192)==bytes(192),'Mirror must begin neutral')
  for key in KEYS:
   s.regs={'pc':0x602cc56f,'sp':SP,'a3':0x1b200000,'d2':key,'psw':0}
   s.ram('boot_loop_live_word',0x1b200000,bytes(4),aliases=False)
   self.run_native(s,{0x602cc576})
  old=s.read(MIRROR,192)
  require(old!=bytes(192),'Native boot loop failed to initialize mirror')
  self.part_write(s,927,encode(0,0))
  require(s.read(MIRROR,192)==old,'ACTIVE staging leaked to mirror')
  self.native(s,0x602cbc74,'d2,d3,a2',20,{'d0':927,'d1':0})
  require(s.read(MIRROR,4)==bytes(4),'Native publication failed to replace pair')
  # Unknown stored versions and -8 fail closed on the actual assembled decoder.
  for bad in (0,0xffffffff,0xe7420000,0xe7417788,0xe741fe00):
   self.part_write(s,927,bad)
   self.native(s,0x602cbc74,'d2,d3,a2',20,{'d0':927,'d1':0})
   require(s.read(MIRROR,4)==bytes(4),'Invalid cell not neutral')
  return dict(native_boot_refresh_cells=48,boot_loop='602cc540 ->602cbc74 ->602cbcb5',
              staging_does_not_publish=True,invalid_cells_neutral=5,
              NVS_reload_not_emulated=True)

 def publication_abi(self):
  cases=[]
  for index in (0,11,12,35,36,47):
   outputs=[]
   for target in (0x6005ea22,self.labels['publish']):
    s=self.state()
    self.part_write(s,KEYS[index],encode(3,-2))
    s.enter(target,'d2,d3,a2,a3',40,{'d0':0xf6fa,'d1':index,'a0':0x6250f860,'a1':4})
    s.regs.update(mdrq=0xa5a51234)
    self.run_native(s,{s.finish})
    outputs.append(s)
   a,b=outputs
   require(a.regs==b.regs,'Publication changed typed writer ABI: '+str(index))
   require(a.read(MODE,SIZE)==b.read(MODE,SIZE),'Publication changed native typed values')
   require(struct.unpack('<2h',b.read(MIRROR+index*4,4))==(3,-2),'Publication pair')
   cases.append(dict(index=index,all_registers_and_Mode_equal=True,mirror_pair=[3,-2]))
  return dict(cases=cases,MDRQ_and_all_registers_equal=True)

 def image_matrix(self):
  view=Preview.__new__(Preview);view.__dict__.update(self.__dict__)
  rows=[[(i+p)%15-7 for i in range(24)] for p in range(4)]
  mirror=struct.pack('<96h',*(v for row in rows for v in row))
  cases=[(p,dict(compact=k),True) for p in range(1,5) for k in (None,*COMPACT)]
  cases += [(3,dict(compact=COMPACT[0],record=i),True) for i in range(16)]
  cases += [(2,dict(callback=0x603e9631),True)]
  cases += [(1,kw,False) for kw in [dict(key=2),dict(key=12),dict(special=True),dict(custom=True),
             dict(callback=0x12345678),dict(record=-1),dict(compact=COMPACT[0],current=0),
             dict(compact=COMPACT[0],current=5),dict(compact=COMPACT[0],current=255)]]
  result=[];previous=None
  for n,(p,kw,eligible) in enumerate(cases):
   regions=view.fixture(p,poison=previous,**kw)
   if eligible:regions.append(self.provider.Region('mirror',MIRROR+0x40000000,mirror))
   old=self.select(f'v4_matrix_{n}_stock',regions,False)
   new=self.select(f'v4_matrix_{n}_new',regions,True)
   require(old['registers']==new['registers'],'v4 image ABI/PSW/MDR/loop register change')
   require(self.captured(old,'context')==self.captured(new,'context'),'v4 context changed')
   require(self.captured(old,'stack')[SP-STACK:]==self.captured(new,'stack')[SP-STACK:],'v4 live stack changed')
   expected=bytearray(self.captured(old,'output'));slot=kw.get('current',p)
   if eligible:
    for i in range(12):
     struct.pack_into('<h',expected,706+i*24,-1000*rows[slot-1][i*2])
     struct.pack_into('<h',expected,710+i*24,L_STEPS[rows[slot-1][i*2+1]+7])
   previous=self.captured(new,'output')
   require(previous==expected,'v4 profile/slot/exclusion parameter mismatch')
   result.append(dict(profile=p,eligible=eligible,fixture=kw,ABI_equal=True,only_expected_HL=True,
                      inaccessible_mirror_when_excluded=not eligible))
  return result

 def query(self,s,key):
  params=bytearray(62);struct.pack_into('<H',params,0,1)
  params[2:6]=b'mode';text=f'{key:04X}'.encode();params[32:32+len(text)]=text
  s.ram('read_query',0x1c000000,params,aliases=False)
  for i in range(2):s.ram('http_heap_'+str(i),0x1c100000+i*0x10000,bytes(16384),aliases=False)
  s.enter(0x60bd2709,'',0,{'a0':0x1c200000,'a1':0x1c000000})
  allocations=0
  while True:
   self.run_native(s,{0x60022782,0x60bc43a3})
   if s.regs['pc']==0x60bc43a3:
    require(s.regs['d0']==200 and allocations==2,'Native get response')
    length=struct.unpack('<I',s.read(s.regs['sp']+32,4))[0]
    body=s.read(s.regs['a1'],length).decode('ascii')
    (self.out/'query-private.json').write_text(json.dumps(dict(length=length,registers=s.regs,body=body,events=s.events)))
    import xml.etree.ElementTree as ET
    node=ET.fromstring(body)
    require(node.tag=='response' and len(node)==1 and node[0].tag=='value','Native response schema')
    value=node[0].text
    require(re.fullmatch('[0-9A-Fa-f]{1,8}',value or '') is not None,'Native response hex')
    return int(value,16)
   require(s.regs['d0']==16384 and allocations<2,'Unexpected HTTP allocation')
   address=0x1c100000+allocations*0x10000;allocations+=1
   s.return_from_model(0);s.regs['a0']=address

 def read_and_stock(self):
  s=self.state()
  cap=self.query(s,0xffff);require(cap==0x45503731,'Native capability query')
  bad=self.query(s,0x8000|926);require(bad==0x80000000,'Invalid axis ID read')
  self.http(s,939,0x4551fffd)
  h=self.query(s,0x8000|939);require(h==0xfffffffd,'Native H query response')
  result=[]
  for key,val,raw_id,raw_value in [(927,3,None,None),(939,-5,None,None),(1655,5,None,None),(909,2,None,None),(927,3,'10000039F','000000003'),(927,0x4551,None,None)]:
   new=self.state();code,events=self.http(new,key,val&0xffffffff,raw_id,raw_value)
   old=self.state()
   # Restore OEM executable regions only; private RAM fixtures are identical.
   def original(q):
    if q.name.startswith('rom'):
     off=q.address-BASE;return replace(q,data=self.data[off:off+len(q.data)])
    return q
   old.regions=[original(q) for q in old.regions]
   stockcode,stockevents=self.http(old,key,val&0xffffffff,raw_id,raw_value)
   require(code==stockcode==200 and not events and not stockevents,'Ordinary command route changed')
   require(old.read(MODE,SIZE)==new.read(MODE,SIZE),'Ordinary command changed native settings behavior')
   result.append(dict(key=key,value=val,native_Mode_equal=True,no_app_event=True))
  stock=self.state()
  stock.regions=[original(q) for q in stock.regions]
  require(self.query(stock,0xffff)==0,'Stock capability control')
  return dict(native_XML_get=True,capability=hex(cap),stock_capability=0,invalid_axis=hex(bad),
              signed_H_response=hex(h),ordinary_regressions=result)

 def classify_v4_references(self,refs):
  from io import BytesIO
  from PIL import Image
  out=[]
  squashed=self.blocks[2].payload[0x21367e0:0x2472fc7]
  require(digest(squashed)=='de0fe0b6ee12013d89f6c0bff455d8c03893f8bd05fc9d8ba5716076897c7f79',
          'Previously validated SquashFS changed')
  self.disassemble('cmio_extent',0x6036e227,0x6036e259)
  require(self.instructions[0x6036e228]==('mov','1616440640,d0') and
          self.instructions[0x6036e23e]==('mov','164928,d0'),'Native CMIO bounds changed')
  # Original short ISA witnesses demonstrate that apparent flash pointers
  # straddle multiple instructions; they are not u32 address operands.
  sp_moves=[0x60802b6f,0x60802d89,0x6080385b,0x6080391c,0x60804202,0x613d01b5]
  for row in refs:
   component=row['component'];off=int(row['offset'],0);data=self.blocks[component].payload
   facts={k:v for k,v in row.items() if k!='source_hex'}
   if component==2 and 0x21367e0<=off and off+4<=0x2472fc7:
    out.append(dict(**facts,classification='Exact previously validated SquashFS bytes; serialized filesystem, not MN103 text',
                    source='research/e142-squashfs-validation.md'));continue
   if component==2 and 0x1e81fe0<=off<0x2136134:
    import zlib
    dec=zlib.decompressobj(31);payload=dec.decompress(data[0x1e81fe0:])
    require(dec.eof and len(data)-len(dec.unused_data)==0x2136134,'Validated gzip extent changed')
    out.append(dict(**facts,classification='gzip encoded data; zlib EOF/CRC passed',decoded_sha256=digest(payload)))
    continue
   if component==0 and 0x6058ed40-BASE<=off and off+4<=0x605b7180-BASE:
    out.append(dict(**facts,classification='Serialized CMIO data within native source/copy extent',
                    native_copy='0x6036e227..0x6036e259',start='0x6058ed40',end='0x605b7180'));continue
   if component==0:
    a=BASE+off;start=a;skip=0
    if a in (0x60034663,0x60036c62):text='add 12,d2\nmov d2,d1\nmov 32,d0\n'
    elif a in sp_moves:text='mov (12,sp),a1\nmov d2,d1\nmov 1,d0\n'
    elif a in (0x60e955ec,0x60e95671):text='mov (a2),a2\nmov d2,d1\nmov 1,d0\n'
    elif a==0x60deee51:
     start=a-1;skip=1;text='mov (12,a0),a0\nmov d2,d1\nmov 1,d0\n'
    elif a==0x6098803c:
     start=0x60988037;skip=a-start
     text='call target,[d2,a2],12\nmov d2,d1\nmov 4,d0\n'
    elif a==0x612c9756:text='beq target\nmov d2,d1\nmov 1,d0\n'
    else:raise ValueError('Unclassified native placement literal '+hex(a))
    target=0x60767ee5 if a==0x6098803c else 0x612c9760
    witness=self.assemble('literal_witness_'+hex(a),text,start,{'target':target})
    require(witness[skip:skip+4]==self.read(a,4),'Instruction-straddling witness differs')
    self.disassemble('literal_boundaries_'+hex(a),start,start+len(witness))
    out.append(dict(**facts,classification='Instruction-straddling byte coincidence; no u32 pointer operand',
                    witness_start=hex(start)));continue
   start=data.rfind(b'\xff\xd8\xff',0,off);end=data.find(b'\xff\xd9',start)+2
   stream=BytesIO(data[start:end])
   try:im=Image.open(stream);entropy=start+stream.tell();im.load()
   except Exception as exc:raise ValueError('Unclassified encoded reference '+str(facts)) from exc
   require(im.format=='JPEG' and entropy<=off and off+4<=end-2,'Unclassified encoded placement reference')
   out.append(dict(**facts,classification='JPEG entropy data; Pillow complete decode passed',
                   start=hex(start),end=hex(end)))
  return out

 def placement(self):
  from ep7_hsl_install_checks import captures,modeled_return
  from penf_code_space_audit import pointer_candidates,branch_candidates
  for a,b in [(0x60045786,0x6004586c),(0x60067102,0x60067146)]:self.disassemble('loader_'+hex(a),a,b)
  # End comes from the native selector; descriptor supplies start/source.
  r=self.provider.Region
  end=self.call('v4_section_end',0x60045786,0,[r('rom',BASE,self.data,'rx')],{'d0':1},mask='')['registers']['d0']
  start,source,dest=struct.unpack('<3I',self.read(0x60027068,12))
  require(start==dest==0x600d7800 and end==0x60211000,'Section 1 bounds')
  require(EXTENSION+len(self.extension)+64<=MIRROR,'Code/mirror separation guard')
  require(self.read(EXTENSION-64,len(self.extension)+128)==b'\xff'*(len(self.extension)+128),'Code padding guard')
  require(self.read(MIRROR-64,320)==b'\xff'*320,'Mirror padding guard')
  loads=[]
  for poison in (0xa5,0x55):
   code=self.assemble('v4_loader_caller','call target,[d2,d3,a2,a3],24\nnop\n',symbols={'target':0x600457e7})
   regions=[r('before',BASE,self.candidate[:start-BASE],'rx'),r('after',end,self.candidate[end-BASE:],'rx'),
            r('loaded',start,bytes([poison])*(end-start),'rwx',True),
            r('loaded_uncached',start+0x40000000,bytes([poison])*(end-start),'rwx',False,'loaded'),
            r('loaded_flags',0xa272e420,bytes(4),'rw',True),r('stack',STACK,bytes(0x2000),'rw',True),
            r('caller',0x18020000,code,'rx')]
   v=self.provider.execute(regions,{'pc':0x18020000,'sp':SP,'d0':1},0x18020000+len(code),
                           breakpoints=[0x6005bc79],limit=1000,trace_limit=1000)
   require(v['status']=='breakpoint','Native load did not reach declared storage boundary')
   regs=v['registers'];args=[regs[k] for k in ('a0','a1','d0','d1')]
   require(args==[start+0x40000000,source+0x40000000,end-start,257],'Unqualified logical section read')
   saved=captures(v);payload=self.candidate[start-BASE:end-BASE]
   regions=[replace(q,data=payload if q.name in ('loaded','loaded_uncached') else saved.get(q.name,q.data)) for q in regions]
   last=self.provider.execute(regions,modeled_return(self,v),0x18020000+len(code),limit=1000,trace_limit=1000)
   require(last['status']=='returned','Native loader return')
   got=self.captured(last,'loaded')
   require(got==payload and got[MIRROR-start:MIRROR-start+192]==bytes(192),'Code/neutral mirror not loaded')
   (self.out/f'loader_{poison}.json').write_text(json.dumps(last)+'\n')
   loads.append(dict(poison=poison,exact_section_copy=True,neutral_mirror=True))
  # Mature bounded reference checks; encoded data matches are classified using
  # the existing repository's Pillow/zlib placement validator, not treated as code.
  refs=[]
  for begin,length in [(EXTENSION,len(self.extension)),(MIRROR,192)]:
   for address in (begin,begin+0x40000000,begin-0x1f980000,begin+0x20680000):
    for block in self.blocks:
     refs.extend(dict(component=block.index,alias_base=hex(address),**z)
                 for z in pointer_candidates(block.payload,address,address+length))
  branches=branch_candidates(self.data,BASE,[(EXTENSION,EXTENSION+len(self.extension)),(MIRROR,MIRROR+192)])[0]
  require(len(branches)==1 and branches[0]['site']=='0x6020ec90','Unclassified relative placement match')
  # Actual indexed jump consumes this word as a switch table element. The
  # apparent JMP16 begins inside data rather than at a native code boundary.
  target=struct.unpack('<I',self.read(0x6020ec90,4))[0]
  proof=self.provider.execute([r('rom',BASE,self.data,'rx'),r('stack',STACK,bytes(0x2000),'rw',True)],
       {'pc':0x601fc6a9,'sp':SP,'d0':(0x6020ec90-0x6020ec48)//4},target,limit=10,trace_limit=10)
  require(proof['status']=='returned' and proof['registers']['pc']==target,'Native switch table proof')
  classified=self.classify_v4_references(refs)
  return dict(section=1,start=hex(start),end=hex(end),code=hex(EXTENSION),mirror_cached=hex(MIRROR),
              mirror_uncached=hex(MIRROR+0x40000000),native_loads=loads,classified_references=classified,
              relative_raw_candidates=1,relative_classification='native switch table element, not code',limits='No exhaustive computed/DMA access or physical cache/coherency proof')


def main():
 os.umask(0o077)
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--upstream',required=True,type=Path);p.add_argument('--stock',required=True,type=Path)
 p.add_argument('--out',required=True,type=Path)
 a=p.parse_args();x=Probe(a.upstream,a.stock,a.out);x.prepare()
 result=dict(issue=65,revision='owner sequential write',stock_sha256=digest(a.stock.read_bytes()),
             decoded_stock_sha256=digest(x.data),extension_sha256=digest(x.extension),
             extension_bytes=len(x.extension),decoded_output_sha256=digest(x.candidate),
             native_windows=x.windows,modified_ranges=[dict(address=hex(v),length=n,
                original_sha256=digest(x.read(v,n)),replacement_sha256=digest(x.candidate[v-BASE:v-BASE+n])) for v,n in x.edits],
             labels={k:hex(v) for k,v in x.labels.items() if k in ['wifi_write','wifi_read','app_edit','publish','id_parse','value_parse']},
             package_files_created=False)
 result['publication_abi']=x.publication_abi()
 result['read_and_stock']=x.read_and_stock()
 result['protocol'],s=x.protocol_matrix()
 (x.out/'checkpoint.json').write_text(json.dumps(result,indent=2)+'\n')
 result['imaging']=x.imaging(s)
 result['image_matrix']=x.image_matrix()
 result['boot_and_staging']=x.boot_and_staging()
 result['placement']=x.placement()
 result['modeled_boundaries']=sorted({v['pc'] for v in x.boundaries})
 (x.out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(native_checks='pass',v4_offline=True,install_file_created=False)))

if __name__=='__main__':main()
