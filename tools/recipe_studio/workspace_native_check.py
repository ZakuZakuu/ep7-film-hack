import sys, ctypes, os, struct, hashlib, random, json, time
import numpy as np
from pathlib import Path
from .workspace_hsl import WorkspaceHSL
from .workspace_probe import private_report_path


def main():
    parser = __import__("argparse").ArgumentParser(
        description="Qualified Windows Acacia native HSL comparison; no camera access"
    )
    parser.add_argument("--dll", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if sys.platform != "win32":
        raise RuntimeError("native verification requires 64-bit Windows Python")
    if ctypes.sizeof(ctypes.c_void_p) != 8:
        raise RuntimeError("native verification requires 64-bit Python")
    path = Path(args.dll).resolve()
    root = path.parent
    version = ctypes.WinDLL("version")
    version.GetFileVersionInfoSizeW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
    version.GetFileVersionInfoW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    version.VerQueryValueW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_uint32),
    ]
    size = version.GetFileVersionInfoSizeW(str(path), None)
    if not size:
        raise ValueError("DLL file version unavailable")
    info = ctypes.create_string_buffer(size)
    if not version.GetFileVersionInfoW(str(path), 0, size, info):
        raise ValueError("DLL version read failed")
    pointer = ctypes.c_void_p()
    length = ctypes.c_uint32()
    if not version.VerQueryValueW(
        info, chr(92), ctypes.byref(pointer), ctypes.byref(length)
    ):
        raise ValueError("DLL version query failed")
    fields = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint32))
    if fields[0] != 0xFEEF04BD or (
        fields[2] >> 16,
        fields[2] & 65535,
        fields[3] >> 16,
        fields[3] & 65535,
    ) != (1, 0, 3, 1):
        raise ValueError(
            "only qualified Acacia DLL 1.0.3.1 from Workspace 2.3.0.22 is supported"
        )
    report_path = private_report_path(args.report)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != args.expected_sha256:
        raise ValueError("DLL fingerprint mismatch")
    model = WorkspaceHSL(path, digest)
    rng = random.Random(74)
    points = [
        (y, cb, cr)
        for y in [0, 1, 32, 128, 254, 255]
        for cb in [0, 64, 128, 192, 255]
        for cr in [0, 64, 128, 192, 255]
    ] + [tuple(rng.randrange(256) for _ in range(3)) for i in range(4096)]
    recipes = [[0] * 36]
    for i in range(36):
        for step in [-7, -5, 5, 7]:
            v = [0] * 36
            v[i] = step
            recipes.append(v)
    recipes += [[rng.randrange(-7, 8) for _ in range(36)] for i in range(30)]
    records = []
    with os.add_dll_directory(str(root)):
        lib = ctypes.WinDLL(str(path))
        V = ctypes.c_void_p
        factory = lib.OlyGetAcaciaInstance
        factory.argtypes = [ctypes.c_int, ctypes.POINTER(V)]
        factory.restype = ctypes.c_int
        init = ctypes.CFUNCTYPE(ctypes.c_int, V)(lib._handle + 0x3D680)
        setter = ctypes.CFUNCTYPE(ctypes.c_int, V, V, V, V)(lib._handle + 0x41350)
        render = ctypes.CFUNCTYPE(ctypes.c_int, V, V, V, V)(lib._handle + 0x413B0)
        for case, values in enumerate(recipes * 2):
            mode = 5 if case < len(recipes) else 0
            obj = V()
            assert factory(4, ctypes.byref(obj)) == 0
            init(obj)
            native_values = [-x for x in values[:12]] + values[12:]
            arrays = [
                (ctypes.c_int16 * 12)(*native_values[start : start + 12])
                for start in [0, 12, 24]
            ]
            setter(obj, *arrays)
            raw = bytes(v for px in points for v in px)
            buffer = ctypes.create_string_buffer(raw, len(raw))
            desc = ctypes.create_string_buffer(
                struct.pack(
                    "<7I4xQ",
                    1,
                    len(points),
                    len(raw),
                    3,
                    8,
                    0,
                    mode,
                    ctypes.addressof(buffer),
                )
            )
            assert render(obj, desc, None, None) == 0
            coefficients = model.coefficients(values)
            nativeco = [
                struct.unpack("<3h", ctypes.string_at(obj.value + 0x134C + 28 * r, 6))
                for r in range(12)
            ]
            if coefficients != nativeco:
                raise RuntimeError("native coefficient mismatch at case " + str(case))
            actual = list(struct.iter_unpack("BBB", buffer.raw))
            pred = list(
                map(
                    tuple,
                    model.pixels8(
                        np.array(points, dtype=np.uint8), values, rgb=(mode != 5)
                    ).tolist(),
                )
            )
            errors = [
                (points[i], a, b)
                for i, (a, b) in enumerate(zip(actual, pred))
                if a != b
            ]
            records.append(
                {
                    "case": case,
                    "color_space": "ycbcr" if mode == 5 else "rgb",
                    "pixels": len(points),
                    "mismatches": len(errors),
                    "first": errors[:4],
                }
            )
            vt = ctypes.c_void_p.from_address(obj.value).value
            release = ctypes.c_void_p.from_address(vt + 16).value
            ctypes.CFUNCTYPE(ctypes.c_int, V)(release)(obj)
            if errors:
                raise RuntimeError("native pixel mismatch: " + str(records[-1]))
            if case % 12 == 0:
                print("case", case, "matched", flush=True)
        assert len(records) == len(recipes) * 2
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {
                    "format": "ep7-workspace-hsl-qualification-v1",
                    "dll": str(path),
                    "sha256": digest,
                    "implementation_sha256": hashlib.sha256(
                        Path(
                            __import__(
                                "tools.recipe_studio.workspace_hsl", fromlist=["x"]
                            ).__file__
                        ).read_bytes()
                    ).hexdigest(),
                    "cases": records,
                    "pixels": sum(x["pixels"] for x in records),
                    "passed": True,
                    "workspace_version": "2.3.0.22",
                    "dll_version": "1.0.3.1",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(
            "completed",
            len(records),
            "mismatches",
            sum(r["mismatches"] for r in records),
        )


if __name__ == "__main__":
    main()
