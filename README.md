# Please do Better

Current release: **r17-config1**, with primary-only configs. The user confirmed
the tested Eden setup on 2026-10-08. [Release details](R17_RELEASE.md) and
[installation guide](DISTRIBUTION_README.md). Earlier reports retain their
original version; Forge remains LOCAL_ONLY.

## Build this mod

Run `./build.sh doctor`, `./build.sh prepare`, `./build.sh build`,
`./build.sh test --host`, `./build.sh test`, `./build.sh verify`, and
`./build.sh package` from this folder. The entry point also works from any other
current directory. `package --release` requires the approved payload and full
validation. `build --diagnostics` produces a development build only.

Dependencies are pinned in `dependencies.lock.json`; Python requirements are
pinned in `requirements.txt`. Downloads occur only with `prepare --fetch`.
Copy `build.local.example.json` to ignored `build.local.json` and configure
copies of your MHGU 1.4.0 main/SDK, Forge loader, and required resource inputs.
No installed emulator package or emulator settings file is needed.

The coordinating workspace retains root `build/` and `work/` outputs. An
independent checkout uses its own ignored `build/` and `work/` directories.
The author keeps all rights to owned code; third-party and font licenses remain separate.


Current source release: **r17-config1**, using only the primary config.
See [config candidate](CONFIG_CANDIDATE.md). The preceding r16 delivery is archived with verified hashes.

The recipe retains **the settings-only panel and quiet release logging**
for MHGU Nintendo Switch 1.4.0 and Forge 1.4.1. Verified extra reward frames get a
subtle pulsing gold border and tiny procedural sparkle, independently of whether
the panel is open. Native frame geometry, clipping and exact slot provenance
control placement. Unknown shader, target or execution paths remain unmarked.
See [highlight implementation](R16_RELEASE.md) and [validation](R16_VALIDATION.md).

The user confirmed visible r14 gold highlighting on Eden and approved local
distribution on 2026-10-07. R15 removes verbose render-log bundles while preserving
rendering, attribution, optional live forcing and preferences. R14's accepted
candidate and commit 1888454 remain unchanged. See [runtime acceptance](RUNTIME.md)
and [release notes](R16_RELEASE.md). R15 gameplay has not been repeated.

The isolated Forge `1.4.1-render1` candidate corrects concatenated draw-list
offsets. Its host regression passes, and the user confirmed the tested Eden setup.
The runtime report records the scope; Forge remains LOCAL_ONLY.

Fresh installs use natural luck. With **Force Miraculous Luck** off, both original
checks run and equipped skills determine rewards. Turning it on reproduces the
wiki's two-site Great Luck cheat, including threshold `0x1F` and the retained
second-site `0x102` check. Forcing needs no equipped luck skill. It does not add
an equipment skill, guarantee rare drops, maximize rewards or add carves. The
second site's broader role remains incompletely traced.

Open the closed-by-default **Please do Better** tree under Forge's **Plugin UI**.
The checkbox changes the request immediately; each observed batch retains its
entry mode. Existing rewards stay unchanged. **Save settings** remembers the
request only in `savedata:/please_do_better.ini` through Forge's counted player
save mount. Existing `_backup.ini` files are ignored and untouched. Writes are
flushed and verified before commit; failures retain the session choice but may
have changed the primary file. Missing or invalid primary files use defaults. Editing the checkbox cancels delayed loading.
Closing the panel leaves highlighting, observation and storage polling active.

The row contains the forcing preference, Save settings and brief edit/save feedback. Runtime status, counters and reward summaries are absent. Actionable failures go to concise, deduplicated Forge logs.
Attribution means extra slots
enabled by positive luck compared with normal luck using the observed rolls.
It cannot predict the items a separate unmodified run would produce. Collection
tracking and item-ID-only matching are absent.

## Versioned build and release

```bash
python3 scripts/please_do_better.py test
python3 scripts/please_do_better.py build
python3 scripts/please_do_better.py verify
python3 scripts/mod_distribution.py package please-do-better
python3 scripts/mod_distribution.py check
```

The recipe uses the maintained pinned offline ARM32 container and Unicorn 2.1.4.
It performs no installation, activation, game launch or real preference/save write.
The deterministic ZIP is
`build/please-do-better/candidates/r17-config1/delivery/please-do-better-r17-config1-candidate.zip`.
Its only member is:

```text
Please do Better/romfs/nativeNX/plugins/please_do_better.nro
```

Documentation, notices, manifest and checksums sit beside the ZIP. The original
r1 candidate/source commit `d01c9c3`, r2/r3 and accepted r4 commit `f789cbb` and
candidate bytes are preserved, including r5 commit `fe87ff1`. The earlier
candidates remain historical inputs; the approved release uses the shared
packager and the authoritative DISTRIBUTION.json record. Maintained Forge and Better Input are unchanged
dependencies and are not bundled.

Disable the legacy Great Luck cheat for a separately authorized gameplay test,
including the old cheat package named Please do Better. Startup rejects prepatched
or conflicting bytes. Do not overlay this candidate onto a package containing
`cheats/`. Removing the plugin requires a full restart.

Hooks publish once at startup; toggles never rewrite game instructions. Failed
startup restores only owned words and preserves external edits. Unsafe restoration
is reported explicitly, retaining reachable executable storage. Effective forcing
stays disabled if batch capture cannot be installed.

Readback, checked cache calls and barriers do not establish Eden translation
freshness. R4 has user evidence of successful forced reward observation on Eden.
R13 visible alignment, natural-luck observation, broader reward coverage and multicore
behavior remain unverified. Ryujinx compatibility is untested.
Native Switch support is not claimed. Crafting, equipment unlocks, inventory edits
and global skill-query hooks remain outside scope.

See [implementation](IMPLEMENTATION.md), [research gate](RESEARCH.md),
[r2 local validation](VALIDATION.md) and [remaining gameplay coverage](MANUAL_TESTS.md).
