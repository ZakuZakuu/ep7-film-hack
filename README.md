# E-P7 Film Hack

**Evidence-driven research on Olympus PEN E-P7 firmware, ART filters, and in-camera film simulations.**  
[中文说明](README.zh-CN.md) · [Research plan](docs/05-execution-plan.md) · [Feasibility gates](docs/09-feasibility-gates.md) · [Prior work](docs/04-reference-projects.md)

> **Status: RESEARCH ONLY — no verified E-P7 firmware patch, arbitrary LUT import, ART-filter replacement, or camera-tested custom effect.** This is not an installer or a supported modification. Unofficial community project, not affiliated with OM Digital Solutions or Olympus.

## Why

The E-P7 has useful Color/Mono Profile Controls and built-in ART effects, but they are difficult to combine and limited for intricate film looks. The long-term user experience we want is *choose a named film look in-camera, preview it, shoot a finished JPEG*, with several switchable presets. We prefer reusing existing ART UI/processing capabilities rather than writing a new ISP engine.

**A goal is not a capability.** We do not know whether E-P7 ART effects are stored as editable tables, code, fixed ISP modes, or a mixture. Firmware access, acceptance of modified updates, and safe recovery remain unverified.

## Research strategy (borrow proven methods, not patches)

| Candidate method | Public precedent | E-P7-specific proof required |
| --- | --- | --- |
| Fit user LUTs to native image controls | [GR4-LUTSmith](https://github.com/lemonadesaltbagel/GR4-LUTSmith) | Editable E-P7 native parameters; enough color degrees of freedom; safe persistence |
| Find/replace effect resources or slot labels | [GR IV firmware research](https://github.com/radium-wang/ricoh-gr4-firmware-analysis-and-feature-expansion) and GR4-LUTSmith | E-P7 ART IDs, relevant data and trusted update pathway |
| Reuse camera firmware analysis and patch guardrails | [NikonHacker](https://github.com/simeonpilgrim/nikon-firmware-tools), [FujiHack](https://github.com/fujihack/fujihack) | E-P7 packaging, exact version, signature checks, rollback reality |
| Explore an add-on or module framework | [Magic Lantern](https://github.com/reticulatedpines/magiclantern_simplified) | E-P7 code execution and a genuinely safe loading path; **not** assumed |
| Read-only camera protocol capability discovery | [olympus-wifi](https://github.com/joergmlpts/olympus-wifi) | E-P7 protocol compatibility and actual supported commands |

Cross-camera implementations are **precedent for an investigation**, not evidence of compatibility or success on the E-P7. We prefer the smallest viable change and stop when facts contradict a proposed route.

## Project state

- Official firmware listing: E-P7 **1.1**, dated 2022-02-28 ([OM SYSTEM](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/)). This is a listing, **not** a verified downloadable firmware image.
- An owner-provided candidate was privately validated as five OE blocks in [PR #6 findings](research/e142-first-sample-analysis.md); no OEM binary is in Git. Filesystem contents and ART remain unverified. [Issue #7 findings](research/e142-squashfs-validation.md) include guarded local carving, upstream LZO synthetic validation and the current attachment transfer blocker.
- No E-P7 hardware has been connected or tested.
- Included helper `tools/inspect_blob.py` only reports metadata and sample entropy on user-provided files; it does **not** parse E-P7 firmware.

## First task (Codex Cloud)

Read [`AGENTS.md`](AGENTS.md), [`CODEX_START.md`](CODEX_START.md) and the existing research notes. Perform **T0 only**: verify official references; assess source/firmware availability and legal/reproducibility constraints; record evidence and concrete next experiments. Do not invent analysis from missing binaries and do not build UI or patches before establishing a substrate.

```bash
python3 -m unittest discover -s tests -v
python3 tools/inspect_blob.py --help
```

## Guardrails

- No camera writes, modified-firmware flashing, unreviewed debug operations or downgrade attempts without a separately authorized, device-specific recovery plan.
- No redistributing OEM firmware, device dumps, personal photos, private network captures, or third-party assets without rights.
- No copying source whose license forbids it. **GR IV research project's newer contributions are noncommercial-licensed; GR4-LUTSmith has no root LICENSE file observed at the time of this review — read and learn, do not copy code without permission.** Other projects have their own licenses.
- Every finding records device model, firmware version, sample SHA-256 if one exists, offsets/addresses if meaningful, source, evidence class, counterexamples and a test that could falsify it.
- A defensible *no-go* result is better than a fabricated working modification. Alternatives must preserve clarity about whether photos are truly rendered in-camera.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [RESEARCH_POLICY.md](RESEARCH_POLICY.md), the [evidence ledger](research/evidence-ledger.md), and the [research blocker template](.github/ISSUE_TEMPLATE/blocker.md).

Original code and documentation in this repository are MIT-licensed (see [LICENSE](LICENSE)). All third-party repositories, firmware, images, trademarks, and algorithms remain under their respective owners' terms. This research does not imply permission to distribute or modify others' proprietary assets.
