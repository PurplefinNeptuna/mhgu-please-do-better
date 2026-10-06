# R4 local validation

Prepared 2026-10-07. Status DEVELOPMENT. R4 gameplay NOT RUN.

NRO SHA-256: `498daa485beb2b8128cd31e0304ca1d11b5cdd2ec059d946fdd3fc2cea852699`.
ZIP SHA-256: `18f781d3e33f9aaddd70488369316c901b5fc833b8a9c1f5b999906d66117b12`.
Candidate: `build/please-do-better/candidates/r4/please-do-better-r4-candidate.zip`.
Its only member is `Please do Better/romfs/nativeNX/plugins/please_do_better.nro`.

| Local check | Result |
|---|---|
| Host transaction/backend/preferences/attribution/hooks | 43 / 21 / 74 / 1,672 / 41 passed |
| Compiled ARM cheat continuations and six SVC ABIs | 2,122 passed |
| Compiled runtime/gateway/TLS/settings/UI fixtures | 100,516 passed |
| Conditional GPR/NZCVQ/GE/VFP preservation | 8,192 cases in runtime suite |
| Full native count/selector RNG equivalence | 1,092 cases in runtime suite |
| Original native copies/world quads | 388 passed; final screen transform remains unverified |
| New compiled observation fixtures | 28,841 passed |
| Four copy gateway GPR/NZCVQ/GE/SP/LR/VFP/FPSCR audits | 4,096 cases in observation suite |
| Initial-count gateway MOV/CMP and state preservation | 5,120 cases in observation suite |
| Native count/selector and compiled capture with exact native copies | 288 batches across four routes, all six tiers, guarantees, stops and cap eight |
| No generator-hook regression | Forced threshold 31 and two extras published with zero generator returns |
| Missing counts/initial/comparison taps, unknown callers, query failures, malformed prefixes and changed destinations | Incomplete or unavailable; never verified zero-bonus coverage |
| Secondary return ABI / absent tables | Void return ignored; empty table validates an empty batch |
| State 18, collection/close and publication overflow | Completed totals retained; live provenance cleared; loss reports incomplete |
| New-site conflicts and final publication flush failures | Safe rejection/rollback retains natural conditional pair; existing unsafe-rollback fixture passes |
| Offline main/signatures, installed exports, NRO relocations, resource limits, forbidden APSR/GE audit | Passed |
| Repeated pinned build, ZIP inventory/member readback, adjacent support/manifest/checksums | Passed; identical NRO and ZIP |
| Full distribution checker and whitespace | Passed; DEVELOPMENT retained |

Fixtures use a fake kernel, TLS thread storage, filesystem and ImGui. Native
counters, selector and copy fragments execute; reward item selection supplies
controlled prefixes, and the full UI builder's scope is entered/left by fixtures.
These tests do not establish Eden translation freshness, multicore behavior,
complete runtime route coverage, gameplay rewards or Ryujinx compatibility.
Highlights remain unimplemented. Gameplay confirmation of added rewards comes
before any rendering work; final display geometry is also pending.

NRO: 40,960 bytes; fixed BSS: 57,344 bytes. Twenty-two detours, eight callable
originals in one 4 KiB arena, one TLS slot, eight contexts and four nested scopes
remain bounded. No heap allocations or additional arenas are introduced.

R1/r2/r3 complete candidate inventories remain unchanged (30 files). Maintained
Forge branch `codex/forge-legacyctx14`, commit
`b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d`, remains clean. Installed Eden Forge
and Better Input match their maintained fingerprints. Installed Please do Better
still matches r3, `c7c6e4b24ac2205f3528e77a311aa91579a9fcdedbc1f4e5a8607069af64af37`.

R3 gameplay evidence and its limits are recorded in R4_OBSERVATIONS.md. Retained
log SHA-256: `31dd041bfff11644a27a0f7492521638ecb0747341eb8e0277952fb57e25f104`;
screenshot SHA-256: `e8fb0e667405762f964eeeed1b070a8cec83321816d159f3ce9d6dbfb1ccaae8`.

No r4 installation, activation, launch, existing save/settings edit, push or
publication is part of this preparation. See MANUAL_TESTS.md for the separately
authorized gameplay checks still required.
