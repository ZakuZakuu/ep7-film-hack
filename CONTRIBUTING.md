# Contributing

Contributions are welcome: OEM documentation links, relevant prior art, analysis scripts, synthetic tests, evidence-backed E-P7 findings, and cautious limitations. **No blind patches or user-ready firmware installers.**

Before opening a PR, ensure:

- A clear, falsifiable research question and exact model / firmware version.
- Evidence type stated as `official`, `verified locally`, `author reported`, `community reported`, `hypothesis` or `unknown`.
- For binary findings: source method, SHA-256 of a legally obtained sample (hash only), exact offsets, commands, and competing explanations. No proprietary binary content.
- A minimal reproducible test on synthetic or user-owned inputs. No hardware claims without hardware output.
- A licensing check for reused code; link upstream, preserve credit and follow incompatible licensing terms.
- A blocker report if the route has no credible next verification step.

Do not upload original firmware, extracted OEM binaries, dumps, logs with IDs, third-party images or unlicensed LUTs. Use synthetic fixtures. See [RESEARCH_POLICY.md](RESEARCH_POLICY.md) and [docs/06-validation-and-safety.md](docs/06-validation-and-safety.md).
