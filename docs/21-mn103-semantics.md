# T15 · Run the admitted synthetic simulator and static copy proofs

T19 extends the default private corpus to149 nominated windows; [current reproduction](25-t19-private-validation.md). Historical counts below remain T14/T15 results. UDF is still unadmitted.

2026-10-12 · [Research/admission report](../research/e142-mn103-semantics.md). Existing owner Cloud Setup call is unchanged:

    cd /workspace/ep7-film-hack
    bash tools/setup_re_environment.sh

Core-only also installs the pinned external GNU simulator; no paid tools/GUI/MCP are required:

    bash tools/setup_re_environment.sh --core-only
    source /tmp/ep7-re-tools/env.sh
    python3 tools/check_re_environment.py
    python3 tools/check_mn103_sim.py

Installation uses the binutils-2_44 source commit815d9a14cbbb3b81843f7566222c87fb22e7255d; archive/hash/license in pins.json. Simulator reports SIM17.0.50.20250202-git. It is a separate build from T14's binutils. Default board configuration is used: advertised --board=none was rejected by this snapshot. Its supported architecture options are mn10300/am33/am33-2; --model-info reports no selectable models. Neither defaults nor common fixture passes identify E-P7's actual core.

check_mn103_sim accepts a tools root, **no binary/firmware path**. It assembles/links only repository-owned fixtures in a private temporary directory, executes them through GNU sim and removes them. Positive fixtures exit0, false-copy expectation73, LIR cached-prefix countercontrol9. Output is selected results only; no traces/OEM content. A drifted result stops admission. GNU's simulator exit hook in these tests is not evidence of an E-P7 syscall interface.

No OEM ELF or decoded window may be passed to GNU sim. Model-based machine execution is restricted to originals; real firmware analysis below is non-executing structural proof.

## Rebuild private evidence

    source /tmp/ep7-re-tools/env.sh
    python3 tools/ep7_re_workbench.py \
      --firmware /tmp/ep7-firmware/E142_EP7_firmware_download.BIN \
      --objdump "$EP7_OBJDUMP" \
      --output-dir /tmp/ep7-re-project
    python3 tools/ep7_re_query.py --loop 0x3338fb
    python3 tools/ep7_re_query.py --incoming 0x3337cb

The builder first verifies original synthetic simulation, then validates original111017984/SHA9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb and all5 OE blocks, checks decoded#0 SHA5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190, and decodes the same26 nominated windows. Two locally justified loops are proved; no whole-image loop/caller/resource scan. Original hashes are rechecked. Workbench prints proof metadata, never opcode text/bytes.

Expected two32-byte proofs, existing43 guards plus4 seed guards/48 curated edges, schema2 project with instruction_effects/loop_proofs and preserved old tables. Producer11→175, receiver103→365, classifier80 unchanged. Unknown indirects, other loops, UDFU01 and unsupported restore groups remain opaque. Counted loop exits have both pointers+32, D1=0, forwarded Z/N/V/C=1/0/0/1 under the documented contract.

Project/instruction effects/full CFG remain mode0600 in0700 private /tmp. Public [selection](../research/e142-mn103-validation.json) contains original numerical findings, not full database/assembly/seed data. A new task reruns public setup and privately obtains the exact authorized sample only if needed; no firmware/serial is part of Setup, reusable image or CI.

Legacy-compatible option, with no simulator prerequisite:

    python3 tools/ep7_re_workbench.py \
      --firmware /tmp/ep7-firmware/E142_EP7_firmware_download.BIN \
      --objdump "$EP7_OBJDUMP" --legacy-flow \
      --output-dir /tmp/ep7-re-project-legacy

This retains T14 stops and does not certify loops. For a custom tool root pass --sim-root to the workbench, and --root to check_mn103_sim. Tool paths are loaded with source in each shell; exports are not assumed to persist between tools/tasks.

## Tests, sources and resource control

    source /tmp/ep7-re-tools/env.sh
    python3 -m unittest discover -s tests -v
    git diff --check

59 tests passed with existing upstream SquashFS tools set by SQUASHFS_TOOLS_DIR. CI provides SquashFS plus core GNU/sim; no OEM input. Tests cover false claims as well as positive behavior, including bad counters, pointer/counter clobbers, prefix boundaries and bypassed setup.

Processor primary manual13250-040E is read from a private archived PDF; it is not redistributed. Printed pages6,30–35,41–47,56–61,81–91 support the admitted contract subset; PDF pages have14 leading pages. Its Lcc fallthrough formula/direction labels are contradictory, so GNU implementation and actual synthetic tests were used as cross-checks. Physical LIR rotation, PSW timing, interrupt/bus/cache state and all extensions are unadmitted.

Source files reviewed externally at the pinned commit: sim/mn10300/mn10300.igen, am33.igen, am33-2.igen, op_utils.c, interp.c, local.mk and sim/COPYING. No source port into MIT code. Our small mn103_analysis module records non-executing contracts and a closed-form loop proof, **not a CPU interpreter or decoder**.

Core+sim needs roughly1.2GiB including source/build/archive, default full provider installation roughly3.5GiB. Setup uses conservative free-space estimates, stops before a low-space build and never prunes OEM data automatically. Avoid duplicating full tool roots inside a4.9GB /tmp. After validation, public source/cache directories can be removed to reclaim space:

    rm -rf /tmp/ep7-re-tools/cache /tmp/ep7-re-tools/binutils-source /tmp/ep7-re-tools/gnu-sim-source

Installed binaries still run. Future rebuilds redownload missing public sources by their pins. Never remove /tmp/ep7-firmware or /tmp/ep7-re-project as part of tool cleanup. --without-sim retains a legacy tool installation; no new environment secrets required. Preserve inherited proxy/CA; restricted allowlists need codeload.github.com in addition to T14 tool hosts.

T18 reuses the existing finite-copy contract for one nominated six-word GUI block,24 bytes, after unresolved lookup SETLB/UDF instructions. This changes no ISA admission and does not certify the earlier loops or full factory. [Exact boundaries and negative control](24-t18-private-validation.md); prior two32-byte effects proofs remain.

T18 also reads manufacturer p55/pinned GNU DIVU and checks an original nonnegative31-bit/MDR0/divisor1000 arithmetic fixture, plus a wrong-expectation73 control. Quotient/remainder support only; no general flags/overflow/zero-divisor or UDF/E-P7 CPU admission. OEM instructions are never run.
