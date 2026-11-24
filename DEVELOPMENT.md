# Please do Better: development and research

**Current state.** r37 is PUBLISHED as the GitHub release `r37`, released at `build/please-do-better/releases/r37/`
and working on MHGURecomp; it was not run on Eden. It registers from `purplelib_on_register`
(Purple-lib API version 3) and needs Purple-lib r17 or later for its Mod Options page. The
tested candidate stays in `build/please-do-better/candidates/r37/` ([where it ran](EVIDENCE.json)). Every hook is installed through Forge's hook API; highlights are white
native frames. [Install and settings](README.md); [status and hashes](DISTRIBUTION.json); [exact
results](EVIDENCE.json); [tester steps](TESTING.md); [provenance](THIRD_PARTY.md); [release
credits](DISTRIBUTION_NOTICES.md).

Marks verified extra luck reward slots by turning their native frame white. Natural luck is the default; optional Force Miraculous Luck reproduces the wiki's two-site cheat without changing equipped skills. The 1x to 5x integer slider scales player reward pages and leaves the Palico page unchanged. The primary INI requires `[PleaseDoBetter]`; old formats use defaults.

Ryubing 1.3.3 has run only the r27 frame-tint probe, where white frames held through the cursor and item pickup.

Still unconfirmed: natural positive luck, no luck, forced and live toggles across repeated batches, save and restart persistence, collection and quantity decreases, repeated grids and transitions, player-page multiplier, Palico exclusion, appraisal and collection, consecutive quests, Ryujinx beyond the r27 probe, and physical Switch. No clean-shutdown claim is made; Maxwell, HLE and unmapped-memory messages in the logs are not attributed to this plugin. The second check's broader role is incompletely traced. Disable the legacy Great Luck cheat for an authorized test, because startup rejects prepatched or conflicting code.

## Developing please-do-better

Run `./build.sh COMMAND` from any directory: `fetch` (once, downloads `vendor/`), `doctor`, `prepare`, `build`, `test --host`, `test`, `verify`, `package` and `export --output DEST`. Builds are offline with the pinned Rust nightly, vendored forge-rs 1.5.0 and the separately pinned cargo-forge 1.4.1 converter.

Copy `build.local.example.json` to ignored `build.local.json`, then set the tools and copied main/SDK/Forge inputs. Their supported SHA-256 values are in `dependencies.lock.json`; the main build ID and hook signatures are checked too. Changing dependencies or hook sites requires a reviewed lock update, import checks, focused fixtures and GE liveness revalidation. `core/` holds the portable logic and `core/tests/` its host tests. `src/` holds the gateways, reward capture, overlay and settings. The ARM probes in `scripts/` execute the compiled plugin and read its private state through hidden `pdb_*` symbols, which never reach the NRO's exports.

Forge's hook API places every hook. Forge copies a target's first eight bytes without relocating them, and the second word at main+0x381fec is `ldr r0,[pc,#0x108]`, so that entry's original is the fixed stub `pdb_main_count_original` in `src/gateway.S`. Forge has no mapping query, program ID or process cache flush, which is what `src/svc.S` supplies.

Use settings-only panels. Format logs in Forge callbacks, outside native hooks. Keep one startup summary, meaningful committed preference changes and readable actionable failures. Never reset failure reason masks; unchanged frames stay silent. Overlays and background work run with settings panels closed.

Export only `EXPORT.json` entries. `source-export.json` records the parent commit and source/export hashes. Exports omit game assets, outputs, caches, backups, private configurations, historical asset editions and Git metadata. Initialize remotes and publish separately.

## How it works

Design, hooks and native detail are in `docs/worked/`: [Please do Better: cache and instruction-state audit](docs/worked/cache-audit.md), [Please do Better: Mod Options](docs/worked/mod-options.md), [Please do Better: capture and attribution](docs/worked/reward-capture.md), [Please do Better: hooks and multiplier](docs/worked/reward-multiplier.md).

## Please do Better native research

The highlight and state rules are under "Implementation and state audit".

### Local research inputs

Read-only RomFS inputs were copied under ignored `work/please-do-better/inputs/`.
Originals are unchanged. Game binaries, shader programs, decompiled functions and
external emulator snapshots are not committed or bundled.

| Copied input | SHA-256 |
|---|---|
| AppShaderPackage.mfx | `2b80892da570f42b38dfe46b31234503af3d593eb634da10109c37534ac36627` |
| root.arc | `63d861e9beb9464ca8308760479ed2514d87e9975568889b9599e7a22d91615c` |
| sc/NX/root.spkg | `7dea1d84f3e64d1a79df8f7a4d7bdf063643e996de6cfab95e7c5d782f8b795e` |

Root ARC holds one shader resource of 58,841,740 bytes unpacked, larger than 24 bits can count; ARC sizes are the low 29 bits of the entry's flags (`SIZE_MASK` in `scripts/mhgu_assets.py`). Native loader `0xCE1FBC` verifies SPK magic, version
0x26 and shader version 0xB2D34C60. Metadata/variant tables were inspected, but the
exact GUI vertex program and constant-buffer bindings remain unresolved. No GPU
equation is accepted from a guessed table entry or unrelated shader variant.

Read-only Ghidra exports retain original bytes/mismatch counts under ignored
work/tmp paths; no GZF or annotations were edited. Saved DTI provides leads,
subordinate to original instructions.

### Reproduce

`./build.sh test` runs the `please_do_better_*_probe.py` fixtures. CPU fixtures do not establish GPU alignment, translation freshness or broader
reward-category coverage.

## Remaining gameplay coverage

For any authorized follow-up, keep the exact payload hashes, launch set and latest emulator log. Disable the legacy Great Luck cheat, verify activation separately from folder presence, and use MHGU 1.4.0.

- [ ] Compare no luck and natural Good/Great/Miraculous Luck across repeated quests.
- [ ] With forcing on and no equipped luck, check repeated batches; one lucky screen is insufficient.
- [ ] Toggle before/during/after generation: batches keep their entry mode and existing rewards remain unchanged.
- [ ] Check Save settings/full restart, delayed storage and manual-edit cancellation with the primary INI.
- [ ] Cover duplicate items, quest guarantees, main A/B, secondary rewards and all four verified copy routes.
- [ ] Cover capacity-16/48 reallocation, repeated grids, row/category changes and screen destruction.
- [ ] Check collection/quantity decreases: stale/empty slots hide and ordinary refreshes produce no false faults.
- [ ] Check the white frames on every reward page layout and with the cursor on and off a highlighted slot.
- [ ] Confirm village return clears live highlights while retaining completed scalar totals.
- [ ] Check Forge combos, navigation and overlays on the exact loader version.
- [ ] Document Eden multicore/translation freshness separately from guest flush/readback.
- [ ] Test Ryujinx startup, modes, quest/return and persistence with its exact revision and fresh log.
- [ ] Trace the second check's broader gameplay role; retaining its `0x102` continuation does not prove complete behavior.

These checks do not authorize installation, launch, save edits or emulator
settings changes. Native Switch and clean shutdown are not established.

## Implementation and state audit

### Logging

Startup safety records and one record per failure class only. No capture or per-frame logs; gateways format no text. The config codec writes no version marker and reads existing `version=2` files without changing preferences.

### Do not

- **Draw the highlight as an ImGui overlay.** Its capture hook inside the GUI texture draw `0xA4FC9C` leaves that per-draw function interpreted on MHGURecomp; the native frame tint needs no render hook. The overlay's native addresses are in the mhgu-understanding native GUI reference.
- **Compare a nested builder's new generation records with the outer empty array.** A same-object new batch supersedes the outer preimage.
- **Read the secondary routine's return register as a count.** It returns void; derive the count from comparisons.
- **Read the old allocation after native return, or compare earlier copy mappings with later destination bytes.**
- **Select slots by item ID alone.** Bindings use exact UI, batch, list, group, index, frame-node and icon-node identity.
- **Log per frame in release.** Run traces and address or matrix dumps were removed.

## Open items

- **MHGURecomp frame cost.** The luck, copy and threshold functions run interpreted there once hooked; they run only while rewards are generated, and the cost is unmeasured (`MHGU_INTERP_STATS=1` measures it).
