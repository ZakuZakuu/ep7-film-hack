# T17 · Adjusted object views, independent ART control roots and deployment audit

2026-10-13 (client date) · Issue43 · baseline main **e85a954d6b1ea10b7b5f1815cd40c160e8130600**, reviewed/merged PR42. **Checkpoint: A/B validated; independent Track C is still in progress. This is not a completed sprint or an ART customization breakthrough.**

E-P7 FW1.1 owner-reported. Original111017984 bytes/SHA2569d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb; decoded#0 SHA2565dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190. All firmware reads static/private; original/five OE residuals/decoded guards unchanged. Coordinates are decoded#0 offsets or explicitly stated static address values; no observed RAM, whole-object file inverse or new physical aliases.

## A · A subobject and two entries, not another imaging worker

1. Factory **a09a5b** supplies static whole-object address **622f2ee0**, then helper **a09c1f** adds **1884**. Returned address **622f363c** is an interior object view, not the main object's base. Constructor a09a88 independently computes whole+1884 before calling a080cf. Using the main object's vptr for this return would misbind the consumed slots.
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

In progress at this checkpoint. Current official update/listing pages are cached with source hashes. Official docs warn of inoperability after interruption and unsupported return to prior firmware. The historical lightsnowdev loader page currently returns410; availability is not recovery proof. No updater/device/service commands, modified package, signing bypass or original-code execution.

## Validation and resume point

63 synthetic tests/0 skips;48 windows/2434 rows/62 relationships/26 T17 guards, with prior evidence/15 stops/2 copy proofs retained. **284 new unique instruction sites;18 sites overlap the existing resolver body** and are not counted as new discovery. This is not whole-program coverage. [Selected evidence](e142-t17-validation.json).

Existing Cloud Setup unchanged. Rebuild with source /tmp/ep7-re-tools/env.sh and the existing guarded ep7_re_workbench command against the authorized private sample. Next resume step is **Track C official/documentary acceptance/recovery plus actual-container coverage audit**, then reconcile G0–G6, update this checkpoint to a final report, inspect CI and submit one integrated PR. A/B do not justify a firmware modification or camera experiment.
