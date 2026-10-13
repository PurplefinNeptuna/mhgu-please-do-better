# Please do Better

Highlights extra reward slots granted by Luck with a pulsing gold border and
sparkle. Optional settings force Miraculous Luck and multiply item quantities by 1x to 5x on
all player reward pages. Palico rewards keep their normal quantities.

## Requirements

MHGU 1.4.0 for Nintendo Switch and Forge 1.4.1.

## Installation

1. Close your emulator.
2. Extract `please-do-better-r23-reward-pages.zip`.
3. Copy the `please-do-better` folder into your emulator's MHGU mod directory.
   For Eden, use `~/.local/share/eden/load/0100770008DD8000/`.
4. Enable the package and launch MHGU. Keep only one enabled copy of
   `please_do_better.nro`.

To update, replace your existing `please-do-better` folder with the extracted
folder. Keep only one enabled copy of `please_do_better.nro`. To remove the mod,
disable or remove its folder in the emulator's mod directory.

## Settings

Open **Plugin UI > Please do Better** in Forge's overlay.

| Setting | Default | Effect |
| --- | --- | --- |
| Force Miraculous Luck | Off | Uses Miraculous Luck for subsequent reward generations. |
| Reward multiplier | 1x | Integer slider from 1x to 5x for each occupied slot on all player reward pages. Palico rewards keep their normal quantities. |

The quantity setting covers main A/B, special, break/capture, subquest,
free-hunt and other items on the player reward pages, including the player's
extra-item page. It keeps the same items and number of slots. The Palico page
keeps its normal quantities, including companion gathering and stolen items.
Changing either setting affects the next reward generation. The multiplier is
independent of Force Miraculous Luck. Closing the panel keeps both settings active. If reward borders look misplaced
while the overlay is open on Forge 1.4.1, close the overlay.

Select **Save settings** to remember both choices in `please_do_better.ini` in
MHGU's player save folder. If saving fails, your session choices remain active;
load a player save and retry **Save settings**.

The saved INI must use this section and both keys:

```ini
[PleaseDoBetter]
force_miraculous=0
reward_multiplier=1
```

The section header is required. Headerless and older formats use Luck forcing
off and multiplier 1x; there is no migration. Select your settings and save to
write the new format.

## Quantity limits

The game's inventory and appraisal capacity limits still apply. Multiplying a
charm quantity supplies additional charms for appraisal within those limits.
Charms on player reward pages are multiplied; the Palico page stays unchanged.
Items already received during the quest into your pouch or box are unchanged.
