# R7 display-copy and texture-class repair

The user supplied an R6 reward-grid screenshot on 2026-10-07. The installed
NRO hash was `07492e80d26684a47a424458aca943254bd7118dbc841b34fed07aceebfc609a`,
matching committed R6. Eden master-10bcd2d849 logged successful conditional,
observation and highlight installation. The screenshot reports eight generated
slots, four extras, zero highlighted slots and one incompatible display copy.
This is evidence of a failed runtime highlight test. It does not identify the
individual mismatched entry or prove which rendering guard rejected the nodes.
A copy of the log and screenshot is retained in ignored `work/please-do-better/r7-report/`.

## Verified repairs

Original main vtables at `0x178FCC8` (`cGUIObjTexture`) and `0x176C7C4`
(`cFestaGUIObjTexture`) share all thirty checked method entries except the
class-specific destructor and DTI method. Both use texture draw `0xA4FC9C`
and the same inherited layout/vertex methods. The saved DTI reports both at
304 bytes. R6 rejected Festa's subclass despite this compatible native ABI.
R7 accepts these two exact vtables; unrelated classes remain rejected.
The source texture resource uses the base class hash; it does not imply that
its instantiated runtime node must retain the base vtable.

List-copy `0x623C08` copies items/quantities by index into list+0x60. R6 published
only the mapping and reread its mutable destination during Forge update.
R7 snapshots the copied entries at native return in bounded eight-entry chunks,
up to 48 entries. A first-chunk flag replaces only bindings for that exact list.
Copying a different list cannot clear existing main-list provenance. A later
copy to the same list supersedes the earlier identity without comparing the
earlier mapping with its newer bytes. Mailbox overflow still rejects attribution.
The existing sixteen-record per-thread mailbox, eight contexts, four scopes,
one TLS slot and pooled arena remain unchanged.

Read-only traces of `0x384848`, `0x386A2C` and `0x386C6C` verify that the reward
UI refresh selects the array descriptor from category fields +0x5C/+0x64/+0x6C/
+0x74 and calls the native list copy during its paired update. Items are not
matched by ID alone. These repairs cover real implementation defects; the
screenshot lacks entry-level data to assign its single fault to either one.
Diagnostics now retain the last mismatched chunk-relative index and expected/current item and
quantity, plus the bound extra-slot count. Startup success is described as
highlight availability, rather than a claim of visible runtime verification.

## Validation scope

Compiled fixtures include both original texture classes, all supported GUI
ordinals and a complete count/copy/list/Festa-binding/presentation/draw chain:
eight generated entries and four extras produce four gold borders and sparkles.
Delayed same-list refreshes, unrelated-list copies and 48-entry chunks are
covered, along with over-capacity and payload-query failure invalidation. Mode/RNG/settings, rollback, register/flag/VFP, clipping and stale-frame
regressions remain required. No emulator or GPU was launched for R7.

R6 candidate files and commit `d9aba55` are retained. The maintained Forge and
installed packages are unchanged. R7 is DEVELOPMENT and its visible alignment
still needs a user-run reward-grid check. Natural luck, no luck, live toggles,
repeat grids, collection, animation/cursor alignment, village return, Eden
multicore/translation and Ryujinx remain pending. See R6_HIGHLIGHTS.md for the
unchanged geometry, shader and native presentation proofs. No guessed placement,
additional RNG, inventory edits or collection tracker is introduced.
