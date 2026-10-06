# Implementation and state audit

## Identity and exact edits

Source main: `work/shared/game-exefs/main`.
SHA-256: `b3935415499549adaf4c0e89822831daa175cfd456a7990791c79be3997645ef`.
Full main build ID: `FB08F1D20FD1204FE7070672777F869B`.
The build recipe validates the exact NSO, segment hashes, both 32-byte windows
and the second site's retained `0x102` continuation against the original input.

| Main-relative instruction | Original word | Replacement |
|---|---|---|
| `0x003822DC` | `0xEBF57AAF` | `0xE3A00001` |
| `0x004D17F4` | `0xEBF67983` | `0xE3A00001` |

The replacement bytes are `01 00 A0 E3`, ARM `mov r0, #1` without S.
Runtime uses `forge_mem_getMainTextAddr()` plus these offsets. It checks title
ID `0100770008DD8000`, executable mapping bounds and the original signatures.
These are compatibility guards; they are not a runtime full-NSO hash/build-ID
verification. Database addresses with base `0x009C9000` are never runtime bases.

Only the two four-byte words are written to game code. The first selects the
existing Miraculous Luck branch (`r5 = 0x1F`); the weaker branches remain intact.
The second leaves `mov r5,#1`, `cmp r0,#1`, the conditional branch, and the later
`movw r1,#0x102` / skill call unchanged. No routine/global query is hooked.

## Forge facilities and verified gaps

Use Forge's main-base lookup, `forge_log`, plugin lifecycle and cimgui exports.
`forge/mem.h` lacks a C++ linkage guard; include it under `extern "C"` to match
the installed unmangled main-base accessor without modifying Forge headers.
The existing native `PluginInitParam` layout is 70 bytes with `name` at offset
6; compile-time assertions enforce ARM32 pointer/layout expectations. There
are no Hook/Patch/Jit instances, trampoline slots, heap allocations, threads,
filesystem operations or preference mounts.

Inspected Forge `patch.c` uses unchecked allocation and `memcpy`, snapshots
whatever original bytes it finds, returns no write/cache result, and performs
no executable-cache synchronization. This cannot express the transaction's
preflight, ownership and failure contracts. Private fixed storage fills that gap.

Installed Forge exports its main-base accessor, logging and UI functions, but
not `forge_mem_queryMemory` or `forge_proc_getProgramId`. Private SVC wrappers
therefore cover only QueryMemory (`0x06`), GetInfo (`0x29`, program ID 18) and
FlushProcessDataCache (`0x5F`), adapted from maintained controls/pinned libnx.
Actual imports are checked against installed Eden and Ryujinx loader exports.

## Transaction and cache contract

Check both original windows before the first store. Recheck each complete window
immediately before its scalar write and recheck both patched windows at the end.
The native backend checks mapping/readback and explicitly reports whether a
store occurred, even if its subsequent readback failed. Ownership starts only
after that store. Prepatched words, including two matching cheat replacements,
are rejected rather than adopted.

On write/readback/flush failure, visit owned sites in reverse order. Restore only
a word still equal to this plugin's replacement, then check flush/readback.
If another writer already restored an attempted site's original word, skip its
store and still check synchronization before reporting completed rollback.
An unreadable word, external modification, failed restore or failed rollback
flush produces an unsafe status with owned/failure masks. Successful byte
restoration with failed synchronization is also unsafe. Repeat initialization
never writes again; it checks retained signatures if previously applied and
reports external changes. There is no per-frame enforcement or runtime teardown.

This is a startup transaction, not thread suspension or an atomic two-address
update. Expected-word reads and stores cannot prevent a concurrent cheat from
racing the plugin. The legacy cheat must be disabled. The startup boundary is
Forge's `sApp_run` before `original_sApp_run`, not a proven pause of every core.

The cache sequence is a compiler barrier, ARM `dsb sy`, checked flush SVC,
`dsb sy` / `isb`, compiler barrier and instruction readback. Mapping checks
precede every read/write/flush. It follows the existing emulator direct-store
publication pattern and does not grant native Switch permission to write RX.

Pinned Eden revision `10bcd2d849` routes
[FlushProcessDataCache](https://git.eden-emu.dev/eden-emu/eden/src/commit/10bcd2d849/src/core/hle/kernel/svc/svc_cache.cpp)
to [Memory::FlushDataCache](https://git.eden-emu.dev/eden-emu/eden/src/commit/10bcd2d849/src/core/memory.cpp),
which handles data/GPU coherency without CPU translation invalidation.
Pinned ARM32 libnx's `armICacheInvalidate` is a no-op, so it is not called.
Eden's separate range invalidation also leaves the cached instruction-page
address intact; full instruction-cache clearing resets it. The relationship
to the reported cheat failure is plausible, not runtime-proven.

No permission transitions, execution self-probe or emulator changes are used.
The candidate can report only applied/readback/flush-checked, never verified
translation freshness. The offline Unicorn fixtures do not test Eden's JIT.

## Instruction and continuation state

Both original instructions are unconditional ARM BL calls. The exact cheat
replacement is an unconditional non-S MOV: it writes r0=1, advances PC normally,
does not update LR, touches no stack/VFP/FPSCR state and preserves NZCVQ and GE.
The skipped callee's side effects and BL's LR write are intentionally omitted,
matching the source cheat. No replacement helper runs in either game path.

At the first continuation, `mov r5,#0x1F` also has no S bit; `cmp r0,#0` then
defines NZCV and the following BNE selects the stronger branch. At the second,
`mov r5,#1` has no S bit; `cmp r0,#1` defines NZCV and BNE falls through to the
retained skill check. CMP leaves Q/GE unchanged. Incoming GE remains intact
through the inserted instruction and immediate continuation. Nothing is
omitted from a register gateway, so GE liveness does not require an APSR restore.
Later unmodified calls retain their original behavior; the broader second-site
role is not inferred from this local audit.

Static disassembly rejects forbidden APSR GE writes. The instruction fixtures
exercise all 32 NZCVQ combinations and all 16 GE patterns, plus both immediate
continuations. Compiled SVC fixtures check 64-bit register/stack argument layouts,
output pointers, return results and callee-saved registers. Host sanitizer tests
exercise production transaction/backend code with fake kernel failures.

These checks establish local instruction/backend contracts, not gameplay.
