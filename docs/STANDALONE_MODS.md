# Standalone mod development

Start future mods with `python3 scripts/mod_distribution.py init NAME --kind
plugin|resource|cheat|tool`. The default kind is plugin. Existing mod folders are
preserved. New scaffolds begin at DEVELOPMENT; they implement no gameplay change.

Each source folder owns its build entry point, recipes, tests, documentation,
licenses and pinned helper/dependency snapshots. Do not import sibling mods or
require installed emulator packages, machine-specific paths or parent Git history.
Dependency refreshes are explicit reviewed changes, followed by relevant tests.

Use `mods/NAME/build.sh doctor`, `prepare`, `build`, `test --host`, `test`,
`verify`, and `package`. `prepare --fetch` is the only download command;
`build --diagnostics` is for development. `package --release` uses the approved
record and complete matching evidence. Commands never install or publish.

Configure copied main/SDK/Forge and resource inputs in ignored `build.local.json`.
The example file describes the configuration. Keep original inputs intact.
Plugin templates carry no hooks or settings until implemented; other kinds
start with an empty `recipe.json` payload map. Empty recipes cannot make a package.

Export a source repo with `python3 scripts/standalone_mods.py export NAME
--output /path/to/unused-directory`. Only entries in `EXPORT.json` are copied;
unsafe paths, symlinks, runtime binaries, game assets and ignored trees are
rejected. Refresh the allowlist deliberately after adding owned source with
`python3 scripts/standalone_mods.py refresh NAME`. The export records the parent
commit and source/export hashes, omits Git metadata, and redacts private machine
paths from prose and JSON. Create remotes or publish only as separate actions.

Workspace builds keep the existing root build/work paths; exported sources use
local ignored build/work folders. No build regenerates tracked native source.
Modern Controls has an optional `help` command requiring explicit base/HD/library
inputs and preserving whole-resource priorities and required companions.

Panels contain only actual settings and their save/reset feedback. Mods without
settings have no panel. Runtime diagnostics use short startup/change/failure
messages, deduplicated for the process lifetime. Default builds log no hit,
geometry, camera or periodic counter dumps. Background overlays remain active
with settings panels closed. Follow the Forge ABI and APSR/GE audit rules.
