# T11 · ART grain gates and custom-item boundaries

2026-10-12 · [Issue #33](https://github.com/ZakuZakuu/ep7-film-hack/issues/33) · main **`a22deacf2ca74e788b64720612ee31b5f72d9be1`** (merged PR #32). E-P7, owner-reported **1.1**; private original **111017984 bytes / SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**; decoded OE #0 **26214336 bytes / SHA-256 `5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190`**. Original/five OE residuals/decoded hashes unchanged before/after; no download or device operation.

**Result: new control-level evidence, no accepted color-grain mode or renderer proved.** Three ART composite keys force MonoEnable; an independent halfword-Type gate clears FilmNoise and other effects while retaining MonoEnable. A conditional local path can preserve FilmNoise without forcing mono, but legality, output and preview remain unknown. The ART ecosystem remains the leading candidate for editable/savable film looks; custom items/names/assets and installation are blocked. Exactly two anchored static checks, no downstream call exploration or resource scan.

**Owner-confirmed workflow constraint:** dedicated ART-gallery Add Effects cannot be invoked through P/A/S/M→OK→Picture Mode ([Issue33](https://github.com/ZakuZakuu/ep7-film-hack/issues/33)). This supersedes T10's proposed cross-entry audit. It is confirmed user-facing behavior, not proof of isolated firmware state or separate renderers. Do not propose that audit again.

## New byte-grounded relationships

Coordinates below are **decoded #0 offsets**, not raw BIN offsets or observed RAM. Reused GNU binutils2.44, existing OE/window helpers and validated main view `0x60020020+offset`. [T10's bit associations](e142-cross-model-style-entrypoints.md) are prerequisites, **not new findings**. Both checks use the already validated receiver `[0x3337cb,0x333c97)`; the existing diagnostic verifies names/widths only. No body of0x334780,0x3954fd or another callee was inspected.

| Check / independent anchor | Verified relationship | Limits |
| --- | --- | --- |
| **1: composite-key normalization**; T5's directly referenced table `[0x501a34,0x501ab4)` | Keys **0x01010068,0x01020068,0x0102006d** point to0x333a6a; **0x333a6b** ORs **0x800000**, then0x333af4 stores to **context+16 = copied parameter+12**. Thus these cases force the T10-associated **MonoEnable bit23**, irrespective of incoming FilmNoise | No exact stock filter/variant names assigned to these keys. The table's ART special-case region contains no OR setting FilmNoise bit14; absence is local. No processing operator, UI setter or persistence proved |
| **2: Type-dependent suppression**; retained parameter+16 pointer at0x333952/56 and independently diagnosed u16 `Type` at0x13c20ec/ef | **0x333af5…0x333b6b** rereads this halfword. If `(T&0xf0)==0x40` **or** `(T&0xf00)==0x100`, six AND/stores clear **0x1443c0**, including FilmNoise at **0x333b24/2a**. The0x40 condition additionally clears **0x62bc00**. Neither mask clears MonoEnable | This halfword **Type+16 differs from PictureType byte+9**. Its semantic values and earlier-callee mutations are unknown; do not call it a color/RAW/JPEG/ISP format. The gate changes flags, not pixels |

The first mask clears diagnostic-associated StarLight, SoftFocus, Diorama and FilmNoise, plus two unassigned fields. The extra mask clears PinHole, BandShading, WhiteEdge and Frame, plus unassigned fields. Label associations do not establish operator compatibility or GUI labels; `FilmNoise` remains unproven as the MONO Film Grain control.

**Conditional local non-mono path:** existing key **0x01010065** directly matches its first hash probe and reaches0x333a03/04, ORing SoftFocus0x80, not MonoEnable. If the flag word **on entry to this local region** has FilmNoise=1/MonoEnable=0 and current Type matches neither suppression condition, the inspected key-and-Type normalization leaves those two bits unchanged. This is a real-instruction conditional relation, not merely T10's independent bit representation. It does **not** prove a valid UI-produced state, completed constructor execution, accepted color mode, grain generation or preview/JPEG. Opaque calls before/after this region and the actual processing consumer remain unresolved. An integer fixture is not a camera mode.

**H2 discriminator from check1:** the sparse table is a **special-case normalizer, not an established full ART registry**. Its empty-key miss at0x3339ed and comparison-bypass branches at0x3339bf/ca go to the shared0x333af5 gate, without locally rejecting a filter. Fourteen nonzero entries/two zero entries are not fourteen filters/two free user slots. Adding a table entry alone cannot register a menu item, renderer or saved preset. The fixed low-nibble hash/16-slot extent are existing T5 facts, not a newly discovered expansion interface.

## Product paths and precise missing mechanisms

| Candidate | Owner value / current evidence | Missing E-P7 evidence / judgment |
| --- | --- | --- |
| **Edit stock ART through its existing gallery** | Current low-invasive baseline: eligible variants/degree/extras; stock color looks such as Vintage/Cross Process/Instant Film are documented. Original entries remain unchanged | Manual stock configuration only, not a named user library/import or independently saved clones. Exact extras are filter-gated. **Continue as ART baseline**, no fake preset store |
| **In-place modified stock ART** | Hypothetically smaller than adding a selector entry because it could reuse existing identity/editor routing | Need actual parameter writer/record, normalization and render consumption, persistence and update/recovery. The new key-forced MonoEnable/Type masks show why changing one input bit may be insufficient. Alters stock behavior; **no implementation or sole-camera installation** |
| **Append one custom ART entry/variant, preserve stock** | Preferred future product: independent saved film look, custom name, original icon/preview | Need selector IDs/list registration and bounds, editor/allowed combinations, independent saved records including global style controls, native preview/JPEG consumer, then UI resource binding and G4/G5. No such registration interface found. **Conditional research, implementation blocked** |
| **Color grain / extra combinations** | Local normalization does not unconditionally enforce FilmNoise⇒MonoEnable; specific key and Type rules are now identified | Missing legal source-state/UI writer, effect eligibility and downstream noise/mono consumers. **Unknown**, not proven feasible or impossible; synthetic preservation is not image evidence |

The [exact E-P7 manual](https://my.omsystem.com/consumer/manuals/cameras/E-P7_MANUAL_EN.pdf) pp70–73 documents filter-dependent ART extras and B&W Grainy Film; pp107/146 identify MONO-grain and preview/exposure exceptions. Existing ART stock output does not establish new combinations. No generic Custom-bank/COLOR fallback replaces the owner's ART priority. Cross-model transfer is a future interaction/data-semantics question; these offsets, masks and keys are **E-P7-only evidence**.

## Names, icons and thumbnails: separate blocked UI gate

| UI category | Evidence retained / missing anchor |
| --- | --- |
| **Text label** | Official ART names and prior language/name observations are available; no ART-item ID→language record→gallery consumer mapping. A diagnostic label or method-name lookup is not the gallery label table |
| **Small icon** | No independently linked icon ID/asset pointer, codec/index/count or registration consumer. T1.2's two640×480 JPEGs are not identified small icons |
| **Gallery preview thumbnail** | No item→thumbnail relation or render callback. Preview may be an asset or dynamically rendered; neither interpretation is proved. Do not equate a JPEG signature with the gallery preview |

[T1.2](e142-resource-mapping.md) identified only two decodable assets and no ART linkage; its [index blocker](blockers/BLOCKER-e142-resource-index.md) remains. No independently grounded resource format/index arrived in this task, so **zero new resource-byte checks**, no guessed strides/base scans, replacements or preview mockups. Original custom artwork is a future requirement after a real binding, not a solution to the index gap.

## Next falsifiable hypothesis and stop

**One grounded next code question:** caller **0x333958/5d** loads parameter+30 and the parameter+16 Type halfword, then supplies them to the known call **0x33395f→0x3954fd**. Its returned value is stored as a class byte and dispatched through T5's bounded0…9 table; the callee's actual read/return semantics remain unknown. Hypothesis: a bounded classification analysis can identify distinctions relevant to the newly located suppression conditions. Confirm exact read/return logic and compare it with the gates; stop if it adds no meaningful Type semantics. **Proposed separately scoped check only**, not executed, not called a grain renderer or an excuse to resume0x334780 traversal. A useful classification result would still leave the legal UI/persistent writer and actual FilmNoise/MonoEnable consumers missing.

**Stop this round:** two code checks completed, no third anchor. New gate facts warrant this concentrated PR; they warrant neither a color-grain feature nor a cosmetic menu prototype. Keep ART as the lead, seek this discriminating Type/state evidence before expanding research. G2 incomplete, G3/G6 not camera-validated, G4/G5 NO-GO. Safe modified-firmware acceptance/recovery remains independent of editable records or assets. [Exact reproduction](../docs/19-art-gates-private-validation.md); all original bytes/transcripts remain private. Await GPT review, no merge.
