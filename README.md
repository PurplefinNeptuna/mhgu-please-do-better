# Please do Better

Current local recipe builds **r15 with quiet release logging**
for MHGU Nintendo Switch 1.4.0 and Forge 1.4.1. Verified extra reward frames get a
subtle pulsing gold border and tiny procedural sparkle, independently of whether
the panel is open. Native frame geometry, clipping and exact slot provenance
control placement. Unknown shader, target or execution paths remain unmarked.
See [highlight implementation](R15_RELEASE.md) and [validation](R15_VALIDATION.md).

The user confirmed visible r14 gold highlighting on Eden and approved local
distribution on 2026-10-07. R15 removes verbose render-log bundles while preserving
rendering, attribution, optional live forcing and preferences. R14's accepted
candidate and commit 1888454 remain unchanged. See [runtime acceptance](RUNTIME.md)
and [release notes](R15_RELEASE.md). R15 gameplay has not been repeated.

Forge's unresolved multi-list renderer issue can corrupt the settings menu while
background overlays are active. The user excluded repairing Forge from this task.
See [handoff](../../docs/FORGE_IMGUI_DAMAGE_CORRUPTION_HANDOFF.md). Adjust settings
outside active highlighting and close Forge while viewing marked rewards.

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
Closing the panel leaves highlighting, observation and storage polling active.

The row reports the mode for new batches, the last completed batch's observed
tier and verified slot totals. Closed diagnostics show startup safety, observation
coverage, currently highlighted slots and genuine capture faults.
Missing or partial observation reports the extra total unavailable. Completed
totals remain after collection; live provenance still clears at screen close.
Attribution means extra slots
enabled by positive luck compared with normal luck using the observed rolls.
It cannot predict the items a separate unmodified run would produce. Collection
tracking and item-ID-only matching are absent.

## Local candidate

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
`build/please-do-better/candidates/r15/please-do-better-r15-candidate.zip`.
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
