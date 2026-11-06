# Please do Better r29: testing

r29 installs its hooks through Forge instead of its own code memory, so it can load on MHGURecomp.
Highlights and settings are r28's.

## Steps

1. On Eden, install r29 and turn on Force Miraculous Luck. Finish a quest and open the Reward Box:
   the extra-luck slots should have white frames, as with r28. Try a reward multiplier above 1x
   and check the player pages' quantities.
2. On MHGURecomp, enable the mod. `run.sh` skips it while `please-do-better` is in its `EXCLUDE`
   list, so take it out of that list first. Then repeat step 1 there.
3. Send both logs: Eden's `eden_log.txt` and MHGURecomp's `recomplog.txt`.

## Log lines

At Forge's shipped `level = error` the plugin logs nothing in a normal run. At `level = warning`
these can appear, each once:

| Line | Meaning |
| --- | --- |
| `[please-do-better] Hooks unavailable: ...; remove conflicting mods, verify game/Forge, then restart` | The hooks were refused or rolled back, so luck forcing, highlights and the multiplier are off. The reason names the check that failed. |
| `[please-do-better] Highlights unavailable: the frame colour setter differs; verify game/Forge` | The game's colour setter did not match at startup, so no frame is tinted. |
| `[please-do-better] Reward mapping incomplete; uncertain highlights skipped; restart if persistent` | A reward copy did not match what was generated, so those slots were not highlighted. |

On MHGURecomp, `recomplog.txt` also shows Recomp's own lines, such as
`hook at main+..., inside the function at main+... (which runs in the interpreter now)` for each
interior site. Those are expected.
