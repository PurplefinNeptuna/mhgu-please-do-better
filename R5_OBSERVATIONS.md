# R5 observation evidence and display gate

Prepared 2026-10-07. DEVELOPMENT; r5 gameplay not run.

## Accepted r4 report

The user identified the first supplied screenshot as the reward grid and the
second as the village, and reported that observation works well. Both show
Miraculous Luck 31, eight generated slots and four extra slots with complete
traced coverage. The second retains those totals. Installed Please do Better
matches r4 NRO SHA-256
`498daa485beb2b8128cd31e0304ca1d11b5cdd2ec059d946fdd3fc2cea852699`.
R4 commit `f789cbb` and its candidate inventory are preserved.

The latest retained Eden log identifies master `10bcd2d849`, MHGU main build
FB08F1D20FD1204FE7070672777F869B, Forge 1.4.1-originalbi1, Better Input,
Damage Numbers Capture, Key Quest Markers, Modern Weapon Controls and Please do
Better. Both r4 startup transactions applied with unsafe masks zero. Screenshot,
log and candidate receipts are retained under ignored
`work/please-do-better/r5-report/`.

This supports that reported forced-observation session. It does not establish
natural luck, all reward categories, translation freshness, multicore safety,
or Ryujinx compatibility. R5 has no gameplay evidence.

## Eight additional dropped observations

The grid screenshot shows zero drops; the village screenshot shows eight.
R4's list-copy consumer demanded exact item and quantity equality with the
generation snapshot. Original collection code at `0x388EE8` legitimately changes
those entries: `0x38A110..0x38A11C` subtracts a transferred quantity, and several
paths clear both fields, including `0x389BC4`, `0x389CB0`, `0x389E58` and
`0x38A164`. R4 would count each later copy of such an entry as a capture drop.

R5 fixtures execute those original fragments and the native indexed list copy.
Same-index quantity decreases and empty pairs remain compatible refreshes;
empty bonus slots lose display eligibility. Changed IDs, quantity increases,
malformed empty pairs and failed reads remain genuine faults and suppress that
display provenance. Original generation totals are retained. No collection
count or collected-item record is added, and no game inventory is written.
Internal expected-refresh and mapping-fault counters distinguish the causes.

The two screenshots contain no event identities. They cannot prove that all
eight historical drops came from collection rather than another capture fault.
This is a verified false-fault mechanism, not a retroactive classification of
every event. Remaining faults stay visible under Diagnostics; they are neither
reset nor relabeled as expected without checking the relevant entries.

## Display-copy repair and compact interface

The existing paired UI update now observes state-1 main-array reallocation by
snapshotting the old prefix before native free, verifying the new prefix after
return, and following exact batch/array/index identity. Duplicate IDs are never
searched for or coalesced. Unknown, stale and incompatible copies stay unmarked.
Native capacity-16 and capacity-48 loop fixtures cover both main A and B offsets.

The normal panel shows the next-batch mode, save result, one completed-reward
summary and highlight availability. Diagnostics contains startup safety,
observation coverage, currently highlighted slots and genuine faults. Actionable
startup failure/site/cache details appear on failure. Raw counters and masks
remain internal; technical cache/resource evidence stays in documentation.

## Gold highlight acceptance

Gold rendering remains **unimplemented and disabled**, under the requested
acceptance gate. R5's compiled `0xA4FE50` boundary gateway passes offline state
fixtures but is never published. RESEARCH.md records the remaining slot-frame,
shader/viewport and presented-frame proofs. No guessed coordinates or claimed
gold-highlight coverage are shipped.
