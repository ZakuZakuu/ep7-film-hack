"""Owned EP71 contract simulator; localhost only, no OEM code/data or camera I/O.

It models protocol-visible current values, not RTOS, ISP, settings NVS or the
stock raw writer. Independent ID tables catch client wheel/tone mapping errors.
"""
import argparse
from http.server import BaseHTTPRequestHandler,HTTPServer
import re
import socket
import time
from urllib.parse import parse_qs,urlsplit
from xml.sax.saxutils import escape


class Model:
    def __init__(self,*,stock=False,model='E-P7',drop_at=None,delay_at=None,delay=.15,mismatch_at=None):
        self.stock=stock;self.model=model;self.drop_at=drop_at;self.delay_at=delay_at
        self.delay=delay;self.mismatch_at=mismatch_at;self.requests=[];self.writes=0;self.rec=False
        self.values={}
        for first in (927,939,951,1655):
            for key in range(first,first+12):
                for axis in ('h','s','l'):self.values[(axis,key)]=0
        for key in (963,964,965,966,967,968,969,970,971,1672,1673,1674,1667,1668,1669,1670):
            self.values[('s',key)]=0

    def handler(self):
        state=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass

            def reply(self,status,body=b''):
                try:
                    self.send_response(status);self.send_header('Content-Type','application/xml')
                    self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
                except (BrokenPipeError,ConnectionResetError):pass

            def number(self,value):
                self.reply(200,f'<?xml version="1.0"?><response><value>{value&0xffffffff:08X}</value></response>'.encode())

            def do_GET(self):
                parsed=urlsplit(self.path)
                try:
                    q=parse_qs(parsed.query,strict_parsing=True)
                    if any(len(v)!=1 for v in q.values()):raise ValueError()
                    q={k:v[0] for k,v in q.items()}
                    state.requests.append((parsed.path,q))
                    if parsed.path=='/get_caminfo.cgi' and not q:
                        self.reply(200,('<caminfo><model>'+escape(state.model)+'</model></caminfo>').encode());return
                    if parsed.path=='/switch_cammode.cgi' and q=={'mode':'rec'}:
                        state.rec=True;self.reply(200,b'<response/>');return
                    if parsed.path not in ('/get_mcon.cgi','/set_mcon.cgi'):raise ValueError()
                    if not state.rec:
                        # Real E-P7 1.1 (stock and v4): HTTP 520, errorcode 1004 before rec mode.
                        self.reply(520,b'<?xml version="1.0"?><errorcode>1004</errorcode>');return
                    if not re.fullmatch('[0-9A-Fa-f]{1,4}',q.get('mode','')):raise ValueError()
                    key=int(q['mode'],16)
                    if parsed.path=='/get_mcon.cgi':
                        if set(q)!={'mode'}:raise ValueError()
                        if key==65535:self.number(0 if state.stock else 0x45503731);return
                        flag=key&0xc000
                        axis='h' if flag==0x8000 else 'l' if flag==0xc000 else 's'
                        native=key&0x3fff
                        if flag==0x4000 or (axis,native) not in state.values:
                            self.number(0x80000000 if flag else 0);return
                        self.number(state.values[(axis,native)]);return
                    if set(q)!={'mode','value'} or state.stock or not state.rec:raise ValueError()
                    if not re.fullmatch('[0-9A-Fa-f]{8}',q['value']):raise ValueError()
                    word=int(q['value'],16);tag=word>>16;raw=word&65535
                    value=raw-65536 if raw&32768 else raw
                    if tag not in (0x4550,0x4551,0x4552):raise ValueError()
                    axis={0x4550:'s',0x4551:'h',0x4552:'l'}[tag]
                    if (axis,key) not in state.values:raise ValueError()
                    maximum=7 if axis in ('h','l') or key in (963,964,965,966,967,968,969,970,971,1672,1673,1674) else 5
                    if not -maximum<=value<=maximum:raise ValueError()
                    state.writes+=1
                    if state.writes!=state.mismatch_at:state.values[(axis,key)]=value
                    if state.writes==state.drop_at:
                        # Applied scalar, missing reply: the client cannot assume
                        # zero changes or infer that the pending edit was canceled.
                        self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
                    if state.writes==state.delay_at:time.sleep(state.delay)
                    self.reply(200);return
                except (ValueError,KeyError):self.reply(520)
        return Handler


def serve(model=None,port=0):
    model=model or Model()
    return HTTPServer(('127.0.0.1',port),model.handler())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',type=int,default=8765);p.add_argument('--stock',action='store_true')
    p.add_argument('--drop-at',type=int);p.add_argument('--mismatch-at',type=int)
    a=p.parse_args();server=serve(Model(stock=a.stock,drop_at=a.drop_at,mismatch_at=a.mismatch_at),a.port)
    print('EP71 模拟相机，仅回环：127.0.0.1:'+str(server.server_port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
