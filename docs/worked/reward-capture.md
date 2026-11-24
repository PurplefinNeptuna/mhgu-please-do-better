# Please do Better: capture and attribution

Worked example from `mods/please-do-better/`. Game facts it rests on are in `mhgu-understanding`.

## Decisions and accepted copies

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

## Native slot and frame bindings

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
