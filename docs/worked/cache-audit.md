# Please do Better: cache and instruction-state audit

Worked example from `mods/please-do-better/`. Game facts it rests on are in `mhgu-understanding`.

## Cache and instruction-state audit

Stores use compiler barriers, DSB, checked flush, DSB/ISB and readback. Pinned
Eden `10bcd2d849` [flush SVC](https://git.eden-emu.dev/eden-emu/eden/src/commit/10bcd2d849/src/core/hle/kernel/svc/svc_cache.cpp)
reaches [data/GPU cache handling](https://git.eden-emu.dev/eden-emu/eden/src/commit/10bcd2d849/src/core/memory.cpp)
without CPU translation invalidation. Successful invocation/order does not prove
translation freshness or gameplay effectiveness. No execution probe is used.
Unicorn reference rewrites invalidate Unicorn's own cached translations; that
fixture action is not an Eden fix.

Gateways save r0-r12/LR, d0-d31, FPSCR and CPSR before changing flags. The
328-byte frame retains native stack arguments; helpers align SP to eight bytes
even when taps enter with four-byte alignment. Restore NZCVQ with exact audited
word `0xE128F002`. GE stays live through helpers; no APSR_g restore is emitted.

The compiled NRO rejects GE-writing parallel add/subtract families and any MSR
other than the audited NZCVQ restore. Gateway helpers call only private byte loops,
query SVC and fingerprinted SDK TLS/thread bodies. GetCurrentThread at SDK
`0x9D56C` is MRC/LDR/BX; GetTlsValue/void SetTlsValue at `0x9D7F8`/`0x9D80C`
use MRC/LDR/ADD/STR/BX without GE writes. C entries tail-call through SDK PLT;
fixtures execute native bodies with synthetic thread storage, not SDK startup.
Filesystem/logging/ImGui and singleton lookup calls remain outside gameplay
gateways.

Fixtures compare natural hasSkill bodies and forced behavior against original
instructions across all GPR/flags/VFP state, both stack alignments and GE patterns.
Comparison taps reproduce native NZCV while preserving Q/GE. Return observations
preserve flag outputs of unmodified native code; no original GE output is dropped.
Runtime emulator/kernel compatibility remains manual.
