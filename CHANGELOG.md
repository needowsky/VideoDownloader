# Changelog

This changelog keeps the current release detailed and summarizes older releases. Source files for historical releases are linked in each section.

## v3.5

Current release candidate for the Windows build.

Planned release: https://github.com/needowsky/VideoDownloader/releases/tag/EXE-3.5

### Added

- Background clipboard watcher now runs for the whole application session.
- Clipboard links can be confirmed through popup prompts, postponed, ignored, or queued for later.
- Clipboard queue, large-file queue, runtime configuration, statistics and history now use SQLite as active storage.
- Total application usage time is tracked in SQLite config data and shown in `stats`.
- `gimmeacookie.bat` can import cookies from the detected default browser.
- Cookie import can self-install missing `browser-cookie3` into the local package folder before failing.
- `gimmeacookie.bat` now reports that the application must be installed first when app files or Python runtime are missing.
- Added a cleaner TUI text/style layer and refreshed progress bars so download status looks more modern.

### Changed

- App version updated to `v3.5`.
- AIO installer version updated to `v3.5`.
- EXE installer release detection now targets releases such as `EXE-3.5`, `EXE_3.5` and `EXE 3.5`.
- Release assets now use `VideoDownloader_AIO_Installer_EXE_3_5.exe` and `VideoDownloader_AIO_Installer_EXE_3_5.zip`.
- Runtime config is no longer actively written to `config.json`; that file is kept as a default/migration template.
- Download progress bars now use a cleaner `<====------>` style instead of `[###...]` output, avoiding Windows console encoding crashes.
- Installer progress display was refreshed to avoid old bracket/hash progress bars.
- `uruchom_downloader.bat` now exposes local `python_packages` before starting bundled Python.
- Download progress display now uses a modern block layout with percent, downloaded/total MB, speed and ETA.
- Clipboard YouTube watch links now default to single-video mode by stripping playlist/radio parameters from copied links.
- Added a Settings option for YouTube clipboard link mode: `auto`, `single` or `playlist`.
- Playlist/channel downloads now show the current item number, for example `Item 3/175`, in the fixed progress block.
- Main menu now shows only the latest detected clipboard link and queue size instead of printing every clipboard event into the console.
- Removed the abandoned external ripper flow from the app, installer and current documentation.
- Download ranks were split into a separate overall scale and separate per-category scales for clearer `stats`.
- Added HQPorner recognition and a dedicated `stats naughties` counter.

### Fixed

- Fixed cookie import failing immediately when `browser-cookie3` was missing from the active Python environment.
- Fixed package visibility issues when helper libraries are installed into the local `python_packages` folder.
- Fixed clipboard command behavior after the background watcher was introduced: it now manages the queue instead of starting another watcher.
- Fixed main menu numbering so `5` opens Settings and `6` exits, preventing the Settings entry from closing the app after menu changes.
- Improved cookie import for Google Chrome, Microsoft Edge and Mozilla Firefox, including clearer full-browser error details.
- Enabled UTF-8 console output so block progress bars render correctly in Windows Terminal.
- Fixed subprocess output decoding so UTF-8 titles/emojis from helper tools no longer crash background reader threads on CP1250 Windows consoles.
- Improved cookie-required download retries so `yt-dlp --cookies-from-browser chrome` is tried before local `cookies.txt`.
- Updated launcher Python detection to find local PythonCore installs and allow Python 3.14 as a last-resort runtime.
- Updated external updater to skip downloads when the installed version is current or newer than the latest GitHub release.
- Reduced playlist/channel console flooding by reusing one locked status block across download, conversion and saved states.
- Added a `file:///...` folder URI fallback when clickable terminal hyperlinks are not supported.
- Fixed playlist/channel progress drawing so the console no longer leaves a long empty receipt-like area above the active item.
- Added a language-pack safety fallback: missing `.lang` files or missing translation keys now show a GitHub update/reinstall hint instead of crashing the app.
- Settings now use selection menus for fixed values such as language, debug, popup, default media type, browser cookies and YouTube clipboard mode.
- Custom language packs are now validated against the English base pack for missing keys and placeholder mismatches.
- Existing filenames are no longer overwritten or skipped silently: new duplicates are saved with ` (1)`, ` (2)` etc., then the app asks whether to keep or remove the newly downloaded duplicate.
- HQPorner downloads now try an alternative-player/direct-media resolver before falling back to the standard yt-dlp extractor.
- HQPorner resolver now has a Selenium browser-render fallback inspired by bulk HQPorner/Eporner downloader projects: when static HTML parsing does not reveal a media URL, the app can render the page, click an alternative player and extract direct `.mp4`/`.m3u8` sources.
- Installer helper packages now include Selenium so the HQPorner browser fallback can work after a fresh setup.
- Pornhub and other naughties now use the same alternative direct-media resolver path: the app checks HTML/player metadata such as `videoUrl`, then can use Selenium browser rendering before falling back to `yt-dlp`.
- Added clearer download error definitions for `HTTP 410 Gone` and browser cookie database failures, and stopped pointless retry loops when a service reports that the material is gone.
- Error logs now prefer the user's AppData folder and fall back to a temp log folder, avoiding crashes when the app cannot write beside installed files.
- Pornhub links from localized domains such as `pl.pornhub.com` are normalized to `www.pornhub.com` and use a dedicated referer/origin header set before download.

## v3.0

Source: https://github.com/needowsky/VideoDownloader/releases/download/EXE-3.0/CHANGELOG.md

Release focused on the Windows AIO EXE installer, safer updates, neutral public configuration, modern UI foundations and local data storage.

- Added Windows AIO `.exe` installer build and release-ready EXE/ZIP assets.
- Added EXE release detection for tags such as `EXE_3.0`, `EXE-3.0` and `EXE 3.0`.
- Added external updater flow through `update.bat`.
- Added custom icon handling for Desktop and Start Menu shortcuts.
- Added source-vs-local validation for direct/large downloads using expected size and MD5/SHA256 when exposed by the source.
- Added Facebook Reels URL handling.
- Added Rich/Textual, SQLite, `browser-cookie3`, BeautifulSoup/lxml and mutagen foundations.
- Moved public download counters out of source code into neutral config/stat files.
- Improved installer reliability, portable Python handling, dependency detection and GitHub archive downloads.

## v2.5

Source: https://github.com/needowsky/VideoDownloader/releases/download/2.5/CHANGELOG.md

Release prepared for GitHub with cleaner installation, safer updates, neutral public configuration and foundations for a more modern interface.

- Added persistent update bootstrap logs and safer update handoff.
- Added YouTube playlist preflight, active download stop control and improved menu clearing/back navigation.
- Added source-vs-local validation for direct/large downloads.
- Added Facebook Reels handling, including links pasted without `https://`.
- Added neutral `config/stats.json` so public GitHub copies no longer inherit the author's local counter.
- Added Rich/Textual dependencies, SQLite storage foundation, `browser-cookie3`, BeautifulSoup/lxml and mutagen foundations.
- Improved portable Python package visibility, shortcut creation and one-command PowerShell install behavior.

## v2.1

Source: https://github.com/needowsky/VideoDownloader/releases/download/2.1/CHANGELOG.md

Focused polish release for updater safety, installer wording and playlist handling.

- Added external `update.bat` updater.
- Added custom icon usage for shortcuts.
- Added YouTube playlist preflight with detected item count, estimated size and confirmation.
- Added `q` stop control during active `yt-dlp` downloads.
- Added persistent PowerShell bootstrap logs.
- Improved installer wording, step/overall progress, installed-component detection and fallback package installation.
- Switched compatible installs toward portable Python 3.12 inside the app folder when global Python is missing or unsuitable.
- Fixed playlist/channel counters so statistics count completed downloads instead of the preflight estimate.
- Fixed clean install startup, package visibility, standard-user read permissions and GitHub download rate-limit issues.

## v2.0

Source: included in later changelogs, including https://github.com/needowsky/VideoDownloader/releases/download/2.1/CHANGELOG.md

Major project refresh focused on automatic detection, large-file reliability, installation, configuration, validation and clearer error handling.

- Added automatic MP3/MP4 input detection for links, multiple links, `.txt` files, playlists and channels.
- Added large-file manager for `.zip`, `.rar`, `.7z` and `.iso` with queue/resume support.
- Added Google Drive, Mega and GitHub release download support.
- Added download validation reports, recognized error definitions and automatic retry strategies.
- Added Spotify mode through `spotDL` and photo downloads through `gallery-dl`.
- Added commands such as `stats`, `help`, `sites`, `settings`, `update`, `history`, `about`, `doctor`, `open downloads`, `open logs` and `ping`.
- Added external language files, English/Polish interface files, settings and easter eggs.
- Improved installer behavior, dependency setup, debug output hiding, progress display and save-folder/URL validation.

## v1.0

Source: https://github.com/needowsky/VideoDownloader/releases/download/downloader/README.md

Initial public Windows console downloader.

- Added MP3 audio and MP4 video downloads through `yt-dlp`.
- Added single URL, YouTube playlist, YouTube channel and `.txt` input modes.
- Added automatic site detection for sources supported by `yt-dlp`.
- Added early support notes for YouTube, Instagram, TikTok, Facebook, Pornhub and Beeg.
- Added photo downloading for Instagram, TikTok and Facebook through `gallery-dl`.
- Added basic installer/launcher workflow, FFmpeg/yt-dlp/gallery-dl setup and quiet progress display.
- Added English/Polish language switch, error logs, retry flow, URL/save-folder validation, stats and offline Snake mode.
