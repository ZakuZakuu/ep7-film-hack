# PR reconciliation (2026-10-11)

User authorized review fixes, preservation, merges and redundant-PR closure before Issue #10.

| PR | Dependency / result | Preserved content |
| --- | --- | --- |
| #5 | main → merged 386cd42d6d5aaf8ac63f77b056a5426aed806800 | T0 report, F01–F15 ledger, pinned prior-art/source/license audits, blocker, two additional CLI tests |
| #6 | main → merged 6586a1d7870f826fd8275aaf94ad5e7bd02ff46b | Original OE decoder, synthetic tests, real-sample report |
| #9 | Originally based on #6; synchronized reconciled main and retargeted; merged c274678f27c481fb2f015ec22237c8f1297d893b | Real FS work; corrected README milestones and consistent absolute /tmp paths; T0 ledger retained alongside later evidence |
| #8 | Independent serial-env implementation; closed as superseded after #9 landed | Equivalent CLI and stronger mock-only tests in #9; unique configuration/network guidance retained at docs/12-codex-cloud-private-download.md |

#8 had a get_serial helper with no unique behavior beyond env/prompt handling. #9 tests cover injected value in mock request/no output, missing/empty/invalid value stopping before prompt/network/output. Its private setup guidance was retained rather than dropped. No repeated feature merge; no remote branch deletion.

All three merge operations used the expected head SHA and merge commits, preserving research history. #5/#6 CI succeeded; reconciled #9 had 22 local tests/0 skipped and successful CI before merge. Conflict resolution retained both T0 and later evidence; historical G1 blockers were explicitly marked superseded, not silently erased.

Issue #10 branch research/e142-resource-mapping starts from c274678f27c481fb2f015ec22237c8f1297d893b, updated main. No firmware/private outputs entered the reconciliation commits.
