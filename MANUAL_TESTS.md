# Remaining gameplay checks

All items below are **NOT RUN**. Installation, activation and game launches
require a separate user-authorized session. This checklist does not authorize
save editing, emulator setting changes or installation. Normally collected
quest rewards can persist through ordinary game saving.

## Required Eden checks

- [ ] Preserve rollback packages and identify the exact r1 NRO/ZIP hashes.
- [ ] Disable the legacy Great Luck cheat, including any old `Please do Better`
      cheat package. Verify the actual selected mod/cheat set, not folder presence.
- [ ] Confirm MHGU 1.4.0/main build `FB08F1D20FD1204FE7070672777F869B`
      and the maintained Forge/Better Input fingerprints in the launch evidence.
- [ ] Retain/hash the launch log. Confirm the plugin startup result reports both
      patches applied without rollback/cache errors. This alone proves no reward effect.
- [ ] Load an ordinary save, open/close the compact plugin row, and confirm normal
      controls and Forge navigation. No new visible equipment skill is expected.
- [ ] Complete and return from comparable quests without equipped luck skills.
      Record reward screens across repeated quests, with an unpatched comparison.
      A single lucky result does not establish the probability effect. Determine
      whether the observations support the expected branch; do not infer rare-drop
      guarantees or an unmeasured success rate.
- [ ] Fully restart and repeat a quest/return. Check that no old cheat or stale
      process state was retained. Document remaining multicore/cache uncertainty.
- [ ] Confirm the observed crafting/equipment availability and inventory behavior
      show no unexplained changes. The plugin contains no changes to these paths.
- [ ] In a separate authorized rollback check, disable/remove the plugin and fully
      restart; retain the log and confirm baseline behavior returns.

## Additional coverage

- [ ] Repeat the required startup/quest/return/restart checks on Ryujinx with its
      actual loader fingerprint and fresh log. Eden evidence does not cover it.
- [ ] Cover additional quest categories/ranks when useful; record which were tested.
- [ ] Investigate the second site's broader gameplay role if a concrete issue appears.

Stop and inspect any signature conflict, unsafe state, cache failure or partial
rollback. Do not use live reinitialization as a recovery mechanism. Preserve
logs before another launch overwrites them.
