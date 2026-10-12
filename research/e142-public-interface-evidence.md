# T8 · Public imaging-interface evidence and source availability

2026-10-12 · [Issue #27](https://github.com/ZakuZakuu/ep7-film-hack/issues/27) · latest main **`d56642ff6eef1ea67a28e51e96db169cdcc1929b`**, including merged PR #26.

**Actionable E-P7 frame/color/ISP interface found: NO. Recommendation: keep firmware-static research and modification engineering paused.** Three different public-source routes establish a model-linked source-code offer, a related-model CPU/processing distinction and an Olympus patent's functional imaging stages. None supplies an E-P7-specific chip/driver binding, frame-transfer ABI, color record or import mechanism. These are provenance/architecture constraints, not proof custom looks are impossible. G2 remains incomplete, G3 unmeasured, G4/G5 NO-GO; import → selection → live preview → SOOC JPEG remains unproved.

This is **public-source research only**: no OEM download/read/decode, MN103 function traversal, camera session, vendor contact or access to personal accounts/identifiers. Prior E-P7 results are reused as documented findings, not remeasured in T8: owner-reported1.1, original111017984bytes / SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`; [T7 scoped mappings/control boundary](e142-system-boundary-map.md), [T1.1 selected ARM/Linux ELF metadata](e142-squashfs-validation.md). No fresh OEM hash or runtime claim is implied.

## Admission rule and three finite routes

An interface candidate needed **both** documented E-P7/processor/version provenance and concrete image-frame/color/transport definitions. An eventual crosswalk would require two independent invariants, such as a model-specific build/driver identity plus matching ABI field widths/command structure or a known driver implementation. A brand, compatible ISA, name, core count, license list or ordinary network frame is insufficient. Issue #27 permits one chosen byte-grounded check **only after** that condition; none qualified, so the check was not used.

| Route | Source-grounded question / bounded work | Result and reason to stop |
| --- | --- | --- |
| **A · Model-linked OSS availability** | Read official index and five linked notices; check limited public repository/code searches for a corresponding E-P7 kernel/source mirror | E-P7-specific notice association and source offer verified. Actual model/version source bundle, build configuration and image ABI not obtained. Generic component links and unrelated repositories do not close that gap |
| **B · Processor and subsystem ownership** | Read two Olympus E-M1 II announcements and the single pinned upstream MN103 Kconfig plus license | Official related-model CPU/image-core distinction verified. Generic development-board/processor support verified. No E-P7 chip identity or imaging-driver interface; do not transfer register/default-address/core assumptions |
| **C · Original imaging disclosure** | Inspect one Olympus image-editing patent's actual description and one search-result assignee countercontrol | Patent describes real imaging concepts but has no E-P7/TruePic/driver binding. An apparently Olympus color-conversion hit belongs to Fujifilm; citation-list matching rejected. Neither justifies binary matching |

These are three source-specific leads, not three new executable milestones. No further broad source search, whole kernel download, speculative processor selection or next-callee issue follows the negative admission result.

## Public-source provenance matrix

All links were retrieved2026-10-12. Notices/HTML have no source-code revision; their content hashes below identify the reviewed snapshot. Model association of E-P7 PDFs comes from the **official index**, not a model/version manifest inside the PDF. Copyright/publication is distinct from implementation/reuse permission.

| Source / exact relevance | Version / model / ISA or ownership | Accessible content and license | Interface admission |
| --- | --- | --- | --- |
| [OM software index](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/notice/notice.html) | Current index explicitly links E-P7 Linux and Expat notices; no firmware revision/ISA | Public HTML, OM Digital Solutions copyright; links to notices, not an E-P7 BSP checkout | **verified model association**, no ABI |
| [E-P7 Linux notice](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/notice/pdf/Software_Notice_ep7_linux.pdf), p1 and component headings |79pages,15named third-party components; no kernel release, chip identifier or E-P7 firmware-version manifest | Notice/license text and conditional source offer; Linux/bcmdhd GPLv2, libc LGPLv2.1 and other components have their own terms. Actual corresponding-source bundle not downloaded/obtained | **verified offer/components**, no image-driver definitions |
| [E-P7 Expat notice](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/notice/pdf/Software_Notice_ep7_expat.pdf) |1page; index says Expat1.95.5; ISA unspecified | XML parser's permissive notice, not camera source/BSP | No processing attribution |
| [E-M10 IV Linux notice](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/notice/pdf/Software_Notice_em10m4_linux.pdf) |79pages; extracted text **identical** to E-P7 notice despite different PDF hashes | Same reviewed license text; not proof identical compiled components, boards or firmware | **countercontrol**, no cross-model transfer |
| [E-M1 II notice](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/notice/pdf/Software_Notice_em1m2_v1.00.pdf) / [E-PL10 notice](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/notice/pdf/Software_Notice_epl10.pdf) |23pages each; filenamev1.00 on first is not a tested firmware/source tag. Headings name Expat1.95.5 and newlib, no processor | Public notices; Expat permissive, newlib composite per-origin notices. No source bundle or complete OS declaration | Differences in notice packaging do not map software ownership |
| [Olympus E-M1 II development announcement](https://www.olympus-global.com/news/2016/nr160920em1mk2pke.html), main-feature detail1(1); [launch announcement](https://www.olympus-global.com/news/2016/nr161102em1mk2e.html), same subsection |2016-09-20 /2016-11-02; E-M1 II TruePic VIII, **four CPU +four image-processing cores** | Official product/architecture claim, Olympus copyright; no ISA/part/BSP or driver source license | **verified official other-model statement**, not E-P7 ABI |
| [Linux MN103 Kconfig](https://github.com/torvalds/linux/blob/0adb32858b0bddf4ada5f364a84ed60b196dbcda/arch/mn10300/Kconfig), lines76–113; [COPYING](https://github.com/torvalds/linux/blob/0adb32858b0bddf4ada5f364a84ed60b196dbcda/COPYING) |v4.16 peeled commit `0adb32858b0bddf4ada5f364a84ed60b196dbcda`; ASB2303/2305/2364, MN103E010/MN2WS0050; MN103/AM33/AM34 platform, not E-P7 | Two publicly readable files, GPL-2.0; read only, not copied into this MIT repository | **generic ISA/platform reference only**, no E-P7 BSP/ISP |
| [US9055219B2](https://patents.google.com/patent/US9055219B2/en), description¶0040/0047–0054 |Original assignee Olympus Imaging Corp; priority2012-09-26, publication2015-06-09; no model/ISA/firmware revision | Published patent description, not executable source or implementation license. Only original paraphrase/citation retained | **verified disclosure**, generic functional stages; no E-P7 field/driver binding |
| [US9787965B2](https://patents.google.com/patent/US9787965B2/en), bibliographic original-assignee field |Fujifilm Corp, publication2017-10-10; Olympus appears among cited prior art | Published patent; no source-code license assumed | **rejected assignee false positive**, not Olympus/E-P7 evidence |

### A · What the source offer does and does not establish

The E-P7 notice's first page describes a request for certain licensed corresponding source, with camera model and purchase date, followed by a download link; its stated offer period is three years from original purchase. **Eligibility, present responsiveness, package contents, download availability and any imaging coverage remain unknown.** Do not infer eligibility/expiry from E-P7's release date. No email/draft, purchase-detail collection or vendor contact occurred; no contact is authorized by this task. Generic upstream URLs in the notice are not the manufacturer's corresponding-source revision.

The15 component headings include networking/web support and libraries; the bcmdhd GPL entry is not a color/ISP ABI. Linux release and camera-specific configuration are not supplied. The E-P7 and E-M10 IV PDFs have different sizes/hashes but produce **byte-identical `pdftotext -layout` text**. This falsifies treating shared notice text as independent evidence of matching processor or driver implementation. The shorter E-M1 II/E-PL10 Expat/newlib notices equally cannot prove those cameras lack Linux or that E-P7's whole application is Linux.

Public searches were bounded discovery aids: `gh search repos 'olympus linux kernel'` returned0; `'TruePic'` returned8 top entries about unrelated authentication/image tools; code searches for the source-offer email and for `"E-P7" "kernel"` returned0. A12-result general TruePic code sample was likewise unrelated. Web source searches for model/kernel mirrors, processor part/datasheet and exact-model teardown returned no provenance-qualified imaging candidate. **This is not an exhaustive proof no source exists.** Search ranks/empty results are mutable and do not replace primary-page review. Selected query results and source snapshots remain in ignored work files; no unrelated repository content was executed or adopted.

### B · A real architecture distinction, without a chip crosswalk

Olympus's two E-M1 II announcements distinguish general CPU and image-processing cores within the TruePic VIII description. That is independent **other-model** support for keeping control software and rendering ownership separate. It does not specify the E-P7's active cores, CPU ISA, silicon part, frame-bus protocol, registers, color coefficient layout or correspondence to OE blocks. The two announcements corroborate wording from **one vendor**, not two independently measured chip implementations.

Upstream Kconfig really supports MN103-family processors and named development boards. It supplies no E-P7 binding; its addresses/peripherals and SMP configuration cannot be assigned to the camera. The documented ARM ELF files in [T1.1](e142-squashfs-validation.md) describe selected Linux user-space components, whereas [T7](e142-system-boundary-map.md) describes MN103-family application/control anchors. Neither the product brand nor generic Linux support resolves which component owns frames or final JPEGs. No register comparison or new OEM decoding was justified.

### C · Patent concepts are not production interfaces

US9055219B2's embodiment separates a microcomputer/bus/SDRAM, basic image processing, optional effects and compression. It discusses live display and image storage. **Verified: Olympus published those concepts. Unknown: whether E-P7 implements that arrangement.** Numbered drawing elements109/121/etc. are patent labels, not firmware addresses, struct offsets or recovered symbols. The disclosure has no E-P7/TruePic-specific build identity, typed transfer interface or color-record ABI to match against T7's request1007 or generic settings IDs53–56. No matching attempt was made.

The color-conversion search hit US9787965B2 is a useful falsifier: its original assignee is Fujifilm, and an Olympus prior-art citation caused apparent relevance. It was excluded from Olympus architecture conclusions. Marketing datasheets, unattributed processor claims and ordinary Linux code were similarly not promoted. No patent-derived operator, codec or model address was implemented.

## Reproducible snapshot checks

Only public files were downloaded into ignored `work/t8/sources/`, with bounded reads and no full source archive. Hashes identify reviewed bytes, not authenticity signatures or firmware versions:

| Public artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| E-P7 Linux PDF |704438|`28b58793da9c9f2ae13c49032836502ed4fb462aab7e0be5e828809e9233e3ed`|
| E-M10 IV Linux PDF |714420|`55cb7c13294ada7b90232ebd7eab99a6108b3429178f50d94d35974d3ceeb185`|
| E-P7 Expat PDF |63899|`fec7fbc1ff3ad4b5c52504388630f166dc63b7dcce61fad8d219a7366d8a2c9a`|
| E-M1 II notice PDF |92037|`fd0291009d04eeac3fe6cb61fa7a7ad6f2c94ce773649fd3e1cb492e6e4084d4`|
| E-PL10 notice PDF |98175|`51c87b9c98239f4ff774b53d87a91602e066ddd5abf2590d53031f1f930ea8f8`|
| Pinned MN103 Kconfig |11686|`24992106c603cd6cc7d2fb5895e8ac9a34e9cd12b41481e82250c5f04d7beffa`|

Example after independently fetching the linked public PDFs, using Poppler `pdftotext`25.03.0, `pdfinfo`, `sha256sum` and stdlib checks:

```bash
pdftotext -layout work/t8/sources/ep7-linux.pdf work/t8/sources/ep7-linux.txt
pdftotext -layout work/t8/sources/em10m4-linux.pdf work/t8/sources/em10m4-linux.txt
sha256sum work/t8/sources/ep7-linux.pdf work/t8/sources/em10m4-linux.pdf
cmp work/t8/sources/ep7-linux.txt work/t8/sources/em10m4-linux.txt
```

Both extracted texts' SHA-256 is `46686588f4f77736aa35fe17e4c8659d2a4e1915239d727c2632b5ad36c31345`. Pages/component counts and relevant first-page/description passages were manually checked, not inferred from HTTP200 or snippets. Initial web-tool fetches of the Olympus patent failed; an ordinary public HTTPS retrieval supplied the complete description for review. One guessed news URL and an inaccessible generic WLAN header were not used as evidence. No content from search-only/unread items supports the verdict.

## Decision and highest-value input

**Pause: there is no admitted interface anchor to restart MN103/other-block work.** Product feasibility remains unknown, not a categorical impossibility. Public-source archaeology has now tested model-linked notices, processor support and imaging disclosure without recovering the required bridge; continuing adjacent calls or broad generic-driver searches would not be justified.

The **most valuable actionable input** is a legitimately obtained **E-P7 corresponding-source package with provenance and build/board configuration**, ideally accompanied by actual camera-specific driver/interface definitions. The verified offer is a possible opt-in acquisition route, not a package we possess or a request to contact the vendor now. If a user independently obtains such material in a separately scoped task, first verify its model/version and per-file license. A kernel-only/network-only release may still leave the proprietary imaging/control bridge absent; source receipt alone must not reopen the gate.

Minimum re-entry decision tree: model/version/build identity → relevant image/parameter/transport definition → two independent OEM/ABI invariants → **one** bounded offline crosscheck. If it only reproduces stock kernel/network code or generic patent stages, stop without opening more firmware blocks. A legitimate exact-model technical interface or otherwise independently linked silicon/BSP could satisfy the same criterion. No automatic T9 or speculative camera/debug experiment is proposed.

| Alternative | Cost / evidence / product consequence |
| --- | --- |
| Obtain and review a provenance-qualified source/interface package, if separately chosen | Highest chance to resolve ownership; availability/eligibility and imaging coverage unknown. Requires no camera writes, but any correspondence needs separate authorization |
| Opt-in stock COLOR response experiment | Requires separate camera authorization and controlled captures; tests G3 expressivity only. Useful only if manual controls have value to owner; does not establish external import or binary consumer |
| Keep project paused | Avoids further uncertain-cost reverse engineering; preserves evidence and product target. Recommended until a qualified source appears; no required owner-camera labor |

Validation for this docs-only task: primary content/notice equality/counts/pinned revision checks; changed-file privacy/relative-link/whitespace checks and existing synthetic CI. No new tool/test/fixture or proprietary data committed; CI tests tooling, not source coverage, imaging or camera functionality. Restartable private handoff retained, one PR for review, no automatic merge.
