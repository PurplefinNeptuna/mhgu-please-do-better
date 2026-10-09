# Remaining gameplay coverage

R4 forced reward observation and R14 visible highlighting were accepted on the
tested Eden sessions. The 2026-10-08 R17-config1 setup was also user-confirmed,
with Forge 1.4.1-render1 and a screenshot showing menu and highlights together.
[RUNTIME.md](RUNTIME.md) records exact versions, hashes and limits. R19-savehint
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
