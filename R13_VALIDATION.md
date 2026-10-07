# R13 local validation

Prepared 2026-10-07. DEVELOPMENT. R12's matching user grid/log confirm the
scissor correction and 15,360 geometry publications, followed by source/acquired
texture mismatch. R13 adds an observed native whole-texture downsample route,
requiring exact provenance, frame, owner, screen fence, size and acquired image.
No visible r13 GPU/gameplay success is claimed.

Candidate: `build/please-do-better/candidates/r13/please-do-better-r13-candidate.zip`.
Only member: `Please do Better/romfs/nativeNX/plugins/please_do_better.nro`.
NRO SHA-256: `026e0af2bcfd1b5d04170ebac454e830e38f8887e79c43f55567834a8f178932`.
ZIP SHA-256: `8e86ae6ccd674e055712d723d0cab8f28dc9c8aeb313c0c318c81a7419788626`.

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
| Native/compiled transfer | 6,238 passed; original equal/differing-format same-size branches reach the untouched NVN callback after the compiled detour; 12 direct/parallel/alternating-image cases |
| Transfer rejection | No observed route, wrong acquired image, view, callback, command buffer, mode, extent, format, source; stale frame/serial/fence/owner/source/destination/size; screen exit and snapshot contention all suppressed |
| New transfer gateway state | 2,048 active flag/GE/stack-alignment cases; exact argument replay; all GPR/SP/LR, VFP/FPSCR, NZCVQ/GE preserved |
| Existing rendering gateway state | 1,024 active geometry plus 1,024 present cases passed |
| Rendering installation failure | Either new-site conflict preserves safe forcing/observation; each rendering-site flush failure restores all four rendering detours |
| Log safety/ABI | 115 checks, 23 formats; conservative maximum 401 bytes inside Forge's 520-byte buffer; callback formatting only, compact panel, bounded output |
| Resource/instruction receipts | 96 ordinals / 162 groups; 13 reflected lists, 12 XY/W=1 shaders; 45 function receipts including NVN initializer; callback GOT/string identity verified |
| NRO/imports/relocations/instruction audit | 73,728 bytes, BSS 69,632; installed export match; no forbidden APSR/GE writes |
| Resource limits | One 4KiB arena, one native TLS slot, eight contexts/four scopes, 64 binding/geometry entries; two fixed transfer snapshots; no heap allocation or extra arena/TLS |

New transfer tests execute the original CPU branch and stub only the external
void NVN command callback to inspect its arguments. They do not execute a GPU.
The observer runs before that unchanged callback; source-to-image enqueue-path
identity does not prove GPU completion or visible alignment. Unsupported
composition/copy routes remain suppressed. Scissor and direct-image rendering
regressions continue to pass. Settings, RNG and rewards are unchanged.

Package/member readback/checksums, whitespace and the full eight-mod distribution
check passed. R12 commit `05beec0` and all 129 recorded R1-R12 candidate
files are preserved. Maintained Forge remains clean at
`b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d` on `codex/forge-legacyctx14`.
Installed Forge/Better Input remain:
`9d472d56f81f834f366171426dbd0131af19c7697e132c731c3fd3f335af53d0` /
`400a8881065b5736debfdd88d167141b624671906187b9460e1a2fd267497f5f`.
Installed r12 remains `b44ae46e23398714eb3a1d20c7d0d1da8a1ada8ea023d9175f9863b6d8a956e5`.
No installation, activation, launch, existing save/settings edits, emulator
changes, push or publication is included. Visible borders/sparkles, cursor and
animation alignment, natural positive luck/no luck, live modes, repeated grids,
collection/transitions/restart, Eden multicore/translation and Ryujinx remain
pending in MANUAL_TESTS.md. DEVELOPMENT continues.
