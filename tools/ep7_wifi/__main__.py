"""Run from repository root: python -m tools.ep7_wifi --help."""
import argparse
import json
import sys
from .client import Camera,Transfer,ClientError,Incompatible,Uncertain,load_recipe,save_new


def main(argv=None):
    p=argparse.ArgumentParser(description='E-P7 EP71 配方读取、备份、逐值写入与回读；不刷固件')
    p.add_argument('--host',default='192.168.0.10');p.add_argument('--port',type=int,default=80)
    p.add_argument('--timeout',type=float,default=3);p.add_argument('--gap',type=float,default=.05)
    p.add_argument('--state-dir',help='仓库外私有目录；默认 ~/.ep7-film-hack')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('discover')
    read=sub.add_parser('read');read.add_argument('--slot',required=True,type=int,choices=range(1,5));read.add_argument('--out',required=True)
    for name in ('write','restore'):
        cmd=sub.add_parser(name);cmd.add_argument('--slot',required=True,type=int,choices=range(1,5))
        cmd.add_argument('recipe');cmd.add_argument('--dry-run',action='store_true')
    ack=sub.add_parser('acknowledge-reconnect');ack.add_argument('--after-manual-reconnect',action='store_true')
    args=p.parse_args(argv)
    try:
        # Recipe validation occurs before constructing a transport, not merely
        # before its first write. Dry-run never creates local state or sockets.
        recipe=load_recipe(args.recipe) if args.command in ('write','restore') else None
        camera=Camera(args.host,args.port,args.timeout,args.gap)
        transfer=Transfer(camera,args.state_dir)
        if args.command=='discover':result=camera.discover()
        elif args.command=='read':
            camera.discover();result={'out':str(save_new(args.out,camera.read(args.slot))),'slot':args.slot,'writes_sent':0}
        elif args.command=='acknowledge-reconnect':result=transfer.reconcile(args.after_manual_reconnect)
        else:result=transfer.write(args.slot,recipe,restore=args.command=='restore',dry_run=args.dry_run)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except Uncertain as exc:
        print(json.dumps(exc.report,ensure_ascii=False,indent=2));return 3
    except (ClientError,OSError,ValueError) as exc:
        # No raw HTTP bodies or low-level request repr are printed.
        print(str(exc),file=sys.stderr);return 4 if isinstance(exc,Incompatible) else 2


if __name__=='__main__':
    # Stable UTF-8 JSON also when Windows stdout is redirected to a file.
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    raise SystemExit(main())
