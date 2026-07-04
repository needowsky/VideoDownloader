# Video Downloader

A Windows console downloader written in Python. It can download audio, video and selected photo content through `yt-dlp` and `gallery-dl`, with a quiet progress view, automatic dependency setup and basic error guidance.

The default interface language is English. Polish is available with `LANG=pl`.

## Repository

GitHub: [needowsky/VideoDownloader](https://github.com/needowsky/VideoDownloader)

## Features

- Download MP3 audio.
- Download MP4 video in the highest available quality.
- Download from a single URL, YouTube playlist, YouTube channel or `.txt` file.
- Automatic site detection for links supported by `yt-dlp`.
- Built-in handling for common sources such as YouTube, Instagram, TikTok, Facebook, Pornhub and Beeg.
- Photo downloading for Instagram, TikTok and Facebook through `gallery-dl`.
- YouTube channel preflight check with detected item count, estimated size and confirmation.
- Clean progress display: title, progress bar, percent, downloaded MB and speed.
- Automatic retry flow with 3 fallback attempts.
- Error log with recognized problem type, likely reason and repair hint.
- Save-folder and URL validation before downloading.
- English/Polish UI switch.
- Offline Snake mini-game when there is no internet connection.

## Legal Notice

Use this tool only for content you own, content you are allowed to download, or content available under a license that permits downloading. You are responsible for following each website's terms of service and applicable law.

## Quick Start

Download or clone the repository, then run:

```text
zainstaluj_wszystko.bat
```

The all-in-one installer prepares the app and required components. After installation, start the app with:

```text
uruchom_downloader.bat
```

or:

```powershell
python youtube_downloader.py
```

## Included Files

- `zainstaluj_wszystko.bat` - all-in-one installer
- `youtube_downloader.py` - main application
- `uruchom_downloader.bat` - launcher
- `README.md` - documentation
- `LICENSE` - MIT license

## Installer

`zainstaluj_wszystko.bat` can be copied by itself to another Windows computer. It downloads the current program files from GitHub and prepares dependencies.

Program files are downloaded from:

```text
https://github.com/needowsky/VideoDownloader
```

The installer checks for existing components before downloading anything:

- Python 3
- pip
- FFmpeg
- yt-dlp
- gallery-dl

By default, technical installation details are hidden:

```bat
set "DEBUG=0"
```

Change it to:

```bat
set "DEBUG=1"
```

to show full installer logs.

Default installer language:

```bat
set "LANG=en"
```

Change it to `pl` before running the installer if you want the generated program to start in Polish.

## Usage

On startup, choose what to download:

1. MP3 - audio only
2. MP4 - video
3. Photos

Then choose the source:

1. Single link
2. YouTube playlist
3. `.txt` file with links
4. YouTube channel

For `.txt` files, put one URL per line. Lines starting with `#` are ignored.

In single-link mode, the app returns to the URL prompt after each download. Type `q` to return to the menu.

## YouTube Channels

For best results, paste a direct channel tab URL:

```text
https://www.youtube.com/@channel/videos
https://www.youtube.com/@channel/releases
https://www.youtube.com/@channel/streams
```

Before downloading a whole channel, the app checks available entries and shows:

- detected item count
- selected output type
- estimated size
- confirmation prompt

The size is an estimate because YouTube does not always expose complete format data before download.

## Output Folder

Default output folder:

```text
%USERPROFILE%\Downloads\YouTube Downloader
```

You can choose another folder at runtime.

After a download finishes, the app clears the console and shows a summary with a clickable folder link in Windows Terminal.

## Configuration

Main settings are near the top of `youtube_downloader.py`:

```python
DEBUG = 0
LANG = "en"
```

Use:

```python
DEBUG = 1
```

to show full technical logs from `yt-dlp` and related tools.

Use:

```python
LANG = "pl"
```

to start the app in Polish.

You can also switch language during runtime by typing:

```text
lang=en
lang=pl
```

## Progress Display

With `DEBUG=0`, the app hides noisy downloader logs and shows the useful status only:

- media title
- progress bar
- percent
- downloaded MB
- download speed
- conversion/saving status

## Errors And Logs

When an error occurs, the app writes:

```text
logs\log_error_data.txt
```

The log includes:

- date and time
- error description
- context
- recognized error type
- likely reason
- short repair instruction
- technical traceback when available

Common recognized problems include missing FFmpeg, missing or outdated `yt-dlp`, missing `gallery-dl`, invalid URLs, login-only/private content, network timeouts, save-folder permission issues and unavailable media formats.

For download failures, the app automatically tries 3 strategies:

1. Standard selected format.
2. Retry with longer timeout and safer connection settings.
3. Fallback format selection when the requested quality is unavailable.

## Stats

The main menu shows a download counter and rank.

English ranks:

```text
rookie, novice, regular, collector, veteran, legend
```

Polish ranks:

```text
swiezak, nowicjusz, regular, kolekcjoner, weteran, legenda
```

After more than 9000 downloads, the rank changes to:

```text
OVER 9000!
```

The counter is stored primarily inside `youtube_downloader.py` as a small hex little-endian value. If the program cannot update its own file, it falls back to hidden local stats files.

## Offline Mode

At startup, the app checks for an internet connection. If no connection is available, it starts an offline Snake mini-game.

Snake stores:

- best score
- total score

The scoreboard uses the same hidden/encoded style as the download counter and is validated on startup.

## Special Commands

These commands can be typed in most input fields:

```text
help
iamtheone
imblue
gothic
lang=en
lang=pl
```

`gothic` opens this YouTube link in the default browser:

```text
https://www.youtube.com/watch?v=DLyqSQhS6E0
```

## Requirements

The installer can prepare everything automatically. Manual requirements are:

- Windows
- Python 3
- FFmpeg
- yt-dlp
- gallery-dl

Manual Python package installation:

```powershell
python -m pip install --upgrade yt-dlp gallery-dl
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
