# Please do Better r31: testing

r31 translates the Purple-lib page and help topic into the game's seven languages, using the
game's own words where it has them (the skill name Miraculous Luck, the Options window's Off/On).
Everything else is r30, accepted on Eden, Ryubing and MHGURecomp. Install Purple-lib r5 beside it.

## Steps

1. With the game in French, German, Spanish, Italian or Chinese, open **Options > Mod Options**:
   the page's rows, labels and help-bar lines should be in that language, for example "Forcer
   Grande fortune" with "Désactivé"/"Activé" in French. Change a value and close: the save line
   should still appear in the log.
2. Open the Village/Hub help: the "Please do Better" topic's three pages should be in that
   language, each fitting the page.
3. Back in English, check the texts read as before.
4. In a quest, open Mod Options, change a value, and let a monster hit you so the menu closes by
   itself: the `Saved:` line should still appear (see Purple-lib's TESTING.md step 4).

## Log lines

| Line | Meaning |
| --- | --- |
| `[please-do-better] r31 loaded; forcing and highlights ready` | Started |
| `[please-do-better] settings and help added to Purple-lib` | Registered with Purple-lib |
| `[purple-lib] Mod Options: 1 sets` | Purple-lib accepted the page |
| `[purple-lib] help category 18 "Village/Hub": 10 game topics + 1 added` | The help topic went in |
| `[please-do-better] Saved: luck on, quantities 3x` | Mod Options closed after a change and the INI was written |
| `Purple-lib API version N is not the supported 1` / `Purple-lib refused the registration` | Send the log |

Without Purple-lib, no Purple-lib line appears; that is expected.
