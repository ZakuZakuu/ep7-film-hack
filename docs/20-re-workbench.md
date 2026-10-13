# T14 · Codex Cloud reverse-engineering workbench

T17 extends the default private corpus to48 nominated windows; [current reproduction](23-t17-private-validation.md). Historical counts below remain T14/T15 results. UDF is still unadmitted.

2026-10-12 · [Issue #37](https://github.com/ZakuZakuu/ep7-film-hack/issues/37) · [Tool decisions and architecture](../research/e142-system-re-workbench.md).

**T15 supersedes the default build/CFG behavior:** [docs21](21-mn103-semantics.md) adds external GNU sim for original fixtures and two static loop proofs. Counts/stops below describe the historical T14 run; use --legacy-flow to reproduce them. The owner Setup entrypoint remains unchanged.

The usable E-P7 provider is GNU binutils 2.44 plus a bounded private SQLite project. Official Ghidra headless works on our synthetic x86-64 ELF; REA is installed but its actual native request is blocked in this Cloud runtime. No MN103 decompiler is admitted. This is an intermediate analysis database, not recovered source, an emulator, a camera application or a firmware editor.

## Paste into Cloud Setup

After this PR is reviewed and its code is available in the checkout, paste:

    set -e
    cd /workspace/ep7-film-hack
    bash tools/setup_re_environment.sh

For a Codex checkout at a different location, change only the cd line to that repository. The script installs public tools only into /tmp/ep7-re-tools, pins archives by SHA-256 and REA/transitive npm packages by the committed lockfile, uses noninteractive installation, and reruns without rebuilding an existing installation. GNU assembler/linker are used only for original synthetic fixtures. No firmware, serial, photo, camera command, MCP registration or OEM project is part of setup.

No environment variables or secrets are required for setup. EP7_SERIAL is neither required nor read. Preserve Cloud's injected proxy/CA configuration; do not print the environment or disable TLS. If network allowances are restricted, public tool installation requires ftp.gnu.org, github.com, release-assets.githubusercontent.com, nodejs.org and registry.npmjs.org. The optional missing-prerequisite branch uses the configured Debian/Ubuntu apt mirrors; do not replace the injected mirror/proxy settings.

The tested Cloud image already supplied Python, GCC/G++, make, curl, tar, xz, unzip and coreutils. If absent, the script installs them using apt-get with root/noninteractive sudo. That fallback was not needed here; a non-Debian base or unavailable sudo is a concrete STOP, not a tested configuration. A separate clean core directory was successfully built from the hash-checked public archive, and repeated core/full setup succeeded. The owner need not install a GUI, paid engine or local desktop tool.

Each task shell must load the generated environment explicitly; Setup exports do not necessarily propagate to later tasks:

    source /tmp/ep7-re-tools/env.sh
    python3 tools/check_re_environment.py
    python3 tools/check_re_environment.py --headless-smoke
    python3 tools/check_re_environment.py --provider-smoke

The second smoke test inspects our generated benign ELF directly in official Ghidra and removes its ephemeral project. The third actually requests its function through REA, rather than checking help. In this task it returns structured blocked/provider_unavailable/runtime_missing, exit 3. Independent Node spawnSync probes also return EPERM on /bin/true and both JDKs despite child status 0; the exact denied syscall is unknown because ptrace is also prohibited. The installed REA6.4.0 distribution also lacks the raw architecture CLI flags documented in the newer audited source, and neither supports MN103. No environment variable/domain change has been shown to fix this. Do not patch REA to ignore its process error or ownership checks. GNU and direct headless Ghidra need no additional Cloud settings here.

To skip the currently blocked adapter and large provider downloads:

    bash tools/setup_re_environment.sh --core-only

This remains a complete usable E-P7 intermediate provider. Full install measured about 2.9 GiB including caches/sources, two GNU build jobs, and a 512 MiB headless smoke heap. Core-only needs substantially less space. Dry-run performs no installation:

    bash tools/setup_re_environment.sh --dry-run
    bash tools/setup_re_environment.sh --help

Public archive/build caches can be discarded after validation:

    rm -rf /tmp/ep7-re-tools/cache /tmp/ep7-re-tools/binutils-source

This does not delete the separate private firmware or project. Installing again may redownload missing archives if tools need rebuilding. To uninstall these task-local public tools, remove only /tmp/ep7-re-tools; do not remove private research unless deliberately discarding it. No home-directory files or agent registrations were created.

## Guarded private project

Setup must never download or embed OEM data in a reusable Cloud image. In a fresh task, obtain the authorized firmware only inside the task-private environment using the existing [private download procedure](12-codex-cloud-private-download.md), if it is not already present. No serial value appears in these instructions. Stop if acquisition/hash validation fails. Task-local /tmp persistence is not guaranteed.

With the existing file:

    source /tmp/ep7-re-tools/env.sh
    python3 tools/ep7_re_workbench.py \
      --firmware /tmp/ep7-firmware/E142_EP7_firmware_download.BIN \
      --objdump "$EP7_OBJDUMP" \
      --output-dir /tmp/ep7-re-project

Expected: 26 nominated windows, 43 selected instruction guards, 47 evidence edges, five OE checksum residuals zero, matching original/decoded hashes before and after analysis, and passing scoped layout checks. The three ART corpus windows decode identically under GNU mn10300/am33/am33-2 selectors. These selectors share an implementation; this is not independent cross-decoder or P-code validation.

Private outputs are project.sqlite and sanitized-graph.json in a mode0700 directory; files are mode0600. The database contains OEM instruction text, so it must never be committed/uploaded/cached in Setup or CI. The name sanitized-graph does not grant permission to publish it wholesale: select and review public numerical findings, as in the committed [validation selection](../research/e142-workbench-validation.json).

Queries publish selected numbers and original interpretations only:

    python3 tools/ep7_re_query.py --incoming 0x3337cb
    python3 tools/ep7_re_query.py --field source+33:u8
    python3 tools/ep7_re_query.py --window effect_receiver
    python3 tools/ep7_re_query.py

The first distinguishes entry-reachable CFG edges from curated instruction guards beyond an unmodeled hardware loop. Empty CFG xrefs never mean no caller. SQL indexes support incoming/outgoing references; instructions, window membership, reachability, unresolved stops and conditional evidence are retained privately. No generic whole-image function discovery, automatic aliases, SSA, value propagation or pseudocode is claimed.

## Recovery, changes and tests

Git preserves the original manifest, typed fields, negative identities, T7 index and guard scripts. A new task reinstalls public tools, privately reacquires the exact sample if needed, and rebuilds the same index. SQLite records the decoder/script/manifest fingerprints; it is replaceable evidence, not the only copy of a finding. Rebuild validates before atomically replacing the database; no OEM binary dump is written. All address ranges remain independently scoped. New windows require source evidence and review rather than recursion from every call.

    source /tmp/ep7-re-tools/env.sh
    python3 -m unittest discover -s tests -v
    git diff --check

Tests are synthetic only. The real GNU integration assembles and links our original branch/call/return fixture, applies ELF relocations, and checks raw decode and finite CFG. It never links OEM code. The existing SquashFS integration requires upstream mksquashfs/unsquashfs; local 50/50 passed with the existing upstream tools directory set through SQUASHFS_TOOLS_DIR. CI installs SquashFS tools and core GNU; it contains no OEM sample or provider project.

The private fixed-result run additionally guards the old source+20→temp+12 transfer, existing keyed MonoEnable branch/table, T12 classifier counterexample and the new source+33→classifier input join. Arithmetic reconstruction is not execution of original firmware. G2 is incomplete, G3/G6 untested, G4/G5 NO-GO.

T18 adds [ART graph validation](24-t18-private-validation.md) without a Setup change:94 windows/5795 rows/82 curated edges and3 **local conditional** copy proofs. Candidate GUI factory still stops at its first lookup loop/UDF; a later24-byte proof does not establish full reachability or a renderer. Counts are private reproduction metadata, not a program-coverage claim.
