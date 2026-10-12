# Blocker · COLOR/Picture Mode processing and persistence ownership

2026-10-12 · [Issue #18](https://github.com/ZakuZakuu/ep7-film-hack/issues/18), updated through [Issue #31](https://github.com/ZakuZakuu/ep7-film-hack/issues/31) · **OPEN for new binary/import/unlocking engineering, G2 incomplete; unguided traversal paused. Stock workflows assessed separately.** E-P7 **owner-reported v1.1**, private original **111017984 bytes / SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`** measured in prior tasks and reverified under T10's bounded authorization; not reread in T8/T9. T10 main baseline `c4caf740dbcb41743b5efb229588b078ab17de78`; historical baselines retained in their reports. All code coordinates are decoded #0 offsets or explicitly qualified static address candidates; no observed device memory. Earlier proposals are historical; the current decision is T10 at the end.

## Missing requirements and the two finite paths tested

Target: personally imported looks with on-camera switching, live preview and JPEG. Missing: COLOR slot IDs/layout, an actual processing consumer, persistence writer and verified import ingress. Stock UI saving is documented, not an identified NVRAM/flash/file format.

| Trace | Actual evidence | Result / counterevidence |
| --- | --- | --- |
| H1 native dial-name reference | Name start0xa50288 → word0x21fa08 under base0x60020020; bounded consecutive string-pointer run; zero exact base/selected-row address matches | Name data only. No selector accessor/profile record; other indexing/relocation not ruled out |
| H2 actual Picture Mode diagnostic references | GNU literal0x13be7c4 → anchor0x13f9f2a; call0x13be658 → selector helper0x2e9e99; six working-buffer reads+0x124…129. Separate CREATE_PARAM entry0x13c1f98 reads mode halfword at0x13c2003 | Real program/typed-field evidence, but movie diagnostics and CREATE_PARAM formatting are not preview/JPEG consumers. External call candidate0x47001052 not present in alias; helper `udfu01` semantics unresolved. Four helper cases cannot be called COLOR1–4 |

This is **insufficient evidence, not technical impossibility**. Full findings, byte locations and provenance: [T4 report](../e142-native-profile-chain.md); commands: [private reproduction](../../docs/14-native-profile-private-validation.md). Neither older comparison firmware nor a full emulator is a prerequisite. No blind extension to other blocks/bases/labels was attempted.

## T5 progress and remaining boundary

[T5 report](../e142-picturemode-producers-and-remote-controls.md) and [reproduction](../../docs/15-picturemode-and-schema-private-validation.md) supersede the earlier diagnostic-only boundary:

- **Verified:** actual caller0x2e50eb→CREATE_PARAM; producer0x301d16 copies source+16/+17/+18 to temporary+8/+9/+0xa, then passes the same object to non-formatting receiver0x3337cb via0x301e88.
- **Verified:** receiver packs the three fields into a 32-bit key at context+0x2c2c, selects a local key→code table and changes flags. One bounded C follow-up resolves16/16 and10/10 local table targets; no callee fan-out.
- **Still unknown:** original source writer/caller, actual COLOR slot IDs, persistent storage and real preview/JPEG/ISP consumer. Producer's PC-relative caller search is empty; its one literal-address match is self reference, not a registration. Hardware loops are manually inspected, not emulated by the reachability helper.
- **B alternative:** fixed OI.Share schema and pinned MIT clients describe named ART controls, with E-P7 allowed values/runtime enablement missing. No explicit native-profile import; official destination exclusions remain. Community constructors/getters have mode side effects, so they are not ready-made passive probes.

This justifies further **bounded offline consumer tracing**, not firmware engineering or a new import tool. G2 remains incomplete; G4/G5 unchanged.

## Alternatives, risks and stop decision

- **A, stock COLOR1–4:** strongest official UI/save/preview foundation. Manual bounded recipes retain native shooting; automatic import, achievable color fit and personal-look equivalence remain unproven. Manual-only is not the requested complete import product.
- **B/D, richer native records or ART:** unknown controls/consumers; no modification implementation until E-P7 evidence appears.
- **C, new LUT/runtime:** no frame/ISP or safe entry; do not build it. External postprocessing loses the in-camera outcome and is not counted as success.

G4/G5 acceptance and independent failed-boot recovery blockers from [T2](BLOCKER-e142-art-install-feasibility.md) persist for every firmware-modification route, not just ART. Unknown call semantics/field widths could otherwise lead to corrupt-state assumptions; this task makes no patch, device call or import operation.

## Previous minimum experiment (completed by T5)

Recover **one verified caller/function-pointer use of 0x13c1f98**, trace its input object backward to writes to **+8/+9/+0xa**, anchored by the existing Picture Mode halfword read **0x13c2003**. Bound to one caller and one producer/setter. Require corroborated native selection/record evidence and a processing or persistence use; reject a producer ending only in menu/debug serialization. No new strings/magic search, guessed field values, 980-byte stride assumption or camera communication. A negative result stops that iteration.

The caller and temporary-object writes are now recovered; the non-formatting consumer advances beyond that minimum but does not satisfy G2's rendering criterion.

## T5's next experiment (completed by T6)

Inspect **0x334780**, reached by observed receiver hand-off0x333c72, and at most one direct downstream receiver. Follow the context key **+0x2c2c** or demonstrably derived flags into a specifically corroborated processing consumer. If the function merely registers/queues an opaque object, record that boundary and stop. No broad offset/name scan, alternate-base guessing or assumed COLOR IDs. COLOR binding and persistence still need independent evidence even if processing ownership is found.

## T6 verdict and new direction

[T6 memo/reproduction](../e142-picturemode-handoff-verdict.md) verifies the actual hand-off, same context-relative group/flag locations and a complete23-instruction local CFG. The primary is an option/group/flag-gated dispatcher, with **no identified imaging request/consumer**. Its two callees lack independent rendering evidence; zero new downstream bodies were inspected. Prior0x3346e9 may change context contents, so earlier values are not presumed intact. This is an evidence boundary, not proof of firmware-level impossibility.

**Do not continue with another same-style callee issue.** Prefer a separately authorized, controlled stock COLOR expressivity pilot: private baseline repeats and one-step saturation/tone responses, declared target color space, then independent JPEG/scene comparison if warranted. No binary G2, automatic import, arbitrary LUT or fitting-quality claim follows from the stock UI; no test is executed here. If manual controls/workflow are already unacceptable, pause the project instead. Full single-page cost/value/evidence comparison is in the T6 memo.

Static investigation can resume for **materially new external/model-specific evidence**, such as an identified processor/color-driver operation or lawful version-specific difference with a concrete relevant anchor; an old paired image is optional, not a prerequisite. Existing upload and G4/G5 acceptance/recovery blockers remain. A later capture/device task requires separate scope/authorization. **T6 stopped; PR #24 is merged into T7's baseline.**

## T7 autonomous system-map result and current stop decision

[Report](../e142-system-boundary-map.md), [numeric index](../e142-system-boundary-map.json) and [private reproduction](../../docs/16-system-map-private-validation.md) retain four distinct finite experiments under the updated owner protocol:

- **Mapping gap reduced:** startup-backed initializer data view explains six-bank/74-group/1525-name lookup; real0x75068f returns a name, not a handler. Startup6-KiB helper relocation explains former external0x47001052 and0x4700115e as copy/fill code within #0. Wrong-map/data-decode controls distinguish code/data attribution from decodability. Physical/cache attributes remain unknown.
- **Independent capture lead:** name-linked one-shot wrapper0x7dcf56→0x77138b constructs request type1007 and reaches a constructor-path actor/executor interface. The route stops at0x80484a runtime virtual+20. No image fields, color parameters, driver/ISP ABI or consumer identified; virtual targets remain conditional on actual runtime objects.
- **Independent setting lead:** saveCustom0x7d9f4f→0x807330 maps generic custom indices0…3 to descriptor IDs53…56. Typed six-byte data hypothesis is bounded, `udfu01 6` traversal unassigned; no COLOR linkage, persistence medium/format or external ingress. Four settings are not COLOR1–4 proof.

The root blocker is **missing processing ownership and meaningful native color/ingress semantics**, despite readable code/data. It is not missing old firmware, complete inability to decode code, or proof a closed ISP makes the goal impossible. A remaining generic virtual edge cannot justify another automatic next-callee task.

**Pause additional firmware-static research now; pivot to an independent evidence source only.** Minimum restart experiment: validate an exact-model/processor-relevant public driver/BSP/interface (license/version/model first), or lawful specific image/color-processing change, then nominate one concrete frame/parameter/transfer operation and discriminate it against the storage/control boundaries here. A related camera name or TruePic brand alone fails that test. No new OEM image, device probe or automatic T8 is requested. If no such anchor is available, remain paused. Optional stock COLOR measurement is G3 only, not mandatory user work or automatic import. G2 remains incomplete; G4/G5 NO-GO.

## T8 public-source decision (2026-10-12)

[Issue #27 matrix and decision](../e142-public-interface-evidence.md), baseline main `d56642ff6eef1ea67a28e51e96db169cdcc1929b` (merged #26), independently tested three public-source routes. **No admitted E-P7 imaging interface.** The official model-linked notice documents a conditional corresponding-source offer, not a source package we possess. Related-model CPU/image-core claims, a generic MN103 development-board Kconfig and an Olympus imaging patent do not bind T7's control edges to a renderer. Identical extracted E-P7/E-M10 IV notice text and a wrong-assignee patent hit provide countercontrols. No additional OEM read or byte experiment was warranted.

**Current recommendation remains pause.** Highest-value input: a legally obtained E-P7 corresponding-source/interface package with model/version provenance, build/board configuration and concrete relevant driver definitions. Eligibility/availability/imaging coverage unknown; no vendor contact or purchase details were requested. A source release containing only stock kernel/network components fails the restart condition. Verify per-file licenses and two independent model/ABI invariants before one bounded offline crosscheck. No automatic T9, importer, camera probe or modification; optional stock COLOR testing is a separately authorized G3 alternative only.

## T9 product-workflow pivot (2026-10-12)

[Capability matrix/routes](../e142-native-style-workflows.md) and [private metadata validation](../../docs/17-native-style-metadata-validation.md) reuse exact-model documented processing across normal Picture Modes, K Custom, COLOR/MONO and eligible ART effects. **The owner does not require a particular LUT or engine.** Stock local-style saving and quick selectors are real partial workarounds; the absence of a binary consumer is a blocker to new engineering, not to evaluating those documented workflows.

Remaining product blockers: no verified atomic recall including WB/shift and other global controls; no documented E-P7 external settings/profile restore; no arbitrary ART operator compatibility/additional named bank evidence. MONO grain's lack of live preview is an explicit stock limitation. Metadata reads recover only a subset and can retain inactive fields; Workspace-processed official images failed original-capture controls. One credible public original E-P7 JPEG confirms selected-field observability, not full backup/import or nondefault profile/ART semantics. Quality relative to desired Ricoh/Fujifilm looks and owner usability remain untested.

**Pivot/continue R1 stock workflow research; keep R2/R3 and firmware-static engineering paused.** Minimum next experiment is a separately chosen A→B→A recall audit of two stored looks and WB/shift, optionally power-off and3/4RAW+JPEG captures; no elaborate calibration or camera action here. If global re-entry defeats the owner's workflow, stop R1 without implementing a faux preset UI. If a limited style set is useful, evaluate it honestly. RAW Data Edit's two development presets are an optional after-shot compromise; optical diffusion is a general untested lens-dependent alternative, neither solves full recall or unlocks grain. G2 incomplete/G4G5 NO-GO; no automatic device task.

## T10 selector/editor and recall boundary (2026-10-12)

[Issue #31 findings](../e142-cross-model-style-entrypoints.md) separate two E-P7 entrances, four-model semantic commonality and complete-state recall. The owner's normal selector/dedicated editor differences are first-hand reports, not binary bindings; WB/shift/tone are global in that observed workflow. Official profile-editor tone storage has an unresolved context difference. Myset/Custom is a real broader recall precedent on other exact models; menu similarity and generic saveCustom do not expose it on E-P7.

Two finite offline anchors, reusing known #0 state:

1. Producer0x301d16 and its existing diagnostic establish compact source+20→parameter+12 subfield conversion, independently associated with ten effect/control labels. This improves record organization evidence but does not prove UI writing, valid combinations, persistence or rendering.
2. Known SettingController text group and real name resolver still cannot bind changePicMode to executable UI code. Previously rejected immediate258 contexts remain false positives. No new candidate/whole-image scan, T6 downstream trace or third anchor.

**Root product blocker:** a daily selector alone recalls neither globals nor independently cloned ART configurations. E-P7 needs a verified whole-state recall/apply boundary and safe supported ingress, while firmware patching additionally needs installation/recovery. Missing old firmware is not a stop requirement, and a complete TruePic reverse engineering is not a prerequisite for evaluating stock UI. However, no independently grounded UI writer exists to extend this byte investigation.

**GO bounded A/B state research; PIVOT cross-model feasibility toward supported native banks; PAUSE E-P7 implementation and arbitrary composition.** Minimum useful next experiment is a separately authorized same-base B→A→B carryover audit (Pop Art I/Frame), controlling WB/shift/tone and recording effects/exposure behavior, optionally narrow private JPEG metadata. It discriminates editor-access-only differences from effect loss but cannot itself prove binary record sharing. For supported banks, check whether two versions of the same ART retain independent extras plus globals. Stop an ineffective route instead of another catalogue/automatic next-callee task. G2 incomplete/G3G6 untested/G4G5 NO-GO; no hardware operation this round.
