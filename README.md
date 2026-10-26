# DualShock 4 Button Prompts — Naruto: Rise of a Ninja Recomp

A mod for [Naruto: Rise of a Ninja Recomp](https://github.com/jorjbarbosa/naruto-rise-recomp) that shows **PlayStation buttons** in the game's hints, tutorials and HUD when you play with a DualShock 4.

![The icons](tools/ds4-icons/preview.png)

| Xbox | PlayStation |
| --- | --- |
| A / B / X / Y | ✕ Cross / ○ Circle / □ Square / △ Triangle |
| LB / RB | L1 / R1 |
| LT / RT | L2 / R2 |
| Left / right stick | L / R stick |
| Start / Back | Options / Touchpad |

The mod has two parts. Use the first alone, or both:

1. **The icon pack** (`tools/ds4-icons`): redraws the button icons inside the game's own files, so the game shows real ✕ ○ □ △ icons. Works with the released port as it is; no build needed.
2. **The code mod** (`files` and `ds4-button-prompts.patch`): built into the port. With the icon pack, it gives LB/RB their own L1/R1 icons (the game's font has one shoulder icon per side, shown as L2/R2) and makes the **touchpad act as Back**. Without the icon pack, it writes the buttons as names instead ("Press [Cross] to jump").

---

## Install the icon pack

1. Install [Python 3](https://www.python.org/downloads/) and tick **Add python.exe to PATH**.
2. Download this repository (green **Code** button → **Download ZIP**) and unzip it.
3. Close the game. Open PowerShell in the unzipped `tools\ds4-icons` folder and run, with your install folder (the one with `narutorise.exe`):

   ```powershell
   python ds4_icons.py install "C:\Program Files (x86)\Steam\steamapps\common\NarutoRisePC"
   ```

   The default port install is `%LOCALAPPDATA%\NarutoRisePC`. The first run backs up `game\naruto.bf` as `game\naruto.bf.ds4bak` (about 630 MB, so keep 1 GB free), then patches it in place; its size does not change. It takes a minute or two.
4. Play. To go back to the Xbox icons: `python ds4_icons.py restore "<same folder>"`.

More detail in [tools/ds4-icons/README.md](tools/ds4-icons/README.md).

---

## Build the code mod (optional)

This mod changes the port's source code, so you build the game once with the mod included. You need a Windows PC and your own Xbox 360 copy of the game.

### 1. Download the port

```powershell
git clone --recursive https://github.com/jorjbarbosa/naruto-rise-recomp
cd naruto-rise-recomp
git checkout 9a0b043
```

The mod was made for commit `9a0b043`. To try a newer version of the port, skip the `git checkout` line and use the **Git way** below. The easy way would put back older copies of the files it replaces.

### 2. Add the mod

Download this repository (green **Code** button → **Download ZIP**) and unzip it. Then do **one** of these:

- **Easy way:** copy everything inside this mod's `files` folder into the `naruto-rise-recomp` folder. When Windows asks, choose **Replace the files in the destination**.
- **Git way:** copy `ds4-button-prompts.patch` into the `naruto-rise-recomp` folder and run:

  ```powershell
  git apply ds4-button-prompts.patch
  ```

### 3. Build the game

Follow the port's build guide, [docs/build-and-run.md](https://github.com/jorjbarbosa/naruto-rise-recomp/blob/main/docs/build-and-run.md). It explains the tools to install, where to put your game files, and the build commands. When it finishes, the game is in `app\out\build\win-amd64-release\`.

### 4. Copy it into your game folder (optional)

If you already have the port installed, copy everything from `app\out\build\win-amd64-release\` into your install folder (by default `%LOCALAPPDATA%\NarutoRisePC`), **except `narutorise.toml`**, so you keep your settings. Your game files and saves are not touched.

### 5. Turn it on

Install the icon pack too (see above), so the buttons show as icons.

1. Connect your DualShock 4 **before** starting the game.
2. Open `narutorise_launcher.exe`.
3. Go to **Settings → Controls → Controller prompts** and choose:
   - **Automatic** (default): PlayStation buttons when a PlayStation controller is connected.
   - **PlayStation (DualShock 4)**: always PlayStation buttons.
   - **Xbox**: the original icons.
4. Play.

---

## Good to know

- **Icon pack and settings:** the icon pack changes the game files, so the icons are PlayStation ones with any controller and any **Controller prompts** setting. Use `restore` to go back.
- **Only button icons:** the game's quick-time-event videos (`FB_QTE_*.bik`) may have Xbox buttons drawn into the video and stay as they are.
- **Touchpad as Back:** needs the code mod. Share works as Back as well.
- **Without the icon pack,** the code mod writes button names such as `[Cross]`, because the game's font has no ✕ ○ □ △ symbols.
- **English game text only** for the code mod's changes to texts. Translation mods, such as the included Brazilian Portuguese one, also work. The icon pack works in every language.
- **Steam Input:** Steam can make a DualShock 4 look like an Xbox controller, so Automatic picks Xbox. Choose **PlayStation (DualShock 4)** instead.
- **Keyboard and mouse mode:** with **Show keys in game texts** on, the game shows your keys instead.
- **Without the launcher:** in `narutorise.toml`, set `controller_prompts = "auto"`, `"playstation"` or `"xbox"`.
- **Game updates:** if `naruto.bf` is replaced (a reinstall, or Steam verifying files), run `install` again.

## Troubleshooting

Still seeing Xbox icons? Run `python ds4_icons.py status "<folder>"`: it counts the PlayStation and Xbox icons in `naruto.bf`. With the code mod, open the newest file in the `logs` folder next to `narutorise.exe` and search for `[pad prompts]`. That line says which controller was found and why it chose the style it did.

## License

GPL-3.0, the same license as the port this mod is based on. See [LICENSE](LICENSE). The icons are drawn from [Kenney's Input Prompts](https://kenney.nl/assets/input-prompts) (CC0); thanks, Kenney. No game files are included: the icon pack patches your own copy.
