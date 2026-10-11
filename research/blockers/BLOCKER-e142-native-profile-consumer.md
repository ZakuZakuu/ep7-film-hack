# Blocker · COLOR/Picture Mode processing and persistence ownership

2026-10-11 · [Issue #18](https://github.com/ZakuZakuu/ep7-film-hack/issues/18), updated by [Issue #21](https://github.com/ZakuZakuu/ep7-film-hack/issues/21) · **OPEN, G2 incomplete**. E-P7 **owner-reported v1.1**, private original **111017984 bytes / SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**. T5 main baseline `034730639a30456637bee627d0366990c83b2f45`; T4 baseline retained in its report. All coordinates below are decoded #0 offsets or explicitly qualified static address candidates; no observed device memory.

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

## Next minimum experiment

Inspect **0x334780**, reached by observed receiver hand-off0x333c72, and at most one direct downstream receiver. Follow the context key **+0x2c2c** or demonstrably derived flags into a specifically corroborated processing consumer. If the function merely registers/queues an opaque object, record that boundary and stop. No broad offset/name scan, alternate-base guessing or assumed COLOR IDs. COLOR binding and persistence still need independent evidence even if processing ownership is found.

No new secret, user upload or hardware access is needed. A later device experiment requires its own scope/authorization; continued research does not authorize writes. **T5 has stopped at this evidence boundary.**
