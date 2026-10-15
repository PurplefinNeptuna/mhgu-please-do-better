# Please do Better

Marks extra reward slots granted by Luck with a pulsing gold border and sparkle.
You can also force Miraculous Luck and multiply item quantities from 1x to 5x
on all player reward pages. Palico rewards keep their normal quantities.

## Requirements

MHGU 1.4.0 for Nintendo Switch and Forge 1.5.1.

## Installation

1. Close your emulator.
2. Extract `please-do-better-r24-forge151.zip`.
3. Copy the `please-do-better` folder into your emulator's MHGU mod directory.
   For Eden, use `~/.local/share/eden/load/0100770008DD8000/`.
4. Enable the package and launch MHGU. Keep only one enabled copy of
   `please_do_better.nro`.

To update, replace your existing `please-do-better` folder with the extracted
folder. To remove the mod, disable or remove its folder in the emulator's mod
directory.

## Settings

Open **Plugin UI > Please do Better** in Forge's overlay.

| Setting | Default | Effect |
| --- | --- | --- |
| Force Miraculous Luck | Off | Uses Miraculous Luck the next time rewards are generated. |
| Reward multiplier | 1x | Integer slider from 1x to 5x for each occupied slot on all player reward pages. Palico rewards keep their normal quantities. |

The quantity setting covers main A/B, special, break/capture, subquest,
free-hunt and other items on the player reward pages, including the player's
extra-item page. It keeps the same items and number of slots. The Palico page
keeps its normal quantities, including companion gathering and stolen items.
Both settings apply the next time rewards are generated. You can use the
multiplier with or without Force Miraculous Luck. Closing the panel keeps both
settings active. If reward borders look misplaced while the overlay is open
on Forge 1.5.1, close the overlay.

Select **Save settings** to remember both choices in `please_do_better.ini` in
MHGU's player save folder. If saving fails, your choices stay active for the
current session. Load a player save and retry **Save settings**.

The saved INI must use this section and both keys:

```ini
[PleaseDoBetter]
force_miraculous=0
reward_multiplier=1
```

The section header is required. The mod cannot import older or headerless
files, so it starts with Luck forcing off and a 1x multiplier. Choose your
settings and save to write the current format.

## Quantity limits

The game's inventory and appraisal capacity limits still apply. Multiplying a
charm quantity supplies additional charms for appraisal within those limits.
Charms on player reward pages are multiplied. The Palico page stays unchanged.
Items already received during the quest into your pouch or box are unchanged.
