# R11 local validation

Prepared 2026-10-07. DEVELOPMENT. The supplied r10 grid confirms four bound
extras but zero visible markers, with no reported draw rejection. R11 verbose
gate logging is user-authorized; the runtime stopping point and visible
highlights remain unverified. No draw-acceptance guard is relaxed.

Candidate: `build/please-do-better/candidates/r11/please-do-better-r11-candidate.zip`.
Only member: `Please do Better/romfs/nativeNX/plugins/please_do_better.nro`.
NRO SHA-256: `60ef558e5df153e4321edbc6cafcd076be83968ddeae680be1e4ed7bf5904b09`.
ZIP SHA-256: `e340c1308d50321f007662e02aceafe931c58a4e8f23646c6fce367072e18b8f`.

| Local check | Result |
|---|---|
| Host transaction/backend/settings/attribution/hooks | 43 / 21 / 74 / 1,993 / 48 passed |
| Host geometry/immutable concurrent snapshots | 728 passed; ASan/UBSan |
| Compiled ARM continuations/SVC ABI | 2,122 passed |
| Compiled mode/RNG/settings/startup/gateways | 100,516 passed |
| Original native copy/world-quad/viewport/texture/view | 498 passed; 80 viewport/clip and 30 texture/resource/view fragments |
| Compiled count/copy observations | 28,841 passed; 288 native batches |
| Display/relocation/collection/compact UI | 16,634 passed |
| Compiled geometry/presentation/render/logging | 7,704 passed |
| Gateway state preservation | 1,024 active geometry and 1,024 present cases; GPR/SP/LR, VFP/FPSCR, NZCVQ/GE |
| Log text safety | 100 checks, 20 formats; maximum conservative bound 401 bytes inside Forge's 520-byte buffer |
| Compiled logging ABI and bounds | Actual ARM softfp double/ll alignment, exact image/dimensions, eight initial bundles, callback 120, per-screen/process caps, nonblocking contention and lock release passed |
| Panel/gateway separation | No logging/formatting in native gateways; no raw render addresses, viewport or shader lists in ImGui; balanced trees |
| Resource/shader receipts | 96 ordinals / 162 groups; 13 reflected lists, 12 XY/W=1 shaders; 44 original function receipts |
| NRO/imports/relocations/instruction audit | 73,728 bytes, BSS 69,632; actual installed exports; no forbidden APSR/GE writes |
| Allocation/resource limits | One 4KiB arena, one native TLS slot, eight contexts/four scopes, 64 binding/geometry entries; no plugin heap allocation or new hook |
| Package/checksums/whitespace/full distribution checker | Passed; deterministic single-member ZIP, member readback and full eight-mod check |

The static NRO budget increased from 64KiB to 80KiB for bounded trace code and
format strings. BSS ceiling, arena/TLS counts and heap restrictions are unchanged.
The ARM fixture now maps the actual NRO plus BSS rather than assuming a 64KiB
code image. All preservation fixtures still reach their exact continuations.

All 107 recorded R1-R10 candidate files retain their hashes. R10 commit
`7b6676911cfda2b7af897df378559732b7598c30` and accepted prior commits are preserved.
Maintained Forge stays clean on `codex/forge-legacyctx14`, commit
`b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d`. Installed Forge/Better Input:
`9d472d56f81f834f366171426dbd0131af19c7697e132c731c3fd3f335af53d0` /
`400a8881065b5736debfdd88d167141b624671906187b9460e1a2fd267497f5f`.
Installed R10 is preserved. No installation, activation, launch, emulator setting
change, real save/settings edit, push or publication occurred. No native Switch or
Ryujinx runtime claim is made. Logs describe CPU decisions and do not prove GPU
execution or visible alignment. See R11_RENDER_LOGGING.md and MANUAL_TESTS.md.
