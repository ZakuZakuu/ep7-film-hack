#!/usr/bin/env python3
"""Original E-P7 T23 offline probes; no firmware edits, export or device I/O.

Runs the separately pinned GNU engine through existing Experiment/BootState
interfaces. References (read/run only, no vendored implementation):
https://github.com/fishcu/oly_fw_analysis/tree/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3
All decoded images, caller objects, traces and results must remain under /tmp.
Dimensions, setting witnesses, successful allocation/acceptance and uncontended
locks are explicit fixtures. No pixels, completions or camera memory capacity
are emulated. Unknown accesses/services fail closed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from ep7_color_min import Experiment, BASE, STACK, SP, CALLER

Q, C, O, M = 0x19000000, 0x19100000, 0x19200000, 0x19300000
J, MASK = 0x19400000, 0x19500000
OUT = None


def dis(a, b):
    return x.disassemble(f"{a:x}_{b:x}", a, b)


def fixture(mode, stage, level, kind=0, shade=0, shadecode=0):
    ctx = bytearray(192)
    struct.pack_into("<3I", ctx, 4, Q, O, O + 0x20C)
    struct.pack_into("<I", ctx, 52, mode)
    req = bytearray(2048)
    req[16] = kind
    struct.pack_into("<HH", req, 10, mode & 0xFFFF, stage)
    req[8] = mode >> 24
    req[9] = mode >> 16 & 255
    req[1828] = level
    req[1829] = shade & 255
    struct.pack_into("<H", req, 1838, shadecode)
    struct.pack_into("<I", req, 276, M)
    return [
        r("rom", BASE, x.data, "rx"),
        r("request", Q, bytes(req)),
        r("context", C, bytes(ctx), "rw", True),
        r("output", O, b"\xa5" * 12288, "rw", True),
        r("seed_sample", M, struct.pack("<H", 0x1234)),
        r("alternate_seed", 0xA27393F8, bytes(4), "rw", True),
    ]


def upload(label, blob, bank):
    start, stop, mmio, flag = (
        (0x603460A9, 0x603460BF, 0x9F000E00, 512)
        if bank == 0
        else (0x603460BF, 0x603460D7, 0x9F804E00, 16777216)
    )
    alloc = bytearray(b"\xa5" * 12288)
    alloc[7364 : 7364 + 188] = blob
    res = x.provider.execute(
        [
            r("rom", BASE, x.data, "rx"),
            r("stack", STACK, bytes(0x2000), "rw", True),
            r("alloc", O, bytes(alloc)),
            r("mmio", mmio, b"\xa5" * 280, "w", True),
        ],
        {"pc": start, "sp": SP, "a2": O, "a3": C, "d3": flag, "psw": 0},
        stop,
        limit=500,
        trace_limit=500,
    )
    assert res["status"] == "returned", res.get("fault")
    assert res["registers"]["sp"] == SP
    x.audit_alignment(res)
    got = x.captured(res, "mmio")
    mapping = {
        0: 12,
        **{i: i + 52 for i in range(4, 120, 4)},
        **{i: i + 72 for i in range(120, 164, 4)},
        **{i: i + 92 for i in range(164, 188, 4)},
    }
    for a, b in mapping.items():
        assert got[b : b + 4] == blob[a : a + 4], (a, b)
    (OUT / f"{label}-bank{bank}.json").write_text(json.dumps(res))
    return {
        "bank": bank,
        "base": hex(mmio),
        "instructions": res["completed"],
        "gain_register": hex(mmio + 208),
        "gain": struct.unpack_from("<I", got, 208)[0],
        "all_47_words_match": True,
    }


def grain_results():
    out = []
    for stage in (0x901, 0x902):
        for level in (0, 1, 2, 3, 4, 255):
            v = x.call(
                f"grain_{stage:x}_{level}",
                0x603A013B,
                20,
                fixture(12, stage, level),
                {"a0": C},
                limit=10000,
            )
            p = x.captured(v, "output")[7364 : 7364 + 188]
            gain = struct.unpack_from("<I", p, 136)[0]
            expected = (
                ([0, 110, 300, 600] if stage == 0x901 else [0, 50, 75, 100])[level]
                if level < 4
                else 0
            )
            assert gain == expected
            out.append(
                {
                    "stage": hex(stage),
                    "level": level,
                    "gain": gain,
                    "seed": hex(struct.unpack_from("<I", p, 172)[0]),
                    "instructions": v["completed"],
                    "aligned": v["alignment_accesses_checked"],
                    "config_sha256": hashlib.sha256(p).hexdigest(),
                    "uploads": [upload(f"g_{stage:x}_{level}", p, b) for b in (0, 1)],
                }
            )
    return out


def state_type(BootState, HOOK_RETURN):
    class State(BootState):
        def __init__(self):
            self.regions = [
                R("rom", BASE, x.data, "rx"),
                R("stack", STACK, bytes(0x3000), "rw", True),
                R("trampoline", HOOK_RETURN, b"\xcb" * 8, "rx"),
            ]
            self.regs = {}
            self.steps = 0
            self.events = []
            self.cpu = 0
            self.regions.append(
                R("helpers", 0x47000800, x.data[0x141C9E0 : 0x141C9E0 + 0x1800], "rx")
            )
            self.regions.append(R("cpu", 0x8050, bytes(4), "r"))
            self.regions.append(R("scenario_1c08", 0x1C08, bytes(4), "r"))

        def enter(self, addr, mask="", frame=0, registers=None):
            code = x.assemble(
                "job_call", f"call target,[{mask}],{frame}\nnop\n", symbols={"target": addr}
            )
            if any(r.name == "caller" for r in self.regions):
                self.regions = [r for r in self.regions if r.name != "caller"]
            self.regions.append(R("caller", CALLER, code, "rx"))
            self.regs = {
                **{f"d{i}": 0 for i in range(4)},
                **{f"a{i}": 0 for i in range(4)},
                "sp": SP,
                "pc": CALLER,
                "psw": 0,
                "mdr": 0,
                **(registers or {"a0": J}),
            }
            self.finish = (
                CALLER + len(code) - 1
            )  # Return breakpoint is the caller-owned trailing NOP.

        def execute_call(self, addr, mask="", frame=0, registers=None):
            self.enter(addr, mask, frame, registers)
            r = self.run({self.finish}, limit=100000)
            if r["status"] != "breakpoint" or self.regs["pc"] != self.finish:
                raise RuntimeError((r["status"], r.get("fault"), hex(self.regs["pc"])))
            assert self.regs["sp"] == SP
            return r

    return State


def desc(pointer, fmt, w, h, pitch=None):
    b = bytearray(64)
    struct.pack_into("<I", b, 0, pointer)
    struct.pack_into("<6H", b, 8, fmt, pitch or w, w, h, w, h)
    return b


def make(mode, shade=-5, grain=3, alternate=0, dims=(5184, 3888)):
    s = State()
    b = bytearray(0x5000)
    struct.pack_into("<H", b, 14, mode)
    b[22:24] = b"\x01\x01"
    b[28] = 1
    struct.pack_into("<I", b, 16, 0x80000)
    b[36:100] = desc(0x40000000, 0x0205, *dims)
    b[4756:4820] = desc(0x50000000, 0x0702, *dims)
    b[4756 + 16 : 4756 + 20] = bytes(4)
    struct.pack_into("<I", b, 11308, mode)
    b[11320] = alternate
    b[5587] = grain
    b[5588] = shade & 255
    struct.pack_into("<I", b, 14240, MASK)
    s.ram("job", J, b, aliases=False)
    s.ram("mask", MASK, bytes(12) + desc(0x60000000, 0x080C, 128, 128), aliases=False)
    return s


def word(s, a):
    return struct.unpack("<I", s.read(a, 4))[0]


def describe(b):
    return {
        "pointer": hex(struct.unpack_from("<I", b)[0]),
        "format": hex(struct.unpack_from("<H", b, 8)[0]),
        "pitch": struct.unpack_from("<H", b, 10)[0],
        "stored": list(struct.unpack_from("<2H", b, 12)),
        "window": list(struct.unpack_from("<2H", b, 16)),
    }


def alljobs(mode, shade=-5, grain=3, alternate=0, dims=(5184, 3888)):
    s = make(mode, shade, grain, alternate, dims)
    s.execute_call(0x60357415, "d2,d3,a2,a3", 52)
    n = struct.unpack("<H", s.read(J + 11314, 2))[0]
    entries = [struct.unpack("<3I", s.read(J + 10984 + 12 * i, 12)) for i in range(n)]
    calls = []
    requests = []
    live = {}
    next_buffer = 0x30000000
    jobs = []
    for idx, (entry, callback, token) in enumerate(entries):
        s.write(J + 11312, struct.pack("<H", idx))
        s.enter(entry)
        before = s.steps
        for turn in range(100):
            r = s.run({s.finish, 0x6035648E, 0x6034442B, 0x60354BB0}, limit=150000)
            pc = s.regs["pc"]
            if r["status"] != "breakpoint" or pc == s.finish:
                break
            if pc == 0x6035648E:
                assert s.regs["a0"] == J + 4
                s.write(s.regs["a1"], struct.pack("<H", dims[0]))
                s.write(s.regs["d0"], struct.pack("<H", dims[1]))
                calls.append({"model": "dimensions", "dimensions": list(dims)})
                s.return_from_model(1)
            elif pc == 0x6034442B:
                assert s.regs["a0"] == J + 4
                op = s.regs["d0"]
                slot = s.regs["a1"]
                if op == 19:
                    assert (slot - J - 6592) % 88 == 0 and 0 <= (slot - J - 6592) // 88 < 48
                    size = word(s, slot + 72)
                    tag = word(s, slot + 76)
                    pointer = next_buffer
                    next_buffer += (size + 0xFFFF) & ~0xFFFF
                    live[slot] = pointer
                    s.write(slot + 64, struct.pack("<I", pointer))
                    calls.append(
                        {
                            "model": "allocate",
                            "slot": hex(slot),
                            "bytes": size,
                            "tag": hex(tag),
                            "pointer": hex(pointer),
                        }
                    )
                    s.return_from_model(1)
                elif op == 14:
                    calls.append(
                        {
                            "model": "availability",
                            "key": struct.unpack("<H", s.read(slot + 4, 2))[0],
                        }
                    )
                    s.return_from_model(1)
                else:
                    raise RuntimeError(("unmodeled service", op, hex(s.regs["mdr"])))
            else:
                assert s.regs["a0"] == J
                kind = s.read(J + 11364 + 16, 1)[0]
                assert kind in (0, 3)
                req = s.read(J + 11364, 1884 if kind == 0 else 712)
                path = OUT / f"request-{mode}-{alternate}-{grain}-{dims[0]}-{len(requests)}.bin"
                path.write_bytes(req)
                requests.append(
                    {
                        "kind": kind,
                        "stage": hex(struct.unpack_from("<H", req, 12)[0]),
                        "mode": struct.unpack_from("<H", req, 10)[0],
                        "source": describe(req[20:84]),
                        "mask": describe(req[532:596] if kind == 0 else req[148:212]),
                        "out": describe(req[340:404] if kind == 3 else req[916:980]),
                        "grain": req[1828] if kind == 0 else None,
                        "shade": req[1829] if kind == 0 else req[661],
                        "shadecode": struct.unpack_from("<H", req, 1838 if kind == 0 else 656)[0],
                        "dependency": hex(word(s, s.regs["sp"] + 28)),
                        "token": hex(0x12340000 + len(requests) + 1),
                        "sha256": hashlib.sha256(req).hexdigest(),
                        "private_path": str(path),
                    }
                )
                s.write(s.regs["d1"], struct.pack("<I", 0x12340000 + len(requests)))
                s.return_from_model(0)
        if r["status"] != "breakpoint" or pc != s.finish:
            (OUT / "job-fault.json").write_text(json.dumps(s.events, indent=2))
            raise RuntimeError((r["status"], r.get("fault"), hex(pc)))
        assert s.regs["sp"] == SP
        jobs.append(
            {
                "index": idx,
                "entry": hex(entry),
                "callback": hex(callback),
                "instructions": s.steps - before,
                "result": hex(s.regs["d0"]),
            }
        )
        assert s.regs["d0"] == 0
    expected_stages = (
        ["0x0"]
        if mode == 11
        else ["0x902", "0xf005", "0x0"] if alternate else ["0x900", "0x901", "0xf005", "0x0"]
    )
    assert [q["stage"] for q in requests] == expected_stages
    assert requests[0]["dependency"] == "0x0"
    assert all(q["dependency"] == p["token"] for p, q in zip(requests, requests[1:]))
    assert requests[-1]["out"]["pointer"] == "0x50000000"
    assert s.read(J + 36, 64) == desc(0x40000000, 0x0205, *dims)
    if mode == 12:
        if not alternate:
            assert requests[1]["mask"]["pointer"] == requests[0]["out"]["pointer"]
            assert requests[1]["source"] == requests[0]["source"]
        assert requests[-2]["source"]["pointer"] == requests[-3]["out"]["pointer"]
        assert requests[-1]["source"]["pointer"] == requests[-2]["out"]["pointer"]
        assert len(live) == (2 if alternate else 3)
    out = {
        "mode": mode,
        "alternate": alternate,
        "grain_input": grain,
        "shading_input": shade,
        "dimensions": list(dims),
        "jobs": jobs,
        "requests": requests,
        "models": calls,
        "live": len(live),
    }
    (OUT / f"jobs-{mode}-{alternate}-{grain}-{dims[0]}.json").write_text(json.dumps(out, indent=2))
    return out


def maskgen():
    s = State()
    U, V, T = 0x19600000, 0x19700000, 0x19800000
    s.ram("radial_out", U, b"\xa5" * 32768, aliases=False)
    s.ram("scratch", V, b"\xa5" * 8320, aliases=False)
    s.ram("input", T, struct.pack("<I5H", U, 5184, 3888, 5184, 3888, 0) + bytes(2), aliases=False)
    s.enter(0x603390A4, "d2,d3,a2,a3", 36, {"a0": T})
    events = []
    for _ in range(4):
        z = s.run({s.finish, 0x60022700, 0x60022732}, limit=500000)
        if z["status"] != "breakpoint":
            raise RuntimeError((z["status"], z.get("fault")))
        pc = s.regs["pc"]
        if pc == s.finish:
            break
        if pc == 0x60022700:
            assert s.regs["d0"] == 8320
            s.regs["a0"] = V
            events.append({"allocate": 8320})
            s.return_from_model(0)
        else:
            assert s.regs["a0"] == V
            events.append({"release": 8320})
            s.return_from_model(0)
    assert s.regs["pc"] == s.finish and s.regs["sp"] == SP and s.regs["d0"] == 0
    data = s.read(U, 32768)
    (OUT / "radial-mask.bin").write_bytes(data)
    words = struct.unpack("<16384H", data)
    return {
        "instructions": s.steps,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "dimensions": [128, 128],
        "min": min(words),
        "max": max(words),
        "symmetry_x": all(
            words[j * 128 + i] == words[j * 128 + 127 - i] for j in range(128) for i in range(64)
        ),
        "symmetry_y": all(
            words[j * 128 + i] == words[(127 - j) * 128 + i] for j in range(64) for i in range(128)
        ),
        "services": events,
    }


def callback_cases():
    out = []
    J = 0x19400000
    for kind in (0, 3):
        for level in (-128, -6, *range(-5, 6), 6, 127):
            job = bytearray(0x5000)
            job[5588] = level & 255
            struct.pack_into("<I", job, 14240, M)
            req = bytearray(2048)
            req[16] = kind
            v = x.call(
                f"shade_cb_{kind}_{level}",
                0x6035B03A,
                0,
                [
                    r("rom", BASE, x.data, "rx"),
                    r("job", J, bytes(job)),
                    r("request", Q, bytes(req), "rw", True),
                    r("radial_descriptor", M, bytes(range(100))),
                ],
                {"a0": J, "a1": Q},
                mask="",
                limit=2000,
            )
            got = x.captured(v, "request")
            code, scale, lev, descr = (1838, 1842, 1829, 532) if kind == 0 else (656, 680, 661, 148)
            expected = bytearray(req)
            expected[descr : descr + 64] = bytes(range(12, 76))
            expected[lev] = level & 255
            active = 1 <= abs(level) <= 5
            recip = 1048576 // [928, 952, 976, 1000, 1024][abs(level) - 1] if active else 1024
            struct.pack_into("<H", expected, code, 0xC00 if active else 0)
            struct.pack_into("<H", expected, scale, recip)
            assert got == expected
            out.append(
                {
                    "kind": kind,
                    "level": level,
                    "active": active,
                    "reciprocal": recip,
                    "full_request_matches": True,
                    "instructions": v["completed"],
                    "aligned": v["alignment_accesses_checked"],
                }
            )
    return out


def configs():
    out = []
    signs = {}
    for kind in (0, 3):
        for level in (-5, -1, 1, 5):
            regs = fixture(11, 0, 0, kind, level, 0xC00)
            if kind == 3:
                reg = next(a for a in regs if a.name == "request")
                b = bytearray(reg.data)
                b[661] = level & 255
                struct.pack_into("<H", b, 656, 0xC00)
                regs = [
                    (
                        r(a.name, a.address, bytes(b), a.permissions, a.capture)
                        if a.name == "request"
                        else a
                    )
                    for a in regs
                ]
            a = x.call(f"shade_sel_{kind}_{level}", 0x603B5200, 12, regs, {"a0": C}, mask="d2,a2")
            assert a["registers"]["d0"] == 33
            a = x.call(f"shade_build_{kind}_{level}", 0x603A013B, 20, regs, {"a0": C})
            blob = x.captured(a, "output")[7364 : 7364 + 188]
            expected = 0x808000 if level < 0 else 0x8080FF
            assert struct.unpack_from("<I", blob, 120)[0] == expected
            sign = -1 if level < 0 else 1
            assert blob == signs.setdefault(sign, blob)
            uploads = [upload(f"sh_{kind}_{level}", blob, bank) for bank in (0, 1)]
            for item in uploads:
                item["configuration136_register"] = item.pop("gain_register")
                item["configuration136_word"] = item.pop("gain")
            out.append(
                {
                    "kind": kind,
                    "level": level,
                    "combiner": 33,
                    "target_color": hex(expected),
                    "config_sha256": hashlib.sha256(blob).hexdigest(),
                    "instructions": a["completed"],
                    "uploads": uploads,
                }
            )
    changed = [i for i, (a, b) in enumerate(zip(signs[-1], signs[1])) if a != b]
    assert changed == [120]
    return {"cases": out, "sign_difference_bytes": changed}


def controls():
    rows = []
    for mode in (11, 12):
        for stage in (0, 0x900, 0x901, 0x902):
            regs = fixture(mode, stage, 3)
            regs = [a for a in regs if a.name != "seed_sample"] + [
                r("result", M, bytes(16), "rw", True)
            ]
            v = x.call(f"tone_{mode}_{stage:x}", 0x603B039B, 24, regs, {"a0": Q, "a1": M})
            ptr = v["registers"]["a0"]
            rows.append(
                {
                    "mode": mode,
                    "stage": hex(stage),
                    "pointer": hex(ptr),
                    "sha256": hashlib.sha256(x.read(ptr, 512)).hexdigest(),
                    "instructions": v["completed"],
                }
            )
    selectors = []
    for mode in (11, 12):
        for stage in (0, 0x900, 0x901, 0x902):
            v = x.call(
                f"icm_{mode}_{stage:x}",
                0x603B5200,
                12,
                fixture(mode, stage, 3),
                {"a0": C},
                mask="d2,a2",
            )
            got = v["registers"]["d0"]
            expected = (31 if stage == 0x901 else 32 if stage == 0x902 else 0) if mode == 12 else 0
            assert got == expected
            selectors.append(
                {"mode": mode, "stage": hex(stage), "selector": got, "instructions": v["completed"]}
            )
    art = []
    for mode in (0x01010068, 0x01020068):
        v = x.call(
            f"art_selector_{mode:x}",
            0x603B5200,
            12,
            fixture(mode, 0x100, 3),
            {"a0": C},
            mask="d2,a2",
        )
        art.append(
            {
                "key": hex(mode),
                "stage": "0x0100",
                "selector": v["registers"]["d0"],
                "instructions": v["completed"],
            }
        )
        assert v["registers"]["d0"] == 1
    mono = []
    for target in (0x603B1311, 0x603B131B):
        for mode in (11, 12):
            v = x.call(
                f"tint_{target:x}_{mode}", target, 0, fixture(mode, 0x900, 3), {"a0": C}, mask=""
            )
            out = x.captured(v, "output")
            mono.append(
                {
                    "helper": hex(target),
                    "mode": mode,
                    "word": hex(struct.unpack_from("<I", out, 0x20C + 76)[0]),
                    "instructions": v["completed"],
                }
            )
    # Own monotonic rational test data, not OEM LUT bytes.
    values = [
        round(1023 * ((4 * i / 1023) ** 2) / ((4 * i / 1023) ** 2 + 16 * (1 - 4 * i / 1023) ** 2))
        for i in range(256)
    ]
    values[-1] = 1023
    table = struct.pack("<256H", *values)
    T = 0x19800000
    uploads = []
    for bank, mmio in enumerate((0x9F00A400, 0x9F00D000)):
        s = State()
        ctx = bytearray(200)
        struct.pack_into("<I", ctx, 12, O)
        struct.pack_into("<I", ctx, 196, bank)
        struct.pack_into("<I", ctx, 56, 0x1234)
        out = bytearray(4096)
        struct.pack_into("<I", out, 2608, T)
        struct.pack_into("<I", out, 4, 16)  # explicitly skip unrelated color-sector upload
        s.ram("ctx", C, ctx, aliases=False)
        s.ram("configuration", O, out, aliases=False)
        s.ram("custom_table", T, table, aliases=False)
        s.ram("tone_cache", 0xA27360EC, bytes(8))
        s.regions.append(r("mmio", mmio + 4096, b"\xa5" * 1024, "w", True))
        s.enter(0x60346E37, "d2,d3,a2,a3", 52, {"a0": mmio, "a1": C})
        locks = []
        for _ in range(4):
            z = s.run({s.finish, 0x603B30E7, 0x603B3109}, limit=10000)
            assert z["status"] == "breakpoint", (z["status"], z.get("fault"))
            if s.regs["pc"] == s.finish:
                break
            assert s.regs["d0"] == 4
            locks.append(hex(s.regs["pc"]))
            s.return_from_model(0)
        assert s.regs["pc"] == s.finish and s.regs["sp"] == SP
        assert s.read(mmio + 4096, 1024) == struct.pack("<256I", *values)
        uploads.append(
            {
                "bank": bank,
                "uploader": hex(0x60346E37),
                "lut_destination": hex(mmio + 4096),
                "nodes": 256,
                "exact_u16_to_u32": True,
                "locks": locks,
                "instructions": s.steps,
                "table_sha256": hashlib.sha256(table).hexdigest(),
            }
        )
    return {
        "tone_selection": rows,
        "ART_selector": art,
        "ICM_selectors": selectors,
        "tint_controls": mono,
        "tone_uploads": uploads,
    }


def settings_refresh():
    rows = []
    for public, g, sh in (
        (54, 0, 1667),
        (55, 0, 1668),
        (56, 0, 1669),
        (64, 0, 1670),
        (57, 981, 995),
        (58, 982, 996),
        (59, 983, 997),
        (65, 1678, 1671),
    ):
        s = State()
        s.enter(0x602B8916, "d2", 164, {"d0": 0, "d1": public})
        writes = {}
        for _ in range(120):
            v = s.run({s.finish, 0x602B2237, 0x602B2250}, limit=2000)
            assert v["status"] == "breakpoint", (v["status"], v.get("fault"))
            if s.regs["pc"] == s.finish:
                break
            key = s.regs["a0"]
            if s.regs["pc"] == 0x602B2237:
                s.return_from_model(public if key == 111 else key)
            else:
                writes[key] = s.regs["a1"]
                s.return_from_model(0)
        assert s.regs["pc"] == s.finish and s.regs["sp"] == SP
        assert writes[980] == g and writes[994] == sh, (public, writes)
        rows.append(
            {
                "public_mode": public,
                "effective_grain_key": 980,
                "grain_witness": writes[980],
                "effective_shading_key": 994,
                "shading_witness": writes[994],
                "instructions": s.steps,
                "typed_getter_and_setter_modeled": True,
            }
        )
    return rows


def coordinates():
    rows = []
    for coeff in (928, 952, 976, 1000, 1024):
        q = 1048576 // coeff
        stack = bytearray(0x2000)
        struct.pack_into("<H", stack, SP - STACK + 44, q)
        z = x.provider.execute(
            [r("rom", BASE, x.data, "rx"), r("stack", STACK, bytes(stack), "rw", True)],
            {"pc": 0x6033D55D, "sp": SP, "a0": 1234, "d1": 2468, "psw": 0},
            0x6033D578,
            limit=30,
            trace_limit=30,
        )
        assert z["status"] == "returned"
        x.audit_alignment(z)
        got = [z["registers"]["a0"], z["registers"]["d1"]]
        assert got == [1234 * 1024 // q, 2468 * 1024 // q]
        rows.append(
            {
                "coefficient": coeff,
                "reciprocal": q,
                "input": [1234, 2468],
                "output": got,
                "instructions": z["completed"],
            }
        )
    return rows


def format_routes():
    rows = []
    for mode in (11, 12):
        for fmt, target in ((0x0302, 0x603B1843), (0x0304, 0x603B1861)):
            regs = fixture(mode, 0xF005, 3, 3)
            req = bytearray(next(a.data for a in regs if a.name == "request"))
            struct.pack_into("<H", req, 28, fmt)
            regs = [
                (
                    r(a.name, a.address, bytes(req), a.permissions, a.capture)
                    if a.name == "request"
                    else a
                )
                for a in regs
            ]
            code = x.assemble(
                "route_call", f"call target,[a2],8\nnop\n", symbols={"target": 0x603AACED}
            )
            res = x.provider.execute(
                [
                    r("caller", CALLER, code, "rx"),
                    r("stack", STACK, bytes(0x2000), "rw", True),
                    *regs,
                ],
                {"pc": CALLER, "sp": SP, "a0": C, "psw": 0},
                0xFFFFFFFF,
                breakpoints={0x603B1843, 0x603B1861},
                limit=200,
                trace_limit=200,
            )
            assert res["status"] == "breakpoint" and res["registers"]["pc"] == target
            (OUT / f"fmtroute-{mode}-{fmt:x}.json").write_text(json.dumps(res))
            rows.append(
                {
                    "mode": mode,
                    "request_kind": 3,
                    "input_format": hex(fmt),
                    "selected_wrapper": hex(target),
                    "instructions": res["completed"],
                    "scope": "native dispatcher stops at actual callee, wrapper not modeled",
                }
            )
    return rows


def main():
    global x, r, R, State, OUT
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stock", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument(
        "--upstream",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "work/upstream/oly_fw_analysis",
    )
    ap.add_argument(
        "--penf-reference", type=Path, help="Optional separately owned exact PEN-F 3101 container"
    )
    args = ap.parse_args()
    OUT = args.out.resolve()
    if not __debug__:
        raise RuntimeError("Do not disable validation with python -O")
    if Path("/tmp") not in OUT.parents:
        raise ValueError("All OEM-derived artifacts must be in private /tmp")
    for private_input in (args.stock, args.penf_reference):
        if private_input and Path("/tmp") not in private_input.resolve().parents:
            raise ValueError("OEM input files must also remain in private /tmp")
    OUT.mkdir(parents=True, exist_ok=False, mode=0o700)
    x = Experiment(args.upstream, args.stock, OUT)
    assert hashlib.sha256(x.provider.ENGINE.read_bytes()).hexdigest() == (
        "645b5cea4727da9bf859108120c76c6908a06e1b4995e1c72358665f7547175b"
    )
    r = R = x.provider.Region
    from penf_boot_emulator import BootState, HOOK_RETURN

    State = state_type(BootState, HOOK_RETURN)
    windows = [
        (0x6039FDB5, 0x603A0B0C),
        (0x603B5200, 0x603B564D),
        (0x60346A43, 0x60346A99),
        (0x603460A9, 0x603460D7),
        (0x6035B03A, 0x6035B100),
        (0x6035AE35, 0x6035AE5F),
        (0x603390A4, 0x60339146),
        (0x60338D49, 0x60338EBB),
        (0x603B039B, 0x603B07F7),
        (0x603B1311, 0x603B132A),
        (0x603AACED, 0x603AAD5D),
        (0x60346E37, 0x60347130),
        (0x6033D55D, 0x6033D578),
        (0x602B7B71, 0x602B8B18),
        (0x602A86CD, 0x602A86F9),
        (0x603E6681, 0x603E66D5),
        (0x60354CE4, 0x60355098),
        (0x60355343, 0x60355409),
        (0x60357327, 0x60357C95),
        (0x60359BC8, 0x60359E6F),
        (0x6035B4CF, 0x6035B937),
        (0x60350560, 0x60350639),
        (0x6033D165, 0x6033D19F),
        (0x603B1861, 0x603B18B5),
        (0x6036D02F, 0x6036D0B9),
    ]
    for a, b in windows:
        dis(a, b)
    mask_hash = hashlib.sha256(x.read(0x605003AA, 512)).hexdigest()
    curve_hash = hashlib.sha256(x.read(0x604EBF1C, 128)).hexdigest()
    assert mask_hash == "f2474dcac3871c3c593f4a790814b443364c860126fe38121f8048486a57370f"
    assert curve_hash == "0aaeeb348982403f55683846bcfe8dc16e73c1482a28d356826e58e17063f7e7"
    assert struct.unpack("<3H", x.read(0x604EC0CE, 6)) == (110, 300, 600)
    assert struct.unpack("<3H", x.read(0x604EC0D4, 6)) == (50, 75, 100)
    assert struct.unpack("<5H", x.read(0x604EC0DA, 10)) == (928, 952, 976, 1000, 1024)
    result = {
        "mask_sha256": mask_hash,
        "curve_sha256": curve_hash,
        "grain": grain_results(),
        "shading_callbacks": callback_cases(),
        "shading_configs": configs(),
        "radial_generation": maskgen(),
        "settings_refresh": settings_refresh(),
        "controls": controls(),
        "coordinates": coordinates(),
        "format_routes": format_routes(),
    }
    cases = [
        (11, 0, (5184, 3888), 3),
        (12, 0, (5184, 3888), 3),
        (12, 1, (5184, 3888), 3),
        (12, 0, (5184, 3888), 0),
        (12, 0, (1280, 720), 3),
    ]
    result["jobs"] = [
        alljobs(mode, grain=grain, alternate=alt, dims=dims) for mode, alt, dims, grain in cases
    ]
    if args.penf_reference:
        from oly_container import parse

        raw = args.penf_reference.read_bytes()
        assert (
            len(raw) == 87031808
            and hashlib.sha256(raw).hexdigest()
            == "77398610b379f80238117f31a6d5bbf65d608b49ec563666c64d84367e969f2c"
        )
        reference = parse(raw)[0].payload
        assert (
            x.read(0x604EBF1C, 128)
            == reference[0x605FC340 - 0x60021020 : 0x605FC340 - 0x60021020 + 128]
        )
        assert (
            x.read(0x605003AA, 512)
            == reference[0x60610742 - 0x60021020 : 0x60610742 - 0x60021020 + 512]
        )
        result["private_reference_equal"] = True
    result["windows"] = [
        {
            "start": hex(a),
            "end_exclusive": hex(b),
            "sha256": hashlib.sha256(x.read(a, b - a)).hexdigest(),
        }
        for a, b in windows
    ]
    (OUT / "checks.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "result": "pass",
                "private_output": str(OUT),
                "native_job_cases": len(cases),
                "grain_configurations": len(result["grain"]),
                "shading_callbacks": len(result["shading_callbacks"]),
                "radial_generation_instructions": result["radial_generation"]["instructions"],
            }
        )
    )


if __name__ == "__main__":
    main()
