#!/usr/bin/env python3
"""Original E142/1100 constant-profile builder; no settings or device I/O.

--verify-only checks the prospective package as a sequence of hash inputs. It
never creates an installable file. Normal output is for an owner-authorized
later build. T20 source/manifest remain independent and unmodified.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
_spec=importlib.util.spec_from_file_location('ep7_t20_build_helpers',ROOT/'patches/hsl-min/e-p7/build.py')
_legacy=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)
require,sha,guarded_range=_legacy.require,_legacy.sha,_legacy.guarded_range


def build(args):
    manifest=json.loads((HERE/'patch.json').read_text())
    raw=args.stock.read_bytes()
    require(len(raw)==manifest['input_bytes'] and sha(raw)==manifest['input_sha256'],
            'Exact E-P7 1.1 stock size/SHA-256 required')
    destination=None
    if not args.verify_only:
        require(args.out is not None,'A new private --out directory is required')
        destination=_legacy.validate_output_directory(args.out)
    else:
        require(args.out is None,'--verify-only does not create an output directory')
    upstream=args.upstream.resolve()
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=upstream,text=True).strip()
            ==_legacy.UPSTREAM,'Wrong external tool revision')
    require(not subprocess.check_output(['git','status','--porcelain'],cwd=upstream,text=True).strip(),
            'External tracked tools are modified')
    sys.path.insert(0,str(upstream/'tools'))
    import oly_container as oe
    blocks=oe.parse(raw)
    require(len(blocks)==5 and blocks[0].kind==0x100,'Component layout mismatch')
    require(oe.reconstruct(blocks)==raw,'Stock roundtrip mismatch')
    original=blocks[0].payload
    require(sha(original)==manifest['decoded_input_sha256'],'Wrong decoded main')
    source=(HERE/'hook.s').read_bytes()
    require(sha(source)==manifest['hook_source_sha256'],'Unqualified hook source edit')
    records=manifest['modified_ranges']
    spans=[guarded_range(original,record) for record in records]
    require(len(spans)==2 and spans[0][0]+spans[0][1]<=spans[1][0],'Invalid patch spans')
    chain=args.toolchain.resolve() if args.toolchain else upstream/'toolchains/mn103-patch-build'
    tools=dict(assembler=chain/'gas/as-new',linker=chain/'ld/ld-new',
               objcopy=chain/'binutils/objcopy',objdump=chain/'binutils/objdump')
    versions={k:subprocess.check_output([str(v),'--version'],text=True).splitlines()[0] for k,v in tools.items()}
    require(all(s.endswith(' '+manifest['tool_version']) for s in versions.values()),'Wrong qualified GNU version')
    payloads=[]
    with tempfile.TemporaryDirectory(prefix='ep7-profiles-assembly-',dir='/tmp') as scratch:
        for index,text in enumerate(('.text\n.global _start\n_start:\njmp ep7_extension\n',source.decode())):
            stem=Path(scratch)/str(index)
            stem.with_suffix('.s').write_text(text)
            subprocess.run([str(tools['assembler']),'-o',str(stem.with_suffix('.o')),str(stem.with_suffix('.s'))],check=True)
            symbols={'ep7_extension':int(records[1]['address'],0)} if index==0 else {
                k:int(v,0) for k,v in manifest['symbols'].items()}
            subprocess.run([str(tools['linker']),'-Ttext',records[index]['address'],'-e','_start',
                *[f'--defsym={k}={v:#x}' for k,v in symbols.items()],'-o',str(stem.with_suffix('.elf')),
                str(stem.with_suffix('.o'))],check=True)
            subprocess.run([str(tools['objcopy']),'-O','binary','-j','.text',str(stem.with_suffix('.elf')),
                            str(stem.with_suffix('.bin'))],check=True)
            code=stem.with_suffix('.bin').read_bytes()
            require(len(code)==records[index]['length'] and sha(code)==records[index]['replacement_sha256'],
                    'Assembled span differs from qualified code')
            payloads.append(code)
    changed=bytearray(original)
    for (offset,size),code in zip(spans,payloads):changed[offset:offset+size]=code
    require(sha(changed)==manifest['decoded_output_sha256'],'Decoded output hash mismatch')
    block=oe.replace_payload(blocks[0],changed)
    require(block.header==blocks[0].header and block.trailer[:28]==blocks[0].trailer[:28],
            'Unexpected container metadata edit')
    require(oe.sum32(block.header+block.payload+block.trailer)==0,'Main checksum mismatch')
    # Hash/write the encoded main and the exact untouched stock tail separately.
    # Verification mode does not materialize a complete update package.
    chunks=(block.header,oe.encode(block.payload),block.trailer,raw[blocks[1].offset:])
    reparsed_main=oe.parse(b''.join(chunks[:3]))
    require(len(reparsed_main)==1 and reparsed_main[0].payload==bytes(changed),
            'Encoded main roundtrip failed before any output creation')
    h=hashlib.sha256()
    for chunk in chunks:h.update(chunk)
    total=sum(len(c) for c in chunks)
    require(total==manifest['output_bytes'] and h.hexdigest()==manifest['output_sha256'],
            'Whole package expected size/hash mismatch')
    require(sha(raw)==manifest['restore_sha256'],'Restore hash mismatch')
    summary=dict(input_sha256=sha(raw),prospective_output_sha256=h.hexdigest(),bytes=total,
                 decoded_output_sha256=sha(changed),unchanged_components=4,
                 hook_source_sha256=sha(source),manifest_sha256=sha((HERE/'patch.json').read_bytes()),
                 tool_versions=versions,verify_only=args.verify_only,package_files_created=not args.verify_only)
    if destination is not None:
        destination.mkdir(parents=True,mode=0o700)
        install=destination/manifest['install_path']
        restore=destination/manifest['restore_path']
        for target in (install,restore):target.parent.mkdir(parents=True,mode=0o700)
        with install.open('xb') as stream:
            for chunk in chunks:stream.write(chunk)
        with restore.open('xb') as stream:stream.write(raw)
        install.chmod(0o600)
        restore.chmod(0o600)
        check=oe.parse(install.read_bytes())
        require(len(check)==5 and check[0].payload==bytes(changed),'Generated package reparse mismatch')
        require(all((a.header,a.payload,a.trailer)==(b.header,b.payload,b.trailer)
                    for a,b in zip(blocks[1:],check[1:])),'Other component changed')
        (destination/'build.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return summary


def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',required=True,type=Path)
    p.add_argument('--upstream',required=True,type=Path)
    p.add_argument('--toolchain',type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--verify-only',action='store_true')
    build(p.parse_args())


if __name__=='__main__':main()
