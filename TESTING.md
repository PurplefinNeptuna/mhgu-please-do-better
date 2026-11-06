# Please do Better r28: testing

r28 highlights extra-luck reward slots by turning their frame white, in place of the gold border.
Run it on Eden or Ryubing.

## Steps

1. Install r28 and turn on Force Miraculous Luck, so the reward screen has highlights.
2. Finish a quest and open the Reward Box. The extra-luck slots should have white frames and no
   gold border; every other frame keeps its red or blue.
3. Move the cursor onto a white slot and away again. It should turn yellow under the cursor and
   white again after.
4. Take the item from a white slot. Its empty frame stays white.
5. Finish a second quest. Only that quest's extra-luck slots should be white.
6. If you can, finish a quest with Force Miraculous Luck off and a Luck skill on, and check the same.

## Log lines

At Forge's shipped `level = error` the plugin logs nothing in a normal run. At `level = warning`
these can appear, each once:

| Line | Meaning |
| --- | --- |
| `[please-do-better] Highlights unavailable: the frame colour setter differs; verify game/Forge` | The game's colour setter did not match at startup, so no frame is tinted. Luck and the multiplier still work. |
| `[please-do-better] Reward mapping incomplete; uncertain highlights skipped; restart if persistent` | A reward copy did not match what was generated, so those slots were not highlighted. |
