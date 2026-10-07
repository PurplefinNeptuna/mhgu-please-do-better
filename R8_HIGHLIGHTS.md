# R8 reward initialization repair

The user tested the committed R7 NRO (`2a0c3a8ad172af468a5f6cc8e41bd26e6ffb0d1fcdaa49f7e98dc0870127d9e3`)
and supplied a reward-grid screenshot before taking or moving any items.
It shows Miraculous Luck, eight generated rewards, two extras, zero bound/
highlighted slots and one capture/mapping fault. The latest Eden log includes
R7 loading and all three successful startup transactions on master-10bcd2d849.
Those startup messages establish publication, not correct display provenance.
The screenshot and log are copied under ignored `work/please-do-better/r8-report/`.

## Cause and repair

The original state-1 routine `0x384AF0`, called inside the paired UI update
`0x384848`, resizes the main reward array BEFORE generating the new rewards.
Its original BL at `0x384FC0` calls builder `0x3874E0` inside that SAME update.
R5-R7's observer saved the old, empty array at update entry and then compared
that snapshot with the generated items at return. The legitimate new contents
failed its relocation check; the clearing record discarded newly verified
provenance while retaining completed diagnostic totals.

The compiled R7 regression now reproduces that sequence, including the original
resize loop and count/copy fragment. It reports eight generated/four extras,
complete summary, exactly one added capture fault, no retained record and zero
bindings. The changed test fails against the preserved R7 binary. The user's
two-extra result varies with actual rolls; the fixture uses four extras to
verify the same provenance-clearing defect independently of RNG outcomes.

R8 supersedes an outer update's pre-generation snapshot when the nested builder
starts a new batch for the SAME UI object. The builder's existing exact native
copy and return validation establish the new array identity and contents.
The outer return no longer interprets new rewards as a copy of old rewards.
Different UI objects retain their relocation checks. An incomplete new batch
still reports unavailable; old provenance cannot be adopted. Actual relocation
and copy mismatches remain capture faults, with their route and available
item/quantity details shown in the closed diagnostics row.

This changes capture bookkeeping only. Native calls, item selection, RNG,
forcing, settings and gold geometry/presentation logic remain unchanged.
No added hooks, arena, TLS slot, heap buffer or game-data writes are required.
The original BL and exported state-1 instructions are checked against the full
pinned offline main identity; runtime identity remains exact guarded signatures,
not a full runtime build-ID check.

## Validation and remaining coverage

Fixtures cover the actual four-scope nesting (update -> builder -> wrapper ->
count), original resize/copy code, subsequent inline list copy, Festa frame
binding, native presentation and four gold borders/sparkles. They also cover
an initially unavailable array, an incomplete replacement batch and a different
UI object's genuine relocation failure. The fault route renders through the
compact panel with balanced trees. Existing register/flag/VFP, mode/RNG/settings,
rollback, bounded snapshots, clipping and stale-frame suites remain required.

No game, GPU or emulator is launched during preparation. R8 visible alignment
is pending. Natural positive luck/no luck, forcing/toggles, repeated grids,
collection/cursor/animation/village return, restart persistence, Eden multicore/
translation freshness and Ryujinx remain pending in MANUAL_TESTS.md.

R7 commit `ae7b2c3` and all 74 recorded R1-R7 candidate files remain preserved.
Maintained Forge and installed packages remain unchanged. DEVELOPMENT status
continues. No installation, activation, settings/save edit, push or publication.
Crafting, unlocks, inventory changes and collection tracking remain outside scope.
See R6_HIGHLIGHTS.md for geometry/shader/presentation proofs and R7_HIGHLIGHTS.md
for inherited Festa node and immutable list-copy guards.
