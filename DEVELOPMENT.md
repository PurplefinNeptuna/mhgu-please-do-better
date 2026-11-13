# Please do Better: development and research

**Current state.** r30 DEVELOPMENT candidate at `build/please-do-better/candidates/r30/`, accepted
on Eden, Ryubing and MHGURecomp with Purple-lib r4 and without it ("working perfectly for both
mod."). r30 keeps r29's reward code and adds an optional registration with Purple-lib: its two
settings as a Mod Options page and a help topic in Village/Hub (*Purple-lib* below). Every hook is
installed through Forge's hook API; highlights are white native frames. [Install and
settings](README.md); [status and hashes](DISTRIBUTION.json); [exact results](EVIDENCE.json);
[tester steps](TESTING.md); [provenance](THIRD_PARTY.md); [release credits](DISTRIBUTION_NOTICES.md).

Marks verified extra luck reward slots by turning their native frame white. Natural luck is the default; optional Force Miraculous Luck reproduces the wiki's two-site cheat without changing equipped skills. The 1x to 5x integer slider scales player reward pages and leaves the Palico page unchanged. The primary INI requires `[PleaseDoBetter]`; old formats use defaults.

Ryubing 1.3.3 has run only the r27 frame-tint probe, where white frames held through the cursor and item pickup.

Still unconfirmed: natural positive luck, no luck, forced and live toggles across repeated batches, save and restart persistence, collection and quantity decreases, repeated grids and transitions, player-page multiplier, Palico exclusion, appraisal and collection, consecutive quests, Ryujinx beyond the r27 probe, and physical Switch. No clean-shutdown claim is made; Maxwell, HLE and unmapped-memory messages in the logs are not attributed to this plugin. The second check's broader role is incompletely traced. Disable the legacy Great Luck cheat for an authorized test, because startup rejects prepatched or conflicting code.

## Developing please-do-better

Run `./build.sh COMMAND` from any directory: `fetch` (once, downloads `vendor/`), `doctor`, `prepare`, `build`, `test --host`, `test`, `verify`, `package` and `export --output DEST`. Builds are offline with the pinned Rust nightly, vendored forge-rs 1.5.0 and the separately pinned cargo-forge 1.4.1 converter.

Copy `build.local.example.json` to ignored `build.local.json`, then set the tools and copied main/SDK/Forge inputs. Their supported SHA-256 values are in `dependencies.lock.json`; the main build ID and hook signatures are checked too. Changing dependencies or hook sites requires a reviewed lock update, import checks, focused fixtures and GE liveness revalidation. `core/` holds the portable logic and `core/tests/` its host tests. `src/` holds the gateways, reward capture, overlay and settings. The ARM probes in `scripts/` execute the compiled plugin and read its private state through hidden `pdb_*` symbols, which never reach the NRO's exports.

Forge's hook API places every hook. Forge copies a target's first eight bytes without relocating them, and the second word at main+0x381fec is `ldr r0,[pc,#0x108]`, so that entry's original is the fixed stub `pdb_main_count_original` in `src/gateway.S`. Forge has no mapping query, program ID or process cache flush, which is what `src/svc.S` supplies.

Use settings-only panels. Format logs in Forge callbacks, outside native hooks. Keep one startup summary, meaningful committed preference changes and readable actionable failures. Never reset failure reason masks; unchanged frames stay silent. Overlays and background work run with settings panels closed.

Export only `EXPORT.json` entries. `source-export.json` records the parent commit and source/export hashes. Exports omit game assets, outputs, caches, backups, private configurations, historical asset editions and Git metadata. Initialize remotes and publish separately.


## Purple-lib

Optional, Purple-lib API version 1 (its `API.md`). `src/purple_lib.rs::register` runs in
`forge_onInit` after the hooks: it walks the mappings with `svcQueryMemory` for a readable and
executable one that starts with an NRO header and defines `purplelib_api_version`
(`core/src/purple_lib.rs::nro_symbol`, the WishFinder bridge's reader), checks the version, and
passes one Mod Options record (2 rows) and one help record (category 18, 3 pages). Without
Purple-lib it returns quietly.

Purple-lib calls `get` and `set` inside the game's update, so they use only the lock-free mode
request (`runtime::requested_preferences` / `request_preferences`). `set` raises `EDITED` and
`closed` raises `SAVE`; `forge_onImGuiFreeRender` turns them into `settings::changed()` (drop a
pending load) and `settings::save(...)`, keeping preference state and the INI on the ImGui
callbacks. Row values: Force 0/1, multiplier label index = multiplier - 1. All strings are static,
because Purple-lib keeps the pointers. The host test `the_symbol_lookup_finds_exports_in_a_real_nro`
runs the reader on this build's own NRO against its nm listing.

## Please do Better native research

The highlight and state rules are under "Implementation and state audit".

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
Native item selection is not rerun. The plugin captures actual four-byte item/quantity
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


### Native slot and frame bindings

List refresh uses group records of stride `0x28`, root ID at
`list+group*0x28+0x160` and node-ID arrays at `+0x16C`. Holder lookup `0x546F84`
selects holder+0x298's table, resolves the root and accesses root+0xD8 node pointers.
Item assignment `0x56E62C` and visibility `0x56E530` trace item-icon nodes; nearby
IDs alone do not identify frame perimeters.

Frame colours are sequence data. Layout setup `0x623A6C` starts sequence `0xF4242` plus a variant on the group's
background root (`0x56E538` to `0x546C74` to root `0xA3896C`, which restarts only on a different ID), which colours
Base rows red and Wound/Cap rows blue. The cursor's yellow cell comes from a path not yet read. List refresh
`0x623C68` only assigns icons (`0x56E62C`) and visibility (`0x56E530`), so a frame keeps its `(group, index)` for
the screen's life. Setter `0xA4E0B8(object, *colour, vertex)` stores `+0xA4 + 4 * vertex` and marks the quad dirty
through vtable slot 0x50. A Base frame's four corners hold `0xA02337DC` (bytes R 0xDC, G 0x37, B 0x23, alpha 0xA0)
over a light texture, so a white vertex colour shows the texture itself. Neither the cursor's yellow nor taking the
item rewrites that colour.

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

Root ARC holds one shader resource of 58,841,740 bytes unpacked, larger than 24 bits can count; ARC sizes are the low 29 bits of the entry's flags (`SIZE_MASK` in `scripts/mhgu_assets.py`). Native loader `0xCE1FBC` verifies SPK magic, version
0x26 and shader version 0xB2D34C60. Metadata/variant tables were inspected, but the
exact GUI vertex program and constant-buffer bindings remain unresolved. No GPU
equation is accepted from a guessed table entry or unrelated shader variant.

Read-only Ghidra exports retain original bytes/mismatch counts under ignored
work/tmp paths; no GZF or annotations were edited. Saved DTI provides leads,
subordinate to original instructions.


### Reproduce

`./build.sh test` runs the `please_do_better_*_probe.py` fixtures. CPU fixtures do not establish GPU alignment, translation freshness or broader
reward-category coverage.


## Remaining gameplay coverage

For any authorized follow-up, keep the exact payload hashes, launch set and latest emulator log. Disable the legacy Great Luck cheat, verify activation separately from folder presence, and use MHGU 1.4.0.

- [ ] Compare no luck and natural Good/Great/Miraculous Luck across repeated quests.
- [ ] With forcing on and no equipped luck, check repeated batches; one lucky screen is insufficient.
- [ ] Toggle before/during/after generation: batches keep their entry mode and existing rewards remain unchanged.
- [ ] Check Save settings/full restart, delayed storage and manual-edit cancellation with the primary INI.
- [ ] Cover duplicate items, quest guarantees, main A/B, secondary rewards and all four verified copy routes.
- [ ] Cover capacity-16/48 reallocation, repeated grids, row/category changes and screen destruction.
- [ ] Check collection/quantity decreases: stale/empty slots hide and ordinary refreshes produce no false faults.
- [ ] Check the white frames on every reward page layout and with the cursor on and off a highlighted slot.
- [ ] Confirm village return clears live highlights while retaining completed scalar totals.
- [ ] Check Forge combos, navigation and overlays on the exact loader version.
- [ ] Document Eden multicore/translation freshness separately from guest flush/readback.
- [ ] Test Ryujinx startup, modes, quest/return and persistence with its exact revision and fresh log.
- [ ] Trace the second check's broader gameplay role; retaining its `0x102` continuation does not prove complete behavior.

These checks do not authorize installation, launch, save edits or emulator
settings changes. Native Switch and clean shutdown are not established.


## Implementation and state audit

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

The plugin has twenty-two Forge hooks, each `ldr pc,[pc,#-4]` (`0xE51FF004`) and a fixed NRO
gateway address. The seven chaining entries ask Forge for an original and the gateway continues
into its trampoline (the two words found, `ldr pc`, site + 8, checked after creation). Interior
sites take no original: their gateways replay the displaced pair. `0x381FEC` takes no original
either; `pdb_main_count_original` replays `push {r4,r5,r6,lr}`, loads the literal at
main+0x382100 (copied at install into `pdb_main_count_literal`) into r0 and jumps to
`0x381FF4` through `pdb_main_count_resume`. On MHGURecomp that jump lands inside a function
Recomp interprets because `0x3820D0` and `0x3820B4` are Forge hooks in it.

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

Installed Forge lacks memory-query, program-ID and process-flush exports; private pinned libnx
ARM32 bindings cover QueryMemory 6, GetInfo 0x29 and FlushProcessDataCache 0x5F, the only SVCs
in the binary. MHGURecomp implements all three.

`install_hooks` in `src/runtime.rs` checks the title, the recipe and all 22 windows before Forge
hooks anything, and takes a disabled Forge `Patch` snapshot of each site. It then creates the
hooks in order, checking each returned Hook, trampoline, branch and flush. Forge's startup boundary
precedes original_sApp_run; this is not thread suspension or an atomic update.

Paired entries other than `0x381FEC` set `chains`: they enter a scope, swap only LR, run the original once and
write after it returns, so they stack on another plugin's Forge hook (see "Chaining" in the forge-modding hooks reference).
Forge copies the foreign pair into our trampoline, so the original runs it, and a later Forge hook over the entry
is not a conflict. `0x381FEC` has a PC-relative second word, and the luck, comparison,
copy and threshold sites are interior or branch-over sites; all of those stay exact.

On any failure, rollback walks the snapshots newest first and restores a site only when each of
its two words is still ours or the original; a foreign word is left and the failure is logged as
needing a restart. Forge's trampolines stay allocated, and a continuation already stored stays
valid for a gateway that remains reachable. Repeat init rechecks every window without hooking
again and disables forcing and capture on conflict. Concurrent cheats are not made safe by
expected-word checks.

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
gateways.

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
No collection tracker is added. Native copy offsets are in "Please do Better native research".

The plugin also snapshots state-1 main-array contents on entry to the existing update
hook. Up to six eight-entry records fit its existing eight-record scope storage.
At return, the new pointer/capacity and every copied prefix entry must match;
only then publish a batch-tagged old/new index mapping. The old allocation is
never read after native return. Count limits remain 48. No allocator/free is
intercepted.

It snapshots list-copy contents at native return in at most six eight-entry
mailbox records, tagged with the current batch serial. The first chunk clears
only that exact list; capture failure publishes a clearing record. Delayed reads
never compare earlier copy mappings with later native destination bytes. The
frame tint accepts only the two verified base/Festa texture vtables with inherited
layout and draw methods; other classes stay rejected.

State 1's `0x384AF0` resizes before its original `0x384FC0` call to builder
`0x3874E0`, all inside the same paired update. The plugin supersedes the outer preimage
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

Repeat initialization checks every installed transaction without republishing.
A lost conditional/observation owner disables forcing, capture and highlighting. External bytes stay untouched; unsafe
transaction status remains explicit. There is no live unpatching or enforcement.

### Logging

Startup safety records and one record per failure class only. No capture or per-frame logs; gateways format no text. The config codec writes no version marker and reads existing `version=2` files without changing preferences.

### Do not

- **Draw the highlight as an ImGui overlay.** Its capture hook inside the GUI texture draw `0xA4FC9C` leaves that per-draw function interpreted on MHGURecomp; the native frame tint needs no render hook. The overlay's native addresses are in the mhgu-understanding native GUI reference.
- **Compare a nested builder's new generation records with the outer empty array.** A same-object new batch supersedes the outer preimage.
- **Read the secondary routine's return register as a count.** It returns void; derive the count from comparisons.
- **Read the old allocation after native return, or compare earlier copy mappings with later destination bytes.**
- **Select slots by item ID alone.** Bindings use exact UI, batch, list, group, index, frame-node and icon-node identity.
- **Log per frame in release.** Run traces and address or matrix dumps were removed.
- **Blame this plugin for Forge menu corruption seen with an older loader.** That was the legacy loader's multi-list buffer-offset defect, and stock Forge 1.5.1 is the baseline.

## Reward-page multiplier

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
arrays and remain unchanged. Layout evidence is in `EVIDENCE.json`.

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

No hook, assembly or GE continuation is added. Writable
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

## Open items

- **MHGURecomp frame cost.** The luck, copy and threshold functions run interpreted there once hooked; they run only while rewards are generated, and the cost is unmeasured (`MHGU_INTERP_STATS=1` measures it).
