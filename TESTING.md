# Please do Better r27: testing

r27 is a probe on Eden. It tints each highlighted reward slot's frame white through the game's own
colour setter, and logs what the frame looked like before. The gold border still draws as before.

The questions it answers:

1. Does a white tint show on the frame, or does the frame look unchanged?
2. Does the tint stay, or does something (the cursor, the screen's own colours) put red or blue back?

## Steps

1. Run on Eden with r27 installed and Force Miraculous Luck on, so the reward screen has highlights.
2. Finish a quest and open the Reward Box. Look at the slots with the gold border: is their frame
   white or grey instead of red or blue?
3. Move the cursor onto a highlighted slot, then away from it. Does the frame go back to white, or
   turn red or blue?
4. Take the item from a highlighted slot.
5. Go on to the next reward page, if there is one, and leave the screen. Then send the Eden log.

## Log lines

All lines start with `[please-do-better]` and appear at Forge's shipped error level.

| Line | Meaning |
| --- | --- |
| `probe: group G slot I frame colours A B C D; set white, reads X` | First sight of that frame. A to D are its four corner colours before the tint; X should be `ffffffff`. |
| `probe: group G slot I tint replaced by A B C D` | Something wrote the frame's colours after the tint. Logged once per frame per screen. Say what you did just before it, if you can tell. |
| `probe: vertex colour setter differs; frames are not tinted` | The setter's bytes did not match at startup, so nothing is tinted. |
