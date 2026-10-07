# Runtime acceptance

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

The user reports Forge's menu corrupts while this background overlay is present,
and explicitly excludes fixing forge-patched from this task. The inspected Forge
multi-list buffer offset defect is documented in
docs/FORGE_IMGUI_DAMAGE_CORRUPTION_HANDOFF.md. Its relevance to this plugin
fits the source mechanism and user report; no fixed Forge build was tested.
The limitation remains disclosed in the release README. Use the settings panel
outside reward highlighting and close Forge's menu while viewing marked rewards.
This guidance does not change or repair Forge.

This is scoped Eden acceptance, not exhaustive coverage. Natural positive luck,
no luck, forced/live toggles across repeated batches, save loading/restart
persistence, collection/quantity decreases, repeated grids/transitions/destruction,
animations, Eden multicore/translation freshness, Ryujinx and the second check's
broader gameplay role remain pending or incompletely traced. No clean-shutdown,
rare-drop guarantee, native Switch or universal emulator compatibility claim.

## r16 standalone/settings/log cleanup

This binary has its own fresh compiled/static checks, recorded in CLEANUP_VALIDATION.json. No new gameplay test was run; the preceding observations retain their original version and scope. Forge remains unchanged.
