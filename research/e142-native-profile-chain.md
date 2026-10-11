# T4 · Native Picture Mode records: real diagnostic reads, processing chain still blocked

2026-10-11 · [Issue #18](https://github.com/ZakuZakuu/ep7-film-hack/issues/18) · latest main baseline **`20f313d638a08154ca604bc7cd267e5d7fbb97b1`**, including PR #17 and the outcome-first scope in PR #19. Model **E-P7**, version **owner-reported 1.1**; private original **111017984 bytes / SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**. Full size/hash, five OE checksum residuals, decoded #0 SHA **`5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190`** and unchanged input reverified. No downloading, serial use, device communication, OEM execution, modification or repacking.

**Decision: prioritize existing COLOR slots as the conditional product route; stop this bounded program investigation with G2 incomplete.** We verified MN103 instructions reading Picture Mode fields and a selector-dependent address helper. These reads terminate in diagnostics, with an unresolved external call and unsupported arithmetic semantics along the candidate record path. They do **not** identify COLOR1–4 storage, a save function, an upload interface or a preview/JPEG consumer. Manual COLOR recipes are officially supported, but manual entry alone does not fulfill the repeatable import/export product. No fitter, LUT codec or firmware feature is implemented.

## Official native capability versus this sample

Re-read the [official manual](https://my.omsystem.com/consumer/manuals/cameras/E-P7_MANUAL_EN.pdf): pp.51–53 explicitly select Color1–4, save adjustments to the current profile, adjust twelve color saturations by ±5 while checking the screen, and control shading/highlights/midtones/shadows. pp.103–104 and 130 define Picture Mode processing and independently stored per-mode adjustments. The [official Japanese specifications](https://jp.omsystem.com/product/dslr/pen/ep7/spec.html), Color Profile/Picture Mode sections, also list COLOR1–4, twelve-color saturation ±5, shading ±5 and highlight/midtone/shadow controls ±7. These are UI ranges, not recovered binary coefficient formats.

| Claim | Evidence class and scope | What remains unknown |
| --- | --- | --- |
| Four stock COLOR profiles can be selected, edited and saved, with on-screen effect and native shooting processing | **verified official documentation**, E-P7; no camera experiment in this task | Power-cycle behavior independently measured by us, storage format/medium, slot selector IDs and binary parameter layout |
| A native Picture Mode has adjustable per-mode parameters | **verified official documentation**, manual pp.103/130 | External write/import API, mapping of documented knobs to firmware fields, richer matrix/curve controls |
| Import arbitrary XMP/3D LUTs or add named slots | **unknown**, no E-P7 implementation evidence | Expression power, ingress, persistence, true live-view/JPEG equivalence and safe deployment |

The fixed existing `oishare` XML slice **#0 `[0xec5a28, 0xec5a28+8011)`** still parses correctly. It declares no explicit COLOR Profile/Picture Mode upload interface. This negative is limited to that schema; it is not proof that every undocumented protocol is impossible. **T5 clarification:** `colorphase` is a named remote property; the schema alone gives no range, typed mapping to partial-color ART or native COLOR profiles. It cannot establish profile upload. The fixed-schema part of Issue #16 is now covered by [T5's offline inquiry](e142-picturemode-producers-and-remote-controls.md), without device responses. Official Profile Library/Profile Load destination exclusions from [T2](art-update-feasibility.md) remain applicable.

## Reuse and investigation budget

Reused the already validated OE decoder, static #0 translation **`A = 0x60020020 + payload_offset`** and **GNU binutils 2.44 MN103 decoder**. No new ISA/decompiler module, scanner suite or camera emulator. [T3 provenance and limits](../docs/13-executable-private-validation.md) remain valid: official Ghidra lacks MN103; the unverified third-party module was not used.

Exactly **two trace hypotheses** were admitted:

1. **H1: native dial selector candidate.** The exact name containing `PictureMode` could lead from the physical profile control to a native selector/accessor.
2. **H2: parameter diagnostic candidate.** Exact Picture Mode diagnostic anchors could disclose a record layout and its real getter/read-use references.

One seed-discovery pass in guarded decoded **#0 only** used the four canonical labels `COLOR1`, `Picture Mode`, `PictureMode`, `ColorProfile`, ASCII and UTF-16LE. Counts were **0/1/15/0** for ASCII and zero for those UTF-16LE spellings. Only bounded NUL context and numeric references were followed; no spelling expansion or new generic strings/JPEG/resource-magic/entropy investigation, block reopening or whole-program disassembly. The isolated spaced occurrence at **0xada086**, within a take-picture diagnostic at **0xada071**, was classified as text context and not promoted to a third trace.

All offsets below are **decoded #0 payload offsets**, not raw `.BIN` offsets. Adding 0x20 does not undo OE's intra-lane permutation. Candidate static addresses are conditional on the tested alias, never observed physical/runtime addresses. PC-relative control flow does not by itself establish a global memory map.

## H1: a name array, no demonstrated selector accessor

The substring at **0xa50299** belongs to the NUL-delimited name `CameraCommon::getPictureModeDialState`, starting **0xa50288**, length **37**. Its expected static address **0x60a702a8** occurs once, as an aligned word at **0x21fa08**.

Bounded inspection shows consecutive in-block ASCII-string pointers under the same translation in **`[0x21f8a4, 0x221078)`**: 1,525 words, the selected name at index **89**. These are **verified pointer-to-text relationships**, not profile records or function pointers. Those endpoints delimit the tested pointer predicate, not a proven complete registry boundary. A forced GNU decode of the local array illustrates the false-positive problem: arbitrary table bytes can decode as instructions and must not be classified as a function.

Exact unaligned little-endian u32 searches for **0x6023f8c4** (run start) and **0x6023fa28** (selected word location) yield **zero** in this payload. No accessor, parallel function table or selector ID was established. Other relocation/indexed representations are not excluded. **H1 stops at name data**, without assuming the dial returns four COLOR slots.

## H2: program-level record reads, with explicit gaps

### Movie-frame diagnostic

The header at **0x13f9f2a** has a real literal reference: encoded word **0x13be7c6**, nominated GNU immediate at **0x13be7c4**, value **0x61419f4a**. The enclosing entry candidate **0x13be62f** has **214 reachable instructions**, return **0x13be943**, no unresolved intra-function branch in the bounded **`[0x13be62f, 0x13be946)`** window. It identifies its output as **`MVR_FRAME_TAKE_INFO`** and uses `MovPictureMode` field labels. This is a movie/frame diagnostic; it cannot be equated with the still COLOR UI.

| Link / byte-grounded observation | Classification and limit |
| --- | --- |
| Selection argument **1**, call **0x13be658 → 0x2e9e99** | **verified instructions and direct call**; meaning of selector 1 is **unknown** |
| Helper **`[0x2e9e99, 0x2e9f08)`**, 36 reachable instructions, return **0x2e9f05** | **verified selector-dependent halfword loads**: cases 0/1/2/3 access candidate locations **0xa273104a / 4c / 4e / 50**. These are outside this static payload alias and not observed RAM contents. Four cases do **not** prove COLOR1–4 |
| Helper operation **0x2e9ef9**, constant **980 / 0x3d4**; address addend **0xa2731098** at **0x2e9eff** | GNU reports **`udfu01`**. Instruction representation is verified, exact CPU semantics **unknown**. A multiply/980-byte record stride is only a hypothesis, not used to enumerate or extract records |
| Returned address-like value passed into call at **0x13be664**, alongside a working buffer and length **660 / 0x294** | Under the supported VMA, external target is **0x47001052**, outside #0's alias. GNU with actual VMA independently confirms it. **Unknown callee**: do not label it memcpy, persistence, ROM or ISP merely from its arguments |
| Working-buffer base + **292 / 0x124**, then six byte reads | **verified read/use** in diagnostic code; not proof the preceding call copied the helper's record |
| Values supplied to repeated formatting/output-shaped calls **0xb9dcd / 0x24df / 0x261d** | **verified callsites and literal diagnostic context**; formatter/logger roles are strongly inferred, no processing ownership. The small 0x261d body reaches return0x264a; no save/ISP call is demonstrated |

The six byte reads are at **0x13be7de / 0x13be7fa / 0x13be817 / 0x13be834 / 0x13be851 / 0x13be86e**, with working-buffer offsets **0x124…0x129**. Their diagnostic labels respectively associate them with **MovPictureMode, MovPictureModeType, ColorTone, ArtEffectMode, ArtEffect, MonoFilter**. Labels establish diagnostic associations, not values, user-selectable mode IDs or algorithms. No personal settings are present or inferred from this update package.

The getter and entry-prefix windows decode identically under GNU `mn10300`, `am33`, `am33-2`; this does not resolve `udfu01` or the exact chip. The payload-relative external call target **0xe6fe1032** is a wrapped coordinate: translating it modulo 2^32 gives **0x47001052**. It is not an in-payload offset or evidence of a decoder failure. No other block/boot ROM was guessed to supply that callee.

### CREATE_PARAM diagnostic: a more useful next anchor

The short `PictureMode` heading at **0x13faf33**, candidate address **0x6141af53**, has two u32 matches: **0x13bfa8e** and **0x13c1fa8**. Both local GNU contexts place the literals at **0x13bfa8c** and **0x13c1fa6**. The latter belongs to diagnostic entry **0x13c1f98**, bounded **`[0x13c1f98, 0x13c217f)`**, **112 reachable instructions**, return **0x13c217c**, titled **`CREATE_PARAM`**.

This code retains its input object and reads:

| Object-relative offset / access instruction | Association in the diagnostic | Evidence limit |
| --- | --- | --- |
| **+8**, byte at **0x13c1fb7** | PictureGroup; cases **0/1/2** select Default/Art/Scene text | These enum-to-diagnostic-name branches are verified; not COLOR slot numbers |
| **+9**, byte at **0x13c1ff3** | PictureType | Value encoding and writer unknown |
| **+0xa**, unsigned halfword at **0x13c2003** | PictureMode | Genuine native record field/read anchor; not yet a rendering consumer |
| **+0xc**, word reads starting **0x13c2024**, bit extraction | Art-effect diagnostic flags | Shows record organization, not an ART algorithm or executable effect |

These are **two different structures**: the six-byte movie parameter group is not interchangeable with the CREATE_PARAM halfword mode field. No valid caller of 0x13c1f98 was found **within the inspected `[0x13bd000, 0x13c3000)` context only**; callers elsewhere are untested. That 24-KiB context helped establish boundaries, not a whole executable section. The lookup helper and small output/allocation-shaped routines were examined only as callees of H2; no third seed was introduced.

**H2 establishes diagnostic read/use and a candidate selector/lookup link, with gaps.** It does not establish a coherent COLOR selector → persistent profile record → live-view/JPEG/ISP consumer chain. Nothing here proves that the update package contains the owner's saved profiles.

## GR Custom Tool: method reused, implementation not transferred

Read [DoYitNow/gr-custom-tool at `549591db6ee7809fa7617c3637296ddc79b34f59`](https://github.com/DoYitNow/gr-custom-tool/tree/549591db6ee7809fa7617c3637296ddc79b34f59), not just its feature list. The reviewed source links native style identities to profile table columns, validates address-building instructions before resource reads, separates static defaults from unavailable camera UserData, and associates editable state with getter/setter and save/load/reset/snapshot routes. Matrix/gamma arithmetic and XMP fitting are **GR-specific, author-reported reconstructions**, not independent camera verification here.

Borrowed the **order of evidence**: identity → verified lookup/descriptor → typed field/consumer → persistence → color fit. We deliberately stopped before unsupported stride/record enumeration and color decoding. **No GR addresses, ARM instruction patterns, field layout, codec or source code were imported/executed.** Author source is **GPL-2.0-only**; this repository's new helper is original MIT code using existing external GNU tooling. The public README explicitly states incomplete independent end-to-end/device validation and that generated files do not prove installation/boot/function. Source/licensing details: [prior-art matrix](../docs/10-prior-art-matrix.md).

## Product-route decision

The desired product remains **at least two personally chosen, selectable film looks, repeatable import/export, live view and in-camera JPEG**. Stock documentation supplies part of this, not our completed product. No E-P7 image-quality fit or live camera comparison was performed.

| Route | Live view / final JPEG | Expression / quality | Import and switching | Modification / recovery | E-P7 evidence / decision |
| --- | --- | --- | --- | --- | --- |
| **A · Reuse COLOR1–4 / existing Picture Mode knobs** | Stock preview/shooting effect documented; imported-look equivalence untested | Twelve saturation controls, tone and shading documented; achievable fit/residual error unknown, no arbitrary LUT promise | Four-slot switching documented; manual recipes possible; automated import/export absent | Manual stock settings require no firmware change; an offline-found API remains unverified | **Best-supported conditional route.** Locate real slot fields/producer first; manual-only remains an incomplete product |
| **B · Extend/repurpose native records or richer controls** | Native consumer not identified | Matrices/gamma/richer ISP controls not located in E-P7 | More/named slots and persistence unproven | Firmware change likely; acceptance and independent recovery unknown | **Research only / blocked**; GR descriptors cannot substitute for E-P7 evidence |
| **C · Custom LUT/operator/runtime module** | No frame/ISP entry or verified shared preview/JPEG hook | Potential freedom is speculative | Loader/import/UI/storage all unknown | Code execution, deployment and failed-boot recovery unknown | **NO-GO engineering**, no basis for implementation |
| **D · Existing ART slot if easier** | Stock ART supported; custom effect unproven | ART editable representation unknown | No verified custom resource ingress | Modification/recovery unresolved | No easier chain shown; **do not prioritize names or JPEG assets** |

External RAW/phone processing would change the product's in-camera outcome and is not counted as a successful route. G1 remains passed; G0 offers qualified community methods rather than an E-P7 import implementation; **G2 is partial/not passed, G3 unmeasured, G4/G5 NO-GO, G6 not demonstrated for custom imported looks**.

## Stop and one next experiment

Recorded [native processing blocker](blockers/BLOCKER-e142-native-profile-consumer.md) after the two bounded hypotheses. No installation, patcher, recipe compiler or fitted look is justified by this result. Continued investment should be **one bounded offline data-flow experiment**, not firmware-modification engineering.

**Next minimum experiment: recover one verified caller/function-pointer use of CREATE_PARAM diagnostic entry #0 `0x13c1f98`, trace the provenance of its input object, then backward-slice the actual writes to its `+8/+9/+0xa` group/type/mode fields.** Limit to one caller and one producer/setter with the same guarded sample and mature decoder. Test whether that producer links a real selected parameter record to a non-formatting consumer; do not assume COLOR IDs. Success requires independently corroborated slot/field semantics plus a processing or persistence reference; a menu/debug-only producer is a falsifier and a stop. This is grounded in the verified halfword read **0x13c2003**, requires no paired older firmware or camera access, and avoids searching for new names. Resolve any unsupported instruction semantics before claiming a record stride.

Validation: **39 synthetic tests passed / 0 skipped**, including upstream LZO integration, seven new reference/guard/redaction counterexamples, and existing control-flow/mapping tests. Three actual-sample reference CLI runs verified guards and nominated literals without publishing OEM bytes/text; GNU entry walks and actual-VMA external-call check were separate private checks. Reproduction and full bounds: [T4 private procedure](../docs/14-native-profile-private-validation.md). Public artifacts contain only original tools/tests, selected numeric findings and short identifying labels, no firmware, proprietary file, raw assembly or secret.
