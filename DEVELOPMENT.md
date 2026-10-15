# Development and research

Current Switch build: r24-forge151 with upstream Forge 1.5.1. Earlier version claims below retain their recorded scope.

## Please do Better

Marks verified extra luck reward slots with a pulsing gold border and sparkle.
Natural luck is the default; optional Force Miraculous Luck reproduces the
wiki's two-site cheat without changing equipped skills.

Current local release: **r23-reward-pages**, READY_TO_DISTRIBUTE and unpublished.
[Installation and settings](README.md); [status and payload hashes](DISTRIBUTION.json).
The 1x to 5x integer slider scales player reward pages and leaves the Palico page
unchanged. The primary INI requires `[PleaseDoBetter]`; old formats use defaults.

The user approved distribution of the unchanged r23 candidate. Its installed
hash and fresh Eden log confirm loading; [the release receipt](EVIDENCE.json)
records the approval and remaining manual/platform limits. The original r23
candidate stays preserved, and r19's delivery and source guides are retained in
the verified rollback archive recorded there.

Earlier r20/r21/r22 reports keep their original payload and coverage scope:
[r20](EVIDENCE.json), [r21](EVIDENCE.json),
[r22](EVIDENCE.json).

### Development and evidence

Use [DEVELOPMENT.md](DEVELOPMENT.md) for pinned inputs, build/test/package/export
commands. [Runtime evidence](DEVELOPMENT.md) retains the version and limits of user
reports. [THIRD_PARTY.md](THIRD_PARTY.md) records development provenance;
[DISTRIBUTION_NOTICES.md](DISTRIBUTION_NOTICES.md) supplies release credits.


R19-savehint changes only the save-success string. Host persistence, 2,122
ARM32 and 100,511 runtime/gateway checks, plus native observation/display/
geometry/highlighting fixtures passed. No fresh game run was performed.
[SAVE_HINT_VALIDATION.json](EVIDENCE.json) pins the payload.

Technical references: [implementation and state audit](DEVELOPMENT.md),
[native research](DEVELOPMENT.md) and [remaining gameplay coverage](DEVELOPMENT.md).
Disable the legacy Great Luck cheat for an authorized test; startup rejects
prepatched/conflicting code. The second check's broader role remains incompletely
traced, and Ryujinx compatibility remains untested.


## Developing please-do-better

Run `./build.sh` from any directory; it defaults to `build`. Commands: `doctor`, `prepare`, `build`, `test --host`, `test`, `verify`, `package` and `export --output DEST`. Only `prepare --fetch` downloads dependencies. Default builds use the pinned compiler image offline and stage candidates.

Copy `build.local.example.json` to ignored `build.local.json`, then set explicit main, SDK and Forge inputs. Their supported SHA-256 values are in `dependencies.lock.json`; the main build ID and hook signatures are checked too. Changing dependencies or hook sites requires a reviewed lock update, ABI/import checks, focused fixtures and GE liveness revalidation.

Use the configured Python environment for the exact `requirements.txt` versions. Host tests need no game files, installed emulator or parent checkout. Complete ARM/resource fixtures require the supplied inputs. Forge headers and required helper snapshots live in this folder. Outputs stay under the coordinating workspace's root build/work, or this repo's ignored local build/work after export.

`build --diagnostics` enables developer captures without diagnostic UI. It cannot be packaged with `package --release`. A release requires an approved, versioned `DISTRIBUTION.json`, matching payload hashes and completed tests; earlier releases stay immutable. Runtime acceptance remains scoped to its recorded version, even when cleanup builds pass static fixtures.

Use settings-only panels. Format logs in Forge callbacks, outside native hooks. Keep one startup summary, meaningful committed preference changes and readable actionable failures. Never reset failure reason masks; unchanged frames stay silent. Overlays and background work run with settings panels closed.

Export only `EXPORT.json` entries. `source-export.json` records the parent commit and source/export hashes. Exports omit game assets, outputs, caches, backups, private configurations, historical asset editions and Git metadata. Initialize remotes and publish separately.


### Forge rendering limits

The legacy NVN backend concatenates ImGui lists but omits preceding-list index
and vertex offsets when submitting later lists. Menu windows/background overlays
can consequently address the wrong geometry. The separate 1.4.1-render1 loader
trial adds cumulative offsets while preserving command-local offsets, texture
bindings, clipping and callbacks. Real-ImGui/NVN-call fixtures recorded 476 bad
submissions in the original and zero in the fix across 201 frames/879 draws.
The 2026-10-08 tested Eden setup was user-confirmed; Forge remains LOCAL_ONLY.
This is scoped evidence, without exhaustive dropdown/transition or new Ryujinx
validation. Keep plugin rendering active with its settings panel closed.


## Please do Better native research

Current overlay/state rules are in [IMPLEMENTATION.md](DEVELOPMENT.md).
The accepted R14 Forge background overlay replaced the experimental native
texture-transfer route. The R13 user log showed valid slot geometry and zero
execution of both downsample hooks. Historical R5-R13 pending-gate notes remain
in Git; they do not describe the current renderer. Gameplay acceptance and
remaining coverage are in [RUNTIME.md](DEVELOPMENT.md) and [MANUAL_TESTS.md](DEVELOPMENT.md).

### Decisions and accepted copies

Selector `0x3822BC` returns normal 22, Horrible Luck 8, Bad Luck 16, Good Luck 25,
Great/Bounty-equivalent Luck 28 or Miraculous Luck 31. Its direct ARM callers are
main count `0x381FEC` and secondary `0x382E1C`. Main count preserves quest
guarantees, RemAddFrameA/B and meal checks 0x10/0x11; it compares threshold >
(randU16 & 31), caps at eight and clamps zero to one. Secondary starts at two and
has six comparisons, the last enabling slot eight. Absent tables generate no items.

Fixtures execute both full native count bodies and selector with deterministic
quest/player/table and RNG-source stubs. Across 1,092 cases, compiled natural mode
matches original counts/consumed rolls; forced mode matches the original cheat.
Native item selection is not rerun. R4 captures actual four-byte item/quantity
entries at the native array-copy boundary; generator returns are diagnostic only.

UI construction `0x3874E0` has these verified eight-entry copies. Fixtures execute
each original fragment with duplicate IDs/distinct quantities and untouched
neighbor sentinels.

| Native return/copy start | End exclusive | Source | Destination |
|---|---|---|---|
| `0x3875BC` | `0x387680` | r7 | `*(ui+0x5C)`, slots 0..7 |
| `0x3878E0` | `0x3879A4` | r7 | `*(ui+0x5C)`, slots 0..7 |
| `0x387B00` | `0x387BC4` | r6 | `*(ui+0x5C)+32`, slots 8..15 |
| `0x388084` | `0x388144` | r5 | `*(ui+0x64)+32`, slots 8..15 |

The first two follow main wrapper `0x381D30`; the third is direct main generation;
the fourth follows secondary `0x382E1C`. Exact caller/destination and all generated
entries must match at UI construction return. Unknown routes publish no attribution.

List copy `0x623C08` copies min(source count, list capacity) by index.
**Items are inline at list+0x60, not behind a pointer.** Flags copy to list+0x120
from the separate r2 descriptor. Thirty-six native count/capacity combinations
verify entries, flags and untouched tails before refresh `0x623C68`. Runtime
follows source-relative offsets into that inline array after contents match;
there is no ID search.

Known category arrays are fields +0x5C/count +0x60, +0x64/count +0x68,
+0x6C/count +0x70 and +0x74/count +0x78. Result update `0x384848` observes
reward states 2..5 at +0x3C; leaving them or destruction invalidates provenance.
This establishes only the listed routes, not every category/display mapping.


### Native geometry bindings

List refresh uses group records of stride `0x28`, root ID at
`list+group*0x28+0x160` and node-ID arrays at `+0x16C`. Holder lookup `0x546F84`
selects holder+0x298's table, resolves the root and accesses root+0xD8 node pointers.
Item assignment `0x56E62C` and visibility `0x56E530` trace item-icon nodes; nearby
IDs alone do not identify frame perimeters.

World-quad helper `0xA4B390` uses anchors +0xA0, size +0xB4, matrix +0x10,
direction bit 0x40 at +0x56 and hard-VFP scale s0. Its 216 original-execution
cases covered nine anchors, two directions, three centre scales, translation,
rotation and shear. World quads alone do not establish framebuffer coordinates.

Texture draw `0xA4FC9C` joins `0xA4FE50` after successful vertex construction.
The displaced LDR r0,[r6] / AND r0,r0,#15 pair writes no flags. GUI publishers
`0xA4EB9C` and `0xA3E3B0` provide model matrices; `0xA397D4` provides globals.
CBGUIMatrix 0x2D7 and CBGUIGlobal 0x2D6 bind at renderer+0x18BC/+0x18B4.
Scissor `0xA37C1C` applies draw-context offsets/scales and viewport intersections.
R12 also reproduces the native sentinel rectangle fallback at `0xBC12D8..0xBC1364`.
Current shader/full-viewport, clip and exact frame/slot identity guards are
documented with the rendering hooks in the implementation audit.

State-1 `0x384AF0` can grow the main reward array to 16 or 48 entries before
opening the grid. Copy loops `0x384BF0..0x384C24` and `0x384C7C..0x384CB0` preserve
indices, then free the old allocation. Capture snapshots the old prefix before
native return and validates the new pointer/capacity/prefix; it never rereads
freed storage or matches solely by item ID.

### Local research inputs

Read-only RomFS inputs were copied under ignored `work/please-do-better/inputs/`.
Originals are unchanged. Game binaries, shader programs, decompiled functions and
external emulator snapshots are not committed or bundled.

| Copied input | SHA-256 |
|---|---|
| AppShaderPackage.mfx | `2b80892da570f42b38dfe46b31234503af3d593eb634da10109c37534ac36627` |
| root.arc | `63d861e9beb9464ca8308760479ed2514d87e9975568889b9599e7a22d91615c` |
| sc/NX/root.spkg | `7dea1d84f3e64d1a79df8f7a4d7bdf063643e996de6cfab95e7c5d782f8b795e` |

Root ARC holds one shader resource. Its large size requires the 30-bit field;
independent bounded zlib extraction produced 58,841,740 bytes without altering
the shared 24-bit helper. Native loader `0xCE1FBC` verifies SPK magic, version
0x26 and shader version 0xB2D34C60. Metadata/variant tables were inspected, but the
exact GUI vertex program and constant-buffer bindings remain unresolved. No GPU
equation is accepted from a guessed table entry or unrelated shader variant.

Read-only Ghidra exports retain original bytes/mismatch counts under ignored
work/tmp paths; no GZF or annotations were edited. Saved DTI provides leads,
subordinate to original instructions.


### Reproduce

```bash
python3 scripts/please_do_better_research.py export
python3 scripts/please_do_better_research.py check
tools/mwc-analysis-venv/bin/python scripts/please_do_better_display_probe.py
```

Export uses `-readOnly -noanalysis` and the shared Ghidra helper. Original bytes,
shader input hashes and SPK bounds are checked; GZF/annotations are preserved.
CPU fixtures do not establish GPU alignment, translation freshness or broader
reward-category coverage.


## Remaining gameplay coverage

R4 forced reward observation and R14 visible highlighting were accepted on the
tested Eden sessions. The 2026-10-08 R17-config1 setup was also user-confirmed,
with Forge 1.4.1-render1 and a screenshot showing menu and highlights together.
[RUNTIME.md](DEVELOPMENT.md) records exact versions, hashes and limits. R19-savehint
has static checks without a fresh game run.

For any authorized follow-up, retain the exact payload hashes, launch set and
latest emulator log. Disable the legacy Great Luck cheat; verify activation
separately from folder presence. Preserve rollback packages and use MHGU 1.4.0.

- [ ] Compare no luck and natural Good/Great/Miraculous Luck across repeated quests.
- [ ] With forcing on and no equipped luck, check repeated batches; one lucky screen is insufficient.
- [ ] Toggle before/during/after generation: batches keep their entry mode and existing rewards remain unchanged.
- [ ] Check Save settings/full restart, delayed storage and manual-edit cancellation with the primary INI.
- [ ] Cover duplicate items, quest guarantees, main A/B, secondary rewards and all four verified copy routes.
- [ ] Cover capacity-16/48 reallocation, repeated grids, row/category changes and screen destruction.
- [ ] Check collection/quantity decreases: stale/empty slots hide and ordinary refreshes produce no false faults.
- [ ] Check gold border/sparkle alignment, animation, clipping and cursor/icon visibility with the panel open/closed.
- [ ] Confirm village return clears live highlights while retaining completed scalar totals.
- [ ] Check Forge combos/navigation and overlays on the exact loader version; the legacy renderer has a multi-list offset defect.
- [ ] Document Eden multicore/translation freshness separately from guest flush/readback.
- [ ] Test Ryujinx startup, modes, quest/return and persistence with its exact revision and fresh log.
- [ ] Trace the second check's broader gameplay role; retaining its `0x102` continuation does not prove complete behavior.

These checks do not authorize installation, launch, save edits or emulator
settings changes. Native Switch and clean shutdown are not established.


## Implementation and state audit

The current release retains the R14 independent overlay and R15 quiet logging.
The revision sections below explain earlier rendering changes; removed telemetry
and transfer hooks are historical. Runtime acceptance is in [RUNTIME.md](DEVELOPMENT.md).

### Identity and hook inventory

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

R10 retains r4's twenty-two detours and adds two fixed rendering detours in a
separate transaction: `0xA4FE50` (LDR/AND) and `0x86A330` (MOV/BX tail call).
The twenty-four eight-byte detours journal 48 words (192 game-code bytes). Each publishes
`ldr pc,[pc,#-4]` (`0xE51FF004`) and a fixed NRO gateway address. Eight callable
originals share one pooled 4 KiB CodeMemory arena. The main-count PC-relative
literal is relocated explicitly; other stolen pairs use a checked whitelist.
Better Input's occupied hook at `0x388EE8` is untouched.

### Modes, storage and callbacks

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

Only `savedata:/please_do_better.ini` is accessed. The file contains
`force_miraculous=0` or `force_miraculous=1` with a trailing newline; no version
marker is written or required. Existing `version=2` files remain readable and
lose the marker on the next explicit save. Missing/invalid primary files use
natural-mode defaults; existing backup files are ignored and untouched.
Use Forge's counted
mount, scoped SDK abort suppression, four-byte ARM32 handles and aligned 64-bit
offsets. Check open/create/resize/read/write/flush/readback and explicit commit.
SDK CloseFile is void. Validate before writing, flush and verify the primary,
then commit through the counted mount. Balance handles/mounts on every failure.
Save failure retains the session choice; previous disk contents are not
guaranteed. No INI is shipped.

### Checked publication and API gaps

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

### Cache and instruction-state audit

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

### Attribution and display gate

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
No collection tracker is added; [RESEARCH.md](DEVELOPMENT.md) records native copy offsets.

R5 also snapshots state-1 main-array contents on entry to the existing update
hook. Up to six eight-entry records fit its existing eight-record scope storage.
At return, the new pointer/capacity and every copied prefix entry must match;
only then publish a batch-tagged old/new index mapping. The old allocation is
never read after native return. Count limits remain 48. No allocator/free is
intercepted.

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
batches remain unavailable.

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


Repeat initialization checks every installed transaction without republishing.
A lost conditional/observation owner disables forcing, capture and highlighting
and invalidates the live binding fence. External bytes stay untouched; unsafe
transaction status remains explicit. There is no live unpatching or enforcement.

### R9 target and viewport correction

The native target resolver accepts the default sentinel and resolved presentation
surface. The native viewport flag selects one of two rectangle banks; accept
either only when clamping gives the full surface. Capture the matching clip from
the immutable packet rather than assuming the renderer's normal clip bank.
Reflected shader-list checks and bounded rejection diagnostics retain the
original native target/viewport guards.

### R10 native texture identity

The r9 user log identifies rejection class 3 for the verified XY shader, with
four bound extras. Surface descriptors differ and the sampled current surface
alternates. Comparing descriptor addresses against that transient global state
cannot establish the presented image. R10 records the native draw image
(`surface+0x10 -> wrapper+0x3C`) and compares it at the existing presentation
boundary with the acquired resource
(`owner+0x48CC`) converted to its NVN texture at resource+0x3C. The original acquire
fragment verifies the three-entry table and cached index. Sentinel draws resolve
through the native default surface at presentation. Nondefault texture views
remain unsupported. Immutable snapshots keep the captured identity across a
producer frame change. No new hooks, arena, TLS slot or game writes were added.

The first rejection for a live screen fence is retained, so alternating images
do not make the displayed diagnostic unreadable. Later rejected draws still
increase the internal counter. New screen fences allow a new diagnostic;
completed reward totals stay retained.

### R12 native scissor semantics

Original BC12D8..BC1364 normalizes the selected viewport/scissor intersection,
compares its complete signed rectangle with a shared sentinel, then substitutes
the cached viewport on equality. The runtime pointer comes from relocated GOT
entry main+0x183F2B0 (BC1314 PC-relative indirection); the offline pointer is
main+0x191EAA0. All pointer/range reads are guarded. R12 reproduces that tail
instead of treating the default empty rectangle as a zero-area draw. Nonmatching
empty rectangles and failed sentinel reads remain suppressed. No reward, RNG,
settings, publication/rollback or resource-allocation behavior changes.
Original ARM execution is compared with compiled capture/ImGui clip calls for
both banks and nonzero sentinels; raw/effective values go only to emulator logs.


### R13 native downsample provenance

Add fixed gateways main+0xBBFB08 and main+0xBBFB44 for equal/differing-format
branches, replaying MOV r1,r11 / MOV r2,r10. The untouched
NVN callback load/call executes with original command/source/destination inputs.
The native initializer and executor both resolve GOT entry main+0x18418F8 to
nvnCommandBufferDownsample. Two immutable fixed snapshots record the exact
native execution frame/serial, owner, fence, source, destination and extent.
Only same-size whole-texture, non-subresource downsample into the acquired image
is accepted. Rendering matches that route to the exact geometry/presentation;
unsupported composition and unobserved offscreen sources stay suppressed.
No additional trampoline/arena, TLS, contexts or heap allocation. Rendering
installation is a guarded four-hook transaction with ownership-aware rollback;
forcing and observation remain independent. GPU execution/alignment remain
pending.

### R14 independent overlay

Use the existing Forge free-render callback/background draw list to submit our
own gold border and procedural sparkle to Forge's acquired image. Damage Numbers
uses the same callbacks and draw list, with projected coordinates rather than
texture identity. The r13 user run confirms valid reward geometry but zero hits
at either downsample hook. R14 removes those two fixed gateways, transfer snapshots
and texture-equality/copy-route acceptance from rendering. The guarded rendering
transaction returns to two fixed hooks: geometry and native presentation.

Native full-viewport shader math, exact slot/batch/array/node binding, owner,
executed serial/index, per-boundary authorization, clip, screen fence, bounded
snapshots and overflow guards remain. Surface/view and successful native draw
validation still protect capture; a nondefault view, reduced viewport, unknown
shader or missing/changed/empty item remains unsupported. This changes overlay
eligibility intentionally: an intermediate offscreen UI image does not suppress
our primitive when its exact projected geometry is valid for the presented frame.
No native texture/sprite asset, game draw-packet edit, new API, heap, arena or TLS
is needed. Visible output/alignment requires a user-run r14 check; local draw-call
fixtures do not prove GPU success.

### R15 quiet release logging

Remove the automatic render trace scope and periodic address/matrix/perimeter/
shader/binding dumps. Retain three startup safety records and one concise
suppression-code record per class per reward screen. No normal capture/present/
render frame logs. Capture counters and immutable safety evidence remain internal;
no gateway logs or formats text. Reward/geometry/hook/mode/settings code retains
r14 behavior. Regression fixtures verify log-free rendering over 240 boundaries,
with the existing complete native/compiled regression suites.

R14 visible Eden acceptance and the later R17-config1/render1 setup confirmation
are recorded in [RUNTIME.md](DEVELOPMENT.md). Later plugin revisions retain separate
static evidence without a fresh gameplay run. The legacy Forge multi-list offset
defect remains external to this plugin; [DEVELOPMENT.md](DEVELOPMENT.md) describes
the separate loader correction. Accepted earlier package bytes are preserved. Shared delivery uses mods/please-do-better/DISTRIBUTION.json
and scripts/mod_distribution.py; no installation or publication.


## Runtime acceptance

On 2026-10-07 the user confirmed: "finally it works", supplied an Eden reward-grid
screenshot with a gold border/sparkle around the final populated slot, and approved
local distribution after cleaning up log diagnostics. The installed r14 NRO
matches e0d21d9fc848d425745833fe813fef638e6f118b37d9127757dec8099929c3e0.
The matching Eden master-10bcd2d849 log records safe startup and bound=1/drawn=1
on the observed reward screen. This establishes visible highlighting on this
installation, alongside the earlier accepted forced reward observation.

The screenshot/log are retained under work/please-do-better/r15-report/.
Log SHA-256: efb1490aa1b49b4e42f00c6f111e0b23b3eb12ed1b3a0ac238ca872520496175.
Screenshot SHA-256: d55744e57859cbf1b65f25ac0a9a70ef3a976eeeba03b78c5f5839f5ef85ce7c.

R15 changes verbose logging only; overlay eligibility, coordinates, shape,
forcing, preferences, reward attribution and hooks are retained. R15's binary
has local compiled/static validation, with no new gameplay run claimed.

The R14 session also exposed Forge menu corruption with the background overlay.
The legacy loader's multi-list buffer-offset defect and subsequent render1
correction are described in [DEVELOPMENT.md](DEVELOPMENT.md). The later
2026-10-08 setup confirmation below uses that separate loader trial.

This is scoped Eden acceptance, not exhaustive coverage. Natural positive luck,
no luck, forced/live toggles across repeated batches, save loading/restart
persistence, collection/quantity decreases, repeated grids/transitions/destruction,
animations, Eden multicore/translation freshness, Ryujinx and the second check's
broader gameplay role remain pending or incompletely traced. No clean-shutdown,
rare-drop guarantee, native Switch or universal emulator compatibility claim.

### r16 standalone/settings/log cleanup

This binary has its own fresh compiled/static checks, recorded in CLEANUP_VALIDATION.json. No new gameplay test was run; the preceding observations retain their original version and scope. Forge remains unchanged.

### 2026-10-08: primary-only config release acceptance

The user reported "all works well" and requested promotion to ready to
distribute, keeping Forge LOCAL_ONLY. The tested Eden installation matches
r17-config1 NRO SHA-256 `bf2263640192b4b6bdb33b0cb507ea7dfe8a65fc86e27f3b90a91fee860eacbe`. The supplied reward-screen screenshot
shows the Forge menu and PDB gold highlights visible together. Eden's retained
log records Forge 1.4.1-render1, PDB r17-config1 and successful Damage Numbers
settings saves. Damage Numbers still prints its older r20 startup label; its
installed file hash identifies the tested r22-config1 bytes.

[Release runtime evidence](EVIDENCE.json) records the
log/screenshot hashes and scope. This is the user's confirmation of the tested
setup, not exhaustive dropdown/transition/save-restart coverage or a clean
shutdown claim. The newest Ryujinx log used older plugin bytes and is not
confirmation of this release. Distribution preparation rebuilds no runtime,
installs nothing and publishes nothing. Earlier entries remain historical.

### 2026-10-08: r18-config2 config simplification

The config codec now writes no version marker and reads existing `version=2`
files without changing their preferences. Host tests execute production storage
with a recording filesystem; compiled ARM32 fixtures cover old-file load,
explicit versionless save and restart. These are simulated storage results,
not a new emulator/game run. Earlier runtime reports keep their original
version and binary scope. Nothing was installed or activated by this task.

### 2026-10-08: r19-savehint save-location wording

The success message names this plugin's INI and MHGU's save folder. Public
instructions use the same location without referencing another plugin.
Persistence, config fields, hooks and gameplay behavior are unchanged.
Scoped validation is recorded in [SAVE_HINT_VALIDATION.json](EVIDENCE.json).
No new gameplay run or installation was performed for this wording revision.

### 2026-10-13: r23 distribution approval

The user requested "good job, mark it ready to distribute". The latest Eden log
records r23-reward-pages loading with forcing/highlights ready, and the installed
NRO matches the preserved candidate SHA-256
`e61e3bda1def28ea2cb03930c59196646573c6bcd27a3d288da0078ce2a4dc00`.
Promotion rebuilds no runtime. [The release receipt](EVIDENCE.json)
records the log fingerprint, original candidate ZIP and r19 rollback archive.

This is explicit distribution approval plus fresh runtime loading evidence.
Individual player-page multiplier, Palico exclusion, appraisal/collection,
persistence and consecutive-quest checks were not separately reported. The log
contains HLE/keyboard and Maxwell assertions and an unmapped-memory error; no
clean-run or clean-shutdown claim is made, and those emulator messages are not
attributed to this plugin. Ryujinx and physical Switch gameplay remain untested.


## Switch r23 reward-page multiplier

r23-reward-pages is READY_TO_DISTRIBUTE and unpublished. Distribution approval
and scoped Eden loading evidence are in R23_RELEASE_APPROVAL.json. Promotion
uses the original candidate NRO without rebuilding. The r20/r21/r22 candidates
and scoped receipts remain preserved; r19's release and source support are in
the verified rollback archive named in the approval receipt. PC is unchanged.
No emulator is installed, configured or launched by this promotion.

### Native data flow

The paired builder at main+0x3874E0 supplies four arrays of four-byte
`(u16 item, u16 amount)` records. Collection at +0x388EE8 selects them by page:

| Page | UI pointer/count | Capacity | Quantity scope |
| --- | --- | --- | --- |
| 0 (also arena selectors 4/5) | +0x5C / +0x60 | 48 normal, 16 arena | Main A/B, special, break/capture; multiplied |
| 1 | +0x64 / +0x68 | 48 | Subquest, free-hunt, bonus items, break/capture overflow; multiplied |
| 2 | +0x6C / +0x70 | 8 | Player extra-item page copied from result save-state +0xAE0; multiplied |
| 3 | +0x74 / +0x78 | 16 or 32 | Palico page: gathered and stolen items; unchanged |

The constructor at +0x3839BC verifies capacities. The builder copies each
companion's gathering row from save-state +0xAF0 and generates its stolen row
through +0x382FFC. Companion count +0xB17 determines page 3's row count at
UI+0x158 (two rows per companion). These records have no quantity writes here.
Items already received during a quest into the pouch/box are outside result
arrays and remain unchanged. Layout evidence is in REWARD_PAGE_LAYOUT.json.

One atomic mode word carries force_miraculous in bit 0 and multiplier-1 in
bits 1..3 (valid multipliers 1..5). Native scopes latch both before generation.
The builder captures all three player pointers/counts before native execution.
On return it preflights all included pages before writing any one of them.
It verifies stable metadata, capacities, alignment, writable bounds, disjoint
ownership including the Palico page, zero/zero empty pairs, signed quantity
bounds and captured snapshots against the unmodified live records.

A result-object latch records the completed attempt even at 1x or on failure.
Later settings changes and repeated builders cannot rescale that same result.
The existing destructor hook at +0x384408 clears the owning gameplay context's
latch before that UI address can be reused for another quest. Native builders
and their UI destructor use the same captured gameplay-thread context.
Fresh constructors zero the player arrays; a nonempty entry preimage also needs
fresh native main/free-hunt count/copy evidence. Lost capture or TLS ownership
never authorizes retrospective writes. Collection/list refresh/render paths do
not invoke the multiplier.

Failure preserves all included quantities and publishes a deduplicated reason
for logging in the update callback. Success writes occupied amount halfwords
on pages 0/1/2 and reconciles both main and secondary pending snapshots.
Item IDs, indices, slot counts, RNG and Luck attribution remain unchanged.

Collection at main+0x388EE8 and appraisal enqueue at +0x3C6C6C read amounts as
signed shorts. The multiplier rejects an input whose product exceeds 32767.
At 5x the maximum input is 6553, keeping the result positive for native collection.
The enqueue body loops once per amount and appends
the item ID to the array at save-state+0xB08; +0xB16 is its current count.
It stops at 150 entries. This native cap is preserved and can truncate a full
appraisal queue. Real inventory/appraisal acceptance remains manual.

No hook, assembly, GE continuation or CodeMemory allocation is added. Writable
range checks reuse the accepted SVC query adapter: the pinned Forge binary does
not export `forge_mem_queryMemory`, although its headers declare it. The native
SDK reader/TLS bindings remain in use for observation and paired ownership.

### Acceptance checklist

- [ ] Slider 1x: normal quantities and existing highlights.
- [ ] Slider 2x..5x: all occupied slots on player pages 0/1/2 scaled once.
- [ ] Both Luck modes retain highlighting; the slider works independently.
- [ ] Village 4-star Great Ore Discovery: guaranteed Dragonite Ore scales with the slider;
      main-reward Mystery Charms appraise as the displayed quantity.
- [ ] Subquest/free-hunt, overflow and player extra items multiply; companion
      gathering/plunder on the Palico page and existing pouch/box items unchanged.
- [ ] Manual collection, Take All, Send to Box, partial stacks and full storage.
- [ ] Move slider while results are visible: existing rewards unchanged.
- [ ] Consecutive quests and settings save/restart retain expected behavior.

Static fixtures and package checks establish their recorded scope only. New
gameplay acceptance requires the tested emulator's fresh log and payload hash.

### Settings format

New saves require [PleaseDoBetter], force_miraculous and reward_multiplier=1..5.
Only this canonical format is read; the user requested no migration from older
settings. Headerless r21 files, old files, invalid multipliers and unsupported
formats use natural Luck and 1x defaults.
Files are rewritten only by explicit Save. The integer slider clamps dragging
and typed values to 1..5; gameplay scopes latch one atomic settings record.
Closing the menu leaves the chosen settings active.
