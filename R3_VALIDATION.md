# R3 local validation

Prepared 2026-10-07. Status: DEVELOPMENT. R3 gameplay NOT RUN.
R2's user-reported Unavailable observation during rewards remains unresolved.
R3 adds execution/publication/clearing counters; it is not a confirmed fix.

NRO SHA-256: `c7c6e4b24ac2205f3528e77a311aa91579a9fcdedbc1f4e5a8607069af64af37`.
ZIP SHA-256: `8360e35e2205858f57d9e4291e1fe48b0ad8e35706742cdba1efaa19b4ff7d70`.

Local results:

| Check | Result |
|---|---|
| Host transaction/backend/preferences/attribution/hooks | 43 / 21 / 74 / 1,547 / 41 passed |
| Compiled ARM cheat continuations and six SVC ABIs | 2,122 passed |
| Compiled runtime/gateway/TLS/settings/UI fixtures | 100,508 passed, including four counter checks |
| Conditional GPR/NZCVQ/GE/VFP preservation | 8,192 cases within runtime suite |
| Full native reward-count/selector RNG comparisons | 1,092 cases within runtime suite |
| Original native copies/world quads | 388 passed; screen transform gate remains incomplete |
| Pinned main/signatures, installed imports, relocations, allocation limits, forbidden APSR/GE audit | Passed |
| Candidate inventory, ZIP member bytes, support/checksums, deterministic payload | Passed |
| Full distribution checker and whitespace | Passed; DEVELOPMENT retained |

Fixtures use fake kernel, filesystem and ImGui with pinned native ARM routines;
they do not establish Eden gateway execution, CPU translation freshness,
multicore behavior, gameplay effectiveness or final screen geometry.
No border renderer or complete screen transform is accepted.

R1 and r2 candidate inventories/checksums are preserved. R2 installed NRO is
`5e7c5d78e97fde875798004cbf4f12d002335e320e4ccd54ebec8b67e1b5394a`.
Maintained Forge source and installed Forge/Better Input are checked unchanged.

No installation, activation, launch, save/preference edit, push or publication
is part of preparing this candidate. See R3_DIAGNOSTICS.md for runtime evidence
and remaining investigation, and MANUAL_TESTS.md for pending gameplay coverage.
