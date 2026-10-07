# R9 local validation

Prepared 2026-10-07. DEVELOPMENT. R8 user-run binding is confirmed for the supplied
grid; visible highlights failed. R9 gameplay is pending.
Candidate: `build/please-do-better/candidates/r9/please-do-better-r9-candidate.zip`.
Only member: `Please do Better/romfs/nativeNX/plugins/please_do_better.nro`.

NRO SHA-256: `eb26371244a7cc74e1f7f3144983993a340a8e0f2029f37890eebba9dd1eb265`.
ZIP SHA-256: `09a31f2e913e0aae1d700c5b1f376e79252cd58c486b064621e111e2d60ab800`.

The compiled resolved-surface fixture produces a gold border/sparkle under R9.
Full alternate viewport banks also render. Null/unrelated targets, actual
offset/reduced viewports, tiled geometry and unknown shaders
remain unmarked. Each rejection has a separate immutable diagnostic, with exact
surface identities, selected viewport values or bounded shader bindings.
Eighty independently executed original ARM viewport-bank/clamp/scissor fragments
cover both banks, out-of-bounds and reduced rectangles, empty clips and intersections. All thirteen original reflected
shader lists match serialized metadata; twelve verified XY/W=1 lists render,
and the perspective variant is rejected. Precise fault text balances the compact
panel trees. Existing forcing/RNG/settings, startup rollback, observation/copy,
geometry/frame ordering, clipping, overflow, ARM/SVC and state preservation suites
are required.
| Local check | Result |
|---|---|
| Host transaction/backend/settings/attribution/hooks | 43 / 21 / 74 / 1,993 / 48 passed |
| Host geometry/immutable concurrent snapshots | 728 passed; ASan/UBSan |
| Compiled ARM continuations/SVC ABI | 2,122 passed |
| Compiled mode/RNG/settings/startup/gateways | 100,516 passed |
| Original native copies/world quads/viewport | 468 passed, including 80 native viewport/clip fragments |
| Compiled count/copy observations | 28,841 passed; 288 native batches |
| Display/relocation/initialization/compact UI | 16,634 passed |
| Compiled geometry/presentation/gold/rejection | 6,621 passed; resolved target and full alternate bank, precise rejection, deferred logging |
| Gateway state preservation | 1,024 active geometry and 1,024 present cases; GPR/SP/LR, VFP/FPSCR, NZCVQ/GE |
| Resource/shader receipts | 96 ordinals / 162 group instances; 13 exact native reflected lists, 12 XY/W=1 shaders; 30 original function traces |
| NRO/imports/relocations/instruction audit | 61,440 bytes, BSS 69,632; actual installed Forge/SDK exports; no forbidden APSR/GE writes |
| Allocation limits | One 4KiB arena, one native TLS slot, eight contexts/four scopes, 64 binding/geometry entries; no added arena or heap allocation |
| Package/checksums/whitespace/full distribution checker | Passed; deterministic single-member ZIP, readback/inventory/checksums and eight-mod distribution check |


All 85 recorded R1-R8 files retain their hashes. R8 commit `49f3a0d` and prior
accepted commits remain preserved. Forge stays clean on `codex/forge-legacyctx14`,
commit `b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d`. Installed Forge/Better Input:
`9d472d56f81f834f366171426dbd0131af19c7697e132c731c3fd3f335af53d0` /
`400a8881065b5736debfdd88d167141b624671906187b9460e1a2fd267497f5f`.
Installed R8 is unchanged. No install/activation/launch/save or settings edits,
push/publication occurred. Static fixtures do not prove GPU alignment or that
this guard defect is the exact gate in the user's screenshot.

See R9_HIGHLIGHTS.md and MANUAL_TESTS.md for pending gameplay coverage.
