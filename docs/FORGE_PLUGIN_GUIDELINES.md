# Forge plugin development

Rules for the maintained Forge fork, requested 2026-10-04. Authority:
[AGENTS.md](../AGENTS.md); baseline: [FORGE_LOCAL_BRANCH.md](FORGE_LOCAL_BRANCH.md).

## Use the loader's facilities

Use Forge APIs fully where applicable. Before duplicating a facility, inspect
`tools/forge-local/include/forge/`, `tools/forge-local/source/forge/` and installed exports. Verify lifecycle,
ARM32 argument/return ABI and ownership.

Use Forge callbacks, logging, input, singletons, memory, hooks, rendering and
filesystem helpers. Preferences use its counted save mount/release, following
the active Eden user. Each plugin has its own config beside `better_inputs.ini`.
Balance mounts/handles and preserve other configs/game saves.

Configs use one plugin-specific primary INI only. Do not create, read, recover
from or delete `_backup` configs, and do not imitate the game's save backups.
Validate before writing, flush and verify the primary, then commit through
Forge's counted save mount. Balance handles and mounts on every failure path.
Keep session settings on failure; previous disk contents are not guaranteed.
Missing or invalid primary files use defaults. Save controls remain explicit.


When Forge lacks a needed operation or a verified ABI, threading or allocation
limit prevents using its wrapper, record that limitation in the plugin's research
or implementation notes. Use a native SDK binding or private implementation only
for the uncovered operation. Existing documented compatibility work remains
valid: ordinary Forge hooks allocate CodeMemory individually, and the legacy
64-byte Better Input shim is specific to its fingerprinted binary. Continue
checking actual ABI and allocation demand when adding hooks.

## Use compact collapsible plugin rows

Put every plugin's settings and save/reset controls inside its own compact,
unframed collapsible tree row under Forge's **Plugin UI**, matching the small
**Better Inputs Config** row. Keep it closed by default. The user clarified this
appearance on 2026-10-04: the large framed `CollapsingHeader` style belongs to
Forge's parent sections, not individual plugins.

Use `ImGui::TreeNode` / `igTreeNode_Str` and pair each opened row with
`TreePop` / `igTreePop`, including paths that return early. Use stable,
plugin-specific widget IDs. Do not show diagnostics, counters, addresses or runtime status in plugin panels.
Plugins without settings have no panel. Keep brief settings-edit/save feedback.
The damage-number plugin's `capture_panel()` in
`mods/damage-numbers/src/capture.cpp` follows this layout and uses scope guards
to balance its tree stack on every exit.

A closed row hides its panel contents; enable switches remain explicit settings.
Run gameplay overlays, update work and required background processing through
the appropriate Forge callbacks independently of the row's open state.

## Avoid APSR_g dependencies

The user retired the Ryujinx APSR GE repair on 2026-10-06. Current and future
plugins must work without that emulator patch. Do not introduce a requirement
for `msr APSR_g` or `msr APSR_nzcvqg` support. Preserve NZCVQ and all other live
state, and audit GE liveness at every hook continuation before omitting GE
restoration. If GE is live, choose a compatible hook site or implementation;
never discard required state. Review emitted restore instructions as part of
static release validation. Damage Numbers r17's eight-site GE audit is specific
to those sites and must not be generalized to new hooks.

## Standalone development and logs

New plugins start with `mod_distribution.py init NAME --kind plugin` and own
their complete source/build/test/export layout. Follow [STANDALONE_MODS.md](STANDALONE_MODS.md).
Use Forge logging: one short startup summary, committed settings changes, and
actionable failures. Deduplicate failures by fixed reason for the process
lifetime. Normal frames/hits/reward screens must not generate periodic logs.
Detailed diagnostics require an explicit development build and never add a UI
panel. Publish bounded faults from native hooks; format logs in safe callbacks.
Check ARM32 variadic arguments and worst-case text against Forge's formatter.
