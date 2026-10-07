# R12 local validation

Prepared 2026-10-07. DEVELOPMENT. The r11 user grid/log isolate empty clipping
as the immediate rejection: 16,653 matched captures stopped there and no geometry
was published. R12 corrects the missing native shared-sentinel comparison and
viewport substitution. The exact raw r11 scissor was not logged. No visible
r12 gameplay/GPU claim is made.

Candidate: `build/please-do-better/candidates/r12/please-do-better-r12-candidate.zip`.
Only member: `Please do Better/romfs/nativeNX/plugins/please_do_better.nro`.
NRO SHA-256: `b44ae46e23398714eb3a1d20c7d0d1da8a1ada8ea023d9175f9863b6d8a956e5`.
ZIP SHA-256: `256595ef5165219a33baa8c896674962027ce9aa9aab79f19f0dcaf115c19af8`.

| Local check | Result |
|---|---|
| Host transaction/backend/settings/attribution/hooks | 43 / 21 / 74 / 1,993 / 48 passed |
| Host geometry/immutable concurrent snapshots | 728 passed; ASan/UBSan |
| Compiled ARM continuations/SVC ABI | 2,122 passed |
| Compiled mode/RNG/settings/startup/gateways | 100,516 passed |
| Original native copy/world-quad/viewport/texture/view | 678 passed, including 180 complete scissor/sentinel cases and 80 viewport/intersection checks |
| Compiled count/copy observations | 28,841 passed; 288 native batches |
| Display/relocation/collection/compact UI | 16,634 passed |
| Compiled geometry/presentation/render/logging | 7,819 passed |
| Original versus compiled clipping | 36 cases; both banks, zero/nonzero sentinels, explicit/empty/inverted/outside clips; unreadable pointer suppressed |
| Reported input regression | R11 logged vertices/model/projection plus native default-scissor semantics produce the exact gold perimeter and full viewport clip |
| Native copied extras regression | Four exact copied bonus slots produce borders/sparkles with default scissor; no fixture-injected binding records |
| Gateway state preservation | 1,024 active geometry and 1,024 present cases; GPR/SP/LR, VFP/FPSCR, NZCVQ/GE |
| Log safety/ABI | 110 checks, 22 formats; maximum conservative bound 401 bytes within Forge's 520-byte buffer; exact raw/runtime-sentinel/effective clipping args checked |
| Panel/gateway separation | No formatter/logger in native gateways; compact panel and balanced trees; bounded callback logging |
| Resource/instruction receipts | 96 ordinals / 162 groups; 13 reflected lists, 12 XY/W=1 shaders; 44 original function receipts; GOT/literal identity checked |
| NRO/imports/relocations/instruction audit | 73,728 bytes, BSS 69,632; actual installed exports; no forbidden APSR/GE writes |
| Allocation limits | One 4KiB arena, one native TLS slot, eight contexts/four scopes, 64 binding/geometry entries; no plugin heap allocation or new hook |

Package inventory/member readback/checksums, whitespace and full eight-mod
distribution checks passed. Deterministic ZIP contains one runtime
NRO; support and evidence remain adjacent. All 118 recorded R1-R11 candidate
files and r11 commit `0d85b77` are preserved.

Maintained Forge stays clean on `codex/forge-legacyctx14`, commit
`b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d`. Installed Forge/Better Input:
`9d472d56f81f834f366171426dbd0131af19c7697e132c731c3fd3f335af53d0` /
`400a8881065b5736debfdd88d167141b624671906187b9460e1a2fd267497f5f`.
Installed r11 remains `60ef558e5df153e4321edbc6cafcd076be83968ddeae680be1e4ed7bf5904b09`.
No installation, activation, launch, emulator setting change, real save/settings
edit, push or publication is included. Eden visible alignment, natural positive
luck/no luck, mode toggles, repeated grids/collection/village return/restart,
multicore/translation freshness and Ryujinx remain pending in MANUAL_TESTS.md.
