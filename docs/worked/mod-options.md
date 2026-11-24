# Please do Better: Mod Options

Worked example from `mods/please-do-better/`. Game facts it rests on are in `mhgu-understanding`.

## Purple-lib

Optional, Purple-lib API version 3 (its `API.md`; Purple-lib r17 and later). The plugin exports
`purplelib_on_register` (`src/lib.rs`, `link/exported.txt`), which Purple-lib calls once from its
first update with its table of functions (`core/src/purple_lib.rs::Api`). `src/purple_lib.rs::register`
checks the table's version is 3 or later, ignores a second call, and
passes one Mod Options record (2 labels rows, no `value_text`), then two help records (category 0,
2 pages each: what the setting does, then why) to `purplelib_add_set_help` for the page's own help,
one per row in row order, titled with the row's name; a topic's `context` is its row index. Without Purple-lib, or with one
older than r17, nothing calls it and nothing is logged. `scripts/please_do_better.py` `CALLBACKS` lists the export for the audit.

Purple-lib calls `get` and `set` inside the game's update, so they use only the lock-free mode
request (`runtime::requested_preferences` / `request_preferences`). `set` raises `EDITED` and
`closed` raises `SAVE`; `forge_onImGuiFreeRender` turns them into `settings::changed()` (drop a
pending load) and `settings::save(...)`, keeping preference state and the INI on the ImGui
callbacks. Row values: Force 0/1, multiplier label index = multiplier - 1. All strings are static,
because Purple-lib keeps the pointers. Text (`core/src/purple_lib.rs`) is in the game's seven
languages, picked from the language byte Purple-lib passes (unknown is English), with the game's own
words where it has them: skillData 502 for Miraculous Luck, StartMenuMsg 175/176 for Off/On,
ResultMsg 8 for rewards and StartMenuMsg 9 for Palicoes. The label pointer arrays are filled in
`register` before Purple-lib can call `row`; a host test keeps every help line within 40 columns
(a CJK character counts two) and five lines.
