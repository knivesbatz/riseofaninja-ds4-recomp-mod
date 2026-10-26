# DualShock 4 icon pack

Redraws the Xbox button icons inside the game's `naruto.bf` as PlayStation ones:

| Xbox icon | Becomes |
| --- | --- |
| A / B / X / Y | ✕ / ○ / □ / △ |
| Shoulder L / R (`<lt>`/`<rt>`, and `<lb>`/`<rb>` without the code mod) | L2 / R2 |
| The font's French, Spanish and Italian shoulder icons (the code mod's `<lb>`/`<rb>`) | L1 / R1 |
| Left / right stick | L / R stick |
| The large A/B/X/Y HUD buttons | ✕ / ○ / □ / △ |

![The icons](preview.png)

It works on its own, with the released port as it is: no build needed. With the DS4 prompts code mod built in, `<lb>`/`<rb>` get their own L1/R1 icons.

## Install

You need [Python 3](https://www.python.org/downloads/) (tick **Add python.exe to PATH**). Close the game, then in this folder run:

```powershell
python ds4_icons.py install "C:\Program Files (x86)\Steam\steamapps\common\NarutoRisePC"
```

Use the folder that has `narutorise.exe` (for the installer's default, `%LOCALAPPDATA%\NarutoRisePC`). The first run copies `game\naruto.bf` to `game\naruto.bf.ds4bak` (about 630 MB), then adds the patched parts at the end of `naruto.bf`. Running it again does nothing.

- `python ds4_icons.py status "<folder>"` counts the PlayStation and Xbox icons in the file.
- `python ds4_icons.py restore "<folder>"` puts the backup back (Xbox icons).

The installer only changes textures whose bytes match the original game's, so other mods' textures are left alone. If you replace `naruto.bf` (a reinstall, or Steam's file check), run `install` again.

## What's in here

- `ds4_icons.py`: the installer. Plain Python, no packages. It finds the bigfile entries holding the font atlas (`0x2F00E652`) and the HUD buttons (`0x1900001F`, `0x19000024`, `0x1900004E`, `0x1900004F`), pastes the icons into them, stores the changed 128 KB chunks again, appends the entries and points their table offset and size at the copies.
- `data/`: the icons as raw pixel rectangles plus `manifest.json` (the checksums before and after). No game art is included; the installer builds the textures from your own copy.
- `compose_icons.py` and `icons-src/`: how `data/` is made, from [Kenney's Input Prompts](https://kenney.nl/assets/input-prompts) (CC0, see `icons-src/LICENSE-Kenney.txt`). To change the icons: `python ds4_icons.py extract "<folder>" originals`, edit `compose_icons.py`, then `python compose_icons.py originals icons-src data` (needs Pillow).

## Limits

- Buttons drawn into the game's videos (such as the quick-time events, `FB_QTE_*.bik`) stay as they are.
- The pack edits the game data, so it shows PlayStation icons with any controller until you `restore`.
