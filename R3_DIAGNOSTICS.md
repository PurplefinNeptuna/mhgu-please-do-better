# R3 execution diagnostics

R3 is a local DEVELOPMENT diagnostic candidate, prepared 2026-10-07.
It adds counters without changing the r2 reward algorithm, hook sites, live-mode
rules, preferences or renderer. R1 and r2 candidates remain preserved.

The user completed Village 3-star Harvest Tour: Deserted Island and a 2-star
Great Maccao hunt. The supplied screenshot was taken with the reward screen
still open: force enabled, observed tier Unavailable (0), zero extra slots,
both hook groups applied, and zero dropped observations. Installed Eden NRO
SHA-256 matched r2; the latest log showed MHGU 1.4.0 and both startup groups
applied. This does not establish gateway execution or a successful reward effect.
The failure is unresolved; it must not be dismissed as an unlucky roll.

Open the nested Diagnostics row to read cumulative process counters:

| Counter | What it establishes |
|---|---|
| Executed checks | Conditional gateway actually entered, independently of published bytes |
| Forced/natural checks | Which path each conditional gateway selected |
| Main/secondary counts and comparison taps | Reward-count observation actually executed |
| Last comparison threshold | Raw threshold at the last comparison; not a displayed-slot attribution |
| Reward builds entered/returned | UI batch scope entered and completed |
| Generation returns | Observed generation scope returned |
| Published reward records | Traced destination passed content verification and publication |
| Clearing events / last UI state | State guard discarded provenance, with native state reported |
| Forge updates | Observation consumer callback is executing |

If checks remain zero after a completed eligible quest, startup readback has
not demonstrated execution. Eden translation freshness is one possible cause,
not a confirmed diagnosis. If checks execute but build/publication counters do
not advance, investigate the native capture/copy route. If records publish then
clearing events remove them during rewards, investigate the state/lifetime guard.
Zero extra slots with a valid observed tier is a different result from Unavailable.

Static tracing also shows native result update uses state 0x13 for transitions
and stores the preceding state at +0x40. R2 clears observations outside states
2..5. R3 retains that behavior and exposes the state; no guessed state/lifetime
fix is accepted from the screenshot alone.

Counters use fixed scalar atomic storage. They are read in ImGui, introduce no
logging/filesystem operations in gateways, no new hooks or allocations, no RNG,
and no gameplay instruction rewrites. Overflow wraps cumulative counters; it
does not change game behavior. The full compiled gateway state audit still applies.

No highlighting is implemented. R3 preparation does not install, activate,
launch, edit existing preferences/saves or change the emulator. A separately
authorized runtime session is still required to obtain these counters.
