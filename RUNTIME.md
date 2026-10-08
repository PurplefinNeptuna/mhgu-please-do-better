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

## 2026-10-08: primary-only config release acceptance

The user reported "all works well" and requested promotion to ready to
distribute, keeping Forge LOCAL_ONLY. The tested Eden installation matches
r17-config1 NRO SHA-256 `bf2263640192b4b6bdb33b0cb507ea7dfe8a65fc86e27f3b90a91fee860eacbe`. The supplied reward-screen screenshot
shows the Forge menu and PDB gold highlights visible together. Eden's retained
log records Forge 1.4.1-render1, PDB r17-config1 and successful Damage Numbers
settings saves. Damage Numbers still prints its older r20 startup label; its
installed file hash identifies the tested r22-config1 bytes.

[Release runtime evidence](docs/CONFIG_RELEASE_RUNTIME.json) records the
log/screenshot hashes and scope. This is the user's confirmation of the tested
setup, not exhaustive dropdown/transition/save-restart coverage or a clean
shutdown claim. The newest Ryujinx log used older plugin bytes and is not
confirmation of this release. Distribution preparation rebuilds no runtime,
installs nothing and publishes nothing. Earlier entries remain historical.

## 2026-10-08: r18-config2 config simplification

The config codec now writes no version marker and reads existing `version=2`
files without changing their preferences. Host tests execute production storage
with a recording filesystem; compiled ARM32 fixtures cover old-file load,
explicit versionless save and restart. These are simulated storage results,
not a new emulator/game run. Earlier runtime reports keep their original
version and binary scope. Nothing was installed or activated by this task.

## 2026-10-08: r19-savehint save-location wording

The success message names this plugin's INI and MHGU's save folder. Public
instructions use the same location without referencing another plugin.
Persistence, config fields, hooks and gameplay behavior are unchanged.
Scoped validation is recorded in [SAVE_HINT_VALIDATION.json](docs/SAVE_HINT_VALIDATION.json).
No new gameplay run or installation was performed for this wording revision.
