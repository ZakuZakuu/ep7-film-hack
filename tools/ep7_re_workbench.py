#!/usr/bin/env python3
"""Guarded GNU-backed private SQLite/CFG project; no full-image code discovery.

OEM operands/CFG stay in /tmp. Public graph is curated numerical evidence only.
No P-code, ABI inference, emulation, decompilation or automatic indirect solving.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import struct
import subprocess
import tempfile

try:
    from .inspect_olympus_oe import FormatError, inspect, check_expected, decode_chunk
    from .probe_oe_executable import (
        Instruction, disassemble, parse_objdump, BRANCHES, CALLS, RETURNS, UNMODELED_FLOW)
except ImportError:
    from inspect_olympus_oe import FormatError, inspect, check_expected, decode_chunk
    from probe_oe_executable import (
        Instruction, disassemble, parse_objdump, BRANCHES, CALLS, RETURNS, UNMODELED_FLOW)

REPO = Path(__file__).resolve().parents[1]


def translate(address, destination, source, size):
    delta = address - destination
    if not 0 <= delta < size:
        raise FormatError('address outside independently nominated view')
    return source + delta


def cfg(rows, entry):
    """Conservative instruction CFG; unknown callees may return, not guaranteed.

    Linear rows are not all reachable. Stop unknown extension/hardware-loop
    semantics. Calls create xrefs, never recursively import callees.
    """
    by = {r.address:r for r in rows}
    following = {a.address:b.address for a,b in zip(rows, rows[1:])}
    pending, visited, edges, stops = [entry], set(), [], []
    while pending:
        at = pending.pop()
        if at in visited:
            continue
        r = by.get(at)
        if r is None:
            stops.append({'at':at, 'reason':'outside window or non-boundary'})
            continue
        visited.add(at)
        if r.mnemonic.startswith(('.', 'udf')) or r.mnemonic in UNMODELED_FLOW | {'break', 'Address', 'trap'}:
            stops.append({'at':at, 'reason':'unmodeled instruction/control'})
            continue
        if r.mnemonic in RETURNS:
            continue
        target = r.direct_target()
        if r.mnemonic in CALLS:
            edges.append({'source':at, 'target':target, 'kind':'call' if target is not None else 'indirect_call',
                          'qualification':'callee not followed; may-return fallthrough'})
        elif r.mnemonic in BRANCHES:
            edges.append({'source':at, 'target':target, 'kind':'branch' if target is not None else 'indirect_branch',
                          'qualification':'decoded direct flow' if target is not None else 'unresolved target'})
            if target is not None:
                pending.append(target)
            else:
                stops.append({'at':at, 'reason':'indirect target unresolved'})
            if r.mnemonic in {'jmp','bra'}:
                continue
        nxt = following.get(at)
        if nxt is None:
            stops.append({'at':at, 'reason':'window end'})
        else:
            edges.append({'source':at, 'target':nxt, 'kind':'fallthrough',
                          'qualification':'may-return' if r.mnemonic in CALLS else 'decoded next boundary'})
            pending.append(nxt)
    return {'visited':sorted(visited), 'edges':edges, 'stops':stops,
            'returns':sorted(at for at in visited if by[at].mnemonic in RETURNS)}


def compare_views(objdump, blob, start, baseline):
    """Same GNU implementation, three machine selectors: NOT independent decoders."""
    with tempfile.TemporaryDirectory(prefix='ep7-view-', dir='/tmp') as d:
        path = Path(d)/'window.bin'
        path.write_bytes(blob)
        path.chmod(0o600)
        for machine in ('am33','am33-2'):
            p = subprocess.run([str(objdump),'-D','-z','-b','binary','-m',machine,
                                '-EL','--no-show-raw-insn',f'--adjust-vma={start}',str(path)],
                               capture_output=True, text=True, timeout=60, check=True)
            if parse_objdump(p.stdout,start,len(blob)) != baseline:
                raise FormatError('GNU machine-selector disagreement in admitted corpus')


def classification(t,s):
    # Original reconstruction of the exhausted T12 scalar logic, not OEM execution.
    h,lo,s = t&0xf0,t&15,s&255
    if h == 0:
        return {0:0,1:1,2:5,3:5,4:6,5:7}.get(lo,0)
    if h in (0x10,0x20):
        return 3 if lo == 1 else 2
    if h == 0x30:
        if s in (15,17): return 5 if lo == 3 else 6
        if s in (22,23): return 7
        if s == 14: return {2:5,3:5,4:6,5:7}.get(lo,5)
        return 5 if s in (18,19,20) else 8
    return 9 if h == 0x40 else 0


def noise_cleared(t):
    return t&0xf0 == 0x40 or t&0xf00 == 0x100


def guard(row, mnemonic, operands=None):
    if row.mnemonic != mnemonic or operands is not None and row.operands != operands:
        raise FormatError('nominated instruction guard failed')


def evidence(data, decoded, inherited):
    """Curated relationship guards, not automatic general data-flow recovery."""
    edges = []
    def edge(kind, source, target, origins, confidence='verified', note=''):
        edges.append(dict(kind=kind,source=source,target=target,origins=origins,
                          coordinate='decoded #0 offsets',confidence=confidence,note=note))
    for e in inherited['direct_calls']:
        r = decoded[e['window']][int(e['source'],16)]
        if r.mnemonic not in CALLS or r.direct_target() != int(e['target'],16):
            raise FormatError('inherited call guard failed')
        edge('direct_call',e['source'],e['target'],[e['source']],note='nominated T7 edge; not imaging ownership')
    for e in inherited['conditional_virtual_evidence']:
        at = int(e['vtable_payload_offset'],16)+e['slot_bytes']
        if struct.unpack_from('<I',data,at)[0]-0x60020020 != int(e['target'],16):
            raise FormatError('conditional initializer guard failed')
        if decoded['submit'][int(e['source'],16)].mnemonic not in CALLS:
            raise FormatError('nominated indirect call guard failed')
        edge('conditional_virtual',e['source'],e['target'],[hex(at),e['source']],
             'hypothesized','T7 constructor/initializer evidence; actual runtime instance/target unknown')
    p,r,c = (decoded[n] for n in ('effect_producer','effect_receiver','type_classifier'))
    guards = [
        (p,0x301d1c,'mov','a0,(28,sp)'),(p,0x301d4d,'mov','a0,a2'),
        (p,0x301d50,'add','8,a2'),(p,0x301d60,'add','40,a3'),
        (p,0x301d75,'mov','(28,sp),a1'),(p,0x301d79,'add','20,a1'),
        (p,0x301d7b,'mov','(a1),d0'),(p,0x301e32,'mov','d3,(52,sp)'),
        (p,0x301e34,'movhu','(16,a2),d0'),(p,0x301e39,'movhu','d0,(56,sp)'),
        (p,0x301e66,'movbu','(25,a2),d0'),(p,0x301e69,'movbu','d0,(70,sp)'),
        (p,0x301e87,'mov','a3,a0'),(p,0x301e91,'mov','d0,(4,a0)'),
        (r,0x3337cd,'mov','a0,a2'),
        (r,0x3338f5,'mov','a3,a0'),(r,0x3338f6,'inc4','a0'),
        (r,0x3338f7,'mov','a0,(4,sp)'),(r,0x3338f9,'mov','-8,d1'),
        (r,0x3338fb,'setlb',''),(r,0x3338fc,'mov','(a2),d0'),
        (r,0x3338fd,'inc4','a2'),(r,0x3338fe,'mov','d0,(a0)'),
        (r,0x3338ff,'inc4','a0'),(r,0x333900,'inc','d1'),(r,0x333901,'lne',''),
        (r,0x333952,'mov','(4,sp),d3'),(r,0x333954,'mov','(4,sp),a0'),
        (r,0x333956,'add','16,d3'),(r,0x333958,'movbu','(30,a0),d1'),
        (r,0x33395d,'movhu','(a0),d0'),
        (r,0x333a6b,'or','8388608,d0'),(r,0x333af4,'mov','d0,(a2)'),
        (r,0x333af9,'mov','240,d1'),(r,0x333afe,'cmp','64,d0'),
        (r,0x333b04,'and','3840,d0'),(r,0x333b08,'cmp','256,d0'),
        (r,0x333b24,'and','-16385,d0'),(r,0x333b2a,'mov','d0,(a2)'),
        (c,0x3954fd,'exthu','d0'),(c,0x3954fe,'mov','240,d2'),
        (c,0x395501,'and','d0,d2'),(c,0x39554d,'extbu','d1')]
    for rows,at,m,o in guards:
        guard(rows[at],m,o)
    # No a2 redefinition on the source+8 alias lifetime; calls/unknowns invalidate it.
    for row in p.values():
        if 0x301d50 < row.address <= 0x301e66:
            if row.mnemonic in CALLS or row.operands.split(',')[-1] == 'a2':
                raise FormatError('source alias lifetime no longer supported')
    for at,target in [(0x301e88,0x3337cb),(0x301e7b,0x2e4e58),(0x33395f,0x3954fd)]:
        row = p[at] if at < 0x333000 else r[at]
        if row.direct_target() != target:
            raise FormatError('ART call guard failed')
        edge('direct_call',hex(at),hex(target),[hex(at)])
    edge('field_transform','source+20','temporary+12',['0x301d75','0x301d79','0x301d7b','0x301e32'],
         note='old compact-effects to expanded mask; NOT source writer')
    edge('field_copy','source+24:u16','temporary+16:u16',['0x301d50','0x301e34','0x301e39'])
    edge('field_copy','source+33:u8','temporary+30:u8',['0x301d50','0x301e66','0x301e69'])
    edge('bounded_copy','temporary[0:32]','context[4:36]',['0x3338f5','0x3338f9','0x3338fb','0x3338fc','0x333901'],
         'verified','instruction guards verified; copy extent strong static inference; hardware-loop CFG explicitly unmodeled')
    edge('scalar_argument','context+34:u8','classifier d1',['0x333954','0x333958','0x33395f'],
         note='new joined provenance: source+33, NOT effect writer or a named ART option')
    edge('scalar_argument','context+20:u16','classifier d0',['0x333952','0x333956','0x33395d','0x33395f'],
         note='Type originates source+24; distinct from source+20 effects')
    records = [struct.unpack_from('<II',data,at) for at in range(0x501a34,0x501ab4,8)]
    if sum(k != 0 for k,v in records) != 14 or not all(v-0x60020020 in r for k,v in records):
        raise FormatError('special-case table guard failed')
    forced = {0x01010064+k for k,v in records if k and v-0x60020020 == 0x333a6a}
    if forced != {0x01010068,0x01020068,0x0102006d}:
        raise FormatError('key/MonoEnable guard failed')
    for at,(key,value) in zip(range(0x501a34,0x501ab4,8),records):
        edge('table_branch',hex(at),hex(value-0x60020020),[hex(at)],
             note='empty sentinel' if not key else 'special-case discriminator; NOT named filter registry')
    targets = [struct.unpack_from('<I',data,at)[0]-0x60020020 for at in range(0x501ab4,0x501adc,4)]
    if targets != [0x33398e]*4+[0x333983]*6:
        raise FormatError('class dispatch table guard failed')
    class_cfg = cfg(list(c.values()),0x3954fd)
    if len(class_cfg['visited']) != 80 or class_cfg['stops'] or len(class_cfg['returns']) != 5:
        raise FormatError('classifier CFG guard failed')
    if classification(0,0) != classification(0x100,0) or noise_cleared(0) == noise_cleared(0x100):
        raise FormatError('known arithmetic counterexample failed')
    return edges, len(guards)


def layout_guards(data, decoded, objdump, inherited):
    """Re-check nominated views; never apply copied bases outside their ranges."""
    boot = decoded['boot_entry']
    for at,value,dest in [(0x1e4,0x408b0800,'a0'),(0x1ea,0xa1f98540,'a1'),
                          (0x258,0xa143ca00,'a1'),(0x25e,0x1800,'d0'),
                          (0x277,0xa143ca00,'a1'),(0x27d,0x47000800,'a0')]:
        guard(boot[at],'mov')
        immediate,reg = boot[at].operands.split(',')
        if int(immediate)&0xffffffff != value or reg != dest:
            raise FormatError('startup view guard failed')
    guard(boot[0x28a],'cmp','1536,d1')
    root = struct.unpack_from('<I',data,0x2211a0)[0]
    copied = lambda address:translate(address,0x61f98540,0x2107e0,0x2e350)
    if not 0x221078 <= copied(root) < 0x2211a0:
        raise FormatError('copied root pointer outside group-vector island')
    resolver = decoded['name_resolver'][0x75069f]
    guard(resolver,'mov','1643810560,a0')  # 0x61fa8f00
    if copied(0x61fa8f00) != 0x2211a0:
        raise FormatError('copied root view mismatch')
    main = 0x60020020
    for address,wid in [(0x47001052,'relocated_copy'),(0x4700115e,'relocated_fill')]:
        offset = translate(address,0x47000800,0x141c9e0,0x1800)
        window = next(w for w in inherited['code_windows'] if w['id']==wid)
        if offset != int(window['start'],16):
            raise FormatError('helper view identity mismatch')
        rows = list(decoded[wid].values())
        relocated = disassemble(objdump,data[offset:int(window['end'],16)],address)
        if [r.mnemonic for r in relocated] != [r.mnemonic for r in rows]:
            raise FormatError('helper view decode mismatch')
    # A data island also decodes as plausible instructions. Preserve its type.
    words = [struct.unpack_from('<I',data,p)[0] for p in range(0x501ab4,0x501adc,4)]
    if not all(v-main in decoded['effect_receiver'] for v in words):
        raise FormatError('branch table view invalid')
    return {'startup_literal_guards':7,'copied_root':'pass','relocated_helpers':2,
            'unknown_bytes':'unclassified; no blanket code/data/physical RAM map'}


def private_directory(path):
    # Reject symlinks including any parent, and repository/workspace output.
    absolute = Path(os.path.abspath(path))
    if not str(absolute).startswith('/tmp/') or absolute == Path('/tmp'):
        raise FormatError('private project must be below /tmp')
    if any(p.is_symlink() for p in [absolute,*absolute.parents]):
        raise FormatError('symlink private output refused')
    absolute.mkdir(mode=0o700,parents=True,exist_ok=True)
    if absolute.stat().st_uid != os.getuid():
        raise FormatError('private directory belongs to another owner')
    absolute.chmod(0o700)
    return absolute


def build(original, objdump, output):
    manifest_path = REPO/'research/e142-workbench-manifest.json'
    m = json.loads(manifest_path.read_text())
    inherited_path = REPO/m['inherited_index']
    inherited = json.loads(inherited_path.read_text())
    if any(m[k] != inherited[k] for k in ('model','firmware_version','input_size','input_sha256','decoded_sha256')):
        raise FormatError('inherited evidence belongs to a different model/sample')
    if not subprocess.run([str(objdump),'--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0].endswith('2.44'):
        raise FormatError('GNU2.44 required')
    # Original synthetic fixture first.
    demo = disassemble(objdump,bytes.fromhex('cd08000000df0000df0000'),0)
    if cfg(demo,0)['returns'] != [5] or cfg(demo,8)['returns'] != [8]:
        raise FormatError('synthetic call/return admission failed')
    before = inspect(original)
    check_expected(before,m['input_sha256'],m['input_size'])
    if before['block_count'] != 5 or any(b['checksum_residual'] != '0x00000000' for b in before['blocks']):
        raise FormatError('OE checksums failed')
    block = before['blocks'][m['block_index']]
    with original.open('rb') as f:
        f.seek(block['payload_offset'])
        data = decode_chunk(f.read(block['payload_length']))
    if len(data) != m['decoded_size'] or hashlib.sha256(data).hexdigest() != m['decoded_sha256']:
        raise FormatError('decoded identity mismatch')
    windows = inherited['code_windows']+m['windows']
    decoded, flows, summaries = {}, {}, []
    for w in windows:
        a,b = int(w['start'],16),int(w['end'],16)
        if not 0 <= a < b <= len(data) or b-a > 128*1024:
            raise FormatError('window outside admitted bounds')
        rows = disassemble(objdump,data[a:b],a)
        decoded[w['id']] = {r.address:r for r in rows}
        flows[w['id']] = cfg(rows,a)
        if w['id'] in {n['id'] for n in m['windows']}:
            compare_views(objdump,data[a:b],a,rows)
        summaries.append({'id':w['id'],'start':w['start'],'end':w['end'],
                          'linear_rows':len(rows),'reachable_rows':len(flows[w['id']]['visited']),
                          'stops':flows[w['id']]['stops'],'role':w['role']})
    edges, guards = evidence(data,decoded,inherited)
    layout = layout_guards(data,decoded,objdump,inherited)
    if inspect(original) != before:
        raise FormatError('input changed during analysis')
    graph = {'schema_version':1,'model':m['model'],'firmware_version':m['firmware_version'],
             'input_size':m['input_size'],'input_sha256':m['input_sha256'],
             'decoded_sha256':m['decoded_sha256'],'coordinate':'decoded #0 offsets; scoped static aliases only',
             'address_views':inherited['address_views'],'windows':summaries,
             'structures':m['structures'],'tables':m['tables'],'edges':edges,
             'negative_identities':m['negative_identities'],
             'validation':{'oe_blocks':5,'checksum_residuals_zero':True,'instruction_guards':guards,
                           'gnu_selector_crosscheck':'mn10300/am33/am33-2 equal in 3 known windows; one implementation',
                           'counterexample':'T=0/0x100 class=0; FilmNoise clearing differs; hypothetical states',
                           'source_effect_writer':'unknown','decompiler':'disabled',
                           'input_unchanged':True}}
    graph['validation']['layout'] = layout
    private = private_directory(output)
    # Build atomically. Existing successful project survives a failed rebuild.
    p = private/'sanitized-graph.json'
    if p.is_symlink():
        raise FormatError('graph symlink refused')
    fd,temp = tempfile.mkstemp(prefix='project-',suffix='.sqlite',dir=private)
    os.close(fd)
    try:
        with sqlite3.connect(temp) as db:
            db.executescript('''
              CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
              CREATE TABLE windows(id TEXT PRIMARY KEY,start INTEGER,end INTEGER,role TEXT);
              CREATE TABLE instructions(window_id TEXT,address INTEGER,mnemonic TEXT,operands TEXT,reachable INTEGER,
                PRIMARY KEY(window_id,address));
              CREATE TABLE cfg(window_id TEXT,source INTEGER,target INTEGER,kind TEXT,qualification TEXT);
              CREATE TABLE stops(window_id TEXT,address INTEGER,reason TEXT);
              CREATE TABLE evidence(id INTEGER PRIMARY KEY,kind TEXT,source TEXT,target TEXT,confidence TEXT,origins TEXT,note TEXT);
              CREATE INDEX incoming_xrefs ON cfg(target,kind);
              CREATE INDEX outgoing_xrefs ON cfg(source,kind);
              CREATE TABLE negative_identities(id TEXT PRIMARY KEY,record TEXT);
            ''')
            fingerprints = {str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (Path(__file__),manifest_path,inherited_path,
                                      REPO/'tools/probe_oe_executable.py',REPO/'tools/inspect_olympus_oe.py')}
            fingerprints['external_objdump_sha256'] = hashlib.sha256(objdump.read_bytes()).hexdigest()
            for key,value in {'graph':graph,'script_fingerprints':fingerprints}.items():
                db.execute('INSERT INTO metadata VALUES (?,?)',(key,json.dumps(value)))
            for w in windows:
                wid = w['id']
                db.execute('INSERT INTO windows VALUES (?,?,?,?)',(wid,int(w['start'],16),int(w['end'],16),w['role']))
                visited = set(flows[wid]['visited'])
                db.executemany('INSERT INTO instructions VALUES (?,?,?,?,?)',
                    [(wid,r.address,r.mnemonic,r.operands,int(r.address in visited)) for r in decoded[wid].values()])
                db.executemany('INSERT INTO cfg VALUES (?,?,?,?,?)',
                    [(wid,e['source'],e['target'],e['kind'],e['qualification']) for e in flows[wid]['edges']])
                db.executemany('INSERT INTO stops VALUES (?,?,?)',[(wid,s['at'],s['reason']) for s in flows[wid]['stops']])
            db.executemany('INSERT INTO evidence(kind,source,target,confidence,origins,note) VALUES (?,?,?,?,?,?)',
                [(e['kind'],e['source'],e['target'],e['confidence'],json.dumps(e['origins']),e['note']) for e in edges])
            db.executemany('INSERT INTO negative_identities VALUES (?,?)',[(n['id'],json.dumps(n)) for n in m['negative_identities']])
        Path(temp).chmod(0o600)
        os.replace(temp,private/'project.sqlite')
    finally:
        if Path(temp).exists(): Path(temp).unlink()
    p.write_text(json.dumps(graph,indent=2)+'\n')
    p.chmod(0o600)
    return {'windows':len(windows),'instruction_guards':guards,'evidence_edges':len(edges),
            'validation':graph['validation'],'private_project_created':True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--firmware',type=Path,required=True)
    p.add_argument('--objdump',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,default=Path('/tmp/ep7-re-project'))
    a = p.parse_args()
    try:
        result = build(a.firmware,a.objdump.resolve(),a.output_dir)
    except (OSError,ValueError,KeyError,sqlite3.Error,subprocess.SubprocessError):
        p.exit(2,'STOP: sample, decoder, evidence or private-output guard failed; no OEM output published.\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
