# T6 · PictureMode hand-off is option-gated dispatch; no imaging consumer established

2026-10-12 · [Issue #23](https://github.com/ZakuZakuu/ep7-film-hack/issues/23) · latest main **`a51099b989fa4a928c2ec9b9e790813c78b68962`**, including merged PR #22. **E-P7, owner-reported firmware1.1**; private original **111017984 bytes / SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**. Decoded OE #0 SHA-256 **`5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190`**. All input/OE/decoded guards rechecked unchanged.

**Verdict: no demonstrated processing request or preview/JPEG/ISP consumer. Stop this incremental call-chain route; do not schedule another same-style callee issue.** The verified hand-off reads the relevant context's group and flags, but its local work is conditional delegation. This is an informative negative result for the hypothesis, not proof that the unexamined callees cannot eventually render images. **G2 remains incomplete; G4/G5 remain NO-GO.** Recommend a separately scoped stock COLOR expressivity measurement, or pause if that manual pilot has no value to the owner. No fitter, importer, firmware edit/package, camera request or hardware experiment here.

## One hypothesis, mature tools, finite scope

Hypothesis: the real success-path **0x333c72 → 0x334780** consumes PictureMode-derived data in an independently identifiable imaging operation/request. Falsifier: only context/option gating with opaque callees and no rendering corroboration. Reused the [T5 field/context evidence](e142-picturemode-producers-and-remote-controls.md), guarded OE decoder and **GNU binutils2.44 MN103 decoder**, with the [fixed source/hash/build provenance](../docs/13-executable-private-validation.md). GR Custom Tool's independently typed field/consumer/lifecycle method remains the methodological precedent in [T4](e142-native-profile-chain.md); no GR addresses/source transferred.

Previous `/tmp` artifacts were absent in this executor. One previously authorized official download through the existing non-echoing downloader restored the exact sample; no serial echoed or saved to task files/Git. GNU was rebuilt from the pinned archive and decoder/opcode source hashes matched T3. This access restoration is separate from the program findings. OEM bytes/transcripts remain in private `/tmp/ep7-firmware/t6/` (directory0700/files0600), outside Git.

Coordinates below are **decoded #0 offsets**, not raw `.BIN` offsets. Alias **`A=0x60020020+offset`** is previously corroborated static mapping, not observed device memory. No arbitrary pointer was identified as a framebuffer/ISP register.

## Actual arguments, typed reads and returns

| Evidence | Verified static observation | Limit |
| --- | --- | --- |
| Caller **0x333c6f / 0x333c70 / 0x333c72** | Supplies context register a3 in a0, saved additional word from stack+24 in a1, then directly calls0x334780 | Same context-register lineage as T5. The additional word was saved at0x3337cb; no buffer/handle meaning assigned |
| Primary **`[0x334780,0x3347be)`**, **62 bytes** | **23 reachable instructions**, return **0x3347bb**, no unresolved local branch or walk truncation. At0x334780/81, a2 becomes **context+4**, the copied CREATE_PARAM base | Complete local CFG under the chosen decoder, not callee execution or actual runtime conditions |
| Read at **0x334782** | Unsigned byte **(22,a2)** = **context+0x1a**, copied parameter+0x16; selects an early alternate call | Option byte's semantic name unknown; not a pixel-format/preview flag |
| Read at **0x334798** | Unsigned byte **(8,a2)** = **context+0xc**, copied parameter+8 = verified group field | group1's **Art** label comes from T4's diagnostic enum. Not a COLOR slot ID |
| Read at **0x3347a9**, test at **0x3347ad** | Word **(12,a2)** = **context+0x10**, copied parameter+0xc, tested with mask **0x80000** | Same flag-word location T5 configures; no meaning such as “JPEG enable” inferred |
| Return at **0x3347ba/bb** and caller **0x333c77…0x333c7c** | Primary normalizes result to unsigned halfword; caller tests that width for zero before returning context or taking its error-shaped path | Numeric result **0x9ec2** is the primary's default; no invented error symbol or rendering-success meaning |

This is **pointer/structure-relative data-flow evidence**, not an offset-only match: caller a3→a0, primary a0→a2 then+4, exactly the copied-object base established at0x3338f5/6. T5 key store0x33391f and flag writes were rechecked in their fixed context windows. Non-group1 comparisons with full keys9/11/12 can set mask0x80000 at0x333ba0/0x333bb4; subsequent checks can clear it at0x333bcb/0x333be0/0x333bf5. **Those integers are not identified COLOR modes.**

Important value-provenance gap: the earlier call **0x333c50 → 0x3346e9** lies between constructor writes and this hand-off. Its body was **not** analyzed. The caller supplies the context register again afterward, but effects on context **contents** are unknown; we do not claim an earlier key/flag value survives unchanged through that call. Hardware-copy-loop semantics in the old constructor remain manually supported rather than emulated. The new primary itself has no hardware-loop ambiguity.

| Local condition, under normal MN103 branch interpretation | Direct effect | Classification |
| --- | --- | --- |
| copied option byte+0x16 nonzero | **0x33478f → 0x33db40**, then return | Option-gated delegation; callee ownership **unknown** |
| Option byte zero, group1 | **0x3347b5 → 0x336289**, then return | ART-associated dispatch; no algorithm identified |
| Option byte zero, group0/2 | Read/test flag0x80000; call0x336289 only when set, otherwise return0 | Also covers Default/Scene diagnostic groups; **not exclusively ART**, and not proved COLOR1–4 |
| Option byte zero, other group | Return default0x9ec2 | Local group validation/status behavior |

In the entire bounded primary, **no composite key+0x2c2c, type byte+0xd or mode halfword+0xe read**, no context stores, pixel traversal, known coefficient operation, identified imaging API or corroborated frame/ISP/JPEG request. a0 and a1 remain available to the selected calls, but their bodies and argument interpretation are unverified. Absence is **local**, not an assertion that delegated processing is impossible. No queue/registry API was identified either: we do not rename opaque calls “task enqueue” merely to classify them.

**Issue #23 classification: E for delegated processing ownership; verified local behavior is option/group/flag dispatch, with B-like ART gating for group1 and distinct non-ART cases. D is not established.** Neither direct callee has an independently verified same-context read plus rendering rationale in the existing evidence. Therefore **zero new downstream functions inspected**. The other earlier hand-off0x3346e9, OI.Share schema, other blocks, new strings/magic and unrelated call chains were not investigated. An initial2-KiB linear decode established the return boundary; adjacent decode output was not used for functional claims. The final primary window is62bytes. Fixed old-context windows: `[0x3337cb,0x3337df)`, `[0x3338f5,0x333925)`, `[0x333b8a,0x333bfc)`, caller `[0x333c4f,0x333c97)`.

## Project decision: compare different evidence routes

| Route | Actual evidence needed / useful result | Relative cost and blocker | Recommendation |
| --- | --- | --- | --- |
| Further static reversing | A materially new anchor: independently sourced processor/color-driver semantics tied to an actual E-P7 operation, or a legitimate additional OEM version with a specific relevant change. Confirm field→processing use and independent COLOR binding | **High/open-ended** without such evidence; ordinary dispatch does not make the next callee a renderer. Install/recovery remain blocked | **Pause this chain.** Do not issue another “inspect next callee” task. A paired older version is optional, not a required stop condition |
| Manual stock COLOR look measurement | Controlled, privately kept stock JPEG/RAW pairs; declared target color space/look; measured responses to documented controls and independent held-out scene comparison | **Moderate, bounded local capture session + offline evaluation**; uses stock UI with no firmware change. Needs separately authorized owner operation/sample collection. Import ingress remains absent even if colors fit | **Preferred next evidence route**, conditional on the owner's interest. Tests whether the existing expression power is worth further investment |
| Pause project | Current findings and blockers retained; resume only for a new model-specific precedent/sample or genuinely useful measurement | **Lowest cost**; no new capabilities promised | Prefer this over continued reversing if manual controls are already ruled out by the owner or the capture pilot is not worthwhile |

Official [E-P7 manual](https://my.omsystem.com/consumer/manuals/cameras/E-P7_MANUAL_EN.pdf) pp.51–53 supports Color1–4, twelve **saturation** adjustments±5, tone/shading controls, on-screen effects and saving adjustments. “Set the hue using the front dial” selects the saturation sector; it is **not proof of twelve editable hue-angle offsets**. Re-read the existing cached manual text; the current task did not test a camera or infer numerical color freedom from UI ranges. The [image-science plan](../docs/07-image-science-and-backup.md) and [GR fitting precedent/limits](../docs/10-prior-art-matrix.md) provide method context, not E-P7 fitting results.

**Proposed minimum pilot, not performed:** after separate authorization, record existing settings and use one agreed test slot, fixed illumination/WB/ISO/exposure and a stationary color/neutral-ramp scene. Capture two baseline repeats, each of twelve saturation sectors at±1 with other controls fixed, and three tone controls at±1: **32 stills**. Keep images private and use them to distinguish one-step color responses from baseline variability. Declare the reference transform's input/output color space and gamma before comparing; do not feed linear RAW into a camera-JPEG-targeted LUT. RAW is a paired audit/control, not automatically the same reference rendering as the stock JPEG.

If responses justify a candidate manual look, test two explicitly recorded stock recipes on separate scenes/illumination and report skin/neutral/hue residuals, clipping and user preference (standard color tools/CIEDE2000 where appropriate). A local±1 model does **not** prove global infeasibility of all±5 combinations or arbitrary-LUT equivalence; held-out actual JPEG evidence is required. Stop if the resulting look remains unacceptable or the manual workflow is not useful. This pilot measures **G3/stock product value** without passing binary G2, adding an import API, or completing the requested automatic-import product. No optimizer/UI implementation until meaningful measurements exist.

## Guarded private reproduction

Requires existing authorized private sample and the fixed external GNU tool; rebuild as in T3 if needed. Run from repo root. This original snippet emits numeric metadata only; all proprietary instruction text stays private. It inspects the primary and already known context/caller windows, **not either new callee**.

```bash
umask 077
mkdir -p /tmp/ep7-firmware/t6
python3 - <<'PY'
from pathlib import Path
import hashlib, json
from tools.inspect_olympus_oe import inspect, check_expected, decode_chunk
from tools.probe_oe_executable import disassemble, walk

gnu = Path('/tmp/ep7-analysis-tools/binutils-build/binutils/objdump')
# Original synthetic call and two separate returns; no OEM fixture.
synthetic = b'\xdd'+(9).to_bytes(4,'little',signed=True)+b'\0\0'+b'\xf0\xfc'*2
rows = disassemble(gnu, synthetic, 0)
assert rows[0].direct_target() == 9
assert walk(rows,0)['return_offsets'] == [7] and walk(rows,9)['return_offsets'] == [9]

original = Path('/tmp/ep7-firmware/E142_EP7_firmware_download.BIN')
info = inspect(original)
check_expected(info,'9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb',111017984)
assert info['block_count'] == 5
assert all(b['checksum_residual'] == '0x00000000' for b in info['blocks'])
block = info['blocks'][0]
with original.open('rb') as f:
    f.seek(block['payload_offset'])
    data = decode_chunk(f.read(block['payload_length']))
assert hashlib.sha256(data).hexdigest() == block['decoded_sha256'] == \
    '5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190'

for start,end in [(0x334780,0x3347be),(0x333c4f,0x333c97),
                  (0x3337cb,0x3337df),(0x3338f5,0x333925),(0x333b8a,0x333bfc)]:
    rows = disassemble(gnu,data[start:end],start)
    private = Path('/tmp/ep7-firmware/t6') / f'{start:x}-private.asm'
    private.write_text('\n'.join(f'{r.address:x}: {r.mnemonic} {r.operands}' for r in rows)+'\n')
    private.chmod(0o600)
    if start == 0x334780:
        result = walk(rows,start)
        assert result['visited_instructions'] == 23 and result['return_offsets'] == [0x3347bb]
        assert not result['unresolved_offsets'] and not result['truncated']
        assert [(r.address,r.direct_target()) for r in rows if r.mnemonic=='call'] == \
            [(0x33478f,0x33db40),(0x3347b5,0x336289)]
        print(json.dumps(result))
    if start == 0x333c4f:
        assert next(r for r in rows if r.address==0x333c72).direct_target() == 0x334780
assert inspect(original) == info
print('synthetic control and unchanged OEM/OE/decoded guards passed')
PY
```

The old copy window contains a hardware loop and is for manual register/provenance review; do not claim a full constructor walk. `target_is_instruction_boundary=false` for the primary's calls means **outside the decoded window**, not invalid code or known callee role. No semantic emulator or decompiler is claimed.

Validation: **39 existing synthetic tests passed /0 skipped**, including mature LZO synthetic extraction; the real-GNU synthetic control and complete private reproduction above passed. Full before/after original/OE/decoded guards unchanged; Markdown links/diff and publication allowlist checked. Tests validate tooling, not color fidelity or device support. [Updated blocker](blockers/BLOCKER-e142-native-profile-consumer.md) preserves T4/T5 progress and records this stop. PR awaits review; no merge authorization, OEM artifacts, firmware writes or camera communication.
