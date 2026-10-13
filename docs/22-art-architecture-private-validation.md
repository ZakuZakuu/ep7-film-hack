# T16 · Reproduce the bounded architecture checks

T17 extends the default corpus to48 windows; [current reproduction](23-t17-private-validation.md). Counts below describe the historical T16 result.

[Finding/decision report](../research/e142-art-architecture-sprint.md) · [Issue41](https://github.com/ZakuZakuu/ep7-film-hack/issues/41). Latest main baseline796f8bec0f695802895dacafc000c9fbf17a2373; E-P7 owner-reported1.1. No new Cloud Setup or owner action is required.

All OEM input and generated project remain mode0600 under0700 /tmp directories. Never pass OEM data or a reconstructed original function to GNU sim. Do not put sample acquisition/serials into Setup/CI. The established authorized private sample is reused here.

    source /tmp/ep7-re-tools/env.sh
    python3 tools/check_mn103_sim.py
    python3 tools/ep7_re_workbench.py \
      --firmware /tmp/ep7-firmware/E142_EP7_firmware_download.BIN \
      --objdump "$EP7_OBJDUMP" \
      --output-dir /tmp/ep7-re-project
    python3 tools/ep7_re_query.py --incoming 0xa15565
    python3 tools/ep7_re_query.py --field 'returned descriptor byte+4'
    python3 tools/ep7_re_query.py --window associated_receiver_lookup

Expected:36 nominated windows,2132 rows,55 selected relationships;43 inherited instruction guards plus4 seed guards and87 T16 guards. Existing15 stops and2 conditional copy-loop proofs retained. T16 added only10 entry-to-return windows /457 bytes /160 rows; inherited fields and classifications are not counted as new results. A and D have no new code windows. The default builder now includes T16; historical T14/T15 counts remain historical. --legacy-flow retains conservative loop stops but includes the newer nominated architecture windows/guards.

Exact original111017984 bytes/SHA9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb; decoded#0 26214336/SHA5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190. Builder verifies all five OE residuals and source identity before/after, nominated call frames/field accesses and a single constructor-backed vtable slot. Wrong slot, wrong view, non-boundary target or drifted instruction fails closed. It never enumerates additional classes/callees.

Constructor-path binding does not observe a live vptr. Explicit address622f4a58 is outside admitted copied initializer bounds: don't invent its file inverse. Resolver+148 is an instance member; virtual+176 is a **vtable** byte offset, not an instance field. Later virtual+4 target/type and processing ownership remain unknown. The candidate initializer alias acrossa09a5b remains conditional on A2/A3 preservation; no general compiler ABI is admitted.

The original UDF fixture now yields controlled status91 on mn10300/am33/am33-2: immediate6 low-product checks pass, then immediate255 produces-2 rather than unsigned expectation510.73 would fail preceding arithmetic;0 would instead match the unsigned expectation and force review of the pinned result. This does not define E-P7 UDF semantics. Existing contracts still mark UDF unmodeled and CFG stops there. Existing normal/long-call fixture0, LIR negative9 and false-copy73 are unchanged. No simulator implementation was modified or copied.

    source /tmp/ep7-re-tools/env.sh
    SQUASHFS_TOOLS_DIR="$PWD/work/squashfs-upstream/source/squashfs-tools" \
      python3 -m unittest discover -s tests -v
    git diff --check

Measured60 tests/0 skipped. If the upstream SquashFS cache is absent, use the existing [filesystem tool setup](11-squashfs-private-validation.md); don't claim a skipped test passed. CI uses synthetic inputs, public GNU tools and repository originals only.

Only original guards, original fixture and selected numerical evidence are public. No complete proprietary listings, bytes, literal text, private SQLite/CFG or photos. The private decision log and handoff are session checkpoints, not repository outputs. Regenerate the private project from the authorized exact input in a later task; don't upload it as a CI artifact.
