# Switch r20 quantity multiplier

r20-doubleqty is a DEVELOPMENT candidate. Switch r19's distribution record,
release payload, installation README and historical evidence remain unchanged.
PC is outside this change. No emulator is installed, configured or launched.

## Native data flow

The paired builder at main+0x3874E0 owns first-screen records at UI+0x5C with
capacity at +0x60. Normal capacity is 48 four-byte `(u16 item, u16 amount)`
records: A/B/special occupy indices 0..23; break/capture occupies 24..47.
Other result arrays (+0x64, +0x6C, +0x74) are excluded. Smaller first-screen
layouts are bounded by their actual count rather than forced to 48.

One atomic mode word carries force_miraculous in bit 0 and double_quantity in
bit 1. Native scopes latch both before generation. The paired return processes
its local scope once; collection, list copies, rendering and presentation never
invoke the multiplier. A nonempty preimage requires freshly captured main
counts/copies, preventing an unproductive builder from doubling an old result.

Before writes, check the unchanged pointer/count, whole readable/writable heap
region, zero/zero empty pairs, signed quantity bounds and all pending snapshots
that overlap the first array. Failure preserves the complete native array and
publishes a deduplicated fault for formatting in the update callback. Success
writes amount halfwords and adjusts only the first-screen pending snapshots.
Item IDs, RNG, indices, counts and Luck masks retain their native meanings.

Collection at main+0x388EE8 and appraisal enqueue at +0x3C6C6C read amounts as
signed shorts. The multiplier therefore rejects inputs above 16383, keeping
the doubled value <=32767. The enqueue body loops once per amount and appends
the item ID to the array at save-state+0xB08; +0xB16 is its current count.
It stops at 150 entries. This native cap is preserved and can truncate a full
appraisal queue. Real inventory/appraisal acceptance remains manual.

No hook, assembly, GE continuation or CodeMemory allocation is added. Writable
range checks reuse the accepted SVC query adapter: the pinned Forge binary does
not export `forge_mem_queryMemory`, although its headers declare it. The native
SDK reader/TLS bindings remain in use for observation and paired ownership.

## Acceptance checklist

- [ ] Toggle off: normal quantities and existing highlights.
- [ ] Toggle on: main A/B, special and break/capture quantities doubled once.
- [ ] Both Luck modes retain highlighting; either option works independently.
- [ ] Village 4-star Great Ore Discovery: guaranteed Dragonite Ore doubled;
      main-reward Mystery Charms appraise as the displayed quantity.
- [ ] Gathering, subquest/free-hunt and separate plunder quantities unchanged.
- [ ] Manual collection, Take All, Send to Box, partial stacks and full storage.
- [ ] Toggle while results are visible: existing rewards unchanged.
- [ ] Consecutive quests and settings save/restart retain expected behavior.

Static fixtures and package checks establish their recorded scope only. New
gameplay acceptance requires the tested emulator's fresh log and payload hash.
