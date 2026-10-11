# Blocker · COLOR/Picture Mode processing and persistence ownership

2026-10-11 · [Issue #18](https://github.com/ZakuZakuu/ep7-film-hack/issues/18) · **OPEN, G2 incomplete**. E-P7 **owner-reported v1.1**, private original **111017984 bytes / SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**. Current main baseline `20f313d638a08154ca604bc7cd267e5d7fbb97b1`. All coordinates below are decoded #0 offsets or explicitly qualified static address candidates; no observed device memory.

## Missing requirements and the two finite paths tested

Target: personally imported looks with on-camera switching, live preview and JPEG. Missing: COLOR slot IDs/layout, an actual processing consumer, persistence writer and verified import ingress. Stock UI saving is documented, not an identified NVRAM/flash/file format.

| Trace | Actual evidence | Result / counterevidence |
| --- | --- | --- |
| H1 native dial-name reference | Name start0xa50288 → word0x21fa08 under base0x60020020; bounded consecutive string-pointer run; zero exact base/selected-row address matches | Name data only. No selector accessor/profile record; other indexing/relocation not ruled out |
| H2 actual Picture Mode diagnostic references | GNU literal0x13be7c4 → anchor0x13f9f2a; call0x13be658 → selector helper0x2e9e99; six working-buffer reads+0x124…129. Separate CREATE_PARAM entry0x13c1f98 reads mode halfword at0x13c2003 | Real program/typed-field evidence, but movie diagnostics and CREATE_PARAM formatting are not preview/JPEG consumers. External call candidate0x47001052 not present in alias; helper `udfu01` semantics unresolved. Four helper cases cannot be called COLOR1–4 |

This is **insufficient evidence, not technical impossibility**. Full findings, byte locations and provenance: [T4 report](../e142-native-profile-chain.md); commands: [private reproduction](../../docs/14-native-profile-private-validation.md). Neither older comparison firmware nor a full emulator is a prerequisite. No blind extension to other blocks/bases/labels was attempted.

## Alternatives, risks and stop decision

- **A, stock COLOR1–4:** strongest official UI/save/preview foundation. Manual bounded recipes retain native shooting; automatic import, achievable color fit and personal-look equivalence remain unproven. Manual-only is not the requested complete import product.
- **B/D, richer native records or ART:** unknown controls/consumers; no modification implementation until E-P7 evidence appears.
- **C, new LUT/runtime:** no frame/ISP or safe entry; do not build it. External postprocessing loses the in-camera outcome and is not counted as success.

G4/G5 acceptance and independent failed-boot recovery blockers from [T2](BLOCKER-e142-art-install-feasibility.md) persist for every firmware-modification route, not just ART. Unknown call semantics/field widths could otherwise lead to corrupt-state assumptions; this task makes no patch, device call or import operation.

## One minimum experiment

Recover **one verified caller/function-pointer use of 0x13c1f98**, trace its input object backward to writes to **+8/+9/+0xa**, anchored by the existing Picture Mode halfword read **0x13c2003**. Bound to one caller and one producer/setter. Require corroborated native selection/record evidence and a processing or persistence use; reject a producer ending only in menu/debug serialization. No new strings/magic search, guessed field values, 980-byte stride assumption or camera communication. A negative result stops that iteration.

No new secret, user upload or hardware access is needed for this offline experiment. A later device experiment requires its own scope/authorization; neither this issue nor continued research authorizes writes. **This iteration has stopped at the evidence boundary.**
