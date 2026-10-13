# Mimi Wallpapers

**English** · [Русский](README.ru.md) · [Español](README.es.md)

Live desktop wallpapers with **Mimi**, the character from the animations by **[Typh](https://www.youtube.com/@crispytyph)**.
A free, non-commercial fan project by **MimiFanStudio**.

> **Mimi images and the bundled video are used with Typh's permission.** Mimi and all animations © Typh.
> The app downloads videos from Typh's official YouTube channel to your computer **for personal wallpaper use only**.
> Please support the creator: watch and like the videos on YouTube.

## Screenshots
| Launcher | Lock screen frame | Setup |
|---|---|---|
| ![Launcher](docs/launcher.jpg) | ![Frame picker](docs/frame_picker.jpg) | ![Setup](docs/setup.jpg) |

## Features
- **Catalog of Typh's animations**: titles and thumbnails come straight from YouTube.
- **Only Typh's channel**: you can add new videos by link, but only from Typh's channel. The app checks the YouTube channel ID.
- **Best quality download**: up to 4K 60 fps with sound, via [yt-dlp](https://github.com/yt-dlp/yt-dlp). The progress bar never goes backwards.
- **No long end credits**: credits at the end of a video are cut automatically after download (lossless).
- **Live wallpaper**: one click sets the video on your desktop in a loop, via [Lively Wallpaper](https://github.com/rocksdanister/lively), with hardware decoding.
- **Lock screen**: pick any frame with a slider; it is set in full resolution with no admin rights.
- **Sound on/off** and wallpaper volume. By default sound plays only on the empty desktop; turn on **Sound everywhere** in Settings to hear it in any window or browser tab.
- **Start with Windows**: your last wallpaper comes back after a reboot.
- **Languages**: English, Русский, Español.
- **Setup wizard with Mimi**: an animated Mimi background from the first second, with terms of use. The first wallpaper (KISS ME) is already inside the installer, so it works right away, even without a VPN. It installs per user (no admin rights) and fetches missing tools via `winget`. The app can be uninstalled from *Apps & features*.

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

The Mimi artwork (`launcher_bg.mp4`, `setup_bg.webp`, `mimi.ico`, `mimi.png`) is in the repository and is used with Typh's permission. The first catalog video is bundled into the installer if it is already downloaded to `%LOCALAPPDATA%\MimiWallpapers\videos`.

## Project structure
| Path | What it is |
|---|---|
| `launcher/mimi_launcher.py` | the launcher (Python + PySide6) |
| `launcher/setup.py` | the setup wizard |
| `launcher/common.py` | shared paths, style, animated background |
| `launcher/i18n.py` | translations, terms of use, Typh channel ID |
| `catalog.json` | video catalog (YouTube IDs and titles) |
| `launcher_bg.mp4`, `setup_bg.webp`, `mimi.ico`, `mimi.png` | Mimi artwork (with Typh's permission) |
| `docs/` | screenshots |
| `tools/make_public_assets.py` | generates fallback graphics at build time |
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
- Mimi and the animations: © Typh, used with permission. The MIT license does not apply to them.
- Third-party software: Lively Wallpaper (GPL-3.0), yt-dlp (Unlicense), FFmpeg (LGPL/GPL), Qt for Python / PySide6 (LGPL-3.0).
