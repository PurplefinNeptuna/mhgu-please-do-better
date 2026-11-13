# Please do Better r33: testing

r33 is r31, accepted on Eden, registering with Purple-lib's API version 2. Install Purple-lib r10
beside it; with an older Purple-lib the page and help topic do not appear.

## Steps

1. In English, open **Options > Mod Options**: both rows change, and closing after a change logs
   the `Saved:` line.
2. With the game in French, German, Spanish, Italian or Chinese, open **Options > Mod Options**:
   the page's rows, labels and help-bar lines should be in that language, for example "Forcer
   Grande fortune" with "Désactivé"/"Activé" in French. Change a value and close: the save line
   should still appear in the log.
3. Open the Village/Hub help: the "Please do Better" topic's three pages should be in that
   language, each fitting the page.
4. Back in English, check the texts read as before.
5. In a quest, open Mod Options, change a value, and leave it open until the quest fails, which
   closes the menu by itself (being hit, stunned or carted leaves it open): the `Saved:` line
   should still appear (Purple-lib's TESTING.md has the same step).

## Log lines

| Line | Meaning |
| --- | --- |
| `[please-do-better] r33 loaded; forcing and highlights ready` | Started |
| `[please-do-better] settings and help added to Purple-lib` | Registered with Purple-lib |
| `[purple-lib] Mod Options: 1 sets` | Purple-lib accepted the page |
| `[purple-lib] help category 18 "Village/Hub": 10 game topics + 1 added` | The help topic went in |
| `[please-do-better] Saved: luck on, quantities 3x` | Mod Options closed after a change and the INI was written |
| `Purple-lib API version N is not the supported 2` | An older Purple-lib: install r8 |
| `Purple-lib refused the registration` | Send the log |

Without Purple-lib, no Purple-lib line appears; that is expected.
