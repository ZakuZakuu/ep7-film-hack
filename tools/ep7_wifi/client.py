"""EP71 v1 client. Only explicit write/restore commands change recipe settings.

Design reference (read only): fishcu/oly_fw_analysis@539fcf1 camera_client docs.
No upstream implementation copied. Native protocol: docs/wifi-recipe-protocol.md.
"""
import contextlib
from datetime import datetime, timezone
import http.client
import ipaddress
import json
import os
from pathlib import Path
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

from tools.recipe_studio.recipe import calibration, load_json, neutral, validate

CAPABILITY=0x45503731
WHEEL=(0,6,1,7,2,8,3,9,4,10,5,11)
STARTS=(927,939,951,1655)
TONE_HIGH=(963,966,969,1672)
ROOT=Path(__file__).resolve().parents[2]
LIMIT=65536


class ClientError(Exception):
    pass


class Incompatible(ClientError):
    pass


class Uncertain(ClientError):
    def __init__(self, report):
        super().__init__('写入结果不确定；已停止，禁止自动重试或回滚')
        self.report=report


def checked_recipe(obj):
    # Exactly the same validation as Recipe Studio; EP71 fixes S to +/-5.
    rules=calibration();rules['limits']['saturation']=5
    return validate(obj,rules)


def load_recipe(path):
    try:
        with Path(path).open('rb') as f:data=f.read(1_000_001)
        if len(data)>1_000_000:raise ValueError('配方文件过大')
        return checked_recipe(load_json(data.decode('utf-8')))
    except (OSError,UnicodeError,ValueError,TypeError) as exc:
        raise ClientError('配方校验失败：'+str(exc)) from exc


def fields(slot):
    if type(slot) is not int or not 1<=slot<=4:raise ClientError('槽必须为 1…4')
    ids=[STARTS[slot-1]+i for i in WHEEL]
    return ([(k,0x4551,7) for k in ids]+[(k,0x4550,5) for k in ids]+
            [(k,0x4552,7) for k in ids]+
            [(TONE_HIGH[slot-1]+2,0x4550,7),(TONE_HIGH[slot-1]+1,0x4550,7),
             (TONE_HIGH[slot-1],0x4550,7),(1666+slot,0x4550,5)])


def vector(recipe):
    s=recipe['settings'];t=s['tone']
    return s['hue']+s['saturation']+s['lightness']+[t['shadows'],t['midtones'],t['highlights'],s['shading']]


def as_recipe(values,slot):
    obj=neutral('COLOR '+str(slot)+' backup '+datetime.now().astimezone().isoformat(timespec='seconds'))
    obj['description']='EP71 当前已发布值备份；不包含白平衡或曝光设置，不证明断电持久性。'
    s=obj['settings'];s['hue']=values[:12];s['saturation']=values[12:24];s['lightness']=values[24:36]
    s['tone']=dict(zip(('shadows','midtones','highlights'),values[36:39]));s['shading']=values[39]
    return checked_recipe(obj)


def private_target(path):
    p=Path(path).expanduser().resolve()
    if p==ROOT or ROOT in p.parents:raise ClientError('备份与状态文件必须保存在仓库外')
    return p


def save_new(path,obj):
    p=private_target(path);p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    return p


def replace_private(path,obj):
    p=private_target(path);p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,name=tempfile.mkstemp(prefix='.ep71-',dir=p.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(name,p)
    finally:
        if os.path.exists(name):os.unlink(name)


class Camera:
    def __init__(self,host='192.168.0.10',port=80,timeout=3.0,gap=0.05):
        try:address=ipaddress.ip_address(host)
        except ValueError as exc:raise ClientError('地址必须是私网 IP，不能使用域名或 URL') from exc
        private=(ipaddress.ip_network('10.0.0.0/8'),ipaddress.ip_network('172.16.0.0/12'),
                 ipaddress.ip_network('192.168.0.0/16'),ipaddress.ip_network('127.0.0.0/8'))
        if not (address==ipaddress.ip_address('::1') or any(address.version==n.version and address in n for n in private)):
            raise ClientError('禁止公网、链路本地、组播、未指定或保留地址')
        if type(port) is not int or not 1<=port<=65535:raise ClientError('端口范围为 1…65535')
        if not 0<timeout<=120 or not 0<=gap<=10:raise ClientError('超时或请求间隔越界')
        self.host=str(address);self.port=port;self.timeout=timeout;self.gap=gap;self.last=0.0

    def request(self,path,params=None):
        delay=self.gap-(time.monotonic()-self.last)
        if delay>0:time.sleep(delay)
        conn=http.client.HTTPConnection(self.host,self.port,timeout=self.timeout)
        url=path+('?' + urlencode(params) if params else '')
        try:
            # Literal private IP only; direct connection, no proxy, no redirects,
            # no cookies, no serial/MAC query or raw-response logging.
            conn.request('GET',url,headers={'Connection':'close','Accept':'application/xml'})
            response=conn.getresponse();body=response.read(LIMIT+1)
            if response.status!=200:
                hint='；相机可能不在遥控模式，或拒绝了该请求' if response.status==520 else ''
                raise ClientError('相机返回 HTTP '+str(response.status)+hint)
            if len(body)>LIMIT:raise ClientError('相机响应过大')
            return body
        except (OSError,http.client.HTTPException) as exc:
            raise ClientError('连接失败、超时或响应中断；请求没有自动重试') from exc
        finally:
            self.last=time.monotonic();conn.close()

    @staticmethod
    def xml(body,root,child):
        try:
            if b'\0' in body or b'<!DOCTYPE' in body.upper() or b'<!ENTITY' in body.upper():raise ValueError()
            node=ET.fromstring(body)
            values=node.findall(child)
            if (node.tag!=root or len(values)!=1 or values[0].text is None or
                    (root=='response' and len(node)!=1)):raise ValueError()
            return values[0].text.strip()
        except (ValueError,ET.ParseError) as exc:raise ClientError('相机响应格式无效；未记录响应内容') from exc

    def get_number(self,key):
        text=self.xml(self.request('/get_mcon.cgi',{'mode':f'{key:04X}'}),'response','value')
        if not 1<=len(text)<=8 or any(c not in '0123456789abcdefABCDEF' for c in text):
            raise ClientError('相机数值响应不是合法 u32 十六进制')
        return int(text,16)

    def discover(self):
        model=self.xml(self.request('/get_caminfo.cgi'),'caminfo','model')
        if model!='E-P7':raise Incompatible('机型不符；拒绝写入')
        # Measured on E-P7 1.1 (B4, 2026-10-27): get_mcon/set_mcon answer HTTP 520
        # with errorcode 1004 until the stock remote rec mode is entered, both on
        # stock and v4. This is the same mode switch OI.Share uses; it does not
        # start live view, press the shutter or change settings.
        self.request('/switch_cammode.cgi',{'mode':'rec'})
        if self.get_number(65535)!=CAPABILITY:raise Incompatible('原厂固件或 EP71 版本不符；拒绝写入')
        return {'model':'E-P7','protocol':'EP71','slots':4}

    def read(self,slot):
        values=[]
        for key,axis,maximum in fields(slot):
            read_key=key|(0x8000 if axis==0x4551 else 0xc000 if axis==0x4552 else 0)
            raw=self.get_number(read_key)
            value=raw-(1<<32) if raw&(1<<31) else raw
            if not -maximum<=value<=maximum:raise ClientError('读取值越界或该轴不可用；不会补零')
            values.append(value)
        return as_recipe(values,slot)

    def write_value(self,field,value):
        key,tag,maximum=field
        if type(value) is not int or not -maximum<=value<=maximum:raise ClientError('逐值参数越界')
        self.request('/set_mcon.cgi',{'mode':f'{key:04X}','value':f'{(tag<<16)|(value&65535):08X}'})


class Transfer:
    def __init__(self,camera,state_dir=None):
        self.camera=camera
        self.directory=private_target(state_dir or Path.home()/'.ep7-film-hack')
        self.marker=self.directory/'uncertain.json'

    @contextlib.contextmanager
    def lock(self):
        self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        path=self.directory/'write.lock'
        try:fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        except FileExistsError as exc:raise ClientError('已有本地写入任务或遗留锁；确认进程结束后再处理') from exc
        try:
            with os.fdopen(fd,'w') as f:f.write(str(os.getpid()))
            yield
        finally:path.unlink()

    def write(self,slot,recipe,*,restore=False,dry_run=False):
        # Complete shared validation before identity, session or any connection.
        recipe=checked_recipe(recipe);wanted=vector(recipe);binding=fields(slot)
        report={'operation':'restore' if restore else 'write','slot':slot,
                'values':wanted,'recommendations_manual_only':recipe['recommendations']}
        if dry_run:return {**report,'dry_run':True,'network_used':False}
        with self.lock():
            if self.marker.exists():raise ClientError('存在不确定写入记录；先手动重连、只读核对并显式解除')
            self.camera.discover()
            before=self.camera.read(slot)
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]
            backup=save_new(self.directory/'backups'/f'COLOR{slot}-{stamp}.json',before)
            report['backup']=str(backup)
            pending={**report,'host':self.camera.host,'port':self.camera.port,'status':'in_progress'}
            # Durable local intent before the first marked request; a killed
            # process must not silently start another write on the next run.
            replace_private(self.marker,pending)
            sent=0
            try:
                for field,old,value in zip(binding,vector(before),wanted):
                    if old!=value:self.camera.write_value(field,value);sent+=1
                after=self.camera.read(slot)
                actual=vector(after)
                if actual!=wanted:raise ClientError('完整回读不一致')
            except (ClientError,OSError,KeyboardInterrupt) as exc:
                # Read-only reconciliation, never another marked request or an
                # automatic rollback; a late application edit may still follow.
                try:actual=vector(self.camera.read(slot));read_status='complete'
                except (ClientError,OSError,KeyboardInterrupt):actual=None;read_status='unavailable'
                report.update(status='uncertain',completed_replies=sent,actual_values=actual,
                              readback=read_status,reason='操作中断或回读不一致；仍可能有迟到编辑')
                replace_private(self.marker,{**pending,**report})
                raise Uncertain(report) from exc
            self.marker.unlink()
            return {**report,'status':'verified_current_values','written_values':sent,
                    'persistent_after_reboot':'not_verified'}

    def reconcile(self,after_manual_reconnect=False):
        if not after_manual_reconnect:raise ClientError('必须先手动重新连接 Wi-Fi，再显式声明 --after-manual-reconnect')
        with self.lock():
            if not self.marker.exists():raise ClientError('没有不确定写入记录')
            try:previous=load_json(self.marker.read_text(encoding='utf-8'))
            except (OSError,ValueError) as exc:raise ClientError('本地状态损坏；保留文件，停止写入') from exc
            if not isinstance(previous,dict):raise ClientError('本地状态损坏；保留文件，停止写入')
            try:
                fields(previous['slot'])
                saved=previous['values']
                if not isinstance(saved,list) or len(saved)!=40:raise ValueError()
                as_recipe(saved,previous['slot'])
            except (KeyError,TypeError,ValueError,ClientError) as exc:
                raise ClientError('本地状态损坏；保留文件，停止写入') from exc
            if previous.get('host')!=self.camera.host or previous.get('port')!=self.camera.port:
                raise ClientError('本地状态的目标不同；不得替其他目标清除标记')
            self.camera.discover();actual=vector(self.camera.read(previous['slot']))
            self.marker.unlink()
            return {'status':'manual_reconnect_acknowledged','slot':previous['slot'],
                    'actual_values':actual,'matches_previous_target':actual==previous['values'],
                    'writes_sent':0,'note':'未还原或重试；下一次写入必须重新明确执行'}
