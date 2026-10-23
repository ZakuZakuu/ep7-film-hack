#!/usr/bin/env python3
"""Original E-P7 build adapter; upstream code is loaded, never vendored.

Reference: fishcu/oly_fw_analysis@539fcf1fa9eda5fdef8ede4deeab94a4691d94c3.
The owner admits a complete Git tree instead of unstable googlesource tar bytes.
No downloads, firmware inputs, source-marker impersonation or camera operations.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

UPSTREAM = '539fcf1fa9eda5fdef8ede4deeab94a4691d94c3'
REVISION = '87ffb882e0f4d73401a0746177ffabb8e8bbe4ac'
TREE = '059d50a3cc76bd13dc10f21023863674e6da515c'
DOCUMENTED_ARCHIVE = 'a5e7cd02f844bb2873c25e0ac8e9a5b50a72c3e8e6570a6b7821d2e4c21178ad'
CORE = {
    'sim/mn10300/interp.c': 'f6c34c6c81ff67bda52d6b57d0ea47954587e36908923cd7e4e59a90424cd37b',
    'sim/mn10300/mn10300.igen': '355754c61879dc24bf6128bbba5a7931355731000e8cb213082b9b9cd4df0129',
}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def output(args, cwd):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def archive_tree(archive, destination):
    """Build the complete index, including upstream-tracked ignored fixtures."""
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as source:
        for member in source:
            require('.git' not in Path(member.name).parts, 'Archive contains Git metadata')
            source.extract(member, destination, filter='data')
    subprocess.run(['git', 'init', '-q', '--template=', str(destination)], check=True)
    git = ['git', '-c', 'core.autocrlf=false', '-c', 'core.filemode=true']
    subprocess.run(git + ['add', '-f', '-A'], cwd=destination, check=True)
    return output(['git', 'write-tree'], destination)


def checked_reference(reference):
    commit = output(['git', 'rev-parse', 'FETCH_HEAD'], reference)
    tree = output(['git', 'rev-parse', 'FETCH_HEAD^{tree}'], reference)
    require(commit == REVISION and tree == TREE, 'Reference commit/tree mismatch')
    return commit, tree


def run_logged(command, directory, log):
    with log.open('w') as stream:
        result = subprocess.run(command, cwd=directory, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'Build failed ({result.returncode}); inspect {log}')


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    root, archive, reference = (p.resolve() for p in (args.upstream, args.archive, args.reference))
    require(1 <= args.jobs <= 8, 'Invalid job count')
    require(output(['git', 'rev-parse', 'HEAD'], root) == UPSTREAM, 'Wrong fishcu revision')
    require(not output(['git', 'status', '--porcelain'], root), 'Modified fishcu checkout')
    checked_reference(reference)
    source = root / 'toolchains/mn103-gnu-src'
    build = root / 'toolchains/mn103-gnu-build'
    receipt = {
        'upstream_commit': UPSTREAM, 'gnu_commit': REVISION, 'gnu_tree': TREE,
        'archive_actual_sha256': sha(archive), 'archive_documented_sha256': DOCUMENTED_ARCHIVE,
        'identity_rule': 'Archive bytes are unstable; verify the complete Git tree and two core hashes.',
        'core_original_sha256': CORE,
    }
    # Always requalify the supplied archive, including on a resumed build.
    with tempfile.TemporaryDirectory(prefix='ep7-gnu-tree-') as temporary:
        staged = Path(temporary) / 'source'
        require(archive_tree(archive, staged) == TREE, 'Archive Git tree mismatch')
        require(all(sha(staged / name) == digest for name, digest in CORE.items()),
                'Core source hash mismatch')
        print(json.dumps(receipt, indent=2), flush=True)
        if args.verify_only:
            return
        if not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.move(str(staged), str(source))
        else:
            marker = source / '.ep7-tree-source.json'
            require(marker.is_file() and json.loads(marker.read_text()) == receipt,
                    'Existing source lacks the exact adapter receipt')
            require(output(['git', 'write-tree'], source) == TREE, 'Original source index changed')
            changes = output(['git', 'diff', '--name-only'], source).splitlines()
            require(set(changes) <= set(CORE), 'Unexpected existing GNU source edits')
    require(not (source / '.penf-source.json').exists(), 'Refuse an upstream source marker')
    (source / '.ep7-tree-source.json').write_text(json.dumps(receipt, indent=2) + '\n')
    tools = root / 'tools'
    providers = ['build_mn103_emulator.py', 'prepare_mn103_sim.py', 'mn103_runner.c', 'mn103_strict.patch']
    before = {name: sha(tools / name) for name in providers}
    # Load the pinned provider's configuration and make recipe at runtime. They
    # stay in its checkout, rather than becoming copied source in this project.
    spec = importlib.util.spec_from_file_location('external_mn103_builder', tools / providers[0])
    provider = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(provider)
    tree = ast.parse((tools / providers[0]).read_text())
    recipes = [node.args[0].value for node in ast.walk(tree)
               if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and isinstance(node.func.value, ast.Name) and node.func.value.id == 'makefile'
               and node.func.attr == 'write_text' and node.args
               and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)]
    require(len(recipes) == 1, 'Pinned runner recipe is ambiguous')
    subprocess.run([sys.executable, str(tools / 'prepare_mn103_sim.py')], check=True)
    require(all(sha(tools / name) == digest for name, digest in before.items()),
            'Pinned provider changed during preparation')
    build.mkdir(parents=True, exist_ok=True)
    if not (build / 'Makefile').exists():
        run_logged([str(source / 'configure'), *provider.CONFIGURE], build, build / 'configure.log')
    run_logged(['make', f'-j{args.jobs}', 'all-sim', 'MAKEINFO=true'], build, build / 'build.log')
    recipe = build / 'sim/penf-harness.mk'
    recipe.write_text(recipes[0])
    run_logged(['make', '-f', 'Makefile', '-f', recipe.name, '../penf-mn103', 'V=1'],
               build / 'sim', build / 'harness-build.log')
    receipt.update(configure=provider.CONFIGURE, provider_sha256=before,
                   patched_core_sha256={name: sha(source / name) for name in CORE},
                   executable_sha256=sha(build / 'penf-mn103'))
    (build / 'ep7-build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Built external engine:', build / 'penf-mn103')


if __name__ == '__main__':
    main()
