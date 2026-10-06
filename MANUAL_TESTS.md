# Remaining gameplay coverage

The user reported an unresolved r2 observation failure on Eden with the reward
screen still open after a 2-star Great Maccao hunt and forcing enabled. R3 gameplay
is **NOT RUN**. Its diagnostic follow-up must record gateway hits, forced/natural
counts, raw threshold, build/publication/clearing counters and UI state while
rewards remain open. See R3_DIAGNOSTICS.md. Startup applied status alone does not
complete that check.

This checklist authorizes no installation, activation, launch, save edit or
emulator setting change. R2/r3 have no accepted highlight renderer;
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
