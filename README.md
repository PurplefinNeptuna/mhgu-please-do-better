# Please do Better

R1 is a local **DEVELOPMENT** candidate for MHGU Nintendo Switch 1.4.0 and
Forge 1.4.1, with Eden as the primary target. Gameplay and CPU translation
freshness have not been tested. This package is not approved for distribution.

The plugin reproduces exactly the two instructions in the wiki's `[Great Luck]`
cheat. The first forces the **Miraculous Luck** reward branch, returning `0x1F`.
You do not need Good Luck, Great Luck or Miraculous Luck equipped. It does not
add a visible equipment skill or guarantee rare drops, maximum rewards or
extra carves. The second change preserves the subsequent `0x102` skill check;
its broader gameplay role remains incompletely traced.

Both patches run once during Forge plugin startup. The compact **Please do
Better** row under **Plugin UI** reports the result and stays closed by default.
There are no toggles, preferences, hot reload or periodic writes. Closing the
row does not undo the patches. Removing/disabling the plugin requires a full
game restart. Crafting, equipment unlocks, inventory, recipes and global skill
queries are outside this plugin's scope.

## Local candidate

```bash
python3 scripts/please_do_better.py test
python3 scripts/please_do_better.py build
python3 scripts/please_do_better.py verify
python3 scripts/mod_distribution.py check
```

The build uses the existing pinned ARM32 container and Unicorn 2.1.4 environment.
It never downloads tools, installs packages into an emulator, activates mods,
launches a game or writes preferences/saves. Sources and tests are tracked;
generated binaries and evidence remain under `work/` and `build/`.

The candidate is `build/please-do-better/candidates/r1/please-do-better-r1-candidate.zip`.
It contains one named runtime package:

```text
Please do Better/romfs/nativeNX/plugins/please_do_better.nro
```

README, notices, manual checklist, candidate manifest and SHA-256 checksums sit
beside the ZIP. The manifest pins source, input-validation, host/ARM checks,
runtime and support bytes. Candidate packaging does not establish readiness;
promotion would require separate approval and the shared distribution packager.

## Compatibility and conflicts

The legacy Great Luck cheat must be disabled before a future authorized test.
An installed package already named **Please do Better** contains the old cheat;
this candidate uses that display name without replacing or merging its files.
Do not blindly overlay the ZIP onto that package: a leftover `cheats/` directory
would still conflict. Future installation must preserve the old package as a
rollback and verify cheat activation separately. This task performs neither step.

Startup rejects wrong titles, invalid mappings, changed signatures and already
patched instructions before editing either site. Failure rolls back only stores
made by this plugin whose current word still matches its replacement. External
modifications are preserved. An unsafe/rollback-failure status requires a full
restart and inspection; the plugin does not stop Forge from continuing startup.

The direct RX-code writes follow the maintained Modern Controls/Damage Numbers
emulator backend. They do not establish native Switch support. Flush SVC results,
barriers and readback are checked, but pinned Eden does not invalidate CPU
translations through that data-cache SVC. Early application is the selected
candidate approach; no Eden fix or increased success rate has been demonstrated.
Ryujinx compatibility is also untested for this NRO.

See [implementation and state audit](IMPLEMENTATION.md) and
[local validation](VALIDATION.md), with [remaining manual coverage](MANUAL_TESTS.md).
The maintained Forge loader and
Better Input are dependencies and are not bundled or changed.
