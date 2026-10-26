#!/usr/bin/env python3
"""Original v3 manifest entry; reuse our unchanged T24 guarded builder.

No upstream source is copied. v2 keeps its own source, manifest and hashes.
Default execution requires a new private --out; --verify-only writes no BIN.
"""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_path = HERE.parents[1] / 'hsl-profiles/e-p7/build.py'
_spec = importlib.util.spec_from_file_location('ep7_v3_guarded_builder', _path)
_builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_builder)
# The existing builder reads its input/source/placement/output expectations only
# from HERE; ROOT remains the repository root. This does not edit the v2 module
# or files and cannot affect a separate v2 process.
_builder.HERE = HERE
build = _builder.build

if __name__ == '__main__':
    _builder.main()
