# T5 · PictureMode producer and keyed consumer; native import still unproved

2026-10-11 · [Issue #21](https://github.com/ZakuZakuu/ep7-film-hack/issues/21) · main baseline **`034730639a30456637bee627d0366990c83b2f45`**, including merged PR #20. **E-P7, owner-reported firmware 1.1**. Private original: **111017984 bytes**, SHA-256 **`9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**; decoded OE #0: **26214336 bytes**, SHA-256 **`5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190`**. Size/full hashes and all five OE residuals reverified; original input unchanged. No download, serial use, camera connection, firmware execution, alteration or repacking.

**New result: a real caller and field producer feed the previously identified PictureMode diagnostic, and the same parameter object has a non-formatting consumer.** That consumer packs group/type/mode into a key, uses an independently bounded code-pointer table, and changes context flags. This improves T4's diagnostic-only evidence. It still does **not** connect native COLOR1–4 selection or persistent settings to actual live-view/JPEG processing. The offline OI.Share check identifies named remote-property interfaces, not a demonstrated custom-profile import path. Continue bounded program research; **G2 remains incomplete, G4/G5 remain NO-GO**. No product or firmware feature is implemented.

## Scope, reuse and evidence classes

Reused the guarded OE decoder, tested static alias **`A = 0x60020020 + decoded_offset`**, existing original reference/window helpers and **GNU binutils 2.44 MN103 disassembler**. [T3 tool provenance](../docs/13-executable-private-validation.md) applies: official Ghidra lacks this language; no unverified module or new ISA decoder. GNU architecture facts were read from [opcode definitions](https://sourceware.org/git/?p=binutils-gdb.git;a=blob;f=opcodes/m10300-opc.c;hb=binutils-2_44) and [PC-relative operand handling](https://sourceware.org/git/?p=binutils-gdb.git;a=blob;f=opcodes/m10300-dis.c;hb=binutils-2_44). External GPL tooling/source remains external; documentation snippets are original.

Issue #21's budget was used as follows:

- **A:** one exact-target PC-relative representation hypothesis, corroborated by GNU and entry-derived windows. Follow the one CREATE_PARAM caller through its forwarding wrapper to **one field producer**. A second source inquiry at that producer's entry found no direct PC-relative caller and only a self-address literal; no speculative dispatch-table search followed.
- **C, once:** the producer's independently observed non-formatting call justified one local investigation of its receiver and two explicitly referenced tables. No nested callee exploration or additional C experiment.
- **B:** because COLOR identity, upstream field origin and rendering ownership remain blocked, parse the already validated fixed `oishare` slice and compare pinned licensed community implementations and official destinations. No new resource/strings/JPEG/magic discovery or other-block reopening.

**Verified** below means byte-grounded static instructions, field accesses, arithmetic, literal mapping or XML structure, not execution on hardware. **Strong inference / hypothesized** covers diagnostic/context-construction roles. **Community-reported** covers other camera responses. **Unknown** covers E-P7 runtime enablement, UI identities, persistence and rendering. All program coordinates below are **decoded #0 payload offsets**. They are not raw `.BIN` offsets or observed runtime addresses; adding the raw OE payload start does not undo its intra-lane permutation.

## A · Real caller and field provenance

### Targeted call representation

GNU's four direct PC-relative forms use signed little-endian displacement from **instruction start**: `call16` (`cd`, 5 bytes total), `call32` (`dd`, 7), `calls16` (`fa ff`, 4) and `calls32` (`fc ff`, 6). The original prefilter tests only those forms against a supplied callee. Four original forward/backward synthetic fixtures first verified the arithmetic with GNU. Prefix matches inside data remain possible: a match is a candidate until its selected function window corroborates the boundary.

For callee **0x13c1f98**, the exact-target pass found one candidate, **0x2e50eb → 0x13c1f98**, confirmed as `call32` in the entry-derived dispatcher decode. The independent exact absolute u32 representation **0x613e1fb8** has zero matches in #0. This explains why the previous nearby 24-KiB inspection found no caller; it does not rule out indirect/relocated/cross-component callers.

| Link | Verified coordinates and field flow | Role / limitation |
| --- | --- | --- |
| Diagnostic dispatcher **0x2e4e75** | Incoming a0 preserved as a3 at entry. At **0x2e50d3**, event low byte is compared with **15**; flag checks precede **0x2e50ea**, which restores the same object to a0; **0x2e50eb** calls CREATE_PARAM | Conditional diagnostic dispatch is a **strong inference** supported by the known formatting callee and flags. It does not produce the three fields |
| Forwarding wrapper **`[0x2e4e58,0x2e4e75)`** | **0x2e4e6d → 0x2e4e75**, preserving the pointer; candidate flags 0xa272e4a8/0xa272e4c4 can bypass the diagnostic | No object-field writes; addresses are candidates under the static model, not read RAM |
| Field producer **`[0x301d16,0x301ef3)`** | Saves incoming source a0 at stack+28, constructs a **32-byte temporary object at stack+40**. Incoming d0 selector **10** selects event15 at **0x301e74**; other selector values use event2. **0x301e7b → 0x2e4e58** supplies that temporary object | **Verified producer/call relationship**; source pointer's caller, original values and selector10's UI meaning unknown |
| Same producer's non-formatting call | **0x301e87** supplies the same temporary object in a0; **0x301e88 → 0x3337cb** also receives the source's first word and a halfword-status pointer. Return value is stored at **source+4** at **0x301e91** | Establishes a use beyond diagnostic serialization. Does not prove a UI setter, persistent record or imaging algorithm |

The wrapper had **41 raw exact-target call candidates**. Only fixed 36-byte preceding / 9-byte following contexts were used for argument triage; the nominated selector10/event15 producer was then re-decoded from its entry. These candidates are **not 41 validated function identities** and unrelated callers were not traced.

| Destination in temporary CREATE_PARAM | Original source-object location | Read / write instructions | Confidence |
| --- | --- | --- | --- |
| group byte **+8** | byte **+0x10 (16)** | **0x301d5e / 0x301d66** | verified pointer arithmetic and typed copy |
| type byte **+9** | byte **+0x11 (17)** | **0x301d68 / 0x301d6c** | verified |
| mode unsigned halfword **+0xa** | unsigned halfword **+0x12 (18)** | **0x301d6f / 0x301d72** | verified; same layout read at T4's 0x13c2003 |
| flags word **+0xc** | selected bits of source word **+0x14 (20)**, combined with a template | bit operations **0x301d7b…0x301e30**, final store **0x301e32** | verified packing; individual effect meanings unknown |

No direct PC-relative caller of **0x301d16** was found using this representation. Exact literal **0x60321d36** occurs once at **0x301ec9**, inside the producer's own immediate instruction **0x301ec7**, supplied to an error/status-shaped call. **This is a self-address literal, not an independent caller/dispatch registration.** Address-taken/indexed/other-component entry paths remain unknown. This is the source-provenance stop; no persistent setter was recovered.

## C · New non-formatting receiver and real keyed dispatch

The grounded follow-up is receiver **`[0x3337cb,0x333c97)`**, reached by the producer's direct call. It retains the input pointer, requests **15488 / 0x3c80** from **0x26e0**, checks for null, and uses the result as a context base. Allocation/context-constructor semantics are a **strong inference**; the allocator and external initialization callee were not resolved. Null/error paths set halfword statuses; the success path returns the context at **0x333c92**, followed by return **0x333c94**.

An eight-word copy loop at **0x3338fb…0x333901** transfers the 32-byte temporary parameter object to **context+4**. Manual register/counter analysis supports that loop; the existing reachability helper intentionally stops at `setlb` and is **not** an emulator or proof of full function reachability.

| Local consumer evidence | Verified relation | What it does not prove |
| --- | --- | --- |
| **0x333909 / 0x33390b / 0x33390e** | Read copied group byte, type byte, mode halfword, respectively. Arithmetic **0x333915…0x33391d** forms **`K = (group << 24) \| (type << 16) \| mode`**; **0x33391f** stores K at **context+11308 / +0x2c2c** | Internal numbers are not identified COLOR slot IDs, EXIF IDs or public protocol values |
| **0x333998…0x33399e** | Group1 enters the keyed path; other groups enter a separate path at **0x333b8a**. T4 independently associates group1 with diagnostic label **Art** | ART-associated **flag configuration**, not a complete ART operator implementation |
| Literal at **0x3339dc**, table **`[0x501a34,0x501ab4)`** | Exactly **16 eight-byte slots**, **14 nonzero relative keys and two zero/default slots**. Search uses K−0x01010064, low-nibble initial slot and bounded +8/wrap probing. On match, record+4 is loaded at **0x3339fe** and used by indirect jump **0x333a01** | This is a dispatch table of special cases; **16 slots do not mean 16 filters**, and zero keys are not filter IDs |
| All sixteen mapped table targets | Under base0x60020020, **16/16** destinations are instruction boundaries **inside this receiver**. Examples: full key **0x01010065 → 0x333a03**, **0x01020069 → 0x333a27**, **0x0102007b → 0x333ac7** | Code targets, not LUT/profile-coefficient addresses. No stock filter name was assigned to those keys |
| Selected branches | **0x333a03…0x333af4** alter the copied parameter flags at context+16 (input+0xc); e.g. key0x01010065 reaches a bit0x80 OR, then a common store | Confirms field-dependent non-formatting behavior. Color transform, ISP/DSP command semantics and effect quality remain unknown |
| Non-group1 path | Full K is compared to **12/9/11** at **0x333b8d…0x333b97** and affects context flags | Native numeric special cases, **not** proven COLOR1–4 or named Picture Modes |
| Direct hand-offs | Context supplied at **0x333c50 → 0x3346e9**, then on success **0x333c72 → 0x334780** with the saved additional argument | Callee roles and eventual preview/JPEG consumption **unknown**; neither function body was investigated in this task |

A second, explicitly referenced **10-word code-pointer table `[0x501ab4,0x501adc)`**, selected by a bounded 0…9 return value of 0x3954fd, maps **10/10** to the two in-function boundaries **0x33398e / 0x333983**. It sets a one-byte context flag used by later cases; the classifier's argument semantics remain unknown. Resolving these two local tables completes the one C follow-up; no table enumeration elsewhere.

This is genuine program-level data-use evidence beyond T4, but the result is best classified as **parameter/context configuration preceding unresolved hand-offs**. There is no observed frame buffer, identified color coefficient array, shared preview/JPEG routine, COLOR slot binding or persistent write. Short directly referenced log labels were checked only to avoid misnaming the component; their acronym is not used to infer imaging ownership. External initialization candidate **0x4700115e** is outside this alias and is not called `memset` or boot ROM merely because of arguments.

## B · Offline native-control inquiry

Revalidated fixed **#0 `[0xec5a28,0xec5a28+8011)`**, SHA-256 **`132cd8eda1c71a26089eb078b70c3b3c44b5745e39cb7f687af9b87b478fc529`**. Standard-library XML parsing succeeds: root `oishare`, version **4.50**, OITrack **3.10**. These are interface versions, **not camera firmware versions**. The slice contains command/property names but **no `<enum>` or `<value>` nodes** establishing E-P7 allowed values or responses.

| Question | Verified fixed-schema facts / community context | Decision and uncertainty |
| --- | --- | --- |
| Can a query expose active native COLOR/Picture Mode identity? | `get_camprop`, HTTP GET: `com=desc` has **33** named properties (includes `desclist`); `com=get` **31**; `com=check` has a property-name node without enumerated children. No explicit COLOR slot/profile/PictureMode property in these lists | ART-related current-value queries are **described**, not run. Neither `takemode` (shooting mode) nor `artfilter` is proved to identify COLOR1–4; empty `check` children are not proof of universal access |
| Does setting select stock ART options or import a look? | `set_camprop`, HTTP POST, `com=set`: **23** named properties, including `artfilter `, `colorphase` and twelve `ArtEffectType…` labels, including BleachBypass. No explicit profile blob, coefficient table, twelve-color editing set or LUT upload is described | Existing ART selection/sub-effect control is a **strong community-backed inference**. Exact E-P7 values, ranges, availability and persistence are **unknown**. Arbitrary preset creation/import is unsupported by this evidence |
| Does `colorphase` mean COLOR profiles? | Listed separately as a named property; no field/range/slot mapping here | **No demonstrated link** to the native twelve-color controls or COLOR slots. Partial-color association is a working interface interpretation, not a typed mapping proved by this schema; it cannot support a profile-import claim |
| Can an existing supported Profile Library workflow be reused? | [Official FAQ007489](https://digital-faq.jp.omsystem.com/faq/public/app/servlet/qadoc?QID=007489), updated2026-09-25: E-P7/PEN-F are not Profile Library write destinations, although their JPEGs can be sources. [FAQ007407](https://digital-faq.jp.omsystem.com/faq/public/app/servlet/qadoc?QID=007407), updated2025-10-07: Workspace Profile Load destinations OM-3/PEN-F3.0+ | **Verified official exclusion** of these functions for E-P7. Source compatibility and ordinary settings backup are not destination/import capability; does not rule out every unknown protocol |

Trailing space in raw **`artfilter `** is preserved in our schema finding. The Python community parser trims property names; no E-P7 request was used to decide actual wire spelling. There is **no established mapping** between OI.Share property values and the receiver's internal composite keys.

### Community implementation and license audit

- **[joergmlpts/olympus-wifi at 364dfcd1d8b12ead9d27dd9837463976e2a068fe](https://github.com/joergmlpts/olympus-wifi/tree/364dfcd1d8b12ead9d27dd9837463976e2a068fe)**, [MIT license](https://github.com/joergmlpts/olympus-wifi/blob/364dfcd1d8b12ead9d27dd9837463976e2a068fe/LICENSE). Re-read `camera.py` constructor, command parser, `get_camprop`, `set_camprop`, request and action-mode helpers; [API](https://olympus-wifi.readthedocs.io/en/stable/api.html) and [usage](https://olympus-wifi.readthedocs.io/en/stable/usage.html). It obtains `desclist`, accepts `getset` properties with dynamic enum values, and sends a single XML `<value>` for a named property. Examples are **TG-5 / interface3.10**, not independently verified E-P7 responses. Crucially **constructor switches rec then play; even the get_camprop helper can switch mode and restart live view**. Neither constructor nor client method was invoked. This is a protocol/side-effect precedent, not a passive read-only probe or importer.
- **[hotchpotch/olympus-camera at 47d2341785ddfde8da6d363c57924d3fe094667e](https://github.com/hotchpotch/olympus-camera/tree/47d2341785ddfde8da6d363c57924d3fe094667e)**, [MIT license](https://github.com/hotchpotch/olympus-camera/blob/47d2341785ddfde8da6d363c57924d3fe094667e/LICENSE.txt). Reviewed README, `lib/olympus-camera.rb`, parser, generated PEN-F/E-M1II docs and PEN-F command-list fixture (interface2.60). It generates methods from command descriptions; documented property lists differ by model. The generic POST path uses form data, unlike the Python single-value XML path: **do not infer a working E-P7 setter from generated method names alone**. No E-P7 fixture, profile importer or E-P7 device validation in the reviewed material; Ruby client not run.

No community source was copied into the repository or substituted for OEM implementation. A Python-client import check lacked its `requests` dependency; no constructor or transport ran. Installing it was unnecessary: fixed-schema analysis used ElementTree, and protocol behavior was reviewed from pinned source. Public GitHub/docs requests are the only network activity relevant to B.

**B stops:** the specific route evidenced here is remote control of named stock settings, with runtime values still missing; it does not supply an E-P7 custom-profile ingress. No protocol client, bridge, setter tool or guessed request payload was developed.

## Gate decision and next experiment

| Requirement | Evidence now | Still missing |
| --- | --- | --- |
| PictureMode field production and non-formatting use | **Verified static** source+16/+17/+18 → temporary+8/+9/+0xa → composite key and branch/flag use | Meaning of upstream source object, actual selected values and COLOR slot binding |
| COLOR1–4 → stored record → rendering | Stock UI capability documented; more useful code anchor found | **Not verified**: native slot selector, persistent writer/format and actual preview/JPEG consumer |
| Non-flash custom-look import | Described ART properties; community named-setting methods | E-P7 runtime capability/value responses and an actual editable-profile ingress; known official import destinations exclude E-P7 |
| Installation, recovery, fitted look quality | No new acceptance/recovery/color-fit evidence | **G4/G5 NO-GO**, G3 unmeasured, custom-look G6 unproved |

Updated [processing/persistence blocker](blockers/BLOCKER-e142-native-profile-consumer.md). The failure is incomplete evidence, not proof of technical impossibility. Manual COLOR recipes remain a documented partial alternative; they do not satisfy automated import/export. External postprocessing changes the product outcome and is not counted as in-camera success. Investment in **one more bounded offline consumer experiment is justified** by the new parameter-to-context chain; investment in firmware-modification engineering is not.

**Most valuable next experiment:** inspect just **0x334780**, the observed success-path hand-off at **0x333c72**, and at most one direct downstream receiver. Trace the context and the composite key at **+0x2c2c** (or demonstrably derived flags) into a specific processing request/consumer. Success requires real field use with corroborated imaging ownership, not an acronym or function-shaped decode. If it only registers/queues an opaque object, record that boundary and stop; no alternate base, broad field-offset search or generic resource scan. COLOR slot/persistence attribution remains a separate necessary proof even if this consumer is found. This task does not execute that proposed next experiment.

A lower-priority, separately authorized **device** experiment could obtain only the actual command list and `get_camprop` descriptions/current values with mode side effects explicitly reviewed. It could falsify runtime ART-query assumptions or reveal different properties, but the offline schema currently gives no reason to promise COLOR import. It is **not authorized or performed here**, and the community constructor/getter is not a safe ready-made read-only procedure.

## Validation and publication boundary

[Private reproduction](../docs/15-picturemode-and-schema-private-validation.md) includes the exact-target method, bounds, synthetic GNU controls and XML summary. **39 existing synthetic unit tests / 0 skipped passed**, including real upstream LZO-tool synthetic extraction. Four GNU forward/backward call fixtures passed before OEM matching; final reproduction additionally checks embedded-data candidates and incorrect PC-after interpretation. Numeric table targets independently verified against entry-derived instruction boundaries. Full original/OE/decoded hashes unchanged after analysis; document links/diff and publication allowlist checked. CI uses synthetic inputs only. Only original research prose/reproduction snippets and selected numeric metadata are committed; no OEM bytes, full XML, proprietary assembly, binary fixture, camera identity or secret.
