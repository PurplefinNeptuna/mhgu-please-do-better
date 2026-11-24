# Please do Better: hooks and multiplier

Worked example from `mods/please-do-better/`. Game facts it rests on are in `mhgu-understanding`.

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

The plugin has twenty-two Forge hooks, each `ldr pc,[pc,#-4]` (`0xE51FF004`) and a fixed NRO
gateway address. The seven chaining entries ask Forge for an original and the gateway continues
into its trampoline (the two words found, `ldr pc`, site + 8, checked after creation). Interior
sites take no original: their gateways replay the displaced pair. `0x381FEC` takes no original
either; `pdb_main_count_original` replays `push {r4,r5,r6,lr}`, loads the literal at
main+0x382100 (copied at install into `pdb_main_count_literal`) into r0 and jumps to
`0x381FF4` through `pdb_main_count_resume`. On MHGURecomp that jump lands inside a function
Recomp interprets because `0x3820D0` and `0x3820B4` are Forge hooks in it.

## Checked publication and API gaps

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
