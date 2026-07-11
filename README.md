# Video Downloader

Windows console downloader written in Python.

Current version: `v3.5`

Repository: https://github.com/needowsky/VideoDownloader

> **Work in progress:** this project is still under active development. Bugs, broken downloads or installer issues may happen. Please report problems in GitHub Issues: https://github.com/needowsky/VideoDownloader/issues

## One-Command Install

Run this in PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/needowsky/VideoDownloader/main/install.ps1 | iex"
```

This downloads the full AIO installer from GitHub, applies settings and launches dependency setup. The installer then downloads or verifies Python, pip, Microsoft C++ Build Tools, FFmpeg, `yt-dlp`, `gallery-dl`, `spotDL`, Rich/Textual UI helpers, `browser-cookie3`, BeautifulSoup/lxml and `mutagen`.

By default, the PowerShell bootstrap downloads the AIO installer from the `main` branch. To force the newest GitHub release instead, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([scriptblock]::Create((irm https://raw.githubusercontent.com/needowsky/VideoDownloader/main/install.ps1))) -DownloadMode release"
```

PowerShell bootstrap logs are saved here:

```text
%TEMP%\VideoDownloaderInstallLogs\install_ps1_latest.log
```

## Windows EXE Installer

The GitHub release also includes an AIO `.exe` installer:

```text
VideoDownloader_AIO_Installer_EXE_3_5.exe
VideoDownloader_AIO_Installer_EXE_3_5.zip
```

This installer contains the application files and launches the same full setup flow as `zainstaluj_wszystko.bat`. It asks for administrator permission, installs the app into `C:\Program Files\VideoDownloader`, verifies or installs required components, and creates Desktop/Start Menu shortcuts.

The `EXE-3.5` installer is intended as the easiest Windows installation path. It bundles the application files, skips downloading the app source again, and lets the internal AIO setup handle Python portable, FFmpeg, downloader tools and helper libraries.

The EXE installer checks GitHub Releases for newer EXE installer releases named or tagged like:

```text
EXE-3.5
```

It also accepts `EXE_3.5` and `EXE 3.5`. If a newer EXE installer release is available, it can download and start the newer installer before continuing.

The EXE installer log is saved here:

```text
%TEMP%\VideoDownloaderAIO\aio_installer_latest.log
```

## What It Does

Video Downloader downloads audio, video, photos and large files from supported sources using proven tools such as `yt-dlp`, `gallery-dl` and `spotDL`.

Use it only for content you own, content you are allowed to download, or content distributed under a license that permits downloading. The app does not bypass DRM, paywalls or unauthorized access.

## Main Features

- MP3 audio downloads.
- MP4 video downloads in the highest available quality.
- Automatic input detection for single links, multiple links, YouTube playlists, YouTube channels and `.txt` files.
- YouTube playlist/channel preflight with item count, estimated size and confirmation.
- Instagram, TikTok and Facebook photo downloads through `gallery-dl`.
- Facebook Reels video links through `yt-dlp`, including `facebook.com/reel/...` pasted without `https://`.
- Spotify mode through `spotDL` metadata matching with YouTube/YouTube Music.
- Naughties/adult video sources supported by `yt-dlp`, including Pornhub, Beeg, HQPorner and similar sites.
- Large-file manager for `.zip`, `.rar`, `.7z`, `.iso`, Google Drive, Mega and GitHub links.
- GitHub repository links can resolve latest release assets with file selection or download-all.
- `.part` resume, retry handling and queue recovery for large downloads.
- Disk-full recovery by moving partial downloads to another folder when possible.
- Clean progress display with title, progress bar, percent, downloaded MB and speed.
- Rich-powered terminal header when available, with Textual included as the foundation for a future full TUI.
- SQLite user database for configuration, statistics, counters, queues and history.
- Browser cookie access through `browser-cookie3` for sites that require logged-in sessions.
- BeautifulSoup/lxml helpers for extracting media links from HTML pages.
- Mutagen dependency prepared for MP3 metadata and cover-art tagging.
- File validation after download: compares downloaded file size and MD5/SHA256 against source metadata when the source provides it; otherwise reports local size and hashes.
- Error logs with recognized error type, reason and repair hint.
- English/Polish interface through `config/lang/*.lang`.
- Runtime settings, user counters, queues and history in `%APPDATA%\VideoDownloader\config\app.db`.
- `config/config.json` is kept only as a default/migration template.
- Clipboard watcher mode runs in the background for the whole app session, detects copied supported links, asks in a popup by default, and can queue unanswered links.
- Cookie importer: `settings` can import cookies from the detected default browser, and `gimmeacookie.bat` can run the same import with UAC.
- Commands: `help`, `stats`, `stats naughties`, `sites`, `settings`, `update`, `history`, `about`, `doctor`, `open downloads`, `open logs`, `ping`, `resume`, `clipboard`.

## Manual Install

Download the repository/release and run:

```text
zainstaluj_wszystko.bat
```

The installer:

- asks for administrator permission,
- installs the app into `C:\Program Files\VideoDownloader`,
- creates shortcuts named `Video Downloader` on the Desktop and in the Start Menu,
- downloads app files from GitHub releases,
- checks whether components are already installed before downloading them,
- installs or verifies Python, pip, Microsoft C++ Build Tools, FFmpeg, `yt-dlp`, `gallery-dl`, `spotDL`, Rich/Textual, `browser-cookie3`, BeautifulSoup/lxml and `mutagen`,
- uses portable Python 3.12 inside the app folder when a compatible Python is missing or broken; it does not install Python globally,
- shows step progress and overall progress, including already-installed and update-check statuses,
- retries failed Python package installs with fallback methods for difficult dependencies,
- hides technical logs by default when `DEBUG=0`.

## Run

Use the desktop shortcut, the Start Menu shortcut, or run:

```text
uruchom_downloader.bat
```

Manual run:

```powershell
python youtube_downloader.py
```

## Included Files

```text
youtube_downloader.py
zainstaluj_wszystko.bat
install.ps1
uruchom_downloader.bat
update.bat
aio_installer/VideoDownloader_AIO_Installer.py
aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.exe
aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.zip
README.md
CHANGELOG.md
LICENSE
config/config.json
config/stats.json
config/lang/en.lang
config/lang/pl.lang
User database: `%APPDATA%\VideoDownloader\config\app.db`
Runtime config/statistics/queues/history are stored in SQLite. The JSON files above are default/migration files.
```

## Usage

On startup, choose what you want to download:

```text
1. Download link, playlist, channel or .txt file
2. Download large file
3. Settings
4. Clipboard queue
5. Exit
```

For MP3/MP4/photo/Spotify flows, paste a link, multiple links or a `.txt` file path. Type `q` to return to the menu.

For `.txt` files, put one URL per line. Lines starting with `#` are ignored.

After a completed download, the app clears the console and shows:

- saved items,
- file validation,
- source-vs-local size check when available,
- source-vs-local MD5/SHA256 check when the source provides checksums,
- local size and MD5/SHA256 when source checksums are unavailable,
- clickable save folder link in Windows Terminal.

Validation reports are appended to:

```text
logs/download_validation.txt
```

Error details are written to:

```text
logs/log_error_data.txt
```

## Large Files

The large-file manager supports:

- direct `.zip`, `.rar`, `.7z`, `.iso` links,
- Google Drive,
- Mega,
- GitHub raw/blob/archive links,
- GitHub repository links with latest-release asset selection.

During large downloads, temporary data is saved as `.part`. If the app or computer closes unexpectedly, the queue is saved in SQLite:

```text
%APPDATA%\VideoDownloader\config\app.db
```

Type:

```text
resume
clipboard
```

to continue pending downloads.

## Configuration

Runtime configuration is stored in SQLite:

```text
%APPDATA%\VideoDownloader\config\app.db
```

Language files:

```text
config/lang/en.lang
config/lang/pl.lang
```

The app detects available `.lang` files and validates that each language file is valid JSON with string keys and values.

You can switch language during runtime:

```text
lang=en
lang=pl
```

## Useful Commands

```text
help
stats
stats naughties
sites
settings
update
history
about
doctor
open downloads
open logs
ping
resume
```

Easter eggs:

```text
iamtheone
imblue
gothic
snake
konami
rickroll
godmode
```

## Update

Type:

```text
update
```

The app checks the latest GitHub release and compares it with local `APP_VERSION`.
When a newer release is available, the app asks for confirmation, starts `update.bat`, and closes so the updater can overwrite existing application files safely.

The updater also copies installer-related files from the release/source package, including:

```text
aio_installer/VideoDownloader_AIO_Installer.py
aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.exe
aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.zip
```

The standalone EXE installer has a separate self-update check for GitHub Releases tagged or named like `EXE-3.5`.

## Clipboard Watcher

The clipboard watcher runs automatically in the background. Use the main menu option `Clipboard queue` or type:

```text
clipboard
```

The watcher runs in the background for the whole app session and checks the Windows clipboard for supported links, including YouTube links. When a new link is detected, it asks in a popup whether to download it using the current default download type from settings, for example `MP4` or `MP3`. Naughties links are always downloaded as `MP4`.

Popup prompts can be disabled in settings or in the SQLite config value:

```json
"popup": 0
```

If no action is taken on the popup, the link is written to the SQLite clipboard queue and mirrored to `%APPDATA%\VideoDownloader\clipboard_queue.txt` for visibility. The queue is cleared automatically on every program start and after queue downloads.

## Notes

- Spotify mode does not download protected Spotify streams. It uses metadata matching through `spotDL`.
- Private/login-required downloads can automatically retry with browser cookies and `cookies.txt` when available.
- To import cookies manually, run:

```bat
gimmeacookie.bat
```

The script asks for administrator permission, detects the default browser where possible, and saves a local `cookies.txt` for the downloader. Keep this file private.
- Adult-site support depends on your installed `yt-dlp` version and each site's current extractor support.

## License

Custom source-available license by needowsky. Personal use, inspection and private modification are allowed. Publishing, redistribution, public forks, modified public releases, author changes, sublicensing or commercial use require prior written permission from needowsky. See `LICENSE`.
