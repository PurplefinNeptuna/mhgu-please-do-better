# R6 local validation

Prepared 2026-10-07. DEVELOPMENT. R6 GPU/gameplay NOT RUN.

NRO SHA-256: `07492e80d26684a47a424458aca943254bd7118dbc841b34fed07aceebfc609a`.
ZIP SHA-256: `cd2fed92eec33d46f9324ad8a78610adb011dcf8168aa01f176553800701249f`.
Candidate: `build/please-do-better/candidates/r6/please-do-better-r6-candidate.zip`.
Only member: `Please do Better/romfs/nativeNX/plugins/please_do_better.nro`.

| Local check | Result |
|---|---|
| Host transactions/backend/preferences/attribution/hooks | 43 / 21 / 74 / 1,993 / 48 checks passed |
| Host highlight layouts/transform/atomic publication | Passed under ASan/UBSan; bounded concurrent snapshot fixture |
| Compiled ARM continuations and six SVC ABIs | 2,122 checks passed |
| Compiled modes/RNG/settings/startup/gateway regressions | 100,516 checks passed |
| Original native copy/world-quad helpers | 388 checks passed |
| Compiled observation/native count-copy paths | 28,841 checks; 4,096 copy state cases; 288 original count/copy batches |
| Native display/collection/remapping and compact panel | 16,611 checks; 4,096 LDR/AND state cases; balanced closed/open trees |
| Gold capture/presentation/draw-call fixtures | 6,544 checks; 1,024 active geometry and 1,024 active present state cases |
| Frame-node identity | 96 original GUI ordinals, 162 compiled group instances; exact batch/list/index/node identity |
| Shader/viewport proof | Exhaustive 6,311-program metadata scan; twelve 2D position programs verified; perspective program rejected |
| Native frame order | Original begin/executor fragments in both modes and both buffer indices; compiled native present wrapper |
| Rendering behavior | Native clip push/pop, 1.5px scaled border, two-second gold pulse, procedural sparkle; no fills |
| Lifetime and bounded capture | Duplicate IDs, quantity decrease, empty slots, wrong identities, stale/reordered frames, real 64-sample overflow; previous valid frame retained |
| Hook safety | Rendering signature conflicts/flush failures leave working modes and observation; common write/readback/owned rollback/foreign edit/residual failure fixtures; core ownership loss also invalidates rendering |
| NRO/ABI/imports | 53,248 bytes, BSS 69,632; one existing 4KiB arena and one TLS slot; no new arena/TLS/owned heap buffers |
| Register audit | GPR, SP/LR, d0-d31/FPSCR and every NZCVQ/GE pattern preserved; no APSR_g/nzcvqg or GE-writing helper instruction |
| Package/source verification | Deterministic ZIP, one member, CRC/readback, imports against installed Forge/SDK exports, ARM relocations and source/support/checksums verified |
| Full distribution checker / whitespace | Passed; all eight records; DEVELOPMENT retained |

## Preservation and runtime limits

All 52 recorded r1-r5 candidate files retain their original hashes. Accepted r4
commit `f789cbb` and r5 commit `fe87ff1` are preserved in history. Maintained Forge
branch `codex/forge-legacyctx14`, commit `b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d`,
remains clean. Installed Forge and Better Input still match their baseline hashes.
Preparation wrote no installed package, real save/settings or activation state,
and launched no game. No push, publication or distribution promotion occurred.

During final readback, the installed Please do Better file had hash
`0e34f52e6b8488b273eee1a8e6452529def3f052959e842174253a675a684ffe`, matching
an earlier intermediate build. It was left untouched and differs from this final
candidate. Folder presence is not activation or runtime acceptance. R4's retained
user screenshots/log support forced observation only, not this renderer.

The CPU fixtures verify compiled draw calls, native instruction behavior and
shader dataflow. They do not execute a GPU or establish visible alignment.
Natural positive luck, no luck, forced mode, toggles, repeated grids, animation/
cursor alignment, collection/village return, restart persistence, Eden multicore/
translation freshness and Ryujinx remain pending in MANUAL_TESTS.md. Alternate
constructors, unknown groups/shaders, half/offset targets and uncertain frames
are suppressed. No collection tracking, crafting/unlocks or inventory changes.

Research and implementation details: [R6_HIGHLIGHTS.md](R6_HIGHLIGHTS.md).
