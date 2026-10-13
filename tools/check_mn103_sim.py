#!/usr/bin/env python3
"""Build/run only repository-owned synthetic fixtures in external GNU sim.

No user binary/firmware argument, OEM execution, simulator source vendoring,
trace export, device IO, or homemade CPU interpreter.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

FIXTURES = Path(__file__).resolve().parents[1]/'tests/fixtures'


def compile_fixture(root, source, output, far=False):
    obj = output.with_suffix('.o')
    assembler,linker = root/'binutils/gas/as-new',root/'binutils/ld/ld-new'
    subprocess.run([str(assembler),'-o',str(obj),str(source)],capture_output=True,check=True,timeout=30)
    options = ['--section-start=.far=0x18000'] if far else [
        '--section-start=.input=0x21000','--section-start=.output=0x22000']
    subprocess.run([str(linker),'--no-relax','-Ttext=0',*options,'-o',str(output),str(obj)],
                   capture_output=True,check=True,timeout=30)


def check(root):
    simulator = root/'gnu-sim/sim/mn10300/run'
    version = subprocess.run([str(simulator),'--version'],capture_output=True,
                             text=True,check=True,timeout=10).stdout.splitlines()[0]
    if not version.endswith('17.0.50.20250202-git'):
        raise ValueError('unadmitted GNU simulator version')
    results = {}
    with tempfile.TemporaryDirectory(prefix='ep7-synthetic-sim-',dir='/tmp') as d:
        private = Path(d)
        for name,far in [('mn103_semantics',False),('mn103_long_calls',True),
                         ('mn103_lir_control',False),('mn103_udf_provider',False),
                         ('mn103_entry_pair',False),('mn103_division',False)]:
            elf = private/(name+'.elf')
            compile_fixture(root,FIXTURES/(name+'.s'),elf,far)
            statuses = {}
            for architecture in ('mn10300','am33','am33-2'):
                p = subprocess.run([str(simulator),'--architecture='+architecture,str(elf)],
                                   capture_output=True,timeout=10)
                expected = {'mn103_lir_control':9,'mn103_udf_provider':91}.get(name,0)
                if p.returncode != expected:
                    raise ValueError('synthetic semantic/fidelity result changed')
                statuses[architecture] = p.returncode
            results[name] = statuses
        # Positive controls alone could hide a fixture that never checked results.
        text = (FIXTURES/'mn103_semantics.s').read_text()
        if text.count('eq a0,0x21020') != 1:
            raise ValueError('negative control location changed')
        negative = private/'negative.s'
        negative.write_text(text.replace('eq a0,0x21020','eq a0,0x21024'))
        elf = private/'negative.elf'
        compile_fixture(root,negative,elf)
        p = subprocess.run([str(simulator),str(elf)],capture_output=True,timeout=10)
        if p.returncode != 73:
            raise ValueError('known incorrect copy result was not rejected')
        results['incorrect_pointer_expectation'] = p.returncode
        # Mistaking the full entry for its CALL-prepared body applies the
        # prologue twice. This original fixture rejects it before returning.
        text = (FIXTURES/'mn103_entry_pair.s').read_text()
        if text.count('call body,[a2],8') != 1:
            raise ValueError('entry-pair countercontrol location changed')
        negative.write_text(text.replace('call body,[a2],8','call full,[a2],8'))
        compile_fixture(root,negative,elf)
        p = subprocess.run([str(simulator),str(elf)],capture_output=True,timeout=10)
        if p.returncode != 73:
            raise ValueError('incorrect double-prologue entry was not rejected')
        results['incorrect_full_entry_expectation'] = p.returncode
        text=(FIXTURES/'mn103_division.s').read_text()
        if text.count('cmp 137,d1')!=1:
            raise ValueError('division countercontrol location changed')
        negative.write_text(text.replace('cmp 137,d1','cmp 138,d1'))
        compile_fixture(root,negative,elf)
        p=subprocess.run([str(simulator),str(elf)],capture_output=True,timeout=10)
        if p.returncode!=73:
            raise ValueError('incorrect arithmetic expectation was not rejected')
        results['incorrect_division_expectation']=p.returncode
        text=(FIXTURES/'mn103_division.s').read_text()
        if 'cmp 15,d2' not in text:
            raise ValueError('signed division countercontrol location changed')
        negative.write_text(text.replace('cmp 15,d2','cmp 14,d2'))
        compile_fixture(root,negative,elf)
        p=subprocess.run([str(simulator),str(elf)],capture_output=True,text=True,timeout=10)
        if p.returncode != 73:
            raise ValueError('signed division countercontrol failed')
        results['incorrect_signed_division_expectation']=p.returncode
    return {'simulator':version,'fixture_results':results,
            'call_data_branch_readonly_loop':'PASSED on these original synthetic fixtures',
            'lir_cached_code_fidelity':'PARTIAL: observed 9; manual cached immediate would remain 7',
            'udf_ep7_admission':'UNADMITTED: user-defined operation; provider immediate255 unsigned expectation fails (91)',
            'division_scope':'DIVU MDR=0/divisor1000/nonnegative31-bit and positive DIV 255/20,32/20,33/64,2112/64; quotient/remainder only, not flags/overflow/zero-divisor',
            'oem_execution':False,'cpu_subtype_of_ep7':'unknown; common fixture passes do not discriminate'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('/tmp/ep7-re-tools'))
    a = p.parse_args()
    try:
        result = check(a.root.resolve())
    except (OSError,ValueError,subprocess.SubprocessError):
        p.exit(2,'STOP: synthetic GNU simulation admission failed; no OEM/trace output.\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
