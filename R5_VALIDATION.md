# R5 local validation

Prepared 2026-10-07. Status DEVELOPMENT. R5 gameplay NOT RUN.

NRO SHA-256: `7c8174e48024e26ffb7ac6cb1fcefbaf4782c9f6678a274e35cb838a6f422093`.
ZIP SHA-256: `9f30b5e389641178e2508a2b4e981db88f1f2256aa204084ec1b228f4a900d30`.
Candidate: `build/please-do-better/candidates/r5/please-do-better-r5-candidate.zip`.
Only member: `Please do Better/romfs/nativeNX/plugins/please_do_better.nro`.

| Local check | Result |
|---|---|
| Host transaction/backend/preferences/attribution/hooks | 43 / 21 / 74 / 1,993 / 48 passed |
| Compiled ARM continuations and six SVC ABIs | 2,122 passed |
| Compiled runtime/gateway/TLS/mode/RNG/settings fixtures | 100,516 passed; includes 8,192 conditional preservation and 1,092 native RNG cases |
| Existing native copy/world-quad fixtures | 388 passed; world quads do not establish screen placement |
| Existing compiled observation fixtures | 28,841 passed; four copy routes, all tiers and missing/conflicting capture cases |
| New compiled boundary/display-copy/collection/panel fixtures | 16,611 passed |
| Proposed draw-boundary state preservation | 4,096 cases; exact LDR/AND, GPR/SP/LR/NZCVQ/GE/VFP/FPSCR outputs; never installed |
| Native state-1 reallocation prefix loops | Capacities 16/48 and main A/B offsets; old allocation poisoned before observer return |
| Reallocation failures and stale epochs | Changed copy, unmapped pointer, invalid/short capacity suppress live provenance; identity/stale publications never invent mapping |
| Native collection/refresh | Four original emptying paths, quantity subtraction, eight repeated collected-slot refreshes; no false faults; incompatible entries still fault |
| Native group and holder lookup | 16 group calculations with stride 0x28; 33 holder/index cases including absent node table; icon nodes only |
| Native CPU scissor | 36 scale/offset/intersection cases including inverted/outside rectangles; not framebuffer correspondence |
| Row/category subarray, duplicates, screen exit and destruction | Exact source-relative indices retained or invalidated; completed generation totals retained |
| Compact UI | Both trees balanced for all open/closed combinations; raw counters/masks absent; unsafe startup still reported |
| Separate optional-boundary transaction | Rejection, write/flush failure, owned rollback, foreign edit and failed rollback preserve core hooks; no extra arena |
| Read-only native trace receipts | 15 requested functions; original bytes match pinned main; shader hashes and SPK bounds checked; rendering gate closed |
| Offline main/signatures, exports/imports, NRO relocations, resources and forbidden APSR/GE audit | Passed |
| Repeated pinned build, deterministic ZIP, member readback, support/manifest/checksums | Identical NRO and ZIP; passed |
| Full distribution checker and whitespace validation | Passed; DEVELOPMENT retained |

NRO: 40,960 bytes; fixed BSS: 57,344 bytes. Twenty-two installed detours,
eight callable originals in the existing single 4 KiB arena, one TLS slot, eight
contexts and four nested scopes remain unchanged. No heap allocation, geometry
publication or additional hook is enabled. The geometry gateway is compiled for
fixtures only. Settings formats/filenames and live mode behavior remain unchanged.

All 41 files in the r1/r2/r3/r4 candidate inventories were rehashed unchanged.
R4 source commit `f789cbb` remains in history. Maintained Forge branch
`codex/forge-legacyctx14`, commit `b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d`,
remains clean. Installed Forge/Better Input fingerprints match the maintained
record; installed Please do Better still matches accepted r4.

Retained r4 launch log SHA-256:
`ddd617bffafc5c9c25facbfd728ab6d8d5a625b6aec0bf0ae1d96fac69eb9852`.
Reward-grid screenshot SHA-256:
`e5e1e76271fab76d5fc88670332c8d8637ff08ad0771a8ddca5c2ca81cb9c9db`.
Village screenshot SHA-256:
`19110d21693c994388859d465055234c723c35598c9ec3df6a779d9d8d1fc9f7`.
The two screenshots do not identify the eight historical fault events individually.
R5 reproduces the strict-equality false-fault cause; it does not claim that every
historical drop is explained. Genuine faults remain visible.

Fixtures execute compiled plugin code and selected original ARM functions with
synthetic kernel/TLS/filesystem/ImGui/native tables. Allocation/free, full UI
construction, item selection and GPU submission are outside those fixtures.
They do not establish runtime route coverage, natural-luck highlights, gameplay
alignment, Eden translation freshness/multicore behavior or Ryujinx compatibility.

Gold rendering remains unimplemented: see RESEARCH.md for the three failed proof
gates. No installation, activation, launch, existing save/settings edit, push or
publication is included. See MANUAL_TESTS.md for pending gameplay coverage.
