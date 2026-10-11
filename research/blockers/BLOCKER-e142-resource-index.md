# BLOCKER: coherent E-P7 resource index / ART reference not established

2026-10-11 / Issue #10 / G2; E-P7 owner-reported 1.1, 111017984-byte candidate SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`.

Private OE validation succeeds. Block #4 has repeatable 512-byte-biased SOI layout and two independently decoded JPEG assets. These establish neither menu IDs nor processing ownership.

Two independent bounded tests: (1) preceding 4/8/16/32-byte LE/BE u32 length candidates failed to produce repeated bounded records; (2) direct block-local u32 references to SOI payload offsets or the unverified header load-candidate plus offsets produced only one isolated numeric match. Neither established count/order/record/reference semantics. Stop further guesses under the issue's bound; no proprietary resource parser or patch generator.

Community sources show historical Olympus resource extraction, but no reviewed, licensed TruePic VIII index implementation applicable to these bytes. Missing evidence may be resolved by old source/format recovery, another referenced start convention, or a cross-block relation. This is evidence missing, not proof that ART is impossible or absent.

Next smallest experiment: obtain/review actual historical resource-extractor source and license; test its documented reference form on the two verified E-P7 candidates before extending to cross-block references. If unavailable, report the source-access blocker rather than guessing all addresses/ISAs. Native Color Profile capability measurement is an alternative preserving official SOOC but cannot promise arbitrary LUT/ART slots. No camera operation required or authorized in this task.

Full sanitized offsets, observations and disconfirming limits: [report](../e142-resource-mapping.md). G2 remains unknown; G4/G5 unknown/no device writes.
