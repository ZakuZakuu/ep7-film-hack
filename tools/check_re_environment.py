#!/usr/bin/env python3
"""Safe tool admission; --provider-smoke inspects an original benign ELF only."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def run(argv, env=None, timeout=30):
    return subprocess.run([str(a) for a in argv], capture_output=True, text=True,
                          timeout=timeout, check=True, env=env).stdout


def check(root: Path, provider_smoke=False, headless_smoke=False):
    objdump = root / 'binutils/binutils/objdump'
    assembler = root / 'binutils/gas/as-new'
    report = {'gnu': run([objdump, '--version']).splitlines()[0],
              'assembler': run([assembler, '--version']).splitlines()[0],
              'mn103_decompiler': 'disabled: no admitted language/P-code'}
    if not report['gnu'].endswith('2.44') or not report['assembler'].endswith('2.44'):
        raise ValueError('GNU version mismatch')
    # An original synthetic fixture: direct call + both returns. No OEM bytes.
    try:
        from .probe_oe_executable import disassemble, walk
    except ImportError:
        from probe_oe_executable import disassemble, walk
    rows = disassemble(objdump, bytes.fromhex('cd08000000df0000df0000'), 0)
    if walk(rows, 0)['direct_calls'][0]['target'] != 8 or walk(rows, 8)['return_offsets'] != [8]:
        raise ValueError('GNU synthetic flow mismatch')
    report['synthetic_gnu'] = 'pass'
    ghidra = root / 'ghidra_12.1.4_PUBLIC'
    if ghidra.is_dir():
        props = (ghidra/'Ghidra/application.properties').read_text()
        if 'application.version=12.1.4' not in props:
            raise ValueError('Ghidra version mismatch')
        report['ghidra'] = '12.1.4'
        languages = '\n'.join(p.read_text() for p in (ghidra/'Ghidra/Processors').rglob('*.ldefs'))
        report['stock_mn103_language'] = any(s in languages.lower() for s in ('mn103', 'am33'))
        report['node'] = run([root/'node/bin/node', '--version']).strip()
        if report['node'] != 'v24.19.0':
            raise ValueError('Node version mismatch')
        release = dict(line.split('=',1) for line in (root/'jdk/release').read_text().splitlines() if '=' in line)
        report['jdk_release'] = release['JAVA_RUNTIME_VERSION'].strip('"')
        if report['jdk_release'] != '21.0.8+9-LTS':
            raise ValueError('JDK version mismatch')
        rea = root/'rea/node_modules/rea-agents'
        if json.loads((rea/'package.json').read_text())['version'] != '6.4.0':
            raise ValueError('REA version mismatch')
        report['rea'] = '6.4.0 installed; provider not yet tested'
        cli_help = run([root/'node/bin/node',rea/'scripts/rea.mjs','analyze','--help'])
        report['rea_raw_architecture_flag'] = '--architecture' in cli_help
        if provider_smoke or headless_smoke:
            with tempfile.TemporaryDirectory(prefix='ep7-rea-smoke-', dir='/tmp') as d:
                private = Path(d)
                source = private/'demo.c'
                source.write_text('__attribute__((noinline)) int film_style_demo(int x) { return x > 3 ? x + 7 : x - 2; }\nint main(void) { return film_style_demo(4); }\n')
                binary = private/'demo'
                run(['gcc', '-g', '-O0', '-fno-inline', '-o', binary, source])
                env = dict(os.environ)  # inherited secrets are never serialized
                env.update(JAVA_HOME=str(root/'jdk'), GHIDRA_INSTALL_DIR=str(ghidra),
                           XDG_CACHE_HOME=str(private/'cache'), XDG_CONFIG_HOME=str(private/'config'),
                           GHIDRA_HEADLESS_MAXMEM='512M', REA_GHIDRA_STARTUP_TIMEOUT_MS='180000')
                if provider_smoke:
                    # Actual native query; failure is recorded rather than
                    # ignored/rewritten to fake provider readiness.
                    completed = subprocess.run(
                        [str(root/'node/bin/node'),str(rea/'scripts/rea.mjs'),'function',
                         str(binary),'film_style_demo','--provider','ghidra','--json'],
                        env=env,capture_output=True,text=True,timeout=220)
                    result = json.loads(completed.stdout)
                    if completed.returncode or result.get('error'):
                        report['rea'] = 'blocked: actual synthetic function request'
                        report['rea_error_code'] = result.get('code','unknown')
                        rejected = result.get('details',{}).get('rejections',[])
                        report['ghidra_rejection_codes'] = [r['code'] for r in rejected if r.get('provider_id')=='ghidra']
                    else:
                        encoded = json.dumps(result)
                        if 'film_style_demo' not in encoded or 'ghidra' not in encoded.lower():
                            raise ValueError('REA did not return the synthetic function')
                        report['rea'] = 'pass: headless Ghidra function query on original x86-64 ELF'
                if headless_smoke:
                    result_path = private/'headless-result.json'
                    env['GHIDRA_HEADLESS_JAVA_OPTIONS'] = '-XX:-UsePerfData'
                    scripts = Path(__file__).resolve().parent/'re_environment'
                    # Python process launching is independently tested here.
                    completed = subprocess.run(
                        [str(ghidra/'support/analyzeHeadless'),str(private),'admission',
                         '-import',str(binary),'-readOnly','-deleteProject','-max-cpu','2',
                         '-scriptPath',str(scripts),'-postScript','BenignAdmission.java',str(result_path)],
                        env=env,capture_output=True,text=True,timeout=220)
                    if completed.returncode or not result_path.is_file():
                        raise ValueError('Direct Ghidra synthetic headless check failed')
                    report['ghidra_direct'] = json.loads(result_path.read_text())
    elif provider_smoke or headless_smoke:
        raise ValueError('Provider tools missing; rerun default setup')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('/tmp/ep7-re-tools'))
    p.add_argument('--provider-smoke', action='store_true')
    p.add_argument('--headless-smoke', action='store_true')
    a = p.parse_args()
    try:
        report = check(a.root.resolve(), a.provider_smoke, a.headless_smoke)
    except (OSError, ValueError, subprocess.SubprocessError):
        p.exit(2, 'STOP: environment admission failed; no private output or environment values published.\n')
    print(json.dumps(report, indent=2))
    if report.get('rea','').startswith('blocked:'):
        raise SystemExit(3)  # installed != admitted


if __name__ == '__main__':
    main()
