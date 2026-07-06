# Changelog

## v2.5

Release prepared for GitHub with a cleaner installer, safer update flow, neutral public configuration and new foundations for a modern interface and local data storage.

### Added

- Added external `update.bat` updater. The app now launches it and closes before replacing files from a newer GitHub release.
- Added a custom application icon used by Desktop and Start Menu shortcuts.
- Added YouTube playlist preflight with detected item count, estimated size and confirmation before downloading all items.
- Added `q` stop control during active yt-dlp downloads.
- Added persistent PowerShell bootstrap logs in `%TEMP%\VideoDownloaderInstallLogs\install_ps1_latest.log`.
- Added source-vs-local validation for large/direct file downloads: expected size and MD5/SHA256 are compared with the downloaded file when the source exposes them.
- Added Facebook Reels video URL handling, including links pasted as `facebook.com/reel/...` without `https://`.
- Added neutral `config/stats.json` for download counters so public GitHub copies no longer inherit the author's local counter.
- Added Rich/Textual dependencies and Rich-powered terminal header fallback.
- Added SQLite storage foundation for user configuration, statistics, counters and history.
- Added `browser-cookie3`, BeautifulSoup/lxml and mutagen foundations for browser cookies, HTML link extraction and MP3 metadata/cover-art tagging.

### Changed

- App version is now `v2.5`.
- Installer step text now says `Downloading application files` instead of `Downloading program files`.
- Installer progress now shows step percent and overall percent, and installed components are reported as already installed, installed, or checked for updates.
- Installer package progress now displays separate step and overall progress bars.
- Installer now retries failed Python package installs with fallback methods, including Python 3.12/VC++ preparation, `--prefer-binary`, and user-site installation.
- Installer now uses portable Python 3.12 inside the app folder when compatible Python is missing or broken, avoiding global Python/winget installation side effects.
- OF-Scraper now installs into its own portable Python 3.12 environment so its dependencies do not conflict with `spotDL`.
- Installer now creates shortcuts both on the Desktop and in the Start Menu.
- PowerShell bootstrap now defaults to downloading the AIO installer from the selected branch, with `-DownloadMode release` available when a release-based install is desired.
- PowerShell bootstrap now logs failures before closing and pauses when launched from a local `.ps1` file.
- Improved menu navigation by clearing previous screens and adding back options in download submenus.
- Download counters are now stored in user/config stats data instead of being embedded in `youtube_downloader.py`.
- Installer now verifies UI/helper libraries as a dedicated dependency step.

### Fixed

- Fixed YouTube playlist/channel statistics so counters use completed items instead of the preflight/expected item count.
- Fixed portable Python package visibility by adding the app `python_packages` folder to the embedded Python path file.
- Fixed launcher startup after clean AIO installs by preferring the bundled Python 3.12 before global Python installations.
- Fixed `PermissionError` on local package imports from `C:\Program Files\VideoDownloader\python_packages` by granting standard users read permissions during installation.
- Fixed AIO GitHub downloads hitting `429 Too Many Requests` by downloading the repository as a single ZIP archive instead of many raw files.
- Fixed PowerShell bootstrap treating administrator hand-off as a failed installer run.
- Fixed one-command install flow so the PowerShell bootstrap opens the AIO installer directly in an administrator window and stops installing in the standard-user shell.
- Fixed AIO installer continuing in the non-admin window after launching the administrator window.
- Fixed OF-Scraper detection by checking the dedicated `tools/ofscraper_python/python.exe -m ofscraper` command.
- Fixed shortcut creation by adding fallback Desktop/Start Menu paths and auto-creating the launcher when possible.
- Fixed `install.ps1` log/file writing to avoid BOM issues in generated batch files and to report AIO installer exit-code failures clearly.

## v2.0

Major project refresh focused on installation, configuration, automatic detection, large-file reliability and clearer download validation.

### Added

- Automatic MP3/MP4 input detection for single links, multiple links, `.txt` files, YouTube playlists and YouTube channels.
- YouTube channel preflight check with item count, selected output type, estimated size and confirmation.
- Large-file download manager for `.zip`, `.rar`, `.7z` and `.iso`.
- Large-file support for Google Drive, Mega and GitHub links.
- GitHub repository links now resolve latest release assets with interactive file selection or download-all.
- Persistent `download_queue.txt` for interrupted large-file downloads.
- `resume` command for continuing queued large-file downloads.
- Disk-full recovery for large files by moving `.part` downloads to another folder when possible.
- Download summaries now include file validation: file size plus local MD5/SHA256 checksums when available.
- Validation reports saved to `logs/download_validation.txt`.
- Error logging to `logs/log_error_data.txt`.
- Recognized error definitions with likely reason and short repair instruction.
- Automatic retry flow with fallback download strategies.
- Spotify mode through `spotDL`.
- Photo downloading for Instagram, TikTok and Facebook through `gallery-dl`.
- Optional OF-Scraper wrapper for authorized OnlyFans workflows.
- Optional cookies support for Facebook downloads through browser cookies or `cookies.txt`.
- Optional cookies support for direct OnlyFans media links through Netscape-format `cookies.txt`.
- Recognition and single-link support for Beeg, Pornhub and other adult video sites handled by `yt-dlp`.
- `stats` command with detailed counters and ranks.
- `stats naughties` command with per-site adult-source counters.
- Hidden/encoded download statistics storage with fallback when `%APPDATA%` is unavailable.
- `help`, `sites`, `settings`, `update`, `history`, `about`, `doctor`, `open downloads`, `open logs` and `ping` commands.
- Easter eggs: `iamtheone`, `imblue`, `gothic`, `snake`, `konami`, `rickroll`, `godmode`.
- Offline internet check with Snake mini-game.
- Snake scoreboard storage.
- Runtime configuration in `config/config.json`.
- External language files in `config/lang/*.lang`.
- Language file detection and syntax validation before use.
- English and Polish interface files.
- Custom source-available license file.

### Changed

- App version is now `v2.0`.
- Installer now targets `C:\Program Files\VideoDownloader`.
- Installer requests administrator permission when needed.
- Installer creates a desktop shortcut named `Video Downloader`.
- Installer downloads program files from GitHub instead of embedding the app code.
- Installer checks existing components before downloading or installing them again.
- Installer hides technical logs by default when `DEBUG=0`.
- Installer installs and verifies Python, pip, FFmpeg, `yt-dlp`, `gallery-dl`, `spotDL` and `OF-Scraper`.
- PowerShell bootstrap installer can start the full installer from GitHub.
- `install.ps1` is now a full `irm | iex` bootstrap that downloads the AIO installer, applies settings and launches dependency setup.
- Main menu now shows only the total download count.
- Detailed counters moved to `stats` and `stats naughties`.
- MP3/MP4 source selection menu was replaced by automatic input detection.
- OnlyFans support is split between direct authorized media links and external OF-Scraper integration.
- Spotify links are handled in a dedicated Spotify mode instead of normal MP3/MP4 mode.
- Adult-site counters stay hidden until a given site has at least one saved download.
- The app clears the console before showing final download summaries.
- Download progress display updates in place instead of flooding the terminal.

### Fixed

- Fixed YouTube `HTTP 403 Forbidden` download-data errors being reported as unknown errors.
- Added a stronger YouTube fallback strategy with browser-like headers and alternate extractor clients.
- Fixed Beeg and similar extractor/server failures such as `HTTP 500 Internal Server Error` being reported as unknown errors.
- Fixed installer dependency failures on Python 3.14 by preferring compatible Python versions and installing Python 3.12 when needed.
- Installer now checks for Microsoft C++ Build Tools and installs the Visual Studio 2022 C++ workload when missing.
- Improved installer messages for `spotDL` and `OF-Scraper` dependency failures caused by missing wheels or build tools.
- PowerShell bootstrap now forces fresh GitHub branch downloads for the AIO installer to avoid stale release files during setup.
- Fixed old menu content remaining visible after download completion.
- Fixed repeated progress lines during conversion/saving.
- Improved progress layout stability when resizing the console window.
- Fixed save-folder validation so URLs cannot be accepted as local save paths.
- Fixed URL validation before downloading.
- Fixed error log extension so logs are saved as `.txt`.
- Fixed installer output noise when `DEBUG=0`.
- Fixed download counter fallback when `%APPDATA%` is unavailable.
- Fixed easter egg commands so they clear the console before output.

### Notes

- The app does not bypass DRM, paywalls or login walls.
- Spotify mode does not download protected Spotify streams; it uses `spotDL` metadata matching.
- OnlyFans support requires authorization and does not implement paywall bypassing.
- Private/login-required Facebook downloads require browser cookies or a user-provided cookies file.
