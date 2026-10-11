# Research policy: evidence, feasibility, reuse

## Accepted precedent

Investigate only methods that have a documented working precedent in a *real camera community project*, an inspectable open source implementation, or an official camera API. **Precedent on another model does not demonstrate E-P7 viability.** Verify the original repo, exact model/version, author claims vs independent reproduction, and licenses before implementation.

## Engineering method

1. Define one narrowly-scoped, falsifiable hypothesis and expected observation.
2. Link one credible prior-art implementation and its exact technique; identify which inputs and assumptions transfer and which do not.
3. Gather primary evidence specific to E-P7. Never supply invented addresses, offsets, symbol names, test fixtures or device traces as findings.
4. Produce the smallest read-only or offline experiment that could refute the hypothesis. Keep original sample hashes and reproducibility notes.
5. Record confirmed results, counterevidence, outcome and next action. If blocked, produce a blocker report rather than compensating with speculative architecture or UI code.

## Go / no-go

- **GO:** An E-P7-specific sample, protocol response, or validated resource maps to a candidate behavior, and a bounded next test exists.
- **CONDITIONAL:** Related-model proof only. Continue *research*, not patch implementation.
- **BLOCKED:** No lawful firmware sample or device access; E-P7 architecture unknown; signature/repacking restrictions; no demonstrated recovery path; ART hard-coded in inaccessible accelerator; native parameters insufficient to reproduce user look.
- **STOP:** Two independent approaches yield no new evidence; publish a precise blocker with alternate routes and user decision required before more effort.

## Alternative routes, honestly labeled

A. Existing native profile + color optimization: may improve workflow without new hue freedoms.  
B. Remote preset management only if E-P7 actually permits protocol writes: may fix switching but not color range.  
C. Offline RAW/JPEG film processing: useful backup experiment, **not in-camera JPEG SOOC**.  
D. New custom processing operator: defer until a proven execution environment, frame access and performance budget exist.

## Release and licensing

Do not ship third-party OEM binaries or derived proprietary resources. Do not merge code from GPL or source-available/noncommercial projects into MIT code without deliberate license review and compatibility confirmation. Preserve attribution. A community-reported feature, simulated test or checksum-valid firmware is not a camera-tested feature.
