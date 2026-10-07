# Please do Better

Current local recipe builds **r12 gold luck highlights and compact diagnostics**
for MHGU Nintendo Switch 1.4.0 and Forge 1.4.1. Verified extra reward frames get a
subtle pulsing gold border and tiny procedural sparkle, independently of whether
the panel is open. Native frame geometry, clipping and exact slot provenance
control placement. Unknown shader, target or execution paths remain unmarked.
See [highlight implementation](R12_RENDER_LOGGING.md) and [validation](R12_VALIDATION.md).

The accepted r4 run observed eight generated slots and four luck extras, retained
in the village. The latest r11 reward grid has ten bound extras and zero
highlights/faults. Its matching Eden log identifies 16,653 captures rejected at
the clipping check, with no geometry published. R12 reproduces the native
sentinel comparison and viewport substitution omitted by earlier candidates.
Raw/sentinel/effective clipping records are confined to the emulator log.
**Visible r12 highlights remain unconfirmed.** Status is **DEVELOPMENT**.

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
python3 scripts/mod_distribution.py check
```

The recipe uses the maintained pinned offline ARM32 container and Unicorn 2.1.4.
It performs no installation, activation, game launch or real preference/save write.
The deterministic ZIP is
`build/please-do-better/candidates/r12/please-do-better-r12-candidate.zip`.
Its only member is:

```text
Please do Better/romfs/nativeNX/plugins/please_do_better.nro
```

Documentation, notices, manifest and checksums sit beside the ZIP. The original
r1 candidate/source commit `d01c9c3`, r2/r3 and accepted r4 commit `f789cbb` and
candidate bytes are preserved, including r5 commit `fe87ff1`. These
candidates are not approved for distribution. Maintained Forge and Better Input are unchanged
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
R12 visible alignment, natural-luck observation, broader reward coverage and multicore
behavior remain unverified. Ryujinx compatibility is untested.
Native Switch support is not claimed. Crafting, equipment unlocks, inventory edits
and global skill-query hooks remain outside scope.

See [implementation](IMPLEMENTATION.md), [research gate](RESEARCH.md),
[r2 local validation](VALIDATION.md) and [remaining gameplay coverage](MANUAL_TESTS.md).
