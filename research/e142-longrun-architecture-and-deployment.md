# T17 · Adjusted object views, independent ART control roots and deployment audit

2026-10-13 (client date) · [Issue43](https://github.com/ZakuZakuu/ep7-film-hack/issues/43) · baseline main **e85a954d6b1ea10b7b5f1815cd40c160e8130600**, reviewed/merged PR42. **All three independent tracks completed. New adjusted-object/entry evidence and two code-bound ART-labelled control roots; no ART style-writer/renderer or safe installation breakthrough.** The validated A/B checkpoint was pushed before C; work continued without awaiting review.

E-P7 FW1.1 owner-reported. Original111017984 bytes/SHA2569d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb; decoded#0 SHA2565dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190. All firmware reads static/private; original/five OE residuals/decoded guards unchanged. Coordinates are decoded#0 offsets or explicitly stated static address values; no observed RAM, whole-object file inverse or new physical aliases.

## A · A subobject and two entries, not another imaging worker

1. Factory **a09a5b** supplies static containing-object base candidate **622f2ee0**, then helper **a09c1f** adds **1884**. Returned address **622f363c** is an interior object view, not the main object's base. Constructor a09a88 separately computes its base-initializer return+1884 before calling a080cf. The two paths converge only if that opaque initializer preserves base identity; this condition is not silently admitted. Using the main object's vptr for the adjusted return would misbind the candidate slots.
2. Factory's CALL at a09a75 saves D2/D3/A2/A3 with frame40; constructor RET at a09b6d restores the matching frame. Explicit local stack writes4/8/12/16/20 do not overlap saved slots24/28/32/36. Return helper adjusts only A0. This improves the T16 A2/A3 preservation condition across a09a5b and therefore the candidate proxy+8 store a154f8, **under normal nested returns, uncorrupted frames and nonaliasing object/stack writes**. It is not a complete ABI or arbitrary-callee proof.
3. Candidate subobject constructor stamps vptr **60b893b8**, whose consumed +176 slot points to **a150a4**. The still-opaque base return keeps exact runtime instance/vptr identity conditional. The target is the known resolver body **a150a9**, preceded by MOVM[A2],(SP) and ADD-4,SP. It is **one shared body with two entry contracts**, not a newly found processing worker.
4. Direct CALL a1556f targets the body with [A2],8; an indirect call through the full entry performs its own4-byte register save and4-byte local allocation. Manufacturer13250-040E printed p39 and [GNU2.44 BFD prologue handling](https://sourceware.org/git/?p=binutils-gdb.git;a=blob;f=bfd/elf-m10300.c;hb=binutils-2_44) support the distinction. GNU's prologue-transfer technique is a reuse precedent, **not identification of E-P7's compiler**.

Original `mn103_entry_pair.s` passes both entry styles under all three GNU simulator architecture selections; selecting the full entry for an already prepared CALL frame fails73 before returning. Only MOVM[A2],(SP) is newly admitted; OTHER/EX, other groups, restores, complete CFG/SSA and OEM simulation remain unadmitted. No GNU implementation source is copied into MIT tools.

**A stops after the two finite tests.** The new object adjustment/preservation/entry evidence is useful architecture progress. It does not identify an ART record, processor ownership or renderer. No parent/callback chain is recursively closed merely to claim a concrete runtime type.

## B · Two new independent ART-labelled roots

A typed audit of the existing1525-word name hierarchy selected **Shooting::setArtPanelFlag, ID0201e6** and **EditRaw::saveArtBktEdit, ID031b0c**. The latter also has an independent exact E-P7 manual anchor: pp137–138 document playback RAW ART BKT development into multiple JPEG copies. That is **post-capture development, not live preview or SOOC at exposure**.

One preregistered deterministic two-key reference operation was confined to **[74e534,7e2516)**, the T7 measured name-resolver call span. Eight raw identity-byte hits yielded four qualified immediate-D0/adjacent-CALL75068f fragments. An existing capture fragment is a positive control; incorrect destination, embedded data, changed target and intervening D0 overwrite are rejected by synthetic tests. This operation does not compute handlers from ordinals, scan all code or establish a GUI caller. Two exact name-record/consumer/backend relationships were then checked.

| Root / new code evidence | Verified relation | Limits / stop |
| --- | --- | --- |
| Panel fragment7dfb4d, resolver7dfb53, call7dfb8c→775af7 | Backend truncates D0 to u16, then74a276 writes low16 to static address **61fa729c**, within the admitted copied-initializer view | ART-labelled control-word write; no proven legal values, GUI effect, source+20 alias, saved look or renderer. Do not infer Boolean semantics from the name |
| RAW ART BKT fragment7cdfa2, resolver7cdfa8, call7cdfdc→7e91c6 | Workflow uses a7088 size-shaped call and constructor764ca0; selected constructor fields are generic actor/state initialization | No selected-filter parameter record, effect source+20 or actual pixel consumer. Allocation/buffer ownership and runtime arguments unobserved. Constructor check completes this root; no generic queue/callee recursion |

These are stronger than names alone: typed metadata, real resolver argument fragments and nominated direct code/field edges converge. They still do not establish native ART-gallery selection→style parameters→preview/JPEG, freely combined effects or a full filter registry. Both B roots stop at their explicit evidence boundaries; no repeat of301d16 caller/self-literal,4c2a84 seed,3954fd classifier,334780 downstream or name-resolver-as-handler.

## C · Independent deployment feasibility audit

**Fresh exact-input audit:** five OE blocks cover all111017984 bytes:111017664 payload bytes plus320 header/trailer bytes, with zero unparsed outer suffix and all additive residuals0. Fixed inversion/permutation is an observed reversible representation, not authenticated encryption by itself. The known nested SquashFS/LZO in block2 is compression, not an authentication primitive. These are existing decoder/FS facts interpreted within explicit security bounds, not new unpacking discoveries.

Full outer coverage does not interpret every header-field meaning or payload. The observed grammar has no separately unparsed appended authenticator. This **does not exclude** authentication inside payloads, trusted metadata, another component or immutable ROM. No device-side verifier/boot chain was identified; no signature/public-key scan or bypass experiment followed. Two original8-byte integer arrays, (100,200) and (150,150), both sum to300 with different SHA-256: a reproducible arithmetic counterexample, **not modified firmware or an update image**. Expected SHA identifies our research input, not the camera's acceptance policy.

| Independently reviewed source | Verified documentary/community fact | E-P7/security limit |
| --- | --- | --- |
| [Current official firmware listing](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/) | E-P7 latest1.1, dated2022-02-28 | Listing/download identity is not modified-package acceptance or recovery proof; binary version remains owner-reported |
| [Current official update instructions](https://explore.omsystem.com/c/en/firmware-update-instructions) | Mobile-update list names OM-1II/OM-1 FW1.1+/OM-5/E-M1III; earlier models use Workspace. Warns interruption can make camera inoperable and prior-version return is unsupported | General OEM workflow documentation, not E-P7-tested rollback or an independent loader. No steps/commands reproduced or executed |
| [Official application lifecycle notice](https://support.jp.omsystem.com/en/support/imsg/digicamera/info/update2024.html) | Old Workspace versions lose camera-update service after April2024; newer versions retain it | Explains host/service availability. This page is **not** an SD/recovery or signing specification |
| [2010 E-P1/E-P2/E-PL1 thread](https://www.dvxuser.com/threads/e-p1-e-p2-e-pl1-hack-research.217453/) | Authors describe old updater emulation; one E-P1 altered-text result is reported | **Author-reported** modified resource/package precedent, not arbitrary code execution or independent E-P7 recovery. Referenced leaked E-3 service files were not obtained/used |
| [2014-era Micro43Club discussion](https://micro43club.pro/forum/threads/modifikacija-proshivki-kamer-olympus.22086/) | E-M1/E-M10 custom-image/rollback claims; another participant reports an E-M1 result | **Community-reported**, historical/other models; no verified E-P7 trust chain or startup-failure recovery in the reviewed page. No attachments or firmware downloaded |
| [Historical loader site](https://lightsnowdev.com/Olympus/) | Current request returns410 | Cannot revalidate its implementation/support/license now. Past SD-loader reports cannot be promoted to current E-P7 recovery |

Additional reuse audit: [FromF/OlympusCameraKit7593857](https://github.com/FromF/OlympusCameraKit/tree/7593857ab68e74ebd669a0210b9f2d799d48fdb0) explicitly targets AIR A01. MIT sample-wrapper license does not license bundled Olympus SDK headers: they refer to a vendor EULA. Read-only API declarations expose dynamic property/value lists; no E-P7 native preset/bootloader bridge. No SDK binaries downloaded/run or headers copied. [libgphoto2 v2.5.34/a4ec9cc](https://github.com/gphoto/libgphoto2/tree/a4ec9cc8b799d3e620c89feeaeb3ec86f362a12f), LGPL2.1+, was inspected as source only: the reviewed model table lacks an explicit E-P7 entry, and related-model PTP controls provide no E-P7 image-authentication/recovery definition. This is not proof generic PTP cannot work; other-vendor firmware operations are not transferred.

Search quality limits are explicit: generic Bing RSS results did not distinguish four targeted questions; GitHub's tool-name query chiefly returned this repository, which was excluded as circular corroboration. No global absence claim follows. Primary documents and actual old-model reports carry the conclusions.

| Eventual capability | Offline verdict / independent evidence missing |
| --- | --- |
| Exact-sample container/FS reading | **GO for research**, already verified; not installation |
| Device-side authenticity and model/version acceptance | **UNKNOWN**; additive checksum/input SHA do not identify checker, signature or trust root |
| Ordinary official E-P7 upgrade | **Documented route**, not performed/tested here; does not imply third-party acceptance |
| E-P7 modified image or version rollback | **UNKNOWN technically / NO-GO for engineering**; ordinary rollback expressly unsupported, low-level acceptance unproved |
| Independent recovery after application/boot failure | **UNKNOWN / G5 NO-GO**; no exact-model independent recovery oracle. Old working-camera updates are insufficient |
| Complete per-device restoration/calibration preservation | **UNKNOWN**; no device snapshot/readback or complete flash/bootloader map. Server update bundle is not demonstrated to be a per-device backup |

No updater/device/service commands, package mutation/construction, signing bypass, original-code execution, camera operation or vendor contact occurred. Even a future lawful recovery precedent would still require separate owner approval; one owned camera is not an experimental rollback oracle.

## T16→T17 evidence and capability comparison

| Evidence/capability | T16 | T17 verified increment / remaining limit |
| --- | --- | --- |
| Proxy+8 source | Opaque factory, register-preservation condition | Adjusted static return+1884; matching frame/local-store contract. Opaque base identity/runtime type still conditional |
| Virtual vs direct entry | Resolver body only | Full MOVM/local-allocation entry and CALL-prepared shared body, tested positive/false-entry controls; no full compiler ABI |
| Independent ART-labelled roots | No new qualified selector/root | Two fresh typed-metadata/code bindings, one u16 control-cell writer and one post-capture workflow; **no style-record/renderer proof** |
| Deployment judgment | Historical broad blocker | Fresh official lifecycle/rollback warning, old-model counterprecedents and full-container/authentication distinction; G4/G5 stay NO-GO |
| Private corpus |36windows/2132rows/55relationships |48/2434/62,26 additional guards. **284 new unique sites;18 overlapping body sites excluded from novelty** |

64 synthetic tests/0 skips; prior negatives/15 stops/2 copy proofs retained. Original/five OE/decoded hashes unchanged. No whole-program decode/SSA or OEM simulation. Existing Cloud Setup is unchanged. [Selected evidence/source hashes](e142-t17-validation.json) · [Reproduction and handoff](../docs/23-t17-private-validation.md).

**Decision:** G0 has lawful tools and historical community methods, not E-P7 customization proof; G1 passes; G2 remains incomplete; G3/G6 untested; G4/G5 NO-GO. Stop the generic proxy and these two bounded control roots. Pause installation/UI/patch engineering. Neither stock ART rendering nor a named software control supplies independently saved custom styles, color grain, new gallery entries/icons or safe installation.

**Shortest meaningful next breakthrough condition:** an independent exact-E-P7 ART selection/parameter registration tying actual source+20 writes to legal filter/effect state and a real consumer. The external evidence needed for deployment is separate: lawful exact-model verifier/trust-boundary documentation plus recovery demonstrated independently of the overwritten application and per-device-state assumptions. Without either, further ordinary call chasing, guessed registries or sole-camera experiments are not justified. No old-version pair, owner setup/device action or vendor contact is required/requested now.

One integrated research PR, no automatic merge or next Issue. A/B were safely checkpointed and C continued independently; the committed report and private decision log/handoff preserve each hypothesis, falsifier, source and stop boundary. Actual research progressed across all three tracks rather than waiting/idle-padding to meet a duration claim.
