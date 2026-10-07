# Please do Better r16

MHGU Nintendo Switch 1.4.0 plugin for Forge. Highlights extra quest reward slots
enabled by positive luck with a subtle pulsing gold border and small sparkle.
Fresh installs use natural luck. Force Miraculous Luck is optional and needs no
equipped luck skill; it reproduces the original two-site Great Luck cheat.

Known Forge limitation: opening the Forge menu while background highlighting
is active can corrupt the menu's visuals. The user has confirmed this alongside
working reward markers. This release leaves Forge unchanged. Adjust settings
outside active highlighting and close the Forge menu when viewing marked rewards.
The existing renderer handoff is included as FORGE_MENU_LIMITATION.md.

## Use

Extract the named please-do-better folder from the ZIP as an emulator mod package.
It contains only romfs/nativeNX/plugins/please_do_better.nro. Forge must be
installed separately. Replace an older copy of this plugin rather than loading
two copies. Disable the legacy Great Luck cheat, including the old cheat package
also named Please do Better. Start a fresh game process after adding/removing
or replacing the plugin; enabling a conflicting/prepatched site is rejected.

Open Please do Better under Forge's Plugin UI outside active highlighting.
Force Miraculous Luck changes the request for subsequent reward batches;
already-generated rewards stay unchanged. Toggling does not require a restart.
Save settings persists the request through Forge's counted player-save mount in
please_do_better.ini and its plugin-specific recovery copy beside Better Input.
Without a valid saved preference, forcing starts off. Closing settings leaves
reward observation/highlighting active.

A gold marker means an extra slot enabled by luck compared with normal luck
using the actual rolls. It does not guarantee rare items, maximum rewards or
extra carves. Duplicate items remain distinct by batch, array, index and node.
Empty, stale, incompatible or unsupported slots are unmarked. Reward observation remains internal; settings show no reward summaries.
Crafting, equipment unlocks, inventory edits and global skill queries are absent.

## Coverage

The user confirmed r14 highlighting on an Eden reward grid; the installed hash,
matching log and screenshot are retained. R15 cleanup was statically verified without a separate gameplay retest. R16 removes diagnostic panels and uses brief, deduplicated Forge logs. Fresh compiled regressions pass; r16 has no new gameplay run. Normal frames emit no traces. The gold markers and background work continue with settings closed.

Natural positive luck/no luck, broader forced/live-toggle quest coverage,
repeated grids, collection/quantity decreases/transitions, animation alignment,
restart persistence, Eden multicore/translation freshness and Ryujinx remain
pending. The second forced check's broader role remains incompletely traced.
Readback/cache success does not establish Eden translation freshness. No native
Switch or universal emulator compatibility claim is made.

This is an approved local distribution, unpublished. Forge and Better Input are
external dependencies and are not bundled. Share the ZIP with NOTICES.txt.
Validation, runtime coverage and manual checks sit beside the ZIP.
