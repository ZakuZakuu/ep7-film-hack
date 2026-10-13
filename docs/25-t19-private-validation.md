# T19 · Private reproduction, decisions and handoff

[Findings/graph](../research/e142-art-native-consumers.md) · [selected validation](../research/e142-t19-validation.json) · [Issue47](https://github.com/ZakuZakuu/ep7-film-hack/issues/47).
Baseline6ce9dccb6fecd7fad597a6d14b3ffee204558df6, mergedPR46. E-P7, owner-reported1.1. Original111017984/SHA2569d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb; decoded#0 SHA2565dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190. Five OE residuals0; inputs unchanged. Coordinates: decoded#0 offsets and explicitly scoped static values; no live RAM.

Existing Cloud Setup remains valid. Use the already verified private sample; no download/serial/device is needed. OEM, decoded bytes, operand listings, SQLite and reference results stay in private /tmp directories (0700 directories/0600 outputs); never upload/store them in public CI. GNU sim runs original fixtures only. The builder guards identities before/after and atomically replaces the private DB; failed guards preserve its preceding checkpoint.

    source /tmp/ep7-re-tools/env.sh
    python3 tools/ep7_re_workbench.py \
      --firmware /tmp/ep7-firmware/E142_EP7_firmware_download.BIN \
      --objdump "$EP7_OBJDUMP" --output-dir /tmp/ep7-re-project
    python3 tools/t19_reference_probe.py \
      --decoded /tmp/ep7-firmware/t6/block0.bin \
      --assembler "$EP7_AS" --objdump "$EP7_OBJDUMP" \
      > /tmp/ep7-t19/reference-candidates.json
    chmod 600 /tmp/ep7-t19/reference-candidates.json
    python3 tools/ep7_re_query.py --field setting872
    python3 tools/ep7_re_query.py --window t19_effect_flags
    python3 tools/ep7_re_query.py --window t19_packet_B_handoff
    python3 tools/ep7_re_query.py --field 'native constructed32-byte parameter'
    python3 tools/ep7_re_query.py --loop 0x290dcc

Expected149windows/8855instruction rows/6903CFG edges/74stops/101curated relations;139+93 T19 guards, inherited guards/negative identities retained;four finite copy proofs (32/32/24/64 bytes). Counts are **not breakthroughs, executed coverage or a whole-program map**. Boundaries in fragment windows and may-return CFG are explicit; unresolved indexed jumps, UDF12/46, generic lookup cache loops and unknown indirect targets remain stops. The new64-byte proof uses the existing verifier; it does not admit other loops or UDF.

The reference helper assembles/decodes112 original instructions with external GNU; max64 byte candidates/pattern and512 total. A hit is not code, an xref, receiver ownership or complete reader discovery. The synthesized24785 form found real readers missed by displacement-only matching. Promotion requires independent function entries/arguments, actual field stores and caller/receiver joins. The public verifier checks those selected relations and symbolically summarizes only an acyclic word-update block; it never executes OEM instructions.

**Central slice:**872→nativef5d1/index0→signed-byte getter→config24785→3cab19→constructed32-byte word12→3337cb. Bank/UDF selection is still conditional; the independent field/constructor/receiver join avoids assuming its semantics. Actual constructor/receiver pairs3d2812/3d281e and3d2b8e/3d2b99 preserve the same buffers. Primary bufferSP324…355 precedes savedD2SP356 in372-byte frame. Type16 comes from3ca8e9; initial auxiliary30 zero is not an unconditional value through opaque calls. The old35-byte source owner remains unbound. No pixel/ISP/JPEG worker was identified, and the exhausted333c50/72/334780 route was not reopened.

**Independent provenance:** key111 has three native leaves and33 physical64-byte enum candidates; selected8/12→native100/104. Per-variant effect records44d1/f5e1 index0/4 match both native update cases and selected18-byte bracketing metadata. The46-byte-shaped bracket record is not48 user presets. Native8b54 active mirror, fixed word shadow and7076-byte backup are distinct views; their runtime alias is not assumed. Applying shadow values through2abc54 bypasses the outer byte gate but is not flash persistence or a proved ART begin/end operation pair.

## Independent metadata falsifier

Reuse ExifTool13.59 at **2200871d9cef988051d2a99d67df3bda6cbb30a8**, Artistic License or GPL. [Source](https://github.com/exiftool/exiftool/blob/2200871d9cef988051d2a99d67df3bda6cbb30a8/lib/Image/ExifTool/Olympus.pm) SHA256f974dc7c82b5e187148e0defc8d733734445df2121175097f001fe551ae08651. Use the T9 external checkout or obtain this pinned public source under ignored work/, not proprietary input:

    mkdir -p work/t19-sources/exiftool
    curl -fL --max-time 60 \
      https://codeload.github.com/exiftool/exiftool/tar.gz/2200871d9cef988051d2a99d67df3bda6cbb30a8 \
      -o work/t19-sources/exiftool.tgz
    tar -xzf work/t19-sources/exiftool.tgz --strip-components=1 \
      -C work/t19-sources/exiftool
    perl -Iwork/t19-sources/exiftool/lib tools/check_art_effect_metadata.pl

The original checker verifies provider version/source hash, supplies only three own20-word metadata vectors to FoundTag/GetValue and rejects the wrong effect-slot placement. It neither writes metadata nor receives OEM code/photos. This independently supports the metadata interpretation of40-byte native block3264 and tags8040/8080/8081; **not an ISP ABI or accepted on-camera combination**. Old-model comments in ExifTool do not establish cross-model firmware compatibility. Only numeric E-P7 serializer mappings are verified; stock labels are externally corroborated associations, not image output or recovered algorithms.

    source /tmp/ep7-re-tools/env.sh
    SQUASHFS_TOOLS_DIR="$PWD/work/squashfs-upstream/source/squashfs-tools" \
      python3 -m unittest discover -s tests -v
    git diff --check

Measured77 synthetic tests/0skipped, including original GNU reference assembly and arithmetic negative controls. Separate ExifTool3 original vectors/wrong-slot control pass. Source/manifest/fixture fingerprints, input/five OE hashes and private permissions are checked. CI uses original/synthetic data only; the optional external metadata checker is not counted as an OEM or camera test. No environment Setup change or proprietary CI artifact.

## Decision and resumable handoff

Completed all warranted stages: two distinct initial consumer negatives; independently grounded native store/descriptor relation; composite/scratch and bracket lifetime hypotheses; targeted positive-DIV reuse/UDF non-admission; actual flags/known-receiver breakthrough; second constructor, second mode/index and external metadata falsifiers. Safe branch checkpoints2b25bc3 and3205aba were pushed while research continued. Final PR integrates results rather than creating multiple dependent PRs.

**Continue a bounded architecture question after review; pause generic tracing and feature/install engineering.** Best discriminator: independently bind the context returned by3337cb and stored at actor+36 to an actual frame/preview/JPEG module/interface. Require concrete ownership/registration or a legitimate exact-model driver contract. Completion callbacks and metadata serializers are countercontrols, not rendering. Do not simply recurse ordinary callees, rescan old301d16/seed/Type classifier, sweep all39 keys, infer RAW banks or treat tagged metadata as ISP commands. If no independent frame/interface anchor emerges, pause that search.

Remaining: original35-byte source ownership; UDF bank semantics; runtime bank/actor roles; actual pixel consumption; grain rendering/freedom to combine; named complete-look persistence/extra entries/import/assets; separate installation acceptance/recovery. G2 incomplete/G3G6 unvalidated/G4G5 NO-GO. No firmware/device/vendor action is authorized here. A future passive device observation would require a separate safe plan/approval; none was performed or supplied as a ready probe.

The private workspace includes /tmp/ep7-re-project/project.sqlite, /tmp/ep7-t19 and ignored work/t19 decision/validation logs. Preserve them with both exact samples. Rebuild on the final branch to verify fingerprints; don't restart T14–T18. Stop is based on the missing independent processing anchor, **not a claimed Cloud timeout or all-day execution**. No background successor was scheduled.
