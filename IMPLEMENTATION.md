# Implementation and state audit

## Identity and hook inventory

Source main: `work/shared/game-exefs/main`, SHA-256
`b3935415499549adaf4c0e89822831daa175cfd456a7990791c79be3997645ef`.
Build ID: `FB08F1D20FD1204FE7070672777F869B`; the full 32-byte NSO field,
including zero padding, and segment hashes are checked offline. Runtime checks
title `0100770008DD8000`, arithmetic, executable mapping bounds and all complete
32-byte signatures. It does not perform a full runtime NSO hash/build-ID check.
Ghidra's imported base `0x009C9000` is not a runtime base.

| Main-relative site | Displaced behavior / observation |
|---|---|
| `0x3822DC` | BL `0xE0DA0`; MOV r5,#31: conditional Miraculous check |
| `0x4D17F4` | BL `0x26FE08`; MOV r5,#1: conditional second cheat check |
| `0x3820D0` | AND r0,#31; CMP r5,r0: main comparison |
| `0x382EDC`, `0x382EFC`, `0x382F1C`, `0x382F3C`, `0x382F5C`, `0x382F7C` | MOV r7,#2..7; CMP r6,r0: all secondary comparisons |
| `0x381FEC`, `0x382E1C`, `0x38211C` | Paired main count, secondary count, generation |
| `0x3874E0`, `0x381D30` | Paired UI-array construction and main wrapper |
| `0x623C08` | Paired indexed copy into inline native list |
| `0x384848`, `0x384408` | Paired result update/destruction |
| `0x3820B4` | MOV r5,r0; CMP r4,#7: selected threshold and initial main count |
| `0x3875BC`, `0x3878E0`, `0x387B00`, `0x388084` | LDR destination; LDRH first item: capture verified native array copies |

R8 retains r4's twenty-two detours and adds two fixed rendering detours in a
separate transaction: `0xA4FE50` (LDR/AND) and `0x86A330` (MOV/BX tail call).
The twenty-four eight-byte detours journal 48 words (192 game-code bytes). Each publishes
`ldr pc,[pc,#-4]` (`0xE51FF004`) and a fixed NRO gateway address. Eight callable
originals share one pooled 4 KiB CodeMemory arena. The main-count PC-relative
literal is relocated explicitly; other stolen pairs use a checked whitelist.
Better Input's occupied hook at `0x388EE8` is untouched.

## Modes, storage and callbacks

The lock-free 32-bit request starts false. Observed roots latch it before calling
native code; nested scopes inherit it. Outside batches, future checks read it.
Natural mode invokes the original callee with native arguments/stack/registers,
then preserves its outputs/flags, replays the MOV and reconstructs BL's LR
(`site+4`). Forced mode supplies r0=1 and r5=31/1, skips the callee and preserves
incoming LR/flags, matching the cheat. Both resume at `site+8`. The later second
check for `0x102` remains unchanged.

Eight fixed thread contexts hold four scopes and sixteen atomic publication slots
each, with one native TLS slot. Overflow keeps an existing root latch, leaves
overflow calls' LR untouched and suppresses attribution. Lost TLS uses immutable
native thread identity to retain entered callers/modes, quarantines attribution
and preserves foreign TLS bytes. Context exhaustion keeps unidentified execution
natural and reports incomplete coverage. Context slots are never recycled.

Forcing requires the verified conditional pair and batch capture. A safe observation
installation failure retains the conditional pair in natural behavior. There is
no always-forced fallback, global skill query, live unpatching or per-frame
instruction enforcement. `fini` leaves process-lived hooks alone.

Preference operations stay on Forge's ImGui presentation callbacks; update only
consumes capture mailboxes. Free-render retries unavailable storage every sixty
presented frames with the panel closed too. UI edits cancel pending load before
publishing the mode, avoiding an assumption that game update and NVN presentation
share a thread.

Only `savedata:/please_do_better.ini` and `savedata:/please_do_better_backup.ini`
are accessed. Exact version-2 decoding accepts force=0/1 only. Use Forge's counted
mount, scoped SDK abort suppression, four-byte ARM32 handles and aligned 64-bit
offsets. Check open/create/resize/read/write/flush/readback and explicit commit.
SDK CloseFile is void. Before replacing the primary, write/read back/commit
a recovery copy, preferring a valid primary, then a valid existing backup, then
the natural-mode default for a fresh save. Failed replacement attempts checked restoration; failed recovery
is reported as uncertain. Save failure retains the session choice. No INI is shipped.

## Checked publication and API gaps

Forge provides lifecycle, main-base lookup, logging, counted mount and ImGui.
The native plugin-load struct is 70 bytes with name at offset 6; static assertions
cover pointers, RawFrame and SDK handle ABI. Its main-base header needs C linkage.

Forge's patch wrapper snapshots arbitrary current bytes and exposes no checked
write/cache/rollback results. Its hook wrapper also lacks checked publication/cache
results and ownership-aware restoration. Private Hooks/NativePlatform fill those
verified gaps using the reviewed Modern Controls backend. Installed Forge lacks
the required memory-query/program-ID exports; private pinned libnx ARM32 bindings
cover QueryMemory 6, CloseHandle 0x16, GetInfo 0x29, CreateCodeMemory 0x4B,
ControlCodeMemory 0x4C and FlushProcessDataCache 0x5F.

Verify title, all original windows, alignment, address arithmetic, executable
ranges and relocation forms before publication. Prepare/read back callable
originals and check arena flush first. Publish scalar literals before LDR-PC
instructions, with checked readback and synchronization. No heap buffer or
permission transition is used. Forge's startup boundary precedes original_sApp_run;
this is not thread suspension or an atomic two-address update.

Rollback visits owned words in reverse order, restoring only owned replacements.
Already-restored originals still require checked sync. Foreign/unreadable bytes,
failed restore/flush and failed cleanup produce UNSAFE status and masks. Keep
storage reachable from residual hooks. Repeat init checks retained signatures
without allocation/writes and disables effective forcing/capture on conflict.
Concurrent cheats are not made safe by expected-word checks.

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
gateways. Rendering gateways call only bounded private helpers and the audited
query SVC.

Fixtures compare natural hasSkill bodies and forced behavior against original
instructions across all GPR/flags/VFP state, both stack alignments and GE patterns.
Comparison taps reproduce native NZCV while preserving Q/GE. Return observations
preserve flag outputs of unmodified native code; no original GE output is dropped.
Runtime emulator/kernel compatibility remains manual.

## Attribution and display gate

Compare actual observed rolls with normal threshold 22; positive tiers 25/28/31
mark slots beyond the first normal stopping point. Negative/normal tiers 8/16/22
mark none. Preserve quest/meal guarantees, minimum-one and cap-eight behavior.
Observe all six secondary comparisons including slot eight. Consume no extra RNG,
select no items and rerun no generation. The initial main-count tap supplies
the actual selected tier even when guaranteed slots reach the cap without rolls.
Complete sequences must start at the observed initial main count or secondary
slot two, progress consecutively, and end at a stop or cap. Missing taps suppress
complete attribution.

Exact epoch/array/index plus item/quantity snapshots distinguish duplicate items.
Snapshot the full eight-entry temporary at each verified native copy boundary,
bind it to the matching count scope/caller/category, and verify the complete
destination at UI build return. Generator returns are diagnostic only. The
secondary routine returns void: derive its count from comparisons and validate
the generated prefix, never read its return register as a count.
Accept only traced copies with matching contents. Lost scopes, overflow, overwritten
mailboxes, empty/incompatible entries or unknown routes suppress attribution.
Last completed batch totals retain scalar generation evidence independently of
live array invalidation. Partial coverage reports the extra total unavailable.
No collection tracker is added. See [R4_OBSERVATIONS.md](R4_OBSERVATIONS.md) for
exact route offsets and runtime evidence.

R5 also snapshots state-1 main-array contents on entry to the existing update
hook. Up to six eight-entry records fit its existing eight-record scope storage.
At return, the new pointer/capacity and every copied prefix entry must match;
only then publish a batch-tagged old/new index mapping. The old allocation is
never read after native return. Count limits remain 48. No allocator/free is
intercepted. See [R5_OBSERVATIONS.md](R5_OBSERVATIONS.md).

R7 snapshots list-copy contents at native return in at most six eight-entry
mailbox records, tagged with the current batch serial. The first chunk clears
only that exact list; capture failure publishes a clearing record. Delayed reads
never compare earlier copy mappings with later native destination bytes. The
renderer accepts the two verified base/Festa texture vtables with inherited
layout and draw methods; other classes stay rejected.

State 1's `0x384AF0` resizes before its original `0x384FC0` call to builder
`0x3874E0`, all inside the same paired update. R8 supersedes the outer preimage
when that nested builder starts a new batch for the same UI object. Newly
validated generation records already refer to the current destination. Their
contents must not be compared with the old empty array. Genuine relocations
without a same-object new batch retain their existing guards. Incomplete new
batches remain unavailable. See [R8_HIGHLIGHTS.md](R8_HIGHLIGHTS.md).

List refresh accepts same-index quantity decreases or fully empty pairs verified
against generation snapshots. Empty slots lose live eligibility. Other IDs,
increased quantities, malformed pairs and read failures report mapping faults.
The internal expected-refresh count is separate from genuine drops. Neither
counter tracks collected items; neither edits inventory. Screen close/destruction
clears live provenance without erasing completed totals. A relocation failure
invalidates live provenance without retroactively invalidating valid generation.

The fixed `0xA4FE50` gateway captures only verified reward frame nodes after
successful normal vertex construction and replays LDR/AND. The `0x86A330`
gateway records the exact native present queue/window/index, replays MOV r0,r12,
and tail-calls r3 with native LR intact. Both use the existing full-state gateway
frame; neither needs a callable original or another arena/TLS slot.

64 immutable binding snapshots and 64 immutable geometry snapshots use atomic
payload words and nonblocking sequence tickets. A mismatched/torn snapshot or
stale fence/frame suppresses rendering. Overflow suppresses its whole frame.
The geometry pool retains current and previous producer serials for native
parallel execution; monotonic per-buffer overflow tags cannot be overwritten
by an older publication. Bindings contain exact UI/batch/list/group/index/frame-node/icon-node identity;
item IDs alone never select slots. Native screen exit/destruction invalidates
the fence before freeing UI state. Live item/quantity checks suppress empty or
incompatible slots; completed scalar totals remain retained.

Forge free-render uses its background draw list. The native shader/model/global
bindings and full viewport determine the perimeter. It pushes native clipping,
draws four gold lines at 1.5px scaled from 720p plus eight lines for a four-point
sparkle, then pops clipping. Alpha follows a deterministic two-second pulse.
No fill covers icons or quantities. Unsupported geometry produces no draw.
The shader/presentation proof is in [R6_HIGHLIGHTS.md](R6_HIGHLIGHTS.md);
[R7_HIGHLIGHTS.md](R7_HIGHLIGHTS.md) documents the texture/copy repairs.

Repeat initialization checks every installed transaction without republishing.
A lost conditional/observation owner disables forcing, capture and highlighting
and invalidates the live binding fence. External bytes stay untouched; unsafe
transaction status remains explicit. There is no live unpatching or enforcement.
