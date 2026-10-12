#!/usr/bin/env python3
"""Read-only numeric/semantic queries of a private workbench; no OEM text export."""
import argparse
import json
from pathlib import Path
import sqlite3


def query(path, incoming=None, field=None, window=None, loop=None):
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True) as db:
        graph = json.loads(db.execute("SELECT value FROM metadata WHERE key='graph'").fetchone()[0])
        if incoming is not None:
            rows = db.execute("SELECT window_id,source,target,kind,qualification FROM cfg WHERE target=? AND kind IN ('call','branch')",
                              (incoming,)).fetchall()
            return {'coordinate':'decoded #0 offset; bounded reachable CFG only',
                    'xref_hits':[dict(window=w,source=hex(s),target=hex(t),kind=k,qualification=q) for w,s,t,k,q in rows],
                    'evidence':[e for e in graph['edges'] if e['target']==hex(incoming)],
                    'qualification':'CFG stops at hardware loops; curated guarded xrefs may lie beyond those stops. No hit is not proof of no caller.'}
        if field is not None:
            return {'evidence':[e for e in graph['edges'] if field in (e['source'],e['target'])],
                    'qualification':'curated guarded relations, not automatic alias/value propagation'}
        if window is not None:
            return {'windows':[w for w in graph['windows'] if w['id']==window]}
        if loop is not None:
            return {'loop_proofs':[p for p in graph.get('copy_loop_proofs',[]) if p['setup']==loop],
                    'qualification':'conditional static proof only; no OEM execution'}
        return {'validation':graph['validation'],'negative_identities':graph['negative_identities']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=Path('/tmp/ep7-re-project/project.sqlite'))
    group = p.add_mutually_exclusive_group()
    group.add_argument('--incoming',type=lambda v:int(v,0))
    group.add_argument('--field')
    group.add_argument('--window')
    group.add_argument('--loop',type=lambda v:int(v,0))
    a = p.parse_args()
    try:
        result = query(a.db,a.incoming,a.field,a.window,a.loop)
    except (OSError,ValueError,sqlite3.Error,TypeError):
        p.exit(2,'STOP: private project query failed; no OEM output.\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
