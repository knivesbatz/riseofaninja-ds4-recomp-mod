# DualShock 4 Button Prompts — Naruto: Rise of a Ninja Recomp

A mod for [Naruto: Rise of a Ninja Recomp](https://github.com/jorjbarbosa/naruto-rise-recomp) that shows **PlayStation buttons** in the game's hints and tutorials when you play with a DualShock 4.

> "Press **[A]** to jump" becomes "Press **[Cross]** to jump".

| Xbox | PlayStation |
| --- | --- |
| A / B / X / Y | Cross / Circle / Square / Triangle |
| LB / RB | L1 / R1 |
| LT / RT | L2 / R2 |
| Start / Back | Options / Share |

Stick and d-pad icons stay as they are. DualSense and DualShock 3 controllers work too.

---

## How to install

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

1. Connect your DualShock 4 **before** starting the game.
2. Open `narutorise_launcher.exe`.
3. Go to **Settings → Controls → Controller prompts** and choose:
   - **Automatic** (default): PlayStation buttons when a PlayStation controller is connected.
   - **PlayStation (DualShock 4)**: always PlayStation buttons.
   - **Xbox**: the original icons.
4. Play.

---

## Good to know

- **Words instead of symbols:** the buttons show as words, such as `[Cross]`, because the game's font has no ✕ ○ □ △ symbols.
- **Only text prompts change:** button icons that the game draws as pictures, outside its text, stay Xbox ones.
- **English game text only:** set the game language to English. Translation mods, such as the included Brazilian Portuguese one, also work.
- **Steam Input:** Steam can make a DualShock 4 look like an Xbox controller, so Automatic shows Xbox icons. Choose **PlayStation (DualShock 4)** instead.
- **Keyboard and mouse mode:** with **Show keys in game texts** on, the game shows your keys instead.
- **Without the launcher:** in `narutorise.toml`, set `controller_prompts = "auto"`, `"playstation"` or `"xbox"`.

## Troubleshooting

Still seeing Xbox icons? Open the newest file in the `logs` folder next to `narutorise.exe` and search for `[pad prompts]`. That line says which controller was found and why it chose the style it did.

## License

GPL-3.0, the same license as the port this mod is based on. See [LICENSE](LICENSE).
