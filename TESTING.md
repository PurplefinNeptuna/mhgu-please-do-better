# Please do Better r37: testing

Its settings are on a Mod Options page, with a help topic for each setting on that page's own
help screen. Install Purple-lib r17 or later
beside it; with an older Purple-lib the page and its help do not appear, and no line says so.

## Steps

1. In English, open **Options > Mod Options**: both rows change, and closing after a change logs
   the `Saved:` line.
2. On the "Please do Better" page, the button guide shows (−) "Mod Help" (or (+) if you swapped
   them). Press it: a help titled "Please do Better" opens with two topics, "Force Miraculous
   Luck" and "Reward multiplier", each with two pages that fit. Close it with B: you are back on the page, cursor where it was.
3. Open the Village/Hub help: it no longer has a "Please do Better" topic.
4. With the game in French, German, Spanish, Italian or Chinese, repeat steps 1 and 2: the rows,
   labels, help-bar lines and help pages are in that language, for example "Forcer Grande
   fortune" with "Désactivé"/"Activé" in French.
5. In a quest, open Mod Options, change a value, and leave it open until the quest fails, which
   closes the menu by itself (being hit, stunned or carted leaves it open): the `Saved:` line
   should still appear (Purple-lib's TESTING.md has the same step).

## Log lines

| Line | Meaning |
| --- | --- |
| `[please-do-better] r37 loaded; forcing and highlights ready` | Started |
| `[please-do-better] settings and help added to Purple-lib` | Purple-lib called the mod and took its page and help |
| `[purple-lib] purplelib_on_register called in N mods` | N counts Please do Better (2 with Purple-lib Tester installed) |
| `[purple-lib] Mod Options: N sets, M topics in their own help` | Purple-lib accepted the page; M counts Please do Better's two topics |
| `[please-do-better] Saved: luck on, quantities 3x` | Mod Options closed after a change and the INI was written |
| `Purple-lib API version N is older than the supported 3` | An older Purple-lib called the mod: install r17 |
| `Purple-lib refused the registration` | Send the log |

Without Purple-lib, no Purple-lib line appears; that is expected.
