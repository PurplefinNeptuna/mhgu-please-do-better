# Please do Better

R2 is a local **DEVELOPMENT** candidate for MHGU Nintendo Switch 1.4.0 and
Forge 1.4.1. It implements guarded live forcing, plugin preferences and bounded
reward attribution. **Slot highlights remain unavailable:** final screen geometry
and complete list-to-node mappings have not passed the required research gate.
This candidate draws no borders or luck markers.

Fresh installs use natural luck. With **Force Miraculous Luck** off, both original
checks run and equipped skills determine rewards. Turning it on reproduces the
wiki's two-site Great Luck cheat, including threshold `0x1F` and the retained
second-site `0x102` check. Forcing needs no equipped luck skill. It does not add
an equipment skill, guarantee rare drops, maximize rewards or add carves. The
second site's broader role remains incompletely traced.

Open the closed-by-default **Please do Better** tree under Forge's **Plugin UI**.
The checkbox changes the request immediately; each observed batch retains its
entry mode. Existing rewards stay unchanged. **Save settings** remembers the
request in `please_do_better.ini` with its plugin-specific recovery copy through
Forge's counted player save mount. Editing the checkbox cancels delayed loading.
Closing the panel leaves observation and storage polling active.

The row reports the mode for new batches, observed tier, verified bonus-slot count,
unavailable features and nested startup diagnostics. Attribution means extra slots
enabled by positive luck compared with normal luck using the observed rolls.
It cannot predict the items a separate unmodified run would produce. Collection
tracking and item-ID-only matching are absent.

## Local candidate

```bash
python3 scripts/please_do_better.py test
python3 scripts/please_do_better.py build
python3 scripts/please_do_better.py verify
python3 scripts/mod_distribution.py check
```

The recipe uses the maintained pinned offline ARM32 container and Unicorn 2.1.4.
It performs no installation, activation, game launch or real preference/save write.
The deterministic ZIP is
`build/please-do-better/candidates/r2/please-do-better-r2-candidate.zip`.
Its only member is:

```text
Please do Better/romfs/nativeNX/plugins/please_do_better.nro
```

Documentation, notices, manifest and checksums sit beside the ZIP. The original
r1 candidate and source commit `d01c9c3` are preserved. Neither candidate is
approved for distribution. Maintained Forge and Better Input are unchanged
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
freshness. Eden gameplay/multicore and separate Ryujinx compatibility are untested.
Native Switch support is not claimed. Crafting, equipment unlocks, inventory edits
and global skill-query hooks remain outside scope.

See [implementation](IMPLEMENTATION.md), [research gate](RESEARCH.md),
[local validation](VALIDATION.md) and [remaining gameplay coverage](MANUAL_TESTS.md).
