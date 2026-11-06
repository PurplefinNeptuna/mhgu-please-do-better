# Please do Better

Marks extra reward slots granted by Luck by turning their frame white.
You can also force Miraculous Luck and multiply item quantities from 1x to 5x
on all player reward pages. Palico rewards keep their normal quantities.

## Requirements

- MHGU 1.4.0 for Nintendo Switch.
- [Fexty's Forge 1.5.1](https://github.com/Fexty12573/forge/releases/tag/v1.5.1).

## Installation

1. Close the emulator.
2. Extract `please-do-better-r28-candidate.zip`.
3. Copy the whole `please-do-better` folder into your emulator's MHGU mod directory:
   - Eden: `~/.local/share/eden/load/0100770008DD8000/`
   - Ryujinx: `mods/contents/0100770008dd8000/` inside its data directory.
4. Enable `please-do-better` and launch MHGU.

Keep only one enabled copy of `please_do_better.nro`.

## Usage

### Settings

Open **Plugin UI > Please do Better** in Forge's overlay.

| Setting | Default | Effect |
| --- | --- | --- |
| Force Miraculous Luck | Off | Uses Miraculous Luck the next time rewards are generated. |
| Reward multiplier | 1x | Set an integer multiplier from 1x to 5x for each occupied slot on all player reward pages. |

The multiplier covers main A/B, special, break/capture, subquest, free-hunt
and other items on the player reward pages, including the player's extra-item
page. It keeps the same items and number of slots. The Palico page keeps its
normal quantities, including companion gathering and stolen items.

Both settings apply the next time rewards are generated. You can use the
multiplier with or without Force Miraculous Luck. Closing the settings row
keeps both settings active.

Use **Save settings** to keep your choices for the next session. It writes
`please_do_better.ini` in MHGU's player save folder. If saving fails, your
choices stay active for the current session. Load a player save and try again.

### INI settings

The saved INI must use this section and both keys:

```ini
[PleaseDoBetter]
force_miraculous=0
reward_multiplier=1
```

The section header is required. The mod cannot import older or headerless
files, so it starts with Luck forcing off and a 1x multiplier. Choose your
settings and save to write the current format.

## Update and removal

Close the emulator before updating or removing the mod. To update, replace
its `please-do-better` folder with the one from the new ZIP. To remove it,
disable the package or delete its folder from the emulator's mod directory.

## Compatibility and known issues

The game's inventory and appraisal capacity limits still apply. Multiplying a
charm quantity supplies additional charms for appraisal within those limits.
Items already received during the quest into your pouch or box are unchanged.

A highlighted slot keeps its white frame after you take the item.

It can load alongside plugins that hook some of the same game functions.

Please do Better doesn't work on MHGURecomp: the game stops while loading, so don't install it there.
