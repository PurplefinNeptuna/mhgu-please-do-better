# R1 local validation

Recorded 2026-10-06. Status: DEVELOPMENT; runtime NOT RUN.

The local candidate is 12,288 bytes (12 KiB), with 4,096 bytes of page-aligned
loader BSS. It adds zero CodeMemory objects and no plugin-owned heap allocations.
NRO SHA-256: `d82fa6155e5b542e18bae4796b94f822b7b4b3c4245ec6cdc18a2030af2d40a4`.
ZIP SHA-256: `99f866e798d3702fe9e2a28a8b52c37a87f8dd57c579f2d04fdd0dd0e84fefa0`.

| Check | Result |
|---|---|
| Original NSO SHA/build ID, segment hashes and both 32-byte signatures | Passed |
| Exact two-site cheat and retained `0x102` continuation | Passed |
| Production transaction host failure/ownership scenarios | 43 passed |
| Production native backend with fake kernel | 21 passed |
| ASan and UBSan | Passed; LeakSanitizer disabled because the host sandbox uses ptrace |
| Offline ARM32 instruction/continuation/SVC checks | 2,090 passed |
| NZCVQ/GE input combinations for the non-S MOV | All 512 passed |
| Compiled SVC success/failure cases | 6 passed |
| NRO layout, supported relocations and native ABI assertions | Passed |
| Imports against installed Eden and Ryujinx loader exports | All 8 resolved |
| Dynamic static constructors and forbidden APSR GE writes | None |
| Reopened ZIP inventory, CRC and payload readback | Passed |
| Support/manifest/checksum inventory and deterministic rebuild | Passed |
| Full distribution checker | Passed, 8 records; this plugin remains DEVELOPMENT |

Rechecked maintained Forge: clean `codex/forge-legacyctx14` at
`b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d`.
Installed Eden Forge SHA-256:
`9d472d56f81f834f366171426dbd0131af19c7697e132c731c3fd3f335af53d0`.
Installed base Better Input SHA-256:
`400a8881065b5736debfdd88d167141b624671906187b9460e1a2fd267497f5f`.
The before/after installed loader/NRO inventories match; bytes do not prove
current activation. Forge source and the loader/Better Input disk files are unchanged.

The inspected current Eden log identifies `master-10bcd2d849-master` but contains
frontend activity, not a new plugin launch. The older launch log records the
maintained Forge/base Better Input adapter. It is historical baseline evidence
and gives no coverage for this new plugin.

No installation, activation, launch, settings/save edit, push or publication
was performed. Gameplay, reward probability, translation freshness, multicore
behavior, quest return/restart and Ryujinx runtime compatibility remain pending
in [MANUAL_TESTS.md](MANUAL_TESTS.md). Readback or flush success cannot promote
these items to passing results.

Machine-readable build/input, host/ARM and binary evidence is under
`build/please-do-better/`; exact source/evidence/support hashes and limits are
in the adjacent candidate manifest. The candidate ZIP holds only the NRO in
its named runtime package. Future runtime changes require a new candidate version.
