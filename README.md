# Mimi Wallpapers

**English** · [Русский](README.ru.md) · [Español](README.es.md)

Live desktop wallpapers with **Mimi**, the character from the animations by **[Typh](https://www.youtube.com/@crispytyph)**.
A free, non-commercial fan project by **MimiFanStudio**.

> **Not affiliated with Typh.** Mimi and all animations © Typh. This repository contains **no** frames, videos or art by Typh.
> The app downloads videos from Typh's official YouTube channel to your computer **for personal wallpaper use only**.
> Please support the creator: watch and like the videos on YouTube.

## Features
- **Catalog of Typh's animations**: titles and thumbnails come straight from YouTube.
- **Only Typh's channel**: you can add new videos by link, but only from Typh's channel. The app checks the YouTube channel ID.
- **Best quality download**: up to 4K 60 fps with sound, via [yt-dlp](https://github.com/yt-dlp/yt-dlp). The progress bar never goes backwards.
- **Live wallpaper**: one click sets the video on your desktop in a loop, via [Lively Wallpaper](https://github.com/rocksdanister/lively), with hardware decoding.
- **Lock screen**: pick any frame with a slider; it is set in full resolution with no admin rights.
- **Sound on/off** and wallpaper volume. By default sound plays only on the empty desktop; turn on **Sound everywhere** in Settings to hear it in any window or browser tab.
- **Start with Windows**: your last wallpaper comes back after a reboot.
- **Languages**: English, Русский, Español.
- **Setup wizard with Mimi**: a slideshow of Typh's video thumbnails (loaded from YouTube) plays from the first second, with terms of use. It installs per user (no admin rights) and fetches missing tools via `winget`. The app can be uninstalled from *Apps & features*.

## Install
1. Download `MimiWallpapers_Setup_public.exe` from [Releases](../../releases).
2. Run it, choose your language, accept the terms and click **Install**.
   If needed, the installer adds Lively Wallpaper, yt-dlp and FFmpeg from the official Windows `winget` catalog.
3. Open **Mimi Wallpapers**, pick a video, then **Download** → **Set as wallpaper**.

Requirements: Windows 10/11 x64, internet connection.

> ⚠️ **Videos are downloaded from YouTube.** If YouTube is blocked or slowed down in your country, wallpapers **will not download without a VPN** (or another way to reach YouTube). Already downloaded wallpapers keep working offline.

## Build from source
```powershell
python -m venv .venv
.venv\Scripts\pip install PySide6-Essentials pyinstaller pywinauto pillow
powershell -ExecutionPolicy Bypass -File build.ps1 -Public
```
The result is `installer\MimiWallpapers_Setup_public.exe`.

Without `-Public`, the build may include personal artwork files (`launcher_bg.mp4`, `setup_bg.webp`, `mimi.ico`, `mimi.png`) if you made them yourself from your own downloads. They are ignored by git and **must not be published**.

## Project structure
| Path | What it is |
|---|---|
| `launcher/mimi_launcher.py` | the launcher (Python + PySide6) |
| `launcher/setup.py` | the setup wizard |
| `launcher/common.py` | shared paths, style, animated background |
| `launcher/i18n.py` | translations, terms of use, Typh channel ID |
| `catalog.json` | video catalog (YouTube IDs and titles) |
| `tools/make_public_assets.py` | generates the icon and animated background at build time |
| `tests/` | UI tests (pywinauto): launcher, setup, uninstall |
| `build.ps1` | build script |

## Tests
```powershell
.venv\Scripts\python tests\ui_test_launcher.py   # 15 checks
.venv\Scripts\python tests\ui_test_setup.py      # 17 checks
.venv\Scripts\python tests\ui_test_sound.py      # 5 checks
```

## Terms & license
- [Terms of use](TERMS.md#english) (also shown in the setup wizard and inside the app).
- Source code: [MIT](LICENSE) © 2026 MimiFanStudio.
- Mimi and the animations: © Typh. Not included and not licensed here.
- Third-party software: Lively Wallpaper (GPL-3.0), yt-dlp (Unlicense), FFmpeg (LGPL/GPL), Qt for Python / PySide6 (LGPL-3.0).
