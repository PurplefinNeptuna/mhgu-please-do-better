# Switch r23 reward-page multiplier

r23-reward-pages is READY_TO_DISTRIBUTE and unpublished. Distribution approval
and scoped Eden loading evidence are in R23_RELEASE_APPROVAL.json. Promotion
uses the original candidate NRO without rebuilding. The r20/r21/r22 candidates
and scoped receipts remain preserved; r19's release and source support are in
the verified rollback archive named in the approval receipt. PC is unchanged.
No emulator is installed, configured or launched by this promotion.

## Native data flow

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

## Acceptance checklist

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

## Settings format

New saves require [PleaseDoBetter], force_miraculous and reward_multiplier=1..5.
Only this canonical format is read; the user requested no migration from older
settings. Headerless r21 files, old files, invalid multipliers and unsupported
formats use natural Luck and 1x defaults.
Files are rewritten only by explicit Save. The integer slider clamps dragging
and typed values to 1..5; gameplay scopes latch one atomic settings record.
Closing the menu leaves the chosen settings active.
