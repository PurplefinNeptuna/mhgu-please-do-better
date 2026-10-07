# R15 release validation

Prepared 2026-10-07. User-approved local distribution, logging-only cleanup of
accepted r14. R14 has visible Eden acceptance; r15 has no separate gameplay run.
The known Forge menu/background-overlay corruption remains unresolved.

NRO SHA-256: 778346ad53b1cb846e33859b37ca7e801660140710d894314d37f76d3cd34249.
Candidate ZIP SHA-256: 9db9c8f19ae9be3927a90c4c6a2df9bc465c66527d1f679c4cc84f5a749fb3ba.
Release ZIP SHA-256: 284edab6220e9a80e94d3583a3d6dfeda18cd56b3be5899b4404a4e52ec1e130.
Release: build/please-do-better/releases/r15/please-do-better-r15.zip.
Only member: please-do-better/romfs/nativeNX/plugins/please_do_better.nro.
The display name remains Please do Better; the named release package uses the
shared distribution convention. The candidate wrapper remains historical.

| Local validation | Result |
|---|---|
| Host transaction/backend/settings/attribution/hooks | 43 / 21 / 74 / 1,993 / 48 passed |
| Host geometry/publications | 728 passed, ASan/UBSan |
| Compiled ARM continuations/SVC ABI | 2,122 passed |
| Compiled runtime/mode/RNG/settings/gateways | 100,516 passed |
| Native copy/world-quad/viewport | 678 passed |
| Compiled observation | 28,841 passed, 288 native count/copy batches |
| Compiled display/collection/compact panel | 16,634 passed |
| Compiled geometry/presentation/gold overlay | 8,286 passed; 160 resource mappings, 36 native clip cases and four native frame cases |
| State preservation | 1,024 active geometry plus 1,024 presentation flag/GE/stack/VFP/FPSCR cases |
| Quiet successful rendering | 240 complete capture/present/render boundaries continue drawing with zero new log records |
| Release log scope | Four formats only; startup and one concise suppression code per class/screen; no verbose formats in the compiled NRO; 20 buffer-bound checks |
| Native/shader/resource receipts | 45 functions, 96 ordinals/162 groups, 13 reflected GUI lists and 12 supported XY/W=1 shaders |
| NRO/import/relocation/ABI audit | 65,536 bytes, BSS 69,632; actual installed exports and supported ARM relocations/SVCs; zero forbidden APSR/GE writes |
| Allocation limits | One pooled 4KiB arena, one TLS slot, eight contexts/four scopes, 64 binding/geometry samples, no heap allocation |

Recipe handles pinned read-only shared input symlinks in a managed worktree;
no Forge source or installed payload changes. Rendering, hooks, forcing,
preferences and reward behavior are retained; logging is the runtime change.
R14 commit 1888454 and all 151 prior candidate files remain unchanged.
Maintained Forge remains clean at b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d.
Installed Forge/Better Input hashes remain 9d472d56f81f834f366171426dbd0131af19c7697e132c731c3fd3f335af53d0 /
400a8881065b5736debfdd88d167141b624671906187b9460e1a2fd267497f5f.
Installed r14 remains e0d21d9fc848d425745833fe813fef638e6f118b37d9127757dec8099929c3e0.

Candidate/release inventory, member readback, checksum and full eight-mod
distribution checks passed. User-approved distribution is separate
from testing: broader natural/no-luck, modes, settings/restart, repeated rewards,
collection/transitions/animation, Eden multicore/translation and Ryujinx remain
pending. No installation, activation, launch, save/settings edit, push or publication.
See RUNTIME.md, R15_RELEASE.md and MANUAL_TESTS.md for scope and limitations.
