# Please do Better r30: testing

r30 adds an optional page in Purple-lib's Mod Options and a help topic. The reward code is
unchanged since r29, which was reported working on Eden and MHGURecomp, so only the Purple-lib
parts need a run. Install Purple-lib r4 beside it.

## Steps

1. Start the game and load a save. Open **Options > Mod Options**: the page should be titled
   "Please do Better" with two rows, Force Miraculous Luck (Off/On) and Reward multiplier
   (1x to 5x). The values should match **Plugin UI > Please do Better**.
2. Change both rows in Mod Options. Open Forge's overlay: the Plugin UI row should show the new
   values at once.
3. Close Mod Options with B. The log should report the save. Restart the game: the values you
   left should still be there, in Mod Options and in Plugin UI.
4. Change a value in Plugin UI, then open Mod Options: it should show that value.
5. Open the Help in the village: a "Please do Better" topic should follow the game's topics, with
   three pages.
6. Disable Purple-lib and start again: Options should open the game's Options directly, and
   Please do Better should work as before through Plugin UI.

## Log lines

| Line | Meaning |
| --- | --- |
| `[please-do-better] r30 loaded; forcing and highlights ready` | Started as r29 did |
| `[please-do-better] settings and help added to Purple-lib` | Registered with Purple-lib |
| `[purple-lib] Mod Options: 1 sets` | Purple-lib accepted the page |
| `[purple-lib] help category 18 "Village/Hub": 10 game topics + 1 added` | The help topic went in |
| `[please-do-better] Saved: luck on, quantities 3x` | Mod Options closed after a change and the INI was written |
| `Purple-lib API version N is not the supported 1` / `Purple-lib refused the registration` | Send the log |

Without Purple-lib, no Purple-lib line appears; that is expected.
