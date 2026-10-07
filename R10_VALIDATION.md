# R10 local validation

Prepared 2026-10-07. DEVELOPMENT. R9 user-run observation/binding is confirmed
for the supplied grid; visible highlights failed. Its log confirms a supported
shader rejected by descriptor identity. R10 gameplay remains pending.
Candidate: `build/please-do-better/candidates/r10/please-do-better-r10-candidate.zip`.
Only member: `Please do Better/romfs/nativeNX/plugins/please_do_better.nro`.

NRO SHA-256: `9a415d34045f384754b4816ad8c16f005a9112b7834c3fcfc6c4138867dd57c8`.
ZIP SHA-256: `8fe9f35d47033df5fa2af0da2d00ccedab3baee6063ead4ac6490e73809976f9`.

R10 fixtures accept equal NVN texture identity with different descriptors,
alternating acquired images, and immutable previous-frame image identity despite
producer mutation. They reject offscreen images, invalid acquired index/cache/
resource tables, null NVN image fields, stale frames and unsupported texture
views. First-rejection values remain stable until a new screen fence; the
compact panel balances every opened tree. Independent original ARM fragments
verify default descriptor resolution, resource-to-texture conversion at all
three window constructor entries, acquired-resource/index caching and the
default/nondefault surface-view branch.

| Local check | Result |
|---|---|
| Host transaction/backend/settings/attribution/hooks | 43 / 21 / 74 / 1,993 / 48 passed |
| Host geometry/immutable concurrent snapshots | 728 passed; ASan/UBSan |
| Compiled ARM continuations/SVC ABI | 2,122 passed |
| Compiled mode/RNG/settings/startup/gateways | 100,516 passed |
| Original native copies/world quads/viewport/image identity | 498 passed; 80 viewport/clip and 30 texture/resource/view fragments |
| Compiled count/copy observations | 28,841 passed; 288 native batches |
| Display/relocation/initialization/compact UI | 16,634 passed |
| Compiled geometry/presentation/gold/rejection | 7,677 passed; stable rejection, image alternation/mismatch, acquired metadata and immutable previous-frame image |
| Gateway state preservation | 1,024 active geometry and 1,024 present cases; GPR/SP/LR, VFP/FPSCR, NZCVQ/GE |
| Resource/shader receipts | 96 ordinals / 162 group instances; 13 exact native reflected lists, 12 XY/W=1 shaders; 44 original function receipts |
| NRO/imports/relocations/instruction audit | 61,440 bytes, BSS 69,632; actual installed Forge/SDK exports; no forbidden APSR/GE writes |
| Allocation limits | One 4KiB arena, one native TLS slot, eight contexts/four scopes, 64 binding/geometry entries; no added arena or heap allocation |
| Package/checksums/whitespace/full distribution checker | Passed; deterministic single-member ZIP, readback/checksums, whitespace and eight-mod distribution check |

The geometry state sweep now explicitly checks arrival at the displaced
continuation before comparing state. The fixture instruction budget increased
because the larger immutable snapshots require more CPU instructions with a
full capture pool; an exhausted Unicorn budget is not a state-preservation
result. Every case reaches the continuation and passes its state comparison.

All 96 recorded R1-R9 files retain their hashes. R9 commit `15fc343` and
prior accepted commits stay preserved. Maintained Forge stays clean on
`codex/forge-legacyctx14`, commit `b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d`.
Installed Forge/Better Input:
`9d472d56f81f834f366171426dbd0131af19c7697e132c731c3fd3f335af53d0` /
`400a8881065b5736debfdd88d167141b624671906187b9460e1a2fd267497f5f`.
Installed R9 is unchanged. No install/activation/launch/save or settings
edits or push/publication occurred. CPU fixtures do not prove GPU compositing,
visibility/alignment or the actual runtime image identity in the user's grid.

See R10_HIGHLIGHTS.md and MANUAL_TESTS.md for pending gameplay coverage.
