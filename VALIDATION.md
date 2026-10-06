# R2 local validation

Recorded 2026-10-06. Status: DEVELOPMENT; gameplay NOT RUN.
Mode/settings and bounded attribution are implemented. **Highlighting is incomplete:**
final display transformation and complete copy/node mappings have not passed the
research gate. The candidate draws no border or luck marker.

NRO: 36,864 bytes, with 49,152 bytes of loader BSS. One pooled 4 KiB CodeMemory
arena and one native TLS slot; zero plugin-owned heap allocations.
NRO SHA-256: `5e7c5d78e97fde875798004cbf4f12d002335e320e4ccd54ebec8b67e1b5394a`.
ZIP SHA-256: `cf694d4cd20818c93bbcb48a85bef24a9f81618712023288d2f632af9837f1c6`.

| Local check | Result |
|---|---|
| Pinned main SHA/full NSO build-ID field/segment hashes; all 17 windows | Passed |
| Cheat branches and retained second-site 0x102 continuation | Passed |
| R1 transaction/backend regression | 43 + 21 passed |
| Settings format, delayed load/edit cancellation and recovery | 74 passed |
| Attribution boundaries, minimum-one/cap-eight and duplicate provenance | 1,547 passed |
| R2 guarded publication/ownership rollback and arena retention | 41 passed |
| ASan/UBSan | Passed; LeakSanitizer disabled under host ptrace |
| Source-cheat MOV/continuations and six compiled SVC ABIs, success/failure | 2,122 passed |
| Compiled startup/gateways/TLS/scopes/copies/settings/UI fixtures | 100,504 passed |
| Conditional gateway GPR/flags/VFP cases | 8,192; original hasSkill executed |
| All seven comparison taps | Native GPR/flags compared across tiers/rolls/GE |
| Full native count/selector execution and consumed RNG stream | 1,092 original/cheat comparisons |
| Original UI/list copies and world quads | 388 passed |
| NRO format/callbacks/relocations/ARM32 ABI; installed Forge + pinned SDK imports | Passed |
| GE-writing arithmetic, forbidden APSR restoration, dynamic constructors | None |
| Screen transform, complete node/category mapping, border renderer | **Unverified / unimplemented** |
| Eden/Ryujinx gameplay/GPU/cache freshness/multicore | **Not run** |

Fixtures use fake kernel/filesystem/ImGui, synthetic thread storage and native
ARM bytes in Unicorn 2.1.4. Settings touch in-memory fake files only. Native copies
stop before allocation/free/refresh callbacks. World quads do not prove final
placement, clipping, cursor overlap or shader equations.

The ZIP contains only the NRO in its named runtime package. Support, manifest and
checksums are adjacent. Reopen/CRC/member bytes and deterministic rebuild are
checked. The full distribution checker passes eight records; this plugin remains
DEVELOPMENT. No distribution readiness or gameplay effect is established.

R1 source commit `d01c9c3` and candidate bytes are preserved:
NRO `d82fa6155e5b542e18bae4796b94f822b7b4b3c4245ec6cdc18a2030af2d40a4`;
ZIP `99f866e798d3702fe9e2a28a8b52c37a87f8dd57c579f2d04fdd0dd0e84fefa0`.

Maintained Forge stays clean on codex/forge-legacyctx14 at
`b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d`.
Installed Eden Forge:
`9d472d56f81f834f366171426dbd0131af19c7697e132c731c3fd3f335af53d0`.
Installed base Better Input:
`400a8881065b5736debfdd88d167141b624671906187b9460e1a2fd267497f5f`.
The build rechecks these before/after; bytes/folder presence do not prove activation.

No Forge source, installed package, emulator, save or existing preference was edited.
There was no installation, activation, launch, push or publication. Remaining
research is in [RESEARCH.md](RESEARCH.md), with gameplay in
[MANUAL_TESTS.md](MANUAL_TESTS.md). This candidate does not implement the complete
r2 visual feature.
