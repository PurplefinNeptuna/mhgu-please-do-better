# R8 local validation

Prepared 2026-10-07. DEVELOPMENT. R7 user-run highlights failed; R8 gameplay is pending.
Candidate: `build/please-do-better/candidates/r8/please-do-better-r8-candidate.zip`.
Only member: `Please do Better/romfs/nativeNX/plugins/please_do_better.nro`.

NRO SHA-256: `f6b6e2acbbc4333d8b422a5d72282d01b89f87bc477896299eb24dac01f8acab`.
ZIP SHA-256: `12a6e53b6d3c6f4cbd3ebf6fec477d37c7e4a547aea2f84bab636542bccc2e75`.

## Before/after regression

The corrected native initialization sequence fails against preserved R7: eight
slots/four extras, complete retained totals, exactly one added capture fault,
no retained record and zero bindings. R8 retains that newly verified record
with zero added capture faults. Subsequent native list copying binds four Festa
frames; capture and native presentation produce four gold borders/sparkles.
The fixture includes state-1's original resize loop and reward-copy code, using
all four scope levels: update -> builder -> wrapper -> count. Allocation/free
and item-selection inputs are fixtures. It does not execute a GPU or emulator.
Original `0x384FC0` BL-to-builder bytes are checked against the pinned main.

| Local check | Result |
|---|---|
| Host transaction/backend/settings/attribution/hooks | 43 / 21 / 74 / 1,993 / 48 checks passed |
| Host geometry/atomic snapshots | ASan/UBSan and bounded concurrent publication passed |
| Compiled ARM continuations and six SVC ABIs | 2,122 checks passed |
| Compiled mode/RNG/settings/startup/gateway | 100,516 checks passed |
| Original native copy/world quads | 388 checks passed |
| Compiled count/copy observations | 28,841 checks; 4,096 gateway cases; 288 native batches |
| Display, relocation, initialization and panel | 16,634 checks; unavailable old array, incomplete new batch, different UI, genuine fault-route text and balanced trees |
| Geometry/presentation/gold drawing | 6,556 checks; corrected nested initialization-to-four-marker chain |
| Active gateway preservation | 1,024 geometry and 1,024 present cases; GPR, SP/LR, all VFP/FPSCR and NZCVQ/GE preserved |
| Resource/shader/frame identity | 96 GUI ordinals, 162 group instances; twelve verified 2D shaders; direct/parallel native presentation |
| Bounded capture and rollback | 64 binding/geometry entries; stale/reordered/overflow checks; optional-render failure leaves working forcing/observation |
| NRO/imports/relocations/instruction audit | 57,344 bytes, BSS 69,632; actual installed Forge/SDK exports; no forbidden APSR_g/nzcvqg or GE writes |
| Runtime allocation limits | Existing one 4KiB arena, one TLS slot, eight contexts/four scopes; no additional hooks or owned heap buffer |
| Candidate/package verification | Deterministic one-member ZIP, CRC/member readback, sources/support/checksums verified |
| Whitespace/full distribution checker | Passed; eight records; DEVELOPMENT retained |

All 74 recorded R1-R7 candidate files retain their hashes. Commits R4 `f789cbb`,
R6 `d9aba55` and R7 `ae7b2c3` remain preserved. Maintained Forge stays clean on
`codex/forge-legacyctx14`, commit `b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d`.
Installed Forge/Better Input retain hashes
`9d472d56f81f834f366171426dbd0131af19c7697e132c731c3fd3f335af53d0` /
`400a8881065b5736debfdd88d167141b624671906187b9460e1a2fd267497f5f`.
Installed R7 is untouched. No installation, activation, game launch, existing
settings/save edit, push or publication occurred.

Actual R8 visible alignment remains pending. Natural positive luck/no luck,
forced mode/live toggles, repeated grids, collection/cursor/animation/village
return, restart persistence, Eden multicore/translation and Ryujinx remain in
MANUAL_TESTS.md. Successful flushes do not prove translation freshness. Unknown
render paths remain suppressed. The second site's broader role remains partly
traced. Crafting, unlocks, inventory edits and collection tracking are excluded.

See [cause and repair](R8_HIGHLIGHTS.md).
