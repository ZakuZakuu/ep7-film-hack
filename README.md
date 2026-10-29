# E-P7 Film Hack

**Evidence-driven research on Olympus PEN E-P7 native profiles, firmware, and in-camera film looks.**

[中文说明](README.zh-CN.md) · [Current instructions](AGENTS.md) · [Historical plan](docs/05-execution-plan.md) · [Historical gates](docs/09-feasibility-gates.md) · [Prior work](docs/04-reference-projects.md)

> **Status: experimental COLOR HSL software.** The owner reported successful T20 effects and v2 COLOR1–4 JPEG tests ([#49](https://github.com/ZakuZakuu/ep7-film-hack/issues/49), [#58](https://github.com/ZakuZakuu/ep7-film-hack/issues/58)). v4 EP71 and the desktop client have offline validation; their B4 camera tests are pending. No OEM firmware or install files are distributed here.

## Current software and goal

Save a useful native COLOR film look, switch profiles, retain camera preview and JPEG output. ART research is paused. [AGENTS.md](AGENTS.md) and the authorized Issue supersede the historical T0–T19 gates and plans below.

- [Recipe Studio](tools/recipe_studio/README.md): offline recipe editing/approximation; a desktop preview is not an E-P7 quality measurement.
- [v4 / EP71 protocol](docs/wifi-recipe-protocol.md): sequential native-setting writes and a published H/L RAM mirror, verified to the ISP coefficient boundary in explicit offline models. Real persistence, Wi-Fi, Myset and cache behavior remain B4 items.
- [Desktop Wi-Fi client and Windows/macOS/WSL commands](tools/ep7_wifi/README.md): discover, read, automatic backup, write, verify and restore. Requires EP71; stock firmware is refused. Timeout does not imply cancellation.

Agents have not connected or operated a camera. Hardware installation and B4 remain owner decisions after review. Arbitrary LUT import, custom ART entries and production-safe firmware are not claimed.

## Historical research strategy (T0–T19)

| Candidate method | Public precedent | E-P7-specific proof required |
| --- | --- | --- |
| Fit user LUTs to native image controls | [GR4-LUTSmith](https://github.com/lemonadesaltbagel/GR4-LUTSmith) | Editable E-P7 native parameters; enough color degrees of freedom; safe persistence |
| Trace native identity, descriptors and save/load lifecycle | [GR Custom Tool](https://github.com/DoYitNow/gr-custom-tool) | E-P7 selector/record/consumer evidence; GR-specific code/addresses are not transferable; public GR tool lacks independent device validation |
| Find/replace effect resources or slot labels | [GR IV firmware research](https://github.com/radium-wang/ricoh-gr4-firmware-analysis-and-feature-expansion) and GR4-LUTSmith | E-P7 ART IDs, relevant data and trusted update pathway |
| Reuse camera firmware analysis and patch guardrails | [NikonHacker](https://github.com/simeonpilgrim/nikon-firmware-tools), [FujiHack](https://github.com/fujihack/fujihack) | E-P7 packaging, exact version, signature checks, rollback reality |
| Explore an add-on or module framework | [Magic Lantern](https://github.com/reticulatedpines/magiclantern_simplified) | E-P7 code execution and a genuinely safe loading path; **not** assumed |
| Read-only camera protocol capability discovery | [olympus-wifi](https://github.com/joergmlpts/olympus-wifi) | E-P7 protocol compatibility and actual supported commands |

Cross-camera implementations are **precedent for an investigation**, not evidence of compatibility or success on the E-P7. We prefer the smallest viable change and stop when facts contradict a proposed route.

## Historical project state (T0–T19)

- T0 review: [findings and three proposed experiments](research/first-pass-findings.md), [acquisition blocker](research/blockers/BLOCKER-firmware-acquisition.md), [source audit](research/source-access-review.md), and [synthetic validation](research/validation-t0.md). The historical G1 access blocker was subsequently resolved by T1/T1.1; protocol/native-profile routes remain conditional research.
- Official firmware listing: E-P7 **1.1**, dated 2022-02-28 ([OM SYSTEM](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/)). This is a listing, **not** a verified downloadable firmware image.
- An owner-provided candidate was privately validated as five OE blocks in [PR #6 findings](research/e142-first-sample-analysis.md); no OEM binary is in Git. [Issue #7 findings](research/e142-squashfs-validation.md) verify the real LZO SquashFS directory and seven selected files using upstream tools. ART remains unknown; no device writes.
- No E-P7 hardware has been connected or tested.
- Included helper `tools/inspect_blob.py` only reports metadata and sample entropy on user-provided files; it does **not** parse E-P7 firmware.

## Historical milestones and decisions (superseded by AGENTS.md)

**Historical T19: [Issue #47 native ART consumers](research/e142-art-native-consumers.md).** Native extra-effect state now joins real32-byte constructors and the previously verified effects receiver; per-variant records are independently shared with bracketing. This route clears FilmNoise, and a separate tagged block has an ExifTool-compatible metadata interpretation. Actual pixel rendering, named user looks and durable persistence remain unverified. [Reproduction/handoff](docs/25-t19-private-validation.md); G2 incomplete, G4/G5 NO-GO.

**Previous: [Issue #45 ART parameter graph](research/e142-art-parameter-graph.md).** Native actuator/cache, registered hooks and156-byte bundle/scalar handoffs remain the baseline.

**Previous: [Issue #43 multi-track investigation](research/e142-longrun-architecture-and-deployment.md).** Adjusted subobject/entry contracts and two ART-labelled control roots; acceptance/recovery audit remains applicable.

**Previous: [Issue #41 architecture sprint](research/e142-art-architecture-sprint.md).** Constructor-path proxy and returned-byte control map; not an ART writer or renderer. GNU UDF semantics remain unadmitted.

**Previous: [Issue #39 GNU simulator and copy-loop admission](research/e142-mn103-semantics.md).** Reused external GNU sim passes original call/data/branch/copy fixtures; a cached-code counterexample limits its LIR fidelity. Two conditional static proofs let the private CFG pass the producer/receiver first loops; no OEM execution or decompiler is claimed. [Commands](docs/21-mn103-semantics.md).

**Previous foundation: [Issue #37 system RE workbench](research/e142-system-re-workbench.md).** Reproducible public tool bootstrap and a tested private GNU/SQLite index are now available; [Cloud Setup and commands](docs/20-re-workbench.md). Direct Ghidra headless passes a synthetic ELF, but no MN103 language/decompiler is admitted and REA native launch is blocked in this Cloud runtime. No ART feature or firmware modification is implemented.

**Previous ART evidence: [Issue #33 ART grain gates/custom-item boundaries](research/e142-art-host-gates.md).** New code relationships identify three composite keys forcing MonoEnable and an independent Type gate clearing FilmNoise while retaining MonoEnable. Conditional local preservation is not accepted color grain or rendering proof. ART remains the lead; selector registration, independent persistence, actual consumers and name/icon/preview bindings remain blocked. **Continue only grounded ART research; no feature implementation or flashing.** [Exact private reproduction](docs/19-art-gates-private-validation.md). Owner-confirmed dedicated ART extras are unavailable through normal P/A/S/M Picture Mode; the old cross-entry audit is superseded. [T10 comparison](research/e142-cross-model-style-entrypoints.md) and [T9 stock capabilities](research/e142-native-style-workflows.md) remain historical evidence, not the current primary route.

[Issue #27 public-interface review](research/e142-public-interface-evidence.md) found no actionable E-P7 frame/color/ISP interface after three source-specific routes. Its driver/ABI and G4/G5 blockers remain for firmware engineering; this does not prevent assessing documented stock workflows.

[Issue #25 system-boundary map](research/e142-system-boundary-map.md) recovered startup-backed initializer/helper relocation, a three-level method-name lookup, a typed one-shot capture request and a generic custom-setting path. The former external copy/fill helpers are located in #0. These are static architecture/control findings; no native COLOR record→actual preview/JPEG consumer or external custom-look import was established. See the [small numeric index](research/e142-system-boundary-map.json) and [guarded reproduction](docs/16-system-map-private-validation.md).

The following milestones retain their historical decisions; T9/T10 distinguish stock-workflow research from paused firmware engineering.

[T0 baseline](research/first-pass-findings.md), [OE validation](research/e142-first-sample-analysis.md), [filesystem findings](research/e142-squashfs-validation.md), [resource layout](research/e142-resource-mapping.md) and [media limits](research/e142-media-triage-and-feasibility.md) are retained. [Issue #13 decision](research/art-update-feasibility.md): OEM-added Bleach Bypass is verified history; E-P7 ART processing/editability and modified-image acceptance/recovery remain unknown. Pause firmware-modification engineering. Official E-P7 profile-import destinations are unsupported; native manual profiles remain an alternative to measure.

[Issue #15 executable map](research/e142-executable-map.md) verifies MN103-family code and call/return relationships in block #0, with strong static reference support for payload base `0x60020020` at tested anchors. T7 adds scoped relocation views; this is not a uniform whole-image map. Exact CPU/OS, ART processing and hardware runtime remain unknown; paired old firmware is optional. Three prior BleachBypass anchors are in valid `oishare` interface XML, not proven image-processing code. See [private reproduction](docs/13-executable-private-validation.md); no proprietary code/disassembly is published.

[Issue #18 native-profile investigation](research/e142-native-profile-chain.md) verifies Picture Mode field reads in two diagnostic structures and a selector-dependent address helper. COLOR1–4 persistence and the live-view/JPEG consumer are still unlocated; the two-hypothesis analysis stopped. Prioritize stock COLOR slots conditionally, without claiming automatic import or a fitted look. See the [blocker](research/blockers/BLOCKER-e142-native-profile-consumer.md) and [private reproduction](docs/14-native-profile-private-validation.md); 39 synthetic tests pass, no device action or OEM data committed.

[Issue #21 producer/consumer follow-up](research/e142-picturemode-producers-and-remote-controls.md) recovers a real CREATE_PARAM caller, source-to-temporary group/type/mode writes and a non-formatting receiver that packs those fields into a key and selects local flag-setting branches. This advances beyond diagnostics; native COLOR slot identities, persistence and actual preview/JPEG processing remain unproved. The fixed OI.Share schema describes named stock ART controls without establishing custom-profile import; official Profile Library excludes E-P7 as a write destination. See [guarded reproduction](docs/15-picturemode-and-schema-private-validation.md). Next: one bounded analysis of the observed downstream hand-off, not firmware modification. G2 incomplete, G4/G5 NO-GO.

[Issue #23 hand-off verdict](research/e142-picturemode-handoff-verdict.md) completes that experiment: `0x334780` reads group/options/flags and conditionally delegates, with no identified imaging consumer. Stop this incremental chain; neither new callee met the independent rendering-evidence condition. G2 is incomplete, G4/G5 remain NO-GO. Prefer a separately authorized stock COLOR expressivity pilot, or pause if manual controls cannot meet the owner's needs. The report includes the route comparison and private reproduction; no camera experiment or automatic import is claimed.

Read current [AGENTS.md](AGENTS.md) and the authorized Issue first; [RESEARCH_POLICY.md](RESEARCH_POLICY.md) is historical. [CODEX_START.md](CODEX_START.md) records the historical T0 scope.

```bash
python3 -m unittest discover -s tests -v
python3 tools/inspect_blob.py --help
```

## Guardrails

- No camera writes, modified-firmware flashing, unreviewed debug operations or downgrade attempts without a separately authorized, device-specific recovery plan.
- No redistributing OEM firmware, device dumps, personal photos, private network captures, or third-party assets without rights.
- No copying source whose license forbids it. **GR IV research project's newer contributions are noncommercial-licensed; GR4-LUTSmith has no root LICENSE file observed at the time of this review — read and learn, do not copy code without permission. GR Custom Tool author source is GPL-2.0-only; no code is imported into this MIT repository.** Other projects have their own licenses.
- Every finding records device model, firmware version, sample SHA-256 if one exists, offsets/addresses if meaningful, source, evidence class, counterexamples and a test that could falsify it.
- A defensible *no-go* result is better than a fabricated working modification. Alternatives must preserve clarity about whether photos are truly rendered in-camera.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [RESEARCH_POLICY.md](RESEARCH_POLICY.md), the [evidence ledger](research/evidence-ledger.md), and the [research blocker template](.github/ISSUE_TEMPLATE/blocker.md).

Original code and documentation in this repository are MIT-licensed (see [LICENSE](LICENSE)). All third-party repositories, firmware, images, trademarks, and algorithms remain under their respective owners' terms. This research does not imply permission to distribute or modify others' proprietary assets.

给 LUT → 得到配方 JSON → ep7wifi：无需照片的用法见 [Recipe Studio](tools/recipe_studio/README.md)。
