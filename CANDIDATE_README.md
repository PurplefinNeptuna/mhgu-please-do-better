# Please do Better

Highlights extra reward slots granted by Luck with a pulsing gold border and
sparkle. Optional settings force Miraculous Luck and double item quantities on
the first reward screen.

## Requirements

MHGU 1.4.0 for Nintendo Switch and Forge 1.4.1. This is a development build for
testing on an emulator; save progress before testing it.

## Installation

1. Close your emulator.
2. Extract `please-do-better-r20-doubleqty-candidate.zip`.
3. Copy the `Please do Better` folder into your emulator's MHGU mod directory.
   For Eden, use `~/.local/share/eden/load/0100770008DD8000/`.
4. Enable the package and launch MHGU. Keep only one enabled copy of
   `please_do_better.nro`.

To remove the mod, disable or remove its folder in the emulator's mod directory.

## Settings

Open **Plugin UI > Please do Better** in Forge's overlay.

| Setting | Default | Effect |
| --- | --- | --- |
| Force Miraculous Luck | Off | Uses Miraculous Luck for subsequent reward generations. |
| Double reward quantities | Off | Doubles each occupied slot's item quantity on the first reward screen. |

The quantity setting covers main A/B rewards, special rewards, and break/capture
rewards. It keeps the same items and number of slots. Subquest, free-hunt,
gathered items and separate plunder/Palico rewards keep their normal quantities.
Changing either setting affects the next reward generation. Both settings can
be enabled independently; closing the panel keeps them active.

Select **Save settings** to remember both choices in `please_do_better.ini` in
MHGU's player save folder. Earlier one-setting files keep their Luck choice and
start with quantity doubling off. If saving fails, your session choices remain
active; load a player save and retry **Save settings**.

## Quantity limits

The game's inventory and appraisal capacity limits still apply. Doubling a
charm quantity supplies additional charms for appraisal within those limits.
Gathered charms are outside the quantity setting's scope.
