# T17 · Reproduce the adjusted-object, entry and control-root evidence

[Report](../research/e142-longrun-architecture-and-deployment.md) · [Selected metadata/source audit](../research/e142-t17-validation.json). E-P7 owner-reported1.1, baseline e85a954d6b1ea10b7b5f1815cd40c160e8130600. Existing Cloud Setup remains unchanged; source the environment in each task shell.

    source /tmp/ep7-re-tools/env.sh
    python3 tools/check_mn103_sim.py
    python3 tools/ep7_re_workbench.py \
      --firmware /tmp/ep7-firmware/E142_EP7_firmware_download.BIN \
      --objdump "$EP7_OBJDUMP" --output-dir /tmp/ep7-re-project
    python3 tools/ep7_re_query.py --incoming 0xa150a4
    python3 tools/ep7_re_query.py --field 'u16 at 0x61fa729c'
    python3 tools/ep7_re_query.py --window raw_art_backend

Only repository originals run in external GNU sim. New entry-pair fixture returns0 for both entry styles on mn10300/am33/am33-2; changing prepared CALL to the full entry returns73 before any incorrect return. Prior LIR9/UDF91/false-copy73 controls remain. MOVM admission is **[A2],(SP) only**,2 bytes: save at SP-4, decrement SP4, preserve flags. No OTHER/EX/general compiler ABI or OEM execution.

Builder guards original111017984/SHA9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb and decoded#0 SHA5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190 plus all5 OE residuals before/after. Expected48 windows/2434 instruction rows/2516CFG edges/15stops/62curated relationships/2copy proofs;26 T17 guards plus inherited43/4seed/87T16 guards.12 new windows cover949 bytes,302 records;284 unique new sites,18 repeated body sites. Counts are not complete-function/runtime coverage.

Object addresses622f2ee0/622f363c are explicit static values outside admitted copied-initializer map; don't invent file inverses. Return adjustment1884 is distinct from a code-address relocation. Constructor's base-return identity remains conditional. Saved-frame check excludes explicit locals4…20 from slots24…36; it assumes normal nested returns, intact frames and no object/stack alias. The full virtual entrya150a4 and CALL-prepared bodya150a9 must not both allocate their save frame on the same invocation.

The one two-key operation scans only [74e534,7e2516), the observed T7 resolver-call span, for IDs0201e6/031b0c. Each has max16 raw hits and96-byte contexts. Observed8 raw/4 qualified fragments; known capture site is a separate positive control. Qualification is immediate-D0/adjacent-known-resolver only, **not a GUI invocation or handler registry**. No third key, different base/range, whole-image decode or downstream recursion. Names are checked through actual root/group/name pointer relationships, not handler ordinals.

    source /tmp/ep7-re-tools/env.sh
    SQUASHFS_TOOLS_DIR="$PWD/work/squashfs-upstream/source/squashfs-tools" \
      python3 -m unittest discover -s tests -v
    git diff --check

Measured64 tests/0 skips, including the two original8-byte additive-sum arrays. These arrays are never an OE/update package. A checksummed bundle is not authenticated-camera acceptance. The container audit uses existing inspect/check_expected on the original read-only descriptor:111017664 payload bytes +320 header/trailer bytes =111017984. No unparsed outer suffix does not exclude an inner/ROM verifier. Existing upstream filesystem cache is required for the no-skip local suite; see docs11 if absent. CI uses only original synthetic inputs/public tools, never OEM.

Private project remains mode0600 under0700 /tmp; no database/listings/bytes/photos/identifiers may be uploaded. Public sources were read/cached only, no SDK/gphoto/update client/device invocation. Source hashes/versions and unavailable loader410 are in selected metadata; cached documents/header content stay out of Git.

Handoff: A's generic resolver route and B's panel/RAW roots are stopped at their recorded limits. Rebuild from the exact private input and read Issue43/PR before future work. Resume ART code only with a genuinely independent selector/source-record/consumer anchor; deployment requires separate exact-model authentication/recovery evidence and authorization. No automatic next-callee task, camera action or vendor contact.
