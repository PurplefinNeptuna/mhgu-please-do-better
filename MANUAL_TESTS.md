# Remaining gameplay coverage

The user reported an unresolved r2 observation failure on Eden with the reward
screen still open after a 2-star Great Maccao hunt and forcing enabled. The r3
item-grid screenshot confirms forced checks and threshold 31 executed, with
zero published records. **R4 gameplay is NOT RUN.** Capture gateway hits,
forced/natural counts, copy taps, published records, last completed tier, generated
and extra totals, coverage status and UI state while rewards remain open. See
R4_OBSERVATIONS.md. Startup applied status alone does not complete that check.

This checklist authorizes no installation, activation, launch, save edit or
emulator setting change. Highlights remain unimplemented until added rewards can
be observed in gameplay; r4 has no accepted highlight renderer. Later
marker tests require a later candidate that passes [RESEARCH.md](RESEARCH.md).

- [ ] Identify exact NRO/ZIP hashes and actual launch set; retain rollback packages
  and a fresh hashed launch log.
- [ ] Disable the legacy Great Luck cheat, including the old Please do Better
  cheat package. Verify selected activation, not directory presence.
- [ ] Verify MHGU 1.4.0/main build and maintained Forge/Better Input fingerprints.
- [ ] Cover startup, ordinary save loading, Forge navigation, quest completion/
  return and full restart. Examine ownership/cache/rollback diagnostics.
- [ ] With forcing off, compare no-luck and natural Good/Great/Miraculous Luck
  across repeated comparable quests. No visible equipment skill is added.
- [ ] With forcing on and no equipped luck, cover the intended Miraculous branch
  across repeated quests. One lucky screen is insufficient evidence.
- [ ] Toggle before, during and after generation: current batches keep their latch,
  future checks use the new choice, and existing rewards stay unchanged.
- [ ] Check Save settings/restart persistence, delayed storage availability and
  edit cancellation through the plugin's own files.
- [ ] Cover repeated reward screens, nested/overflow diagnostics, closing and return;
  inspect incomplete/lost attribution.
- [ ] Verify completed totals survive UI state 18, collection and return. Missing
  records/taps must report unavailable or incomplete, never a verified zero bonus.
- [ ] Compare all four copy routes and absent tables against visible item prefixes;
  cover duplicate items, capped guarantees, main A/B and secondary rewards.
- [ ] Document Eden translation freshness/multicore separately from flush/readback.
  Cover removal and full-restart baseline recovery when authorized.
- [ ] Repeat startup/modes/quest/return/persistence on Ryujinx with its exact revision,
  loader fingerprint and fresh log.
- [ ] Investigate the second site's broader gameplay role; retaining its 0x102
  continuation does not establish its complete behavior.
- [ ] After the display gate passes, test natural positive-luck markers, no-luck
  suppression, forced mode, scale/animation/clipping, rows, duplicate items,
  cursor/icons, empty/changed entries and repeated screen lifetimes.

Normal collection is outside attribution and may persist through ordinary game
saving. No collection tracker is planned. Crafting, equipment unlocks and
inventory editing remain outside scope.
