# T18 · Private ART linkage reproduction and handoff

[Report/graph/matrix](../research/e142-art-parameter-graph.md) · [selected checks](../research/e142-t18-validation.json). Baseline d12070d9a662f8a1281cbd9609b566a2951daf9e, Issue45. Owner-reported E-P7 FW1.1; exact original size111017984 and SHA9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb, decoded#0 SHA5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190. All five OE residuals remain0. No firmware download, serial use, device/transport or OEM execution.

Existing Cloud Setup needs no changes. All original/decoded/private SQLite/operands must remain below private `/tmp` directories. The builder guards input/decoder/manifest/selected fields before replacing the private project and checks the original again afterward. Only repository-owned fixtures run under external GNU sim.

    source /tmp/ep7-re-tools/env.sh
    python3 tools/ep7_re_workbench.py \
      --firmware /tmp/ep7-firmware/E142_EP7_firmware_download.BIN \
      --objdump "$EP7_OBJDUMP" --output-dir /tmp/ep7-re-project
    python3 tools/ep7_re_query.py --field 'u16 at 0x61fa729c'
    python3 tools/ep7_re_query.py --window panel_gui_mode_change
    python3 tools/ep7_re_query.py --window raw_art_request_fields
    python3 tools/ep7_re_query.py --window art_actuator_ctor
    python3 tools/ep7_re_query.py --field 'setting363/record0x414900+24'
    python3 tools/ep7_re_query.py --window art_bundle_producer
    python3 tools/ep7_re_query.py --loop 0xe2ceee

Expected94 windows/5795 instruction rows/4706CFG edges/28 stops/82 curated relations;60+74 T18 guards, inherited43/4seed/87T16/26T17 guards;3 copy proofs (32/32/24 bytes). These are a private bounded index, not whole-program decode or executed coverage. `gui_candidate_factory` entry visits only7 rows and stops at e2ce92; the local24-byte proof does **not** admit either earlier lookup loop/UDF. `art_bundle_producer` stops at indirect selector jumps; its two nominated table/case bindings are guarded curated relations, not general jump-table solving. T15 hardware-cache/provider countercontrols and UDF rejection remain.

`panel_reference_probe` reuses the four GNU2.44 PC-relative forms for exactly74a27f/775b02, max4 hits/target; exact61fa729c u32 max4. For slots816/820 GNU assembles the original `mn103_virtual_access.s` sixteen register pairs, max64 raw matches/slot, without executing them. Actual6/7 slot hits are only candidates. The fixed curated set contains3 setter input fragments and4 getter fragments; one getter result is overwritten. Three remaining getter matches/two remaining setter forwarding matches lack independent type binding; the other setter is the known debug path. No automatic recursive extension, arbitrary new selector, full-image code/strings/JPEG scan or virtual-ordinal map.

Qualified fragments need the actual constructor/vptr/return path; identical offsets cannot establish type. Full setter scalar propagation across opaque callees and getter return retention remain conditional on normal nested returns/register/state assumptions. No observed RAM or GUI response is claimed. Object622ce15c has no asserted file inverse. Control cell61fa729c is in the previously admitted copied-initializer view;61fa96b4 is a static publication location, not a captured live pointer.

RAW request+12/+14 are u16 routes; known temporary effects+12 is a word. RAW actor+252 result region is not identified as either a frame or style payload. Candidate GUI metadata+20 is a callback-shaped field consumed into output-object+24. No equality of offsets identifies the known effects source. Physical GUI grouping/count evidence is distinct from runtime UDF semantics; candidate417's null callback and SCN neighbor are counterevidence, not unused ART slots/custom registration proof.

The evidence-supported deeper pivot uses exactly the real component49 keyed record, ART actuator/cache, two nominated native setting identities, twelve property/callback records and selected363/364 hooks/cases8/12. Registry initializer's source41178c/count439/step60 and consumed callback+24 are guarded separately from its unadmitted lookup loops/runtime nodes. The one new builder297b51 direct-reference query (max16) found only2988fb, including its positive control; old301d16 direct-caller/self-literal probes were not repeated. No RAW/capture meaning is assigned to context0/1 or descriptor+48.

`bundle_layout` verifies39 word destinations and39 matching current-caller-SP+4 scalar arguments, with unchanged bank/type argument forms. Selected mappings are+32→setting362 and+76→872. It rejects missing/duplicated fields, halfword stores, wrong source-buffer basis and changed type. The156-byte bundle fits below handoff saved-D2 slotSP+160; normal-return/frame/opaque-getter assumptions remain. Bank dispatch292217/292230 still contains unadmitted UDF12. No array of pixels, actual processor target, old35-byte source or colour/grain outcome is inferred.

    source /tmp/ep7-re-tools/env.sh
    SQUASHFS_TOOLS_DIR="$PWD/work/squashfs-upstream/source/squashfs-tools" \
      python3 -m unittest discover -s tests -v
    git diff --check

Measured70 tests/0 skipped after sourcing the existing tool environment. Includes GNU assembly/decoding of both slots/all register pairs, wrong producer/slot/register/scalar, signed/truncated PC-relative cases, record geometry/type controls and a local24-byte proof that cannot bypass an earlier UDF. The added original division fixture checks137042/0/0x7fffffff with MDR=0/divisor1000; wrong quotient expectation returns73. Limited quotient/remainder evidence only, no flags/fault/general UDF admission. No synthetic fixture is a reconstructed OEM function. CI needs public GNU/core+sim and filesystem tools only; no OEM input.

**Handoff:** all six hypotheses in Issue45's three tracks are bounded and complete, including the newly grounded native ART configuration-record pivot. Preserve the private project, exact hashes and negative identities. No actual processor/old35-byte-source link or custom-look feature. A worthwhile separately reviewed next test is a single outgoing362/872 typed consumer with independent address/lifetime/ownership evidence; require exact-model UDF or registration definitions where needed. Pause generic tracing/feature/install engineering; do not auto-open/execute a next Issue, assume GNU UDF behavior, expand across all39 keys, recurse through generic queues/proxies, or operate a camera. Separate authorization and a safe method are required for device work. No Setup/environment change or owner action is needed to reproduce existing evidence.
