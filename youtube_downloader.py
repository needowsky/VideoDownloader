from __future__ import annotations

import base64
from datetime import datetime
import hashlib
import importlib
import importlib.util
import errno
import json
import os
from pathlib import Path
import random
import re
import shutil
from shutil import which
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from http.cookiejar import MozillaCookieJar
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen


def enable_utf8_console() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


enable_utf8_console()
SUBPROCESS_TEXT_OPTIONS = {"text": True, "encoding": "utf-8", "errors": "replace"}

PROGRAM_DIR = Path(__file__).resolve().parent
LOCAL_PACKAGE_DIR = PROGRAM_DIR / "python_packages"
LOCAL_PYTHON_EXE = PROGRAM_DIR / "tools" / "python312" / "python.exe"
LOCAL_FFMPEG_BIN = PROGRAM_DIR / "tools" / "ffmpeg" / "bin"
REMOTE_VALIDATION_BY_URL: dict[str, dict[str, object]] = {}
REMOTE_VALIDATION_BY_PATH: dict[str, dict[str, object]] = {}

def is_local_app_python() -> bool:
    try:
        return Path(sys.executable).resolve() == LOCAL_PYTHON_EXE.resolve()
    except OSError:
        return False


if LOCAL_PACKAGE_DIR.exists():
    sys.path.insert(0, str(LOCAL_PACKAGE_DIR))

if (LOCAL_FFMPEG_BIN / "ffmpeg.exe").exists():
    os.environ["PATH"] = str(LOCAL_FFMPEG_BIN) + os.pathsep + os.environ.get("PATH", "")

try:
    import winreg
except ImportError:
    winreg = None

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    Console = None
    Panel = None

try:
    import browser_cookie3
except ImportError:
    browser_cookie3 = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import lxml  # noqa: F401
except ImportError:
    lxml = None

try:
    import mutagen
except ImportError:
    mutagen = None

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    tk = None
    messagebox = None

try:
    import msvcrt
except ImportError:
    msvcrt = None


DEFAULT_DOWNLOAD_DIR = Path.home() / "Downloads" / "YouTube Downloader"
APP_DATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / "VideoDownloader"
CONFIG_DIR = PROGRAM_DIR / "config"
APP_CONFIG_DIR = APP_DATA_DIR / "config"
LOCAL_CONFIG_FILE = CONFIG_DIR / "config.json"
CONFIG_FILE = APP_CONFIG_DIR / "config.json"
LOCAL_STATS_CONFIG_FILE = CONFIG_DIR / "stats.json"
STATS_CONFIG_FILE = APP_CONFIG_DIR / "stats.json"
DATABASE_FILE = APP_CONFIG_DIR / "app.db"
LANG_DIR = CONFIG_DIR / "lang"
APP_LANG_DIR = APP_CONFIG_DIR / "lang"
HISTORY_FILE = APP_DATA_DIR / "history.jsonl"
LOCAL_LARGE_FILE_QUEUE_FILE = PROGRAM_DIR / "download_queue.txt"
LARGE_FILE_QUEUE_FILE = APP_DATA_DIR / "download_queue.txt"
CLIPBOARD_QUEUE_FILE = APP_DATA_DIR / "clipboard_queue.txt"
LEGACY_DOWNLOAD_STATS_FILE = APP_DATA_DIR / ".download_stats"
LEGACY_DOWNLOAD_BREAKDOWN_FILE = APP_DATA_DIR / ".download_breakdown"
LOCAL_SNAKE_STATS_FILE = PROGRAM_DIR / ".snake_scoreboard"
SNAKE_STATS_FILE = APP_DATA_DIR / ".snake_scoreboard"
FALLBACK_SNAKE_STATS_FILE = Path(".snake_scoreboard")
WINDOWS_INVALID_PATH_CHARS = set('<>"|?*')
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}
DEBUG = 0
LANG = "en"
APP_VERSION = "v3.5"
GITHUB_REPO = "needowsky/VideoDownloader"
SKIP_EXIT_PAUSE = False
FACEBOOK_COOKIES_FROM_BROWSER = "chrome"  # chrome/edge/firefox/opera/brave/vivaldi or empty
FACEBOOK_COOKIES_FILE = ""  # optional Netscape cookies.txt path
DEFAULT_MEDIA_TYPE = "mp4"
CLIPBOARD_POPUP = 1
CLIPBOARD_POPUP_TIMEOUT_SECONDS = 20
YOUTUBE_CLIPBOARD_LINK_MODE = "auto"  # auto/single/playlist
COOKIE_BROWSER_FALLBACKS = ("chrome", "edge", "firefox", "brave", "opera", "vivaldi")
COOKIE_BROWSER_NAMES = {
    "chrome": "Google Chrome",
    "edge": "Microsoft Edge",
    "firefox": "Mozilla Firefox",
    "brave": "Brave",
    "opera": "Opera",
    "vivaldi": "Vivaldi",
}
LARGE_FILE_EXTENSIONS = (".zip", ".rar", ".7z", ".iso")
LARGE_FILE_MAX_RETRIES = 10
LARGE_FILE_CHUNK_SIZE = 1024 * 1024
_SNEK_FF = "0700000007000000"
PROGRESS_BAR_WIDTH = 15
MIN_PROGRESS_BAR_WIDTH = 10
STATUS_LINE_WIDTH = 72
STATUS_TITLE_WIDTH = 22
STATUS_CLEAR_SEQUENCE = "\033[2K\r"
STATUS_BLOCK_LINES = 0
LOG_DIR = Path("logs")
ERROR_LOG_FILE = LOG_DIR / "log_error_data.txt"
COMMON_ERROR_HINTS = [
    "Brak FFmpeg/FFprobe - zainstaluj FFmpeg i uruchom program ponownie.",
    "Nieaktualne yt-dlp - uruchom: python -m pip install -U yt-dlp",
    "Brak gallery-dl - zainstaluj: python -m pip install -U gallery-dl",
    "Material prywatny albo wymagajacy logowania - uzyj publicznego linku.",
    "Bledny albo nieobslugiwany URL - sprawdz, czy link zaczyna sie od http:// lub https://.",
    "Problem sieciowy/timeout - sprawdz internet albo sprobuj ponownie pozniej.",
    "Brak uprawnien do folderu zapisu - wybierz np. folder Pobrane.",
    "Format niedostepny na danej stronie - aplikacja sprobuje awaryjnego formatu.",
]

TEXTS: dict[str, dict[str, str]] = {}
FALLBACK_TEXTS = {
    "en": {
        "choose_option": "Choose option: ",
        "invalid_choice": "Invalid choice. Try again.",
        "language_changed": "Language changed.",
        "details_saved": "Details saved in: {path}",
        "error_type": "Error type: {value}",
        "reason": "Reason: {value}",
        "how_to_fix": "How to fix: {value}",
        "exit_prompt": "Press Enter to close the window...",
    }
}


def validate_language_data(data: object, language_name: str) -> dict[str, str]:
    if not isinstance(data, dict):
        raise ValueError(f"{language_name}: language file must contain a JSON object.")

    validated: dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"{language_name}: every translation key must be a non-empty string.")
        if not isinstance(value, str):
            raise ValueError(f"{language_name}: translation value for '{key}' must be a string.")
        validated[key] = value

    if not validated:
        raise ValueError(f"{language_name}: language file is empty.")
    return validated


def load_language_file(path: Path) -> tuple[str, dict[str, str]]:
    language_name = path.stem.lower()
    if not re.fullmatch(r"[a-z]{2,12}(?:[-_][a-z0-9]{2,12})?", language_name):
        raise ValueError(f"{path.name}: invalid language file name.")
    data = json.loads(path.read_text(encoding="utf-8"))
    return language_name, validate_language_data(data, path.name)


def load_language_files() -> None:
    TEXTS.clear()
    errors: list[str] = []
    for directory in (LANG_DIR, APP_LANG_DIR):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.lang")):
            try:
                language_name, data = load_language_file(path)
                TEXTS[language_name] = data
            except Exception as exc:
                errors.append(f"{path}: {exc}")

    if "en" not in TEXTS:
        TEXTS.update(FALLBACK_TEXTS)

    for error in errors:
        print(f"Language file error: {error}")


def get_available_languages() -> list[str]:
    if not TEXTS:
        load_language_files()
    return sorted(TEXTS)


def t(key: str, **kwargs: object) -> str:
    if not TEXTS:
        load_language_files()
    lang = LANG.lower()
    if lang not in TEXTS:
        lang = "en"
    fallback_language = TEXTS.get("en") or next(iter(TEXTS.values()))
    value = TEXTS.get(lang, fallback_language).get(key, fallback_language.get(key, key))
    try:
        return value.format(**kwargs)
    except Exception:
        return value


ERROR_DEFINITIONS = [
    {
        "name": "Material prywatny lub wymagajacy cookies",
        "keywords": [
            "private video",
            "sign in",
            "cookies-from-browser",
            "cookies for the authentication",
            "use --cookies",
            "login required",
            "requires login",
        ],
        "reason": "Material wymaga zalogowanej sesji albo jest prywatny. Bez poprawnych cookies serwis nie pozwoli pobrac pliku.",
        "repair": "Program sprobuje automatycznie cookies z przegladarki i pliku cookies.txt. Jesli nadal sie nie uda, zaloguj sie w przegladarce albo umiesc aktualny cookies.txt w folderze programu lub config.",
    },
    {
        "name": "HTTP 403 Forbidden",
        "keywords": ["http error 403", "403: forbidden", "403 forbidden", "unable to download video data"],
        "reason": "Serwis odrzucil pobieranie danych wideo. Najczesciej oznacza to blokade po stronie YouTube/serwisu, nieaktualny yt-dlp, ograniczenie regionalne, cookies albo chwilowa blokade adresu IP.",
        "repair": "Zaktualizuj yt-dlp, sprobuj ponownie pozniej, uzyj innego formatu/jakosci albo dodaj cookies z przegladarki dla materialow wymagajacych sesji.",
    },
    {
        "name": "HTTP 500 / blad serwera",
        "keywords": ["http error 500", "500: internal server error", "internal server error", "unable to download json metadata"],
        "reason": "Serwis zwrocil blad po swojej stronie albo extractor nie moze aktualnie pobrac metadanych z tej strony.",
        "repair": "Sprobuj ponownie pozniej, zaktualizuj yt-dlp i sprawdz czy link dziala w przegladarce. Dla Beeg i podobnych stron problem czesto lezy po stronie serwisu.",
    },
    {
        "name": "Brak FFmpeg/FFprobe",
        "keywords": ["ffmpeg", "ffprobe"],
        "reason": "Program nie ma narzedzia do konwersji MP3 albo scalania MP4.",
        "repair": "Uruchom zainstaluj_wszystko.bat albo zainstaluj FFmpeg: winget install Gyan.FFmpeg",
    },
    {
        "name": "Brak albo nieaktualny yt-dlp",
        "keywords": ["yt_dlp", "yt-dlp", "no module named yt_dlp"],
        "reason": "Biblioteka pobierania nie jest zainstalowana albo jest zbyt stara.",
        "repair": "Uruchom zainstaluj_wszystko.bat albo: python -m pip install --upgrade yt-dlp",
    },
    {
        "name": "Brak albo nieaktualny gallery-dl",
        "keywords": ["gallery_dl", "gallery-dl", "no module named gallery_dl"],
        "reason": "Biblioteka do pobierania zdjec nie jest zainstalowana albo jest zbyt stara.",
        "repair": "Zainstaluj ja poleceniem: python -m pip install --upgrade gallery-dl",
    },
    {
        "name": "Brak uprawnien",
        "keywords": ["permission", "odmowa", "access is denied", "access denied"],
        "reason": "Windows blokuje odczyt albo zapis w wybranym miejscu.",
        "repair": "Wybierz folder Pobrane albo inny folder, do ktorego masz pelne uprawnienia.",
    },
    {
        "name": "Nieprawidlowy albo nieobslugiwany link",
        "keywords": ["unsupported url", "invalid url", "nieprawidlowy link", "no suitable extractor"],
        "reason": "Link jest bledny, prywatny albo dana strona nie jest obslugiwana przez yt-dlp.",
        "repair": "Sprawdz link w przegladarce i upewnij sie, ze zaczyna sie od http:// albo https://.",
    },
    {
        "name": "Material prywatny lub wymagajacy logowania",
        "keywords": ["private", "login", "cookies", "sign in", "zaloguj"],
        "reason": "Strona wymaga zalogowania albo material nie jest publiczny.",
        "repair": "Uzyj publicznego linku do materialu dostepnego bez logowania.",
    },
    {
        "name": "Problem z internetem",
        "keywords": ["network", "timeout", "connection", "temporarily unavailable", "remote end closed"],
        "reason": "Polaczenie zostalo przerwane, strona nie odpowiedziala albo wystapil timeout.",
        "repair": "Sprawdz internet i uruchom pobieranie ponownie za chwile.",
    },
    {
        "name": "Format niedostepny",
        "keywords": ["requested format is not available", "format not available", "no video formats"],
        "reason": "Wybrana jakosc albo format nie jest dostepny dla tego materialu.",
        "repair": "Program sam sprobuje formatu awaryjnego. Jesli blad wraca, wybierz MP3 albo inny link.",
    },
    {
        "name": "Blad zapisu pliku",
        "keywords": ["file name too long", "cannot open", "being used by another process", "oserror"],
        "reason": "Nazwa pliku jest za dluga, plik jest zajety albo system blokuje zapis.",
        "repair": "Wybierz krotszy folder zapisu, zamknij odtwarzacze i sprobuj ponownie.",
    },
]
NAUGHTY_SITE_HINTS = {
    "pornhub.com": ("pornhub", "Pornhub"),
    "beeg.com": ("beeg", "Beeg"),
    "hqporner.com": ("hqporner", "HQPorner"),
    "xvideos.com": ("xvideos", "XVideos"),
    "xhamster.com": ("xhamster", "xHamster"),
    "xnxx.com": ("xnxx", "XNXX"),
    "youporn.com": ("youporn", "YouPorn"),
    "redtube.com": ("redtube", "RedTube"),
    "tube8.com": ("tube8", "Tube8"),
    "spankbang.com": ("spankbang", "SpankBang"),
    "tnaflix.com": ("tnaflix", "TNAFlix"),
    "motherless.com": ("motherless", "Motherless"),
    "eporner.com": ("eporner", "Eporner"),
    "thisvid.com": ("thisvid", "ThisVid"),
    "drtuber.com": ("drtuber", "DrTuber"),
    "vporn.com": ("vporn", "VPorn"),
    "porntrex.com": ("porntrex", "Porntrex"),
    "xozilla.com": ("xozilla", "Xozilla"),
    "txxx.com": ("txxx", "TXXX"),
}
NAUGHTY_STAT_KEYS = tuple(site_key for site_key, _label in NAUGHTY_SITE_HINTS.values())

SUPPORTED_SITE_HINTS = {
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "fb.watch": "Facebook",
    "spotify.com": "Spotify",
    "open.spotify.com": "Spotify",
    "drive.google.com": "Google Drive",
    "docs.google.com": "Google Drive",
    "mega.nz": "Mega",
    "mega.co.nz": "Mega",
    "github.com": "GitHub",
    "raw.githubusercontent.com": "GitHub",
    "objects.githubusercontent.com": "GitHub",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
}
SUPPORTED_SITE_HINTS.update({domain: label for domain, (_site_key, label) in NAUGHTY_SITE_HINTS.items()})
MATRIX_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ#$%&*+-/<=>?"
MAX_REASONABLE_DOWNLOAD_COUNT = 10_000_000
SNAKE_WIDTH = 30
SNAKE_HEIGHT = 14
GOTHIC_URL = "https://www.youtube.com/watch?v=DLyqSQhS6E0"
RICKROLL_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
GODMODE_URL = "https://www.youtube.com/watch?v=tnROqOCwVVY"
CONVERSION_STATUS_STOP = threading.Event()
CONVERSION_STATUS_THREAD: threading.Thread | None = None
CONVERSION_STATUS_TITLE = "Konwertowanie"
CONVERSION_STATUS_FULLSCREEN = False
DOWNLOAD_CANCEL_REQUESTED = False
COMPLETED_DOWNLOAD_KEYS: set[str] = set()
COMPLETED_DOWNLOAD_TITLES: list[str] = []
COMPLETED_DOWNLOAD_FILES: list[str] = []
DOWNLOAD_STAT_KEYS = ("total", "spotify", "youtube", "naughties", *NAUGHTY_STAT_KEYS, "other")
TOTAL_USAGE_SECONDS = 0
SESSION_STARTED_AT = time.time()
CLIPBOARD_WATCHER_STOP = threading.Event()
CLIPBOARD_WATCHER_THREAD: threading.Thread | None = None
CLIPBOARD_WATCHER_LAST_URL = ""
CLIPBOARD_PROMPT_LOCK = threading.Lock()
CLIPBOARD_DOWNLOAD_LOCK = threading.Lock()
CLIPBOARD_STATUS_LAST_URL = ""
CLIPBOARD_STATUS_QUEUE_COUNT = 0
STATUS_LOCK = threading.RLock()


class DownloadCancelled(Exception):
    pass


def ask_choice(prompt: str, options: dict[str, str]) -> str:
    while True:
        print()
        console = get_rich_console()
        if console is not None:
            console.print(f"[bold cyan]{prompt}[/bold cyan]")
            for key, label in options.items():
                console.print(f"[bold green]{key}[/bold green]. {label}")
        else:
            print(prompt)
            for key, label in options.items():
                print(f"{key}. {label}")

        choice = input(t("choose_option")).strip()
        if choice in options:
            clear_console()
            return choice
        if handle_easter_egg(choice):
            continue

        print(t("invalid_choice"))


def ask_download_type_choice() -> str:
    options = {
        "0": t("back_to_menu").strip(),
        "1": t("mp3"),
        "2": t("mp4"),
        "3": t("photos"),
        "4": t("spotify"),
    }
    default_choice = "1" if DEFAULT_MEDIA_TYPE == "mp3" else "2"
    while True:
        print()
        console = get_rich_console()
        if console is not None:
            console.print(f"[bold cyan]{t('what_download')}[/bold cyan]")
            for key, label in options.items():
                suffix = " [default]" if key == default_choice else ""
                console.print(f"[bold green]{key}[/bold green]. {label}{suffix}")
        else:
            print(t("what_download"))
            for key, label in options.items():
                suffix = " [default]" if key == default_choice else ""
                print(f"{key}. {label}{suffix}")

        choice = input(t("choose_option")).strip()
        if not choice:
            clear_console()
            return default_choice
        if choice in options:
            clear_console()
            return choice
        if handle_easter_egg(choice):
            continue
        print(t("invalid_choice"))


def ask_non_empty(prompt: str) -> str:
    while True:
        value = input(prompt).strip().strip('"')
        if handle_easter_egg(value):
            continue
        if value:
            return value
        print(t("empty_field"))


def handle_easter_egg(value: str) -> bool:
    global LANG
    command = value.strip().lower()
    if command.startswith("lang="):
        requested_language = command.split("=", 1)[1].strip().lower()
        available_languages = get_available_languages()
        if requested_language in available_languages:
            LANG = requested_language
            save_config()
            print(t("language_changed"))
        else:
            print(t("invalid_choice"))
            print("Available languages: " + ", ".join(available_languages))
        return True
    if command == "help":
        show_command_help()
        return True
    if command == "stats":
        clear_console()
        print_app_header()
        show_download_stats()
        input(t("continue_prompt"))
        return True
    if command == "stats naughties":
        clear_console()
        print_app_header()
        show_download_stats(show_naughties=True)
        input(t("continue_prompt"))
        return True
    if command == "sites":
        show_supported_sites()
        return True
    if command == "update":
        check_for_update()
        return True
    if command == "history":
        show_history()
        return True
    if command == "settings":
        show_settings_menu()
        return True
    if command == "version":
        show_about()
        return True
    if command == "about":
        show_about()
        return True
    if command == "doctor":
        run_doctor()
        return True
    if command == "open downloads":
        open_path(DEFAULT_DOWNLOAD_DIR)
        return True
    if command == "open logs":
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        open_path(LOG_DIR)
        return True
    if command == "ping":
        ping_youtube()
        return True
    if command == "file":
        run_large_file_flow()
        return True
    if command == "resume":
        resume_large_file_queue()
        return True
    if command == "clipboard":
        prompt_clipboard_queue(DEFAULT_DOWNLOAD_DIR)
        return True
    if command == "konami":
        print(t("konami"))
        return True
    if command == "rickroll":
        webbrowser.open(RICKROLL_URL)
        return True
    if command == "godmode":
        print(t("godmode"))
        webbrowser.open(GODMODE_URL)
        return True
    if command == "iamtheone":
        clear_console()
        show_matrix_rain()
        return True
    if command == "imblue":
        set_blue_console()
        return True
    if command == "gothic":
        start_gothic_music()
        return True
    if command == "snake":
        play_snake()
        return True
    return False


def show_command_help() -> None:
    print()
    print(t("commands_title"))
    print(t("help_help"))
    print(t("help_matrix"))
    print(t("help_blue"))
    print(t("help_gothic"))
    print(t("help_lang"))
    print(t("help_stats"))
    print(t("help_stats_naughties"))
    print(t("help_sites"))
    print(t("help_update"))
    print(t("help_history"))
    print(t("help_settings"))
    print(t("help_about"))
    print(t("help_doctor"))
    print(t("help_open_downloads"))
    print(t("help_open_logs"))
    print(t("help_ping"))
    print(t("help_file"))
    print(t("help_resume"))
    print(t("help_clipboard"))
    print()


def show_about() -> None:
    print()
    print(t("about_title"))
    print(t("about_version", version=APP_VERSION))
    print(t("about_author"))
    print(t("about_license"))
    print(t("about_copyright"))
    print(t("about_open_source"))
    print(t("about_repo"))
    print()


def open_path(path: Path) -> None:
    target = path.expanduser().resolve()
    print(t("opening_path", path=target))
    try:
        if os.name == "nt":
            os.startfile(str(target))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
    except Exception as exc:
        print_error_details(exc)


def doctor_line(label: str, ok: bool, detail: str = "") -> None:
    status = t("doctor_ok") if ok else t("doctor_fail")
    suffix = f" - {detail}" if detail else ""
    print(f"- {label}: {status}{suffix}")


def run_doctor() -> None:
    print()
    print(t("doctor_title"))
    doctor_line("Python", True, sys.version.split()[0])
    doctor_line("FFmpeg", has_ffmpeg())
    doctor_line("yt-dlp", yt_dlp is not None)
    doctor_line("gallery-dl", has_gallery_dl())
    doctor_line("spotDL", has_spotdl())
    doctor_line("Rich/Textual", Console is not None and importlib.util.find_spec("textual") is not None)
    doctor_line("browser-cookie3", browser_cookie3 is not None)
    doctor_line("BeautifulSoup/lxml", BeautifulSoup is not None and lxml is not None)
    doctor_line("mutagen", mutagen is not None)
    doctor_line("SQLite", True, sqlite3.sqlite_version)
    doctor_line(t("doctor_internet"), has_internet_connection())
    path, error = validate_download_dir(str(DEFAULT_DOWNLOAD_DIR))
    doctor_line(t("doctor_save_dir"), path is not None, str(path or error))
    print()


def ping_youtube() -> None:
    started = time.perf_counter()
    try:
        request = Request("https://www.youtube.com/generate_204", headers={"User-Agent": "VideoDownloader"})
        with urlopen(request, timeout=10):
            pass
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        print(t("ping_result", ms=elapsed_ms))
    except Exception as exc:
        print(t("ping_error", error=exc))


def show_supported_sites() -> None:
    standard_sites = [
        "YouTube",
        "Instagram",
        "TikTok",
        "Facebook",
        "Spotify",
    ]
    naughty_sites = [label for _domain, (_site_key, label) in NAUGHTY_SITE_HINTS.items()]
    print()
    print(t("sites_title"))
    print(", ".join(standard_sites))
    print(", ".join(naughty_sites))
    print(t("sites_note"))
    print()


def get_rich_console() -> object | None:
    if Console is None:
        return None
    try:
        return Console()
    except Exception:
        return None


def print_app_header() -> None:
    title = t("app_title", version=APP_VERSION)
    console = get_rich_console()
    if console is not None and Panel is not None:
        console.print(Panel.fit(title, border_style="cyan"))
        return
    print(title)


def init_database() -> None:
    try:
        DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DATABASE_FILE) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS kv ("
                "key TEXT PRIMARY KEY, "
                "value TEXT NOT NULL, "
                "updated_at TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS history ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "created_at TEXT NOT NULL, "
                "media_type TEXT NOT NULL, "
                "site TEXT NOT NULL, "
                "url TEXT NOT NULL, "
                "title TEXT NOT NULL)"
            )
            conn.commit()
    except sqlite3.Error:
        return


def db_get_json(key: str) -> dict[str, object] | None:
    try:
        init_database()
        with sqlite3.connect(DATABASE_FILE) as conn:
            row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        data = json.loads(str(row[0]))
        return data if isinstance(data, dict) else None
    except (sqlite3.Error, json.JSONDecodeError, OSError):
        return None


def db_set_json(key: str, value: dict[str, object]) -> None:
    try:
        init_database()
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        with sqlite3.connect(DATABASE_FILE) as conn:
            conn.execute(
                "INSERT INTO kv(key, value, updated_at) VALUES(?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (key, payload, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
    except (sqlite3.Error, OSError):
        return


def db_delete_key(key: str) -> None:
    try:
        init_database()
        with sqlite3.connect(DATABASE_FILE) as conn:
            conn.execute("DELETE FROM kv WHERE key = ?", (key,))
            conn.commit()
    except (sqlite3.Error, OSError):
        return


def get_config_file() -> Path:
    if LOCAL_CONFIG_FILE.exists():
        return LOCAL_CONFIG_FILE
    if CONFIG_FILE.exists():
        return CONFIG_FILE
    return LOCAL_CONFIG_FILE


def get_config_data() -> dict[str, object]:
    return {
        "lang": LANG,
        "debug": DEBUG,
        "popup": CLIPBOARD_POPUP,
        "total_usage_seconds": TOTAL_USAGE_SECONDS,
        "default_download_dir": str(DEFAULT_DOWNLOAD_DIR),
        "default_media_type": DEFAULT_MEDIA_TYPE,
        "facebook_cookies_from_browser": FACEBOOK_COOKIES_FROM_BROWSER,
        "facebook_cookies_file": FACEBOOK_COOKIES_FILE,
        "youtube_clipboard_link_mode": YOUTUBE_CLIPBOARD_LINK_MODE,
    }


def save_config() -> None:
    data = get_config_data()
    db_set_json("config", data)


def load_config() -> None:
    global DEBUG, LANG, DEFAULT_DOWNLOAD_DIR, DEFAULT_MEDIA_TYPE, CLIPBOARD_POPUP
    global FACEBOOK_COOKIES_FROM_BROWSER, FACEBOOK_COOKIES_FILE
    global YOUTUBE_CLIPBOARD_LINK_MODE
    global TOTAL_USAGE_SECONDS

    db_config = db_get_json("config")
    if db_config:
        data = db_config
    else:
        path = get_config_file()
        if not path.exists():
            save_config()
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            save_config()
            return

    if not isinstance(data, dict):
        save_config()
        return

    configured_language = str(data.get("lang", LANG)).lower()
    if configured_language in get_available_languages():
        LANG = configured_language
    try:
        DEBUG = 1 if int(data.get("debug", DEBUG)) else 0
    except (TypeError, ValueError):
        DEBUG = 0
    try:
        CLIPBOARD_POPUP = 1 if int(data.get("popup", CLIPBOARD_POPUP)) else 0
    except (TypeError, ValueError):
        CLIPBOARD_POPUP = 1
    try:
        TOTAL_USAGE_SECONDS = max(0, int(float(data.get("total_usage_seconds", TOTAL_USAGE_SECONDS))))
    except (TypeError, ValueError):
        TOTAL_USAGE_SECONDS = 0

    configured_dir = str(data.get("default_download_dir", DEFAULT_DOWNLOAD_DIR)).strip()
    if configured_dir:
        DEFAULT_DOWNLOAD_DIR = Path(configured_dir).expanduser()
    media_type = str(data.get("default_media_type", DEFAULT_MEDIA_TYPE)).lower()
    if media_type in {"mp3", "mp4"}:
        DEFAULT_MEDIA_TYPE = media_type
    FACEBOOK_COOKIES_FROM_BROWSER = str(data.get("facebook_cookies_from_browser", FACEBOOK_COOKIES_FROM_BROWSER)).strip()
    FACEBOOK_COOKIES_FILE = str(data.get("facebook_cookies_file", FACEBOOK_COOKIES_FILE)).strip()
    youtube_clipboard_mode = str(data.get("youtube_clipboard_link_mode", YOUTUBE_CLIPBOARD_LINK_MODE)).strip().lower()
    if youtube_clipboard_mode in {"auto", "single", "playlist"}:
        YOUTUBE_CLIPBOARD_LINK_MODE = youtube_clipboard_mode
    save_config()


def show_settings_menu() -> None:
    global DEBUG, LANG, DEFAULT_DOWNLOAD_DIR, DEFAULT_MEDIA_TYPE, CLIPBOARD_POPUP
    global FACEBOOK_COOKIES_FROM_BROWSER, FACEBOOK_COOKIES_FILE
    global YOUTUBE_CLIPBOARD_LINK_MODE

    while True:
        print()
        print(t("settings_title"))
        available_languages = get_available_languages()
        options = {
            "1": f"{t('settings_language')}: {LANG} ({', '.join(available_languages)})",
            "2": f"{t('settings_debug')}: {DEBUG}",
            "3": f"{t('settings_download_dir')}: {DEFAULT_DOWNLOAD_DIR}",
            "4": f"{t('settings_default_media')}: {DEFAULT_MEDIA_TYPE}",
            "5": f"{t('settings_popup')}: {CLIPBOARD_POPUP}",
            "6": f"{t('settings_fb_browser')}: {FACEBOOK_COOKIES_FROM_BROWSER}",
            "7": f"{t('settings_fb_file')}: {FACEBOOK_COOKIES_FILE or '-'}",
            "8": t("settings_import_cookies"),
            "9": f"{t('settings_youtube_clipboard_mode')}: {YOUTUBE_CLIPBOARD_LINK_MODE}",
            "10": t("back_to_menu").strip(),
        }
        choice = ask_choice(t("settings_title"), options)
        if choice == "10":
            return

        if choice == "8":
            ok, _browser, message = import_cookies_from_default_browser()
            print(message)
            if not ok:
                print(t("cookies_import_hint"))
            input(t("continue_prompt"))
            continue

        value = input(t("settings_prompt_value")).strip().strip('"')
        if choice == "1" and value.lower() in available_languages:
            LANG = value.lower()
        elif choice == "2" and value in {"0", "1"}:
            DEBUG = int(value)
        elif choice == "3" and value:
            path, error = validate_download_dir(value)
            if path is None:
                print(t("invalid_save_path", error=error))
                continue
            DEFAULT_DOWNLOAD_DIR = path
        elif choice == "4" and value.lower() in {"mp3", "mp4"}:
            DEFAULT_MEDIA_TYPE = value.lower()
        elif choice == "5" and value in {"0", "1"}:
            CLIPBOARD_POPUP = int(value)
        elif choice == "6":
            FACEBOOK_COOKIES_FROM_BROWSER = value.lower()
        elif choice == "7":
            FACEBOOK_COOKIES_FILE = value
        elif choice == "9" and value.lower() in {"auto", "single", "playlist"}:
            YOUTUBE_CLIPBOARD_LINK_MODE = value.lower()
        elif value:
            print(t("invalid_choice"))
            continue
        save_config()
        print(t("settings_saved"))


def add_history_entries(urls: Iterable[str], media_type: str, saved_items: Iterable[str]) -> None:
    items = list(saved_items)
    if not items:
        return
    urls_list = list(urls)
    history_rows: list[dict[str, str]] = []
    for index, item in enumerate(items):
        source_url = urls_list[0] if len(urls_list) == 1 else urls_list[index] if len(urls_list) == len(items) else ""
        history_rows.append(
            {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "media_type": media_type,
                "site": detect_site(source_url) if source_url else "",
                "url": source_url,
                "title": item,
            }
        )

    try:
        init_database()
        with sqlite3.connect(DATABASE_FILE) as conn:
            conn.executemany(
                "INSERT INTO history(created_at, media_type, site, url, title) VALUES(?, ?, ?, ?, ?)",
                [
                    (row["date"], row["media_type"], row["site"], row["url"], row["title"])
                    for row in history_rows
                ],
            )
            conn.commit()
    except sqlite3.Error:
        return


def show_history(limit: int = 15) -> None:
    print()
    print(t("history_title"))
    try:
        init_database()
        with sqlite3.connect(DATABASE_FILE) as conn:
            rows = conn.execute(
                "SELECT created_at, media_type, site, title FROM history ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        if rows:
            for date, media_type, site, title in reversed(rows):
                print(f"- {date} | {media_type} | {site} | {title}")
            return
    except sqlite3.Error:
        pass

    if not HISTORY_FILE.exists():
        print(t("history_empty"))
        return
    try:
        lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()[-limit:]
    except OSError:
        print(t("history_empty"))
        return
    if not lines:
        print(t("history_empty"))
        return
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        title = str(item.get("title", ""))
        site = str(item.get("site", ""))
        media_type = str(item.get("media_type", ""))
        date = str(item.get("date", ""))
        print(f"- {date} | {media_type} | {site} | {title}")


def parse_version(value: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", value)
    return tuple(int(part) for part in numbers) if numbers else (0,)


def get_release_version_label(release: dict[str, object]) -> str:
    name = str(release.get("name") or "").strip()
    tag = str(release.get("tag_name") or "").strip()
    if re.search(r"\d", name):
        return name
    return tag or name


def get_update_release() -> dict[str, object]:
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    request = Request(api_url, headers={"User-Agent": "VideoDownloader"})
    with urlopen(request, timeout=20) as response:
        release = json.loads(response.read().decode("utf-8"))
    if not isinstance(release, dict):
        raise RuntimeError("GitHub latest release response is invalid.")
    return release


def start_external_updater() -> None:
    updater = PROGRAM_DIR / "update.bat"
    if not updater.exists():
        raise FileNotFoundError(f"Missing updater file: {updater}")

    if os.name == "nt":
        subprocess.Popen(
            ["cmd.exe", "/c", "start", "Video Downloader Updater", str(updater)],
            cwd=PROGRAM_DIR,
            shell=False,
        )
    else:
        subprocess.Popen([str(updater)], cwd=PROGRAM_DIR)


def check_for_update() -> None:
    global SKIP_EXIT_PAUSE
    print()
    print(t("update_checking"))
    try:
        release = get_update_release()
        latest = get_release_version_label(release)
        print(t("update_current", current=APP_VERSION))
        print(t("update_latest", latest=latest or "?"))
        if not latest or parse_version(latest) <= parse_version(APP_VERSION):
            print(t("update_none"))
            return

        body = str(release.get("body") or "").strip()
        if body:
            print()
            print(t("update_body"))
            print(body[:3000])
            print()

        if not ask_yes_no(t("update_prompt")):
            return

        start_external_updater()
        print(t("update_external_started"))
        SKIP_EXIT_PAUSE = True
        raise SystemExit(0)
    except Exception as exc:
        print(t("update_error", error=exc))
        log_path = write_error_log(exc, "GitHub update check/apply")
        print(t("details_saved", path=log_path))


def clear_console() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def terminal_supports_hyperlinks() -> bool:
    return bool(os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"))


def make_folder_uri(path: Path) -> str:
    resolved = path.expanduser().resolve()
    try:
        return resolved.as_uri()
    except ValueError:
        return "file:///" + quote(resolved.as_posix(), safe="/:")


def make_folder_hyperlink(path: Path) -> str:
    resolved = path.expanduser().resolve()
    label = str(resolved)
    if not terminal_supports_hyperlinks():
        return label

    uri = make_folder_uri(resolved)
    return f"\033]8;;{uri}\033\\{label}\033]8;;\033\\"


def hash_file(path: Path) -> tuple[str | None, str | None]:
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    try:
        with path.open("rb") as file:
            while True:
                chunk = file.read(1024 * 1024)
                if not chunk:
                    break
                md5.update(chunk)
                sha256.update(chunk)
        return md5.hexdigest(), sha256.hexdigest()
    except OSError:
        return None, None


def normalize_hex_checksum(value: object, algorithm: str) -> str | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    if ":" in text:
        prefix, digest = text.split(":", 1)
        if prefix.strip().lower() == algorithm:
            text = digest.strip().lower()
    text = text.strip('"').strip("'")
    expected_length = 64 if algorithm == "sha256" else 32
    if re.fullmatch(rf"[0-9a-f]{{{expected_length}}}", text):
        return text
    return None


def base64_digest_to_hex(value: str) -> str | None:
    try:
        return base64.b64decode(value.strip(), validate=True).hex()
    except Exception:
        return None


def get_header_value(headers: object, name: str) -> str:
    try:
        return str(headers.get(name, "") or "")  # type: ignore[attr-defined]
    except AttributeError:
        return ""


def extract_remote_checksums_from_headers(headers: object) -> dict[str, str]:
    checksums: dict[str, str] = {}

    md5_hex = normalize_hex_checksum(get_header_value(headers, "Content-MD5"), "md5")
    if md5_hex is None and get_header_value(headers, "Content-MD5"):
        md5_hex = base64_digest_to_hex(get_header_value(headers, "Content-MD5"))
    if md5_hex:
        checksums["md5"] = md5_hex

    for header_name in ("x-checksum-md5", "x-amz-meta-md5", "x-amz-meta-checksum-md5"):
        md5_hex = normalize_hex_checksum(get_header_value(headers, header_name), "md5")
        if md5_hex:
            checksums["md5"] = md5_hex
            break

    for header_name in ("x-checksum-sha256", "x-amz-checksum-sha256", "x-amz-meta-sha256", "x-amz-meta-checksum-sha256"):
        sha256_hex = normalize_hex_checksum(get_header_value(headers, header_name), "sha256")
        if sha256_hex is None and get_header_value(headers, header_name):
            decoded = base64_digest_to_hex(get_header_value(headers, header_name))
            sha256_hex = decoded if decoded and len(decoded) == 64 else None
        if sha256_hex:
            checksums["sha256"] = sha256_hex
            break

    goog_hash = get_header_value(headers, "x-goog-hash")
    if goog_hash:
        for part in goog_hash.split(","):
            key, sep, value = part.strip().partition("=")
            if sep and key.lower() == "md5":
                md5_hex = base64_digest_to_hex(value)
                if md5_hex:
                    checksums["md5"] = md5_hex

    etag = get_header_value(headers, "ETag").strip('"').lower()
    if "md5" not in checksums and re.fullmatch(r"[0-9a-f]{32}", etag):
        checksums["md5"] = etag

    return checksums


def register_remote_validation(
    url: str,
    *,
    filename: str | None = None,
    size: int | None = None,
    md5: str | None = None,
    sha256: str | None = None,
) -> dict[str, object]:
    checksums: dict[str, str] = {}
    md5 = normalize_hex_checksum(md5, "md5")
    sha256 = normalize_hex_checksum(sha256, "sha256")
    if md5:
        checksums["md5"] = md5
    if sha256:
        checksums["sha256"] = sha256
    metadata: dict[str, object] = {
        "url": url,
        "filename": filename or "",
        "size_bytes": int(size) if isinstance(size, int) and size > 0 else None,
        "checksums": checksums,
    }
    REMOTE_VALIDATION_BY_URL[url] = metadata
    return metadata


def register_downloaded_file_validation(path: Path, metadata: dict[str, object] | None) -> None:
    if not metadata:
        return
    try:
        REMOTE_VALIDATION_BY_PATH[str(path.resolve())] = metadata
    except OSError:
        REMOTE_VALIDATION_BY_PATH[str(path)] = metadata


def get_remote_validation_for_path(path: Path) -> dict[str, object] | None:
    try:
        return REMOTE_VALIDATION_BY_PATH.get(str(path.resolve()))
    except OSError:
        return REMOTE_VALIDATION_BY_PATH.get(str(path))


def remote_validation_status(size_bytes: int, md5: str | None, sha256: str | None, metadata: dict[str, object] | None) -> tuple[str, list[str]]:
    if not metadata:
        return "local-only", ["source metadata unavailable"]

    problems: list[str] = []
    expected_size = metadata.get("size_bytes")
    if isinstance(expected_size, int) and expected_size > 0 and size_bytes != expected_size:
        problems.append(f"size mismatch: expected {expected_size} B, got {size_bytes} B")

    checksums = metadata.get("checksums")
    if isinstance(checksums, dict):
        expected_md5 = checksums.get("md5")
        expected_sha256 = checksums.get("sha256")
        if expected_md5:
            if not md5:
                problems.append("MD5 unavailable locally")
            elif str(expected_md5).lower() != md5.lower():
                problems.append("MD5 mismatch")
        if expected_sha256:
            if not sha256:
                problems.append("SHA256 unavailable locally")
            elif str(expected_sha256).lower() != sha256.lower():
                problems.append("SHA256 mismatch")

    if problems:
        return "mismatch", problems
    if (isinstance(expected_size, int) and expected_size > 0) or (isinstance(checksums, dict) and checksums):
        return "ok", []
    return "local-only", ["source size/checksum unavailable"]


def find_matching_downloaded_file(base_path: Path, item: str) -> Path | None:
    if not item:
        return None
    candidates: list[Path] = []
    raw_path = Path(item)
    if raw_path.is_absolute() and raw_path.is_file():
        return raw_path
    direct = base_path / item
    if direct.is_file():
        return direct

    item_lower = item.lower()
    base_stem = raw_path.stem.lower()
    try:
        for path in base_path.rglob("*"):
            if not path.is_file() or path.name.endswith(".part"):
                continue
            name_lower = path.name.lower()
            stem_lower = path.stem.lower()
            if name_lower == item_lower or item_lower in name_lower or (base_stem and base_stem == stem_lower):
                candidates.append(path)
    except OSError:
        return None

    if candidates:
        return max(candidates, key=lambda path: path.stat().st_mtime)
    return None


def collect_recent_downloaded_files(base_path: Path, limit: int = 20) -> list[Path]:
    now = time.time()
    files: list[Path] = []
    try:
        for path in base_path.rglob("*"):
            if not path.is_file() or path.name.endswith(".part"):
                continue
            try:
                if now - path.stat().st_mtime <= 3600:
                    files.append(path)
            except OSError:
                continue
    except OSError:
        return []
    return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


def get_validation_targets(saved_path: Path, saved_items: Iterable[str]) -> list[Path]:
    targets: list[Path] = []
    seen: set[Path] = set()

    if saved_path.is_file():
        return [saved_path]

    for file_path in COMPLETED_DOWNLOAD_FILES:
        path = Path(file_path)
        if path.exists() and path.is_file() and path.suffix != ".part":
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                targets.append(path)
                continue
        if path.suffix:
            for extension in (".mp3", ".mp4", ".m4a", ".webm", ".mkv"):
                alternative = path.with_suffix(extension)
                if alternative.exists() and alternative.is_file():
                    resolved = alternative.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        targets.append(alternative)
                    break

    for item in saved_items:
        match = find_matching_downloaded_file(saved_path, item)
        if match:
            resolved = match.resolve()
            if resolved not in seen:
                seen.add(resolved)
                targets.append(match)

    if not targets:
        for path in collect_recent_downloaded_files(saved_path):
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                targets.append(path)

    return targets


def write_validation_report(rows: list[dict[str, object]]) -> Path | None:
    if not rows:
        return None
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        report_path = LOG_DIR / "download_validation.txt"
        with report_path.open("a", encoding="utf-8") as file:
            file.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
            for row in rows:
                file.write(f"File: {row['path']}\n")
                file.write(f"Size: {row['size_bytes']} bytes ({row['size_mb']})\n")
                file.write(f"Source validation: {row.get('remote_status', 'local-only')}\n")
                if row.get("remote_size_bytes"):
                    file.write(f"Expected size: {row['remote_size_bytes']} bytes ({row['remote_size_mb']})\n")
                if row.get("md5") and row.get("sha256"):
                    file.write(f"MD5: {row['md5']}\n")
                    file.write(f"SHA256: {row['sha256']}\n")
                else:
                    file.write("MD5/SHA256: unavailable\n")
                if row.get("remote_md5"):
                    file.write(f"Expected MD5: {row['remote_md5']}\n")
                if row.get("remote_sha256"):
                    file.write(f"Expected SHA256: {row['remote_sha256']}\n")
                for problem in row.get("remote_problems", []):
                    file.write(f"Validation problem: {problem}\n")
                file.write("\n")
        return report_path
    except OSError:
        return None


def build_file_validation_rows(saved_path: Path, saved_items: Iterable[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in get_validation_targets(saved_path, saved_items):
        try:
            size_bytes = path.stat().st_size
        except OSError:
            continue
        md5, sha256 = hash_file(path)
        remote_metadata = get_remote_validation_for_path(path)
        remote_status, remote_problems = remote_validation_status(size_bytes, md5, sha256, remote_metadata)
        remote_size = None
        remote_md5 = None
        remote_sha256 = None
        if remote_metadata:
            raw_remote_size = remote_metadata.get("size_bytes")
            remote_size = raw_remote_size if isinstance(raw_remote_size, int) and raw_remote_size > 0 else None
            checksums = remote_metadata.get("checksums")
            if isinstance(checksums, dict):
                remote_md5 = checksums.get("md5")
                remote_sha256 = checksums.get("sha256")
        rows.append(
            {
                "path": str(path),
                "name": path.name,
                "size_bytes": size_bytes,
                "size_mb": format_mb(size_bytes),
                "md5": md5,
                "sha256": sha256,
                "remote_status": remote_status,
                "remote_problems": remote_problems,
                "remote_size_bytes": remote_size,
                "remote_size_mb": format_mb(remote_size) if remote_size else "",
                "remote_md5": remote_md5,
                "remote_sha256": remote_sha256,
            }
        )
    return rows


def print_file_validation(saved_path: Path, saved_items: Iterable[str]) -> None:
    rows = build_file_validation_rows(saved_path, saved_items)
    if not rows:
        print(t("validation_unavailable"))
        return

    print(t("validation_title"))
    preview_limit = 10
    for row in rows[:preview_limit]:
        print(f"- {row['name']}")
        print(f"  {t('validation_size')}: {row['size_mb']} ({row['size_bytes']} B)")
        print(f"  Source check: {row.get('remote_status', 'local-only')}")
        if row.get("remote_size_bytes"):
            print(f"  Expected size: {row['remote_size_mb']} ({row['remote_size_bytes']} B)")
        if row.get("md5") and row.get("sha256"):
            print(f"  MD5: {row['md5']}")
            print(f"  SHA256: {row['sha256']}")
        else:
            print(f"  {t('validation_hash_unavailable')}")
        if row.get("remote_md5"):
            print(f"  Expected MD5: {row['remote_md5']}")
        if row.get("remote_sha256"):
            print(f"  Expected SHA256: {row['remote_sha256']}")
        for problem in row.get("remote_problems", []):
            print(f"  Validation problem: {problem}")
    if len(rows) > preview_limit:
        print(t("saved_more", count=len(rows) - preview_limit))

    report_path = write_validation_report(rows)
    if report_path:
        print(t("validation_report", path=report_path))


def print_saved_summary(saved_path: Path, saved_items: Iterable[str] | None = None) -> None:
    clear_console()
    items = [item for item in (saved_items or []) if item]
    print(t("finished_title"))
    print()
    if items:
        print(t("saved_items"))
        preview_limit = 10
        for item in items[:preview_limit]:
            print(f"- {item}")
        if len(items) > preview_limit:
            print(t("saved_more", count=len(items) - preview_limit))
    else:
        print(t("saved_files"))

    print()
    print_file_validation(saved_path, items)
    print()
    print(f"{t('location')}: {make_folder_hyperlink(saved_path)}")
    if not terminal_supports_hyperlinks():
        print(f"URI: {make_folder_uri(saved_path)}")
    print()
    COMPLETED_DOWNLOAD_FILES.clear()


def has_internet_connection(timeout: float = 3.0) -> bool:
    test_targets = [
        ("1.1.1.1", 53),
        ("8.8.8.8", 53),
    ]
    for host, port in test_targets:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def wait_for_snake_key() -> str | None:
    if os.name != "nt":
        return None
    try:
        import msvcrt

        if not msvcrt.kbhit():
            return None
        key = msvcrt.getch()
        if key in {b"\x00", b"\xe0"}:
            key = msvcrt.getch()
            return {
                b"H": "up",
                b"P": "down",
                b"K": "left",
                b"M": "right",
            }.get(key)
        return {
            b"w": "up",
            b"W": "up",
            b"s": "down",
            b"S": "down",
            b"a": "left",
            b"A": "left",
            b"d": "right",
            b"D": "right",
            b"q": "quit",
            b"Q": "quit",
        }.get(key)
    except ImportError:
        return None


def draw_snake_board(
    snake: list[tuple[int, int]],
    food: tuple[int, int],
    score: int,
    best_score: int,
    total_score: int,
) -> None:
    snake_cells = set(snake)
    head = snake[0]
    print(t("offline_snake", score=score, best=max(best_score, score), total=total_score + score))
    print("#" * (SNAKE_WIDTH + 2))
    for y in range(SNAKE_HEIGHT):
        row = []
        for x in range(SNAKE_WIDTH):
            cell = (x, y)
            if cell == head:
                row.append("@")
            elif cell == food:
                row.append("*")
            elif cell in snake_cells:
                row.append("o")
            else:
                row.append(" ")
        print("#" + "".join(row) + "#")
    print("#" * (SNAKE_WIDTH + 2))


def spawn_snake_food(snake: list[tuple[int, int]]) -> tuple[int, int]:
    snake_cells = set(snake)
    while True:
        food = (random.randrange(SNAKE_WIDTH), random.randrange(SNAKE_HEIGHT))
        if food not in snake_cells:
            return food


def play_snake() -> None:
    if os.name != "nt":
        print(t("snake_windows_only"))
        input(t("press_enter_continue"))
        return

    snake = [(SNAKE_WIDTH // 2, SNAKE_HEIGHT // 2)]
    direction = (1, 0)
    food = spawn_snake_food(snake)
    score = 0
    best_score, total_score = load_snake_scoreboard()

    while True:
        clear_console()
        draw_snake_board(snake, food, score, best_score, total_score)
        key = wait_for_snake_key()
        if key == "quit":
            save_snake_scoreboard(max(best_score, score), total_score + score)
            break
        if key == "up" and direction != (0, 1):
            direction = (0, -1)
        elif key == "down" and direction != (0, -1):
            direction = (0, 1)
        elif key == "left" and direction != (1, 0):
            direction = (-1, 0)
        elif key == "right" and direction != (-1, 0):
            direction = (1, 0)

        head_x, head_y = snake[0]
        next_head = (head_x + direction[0], head_y + direction[1])
        hit_wall = not (0 <= next_head[0] < SNAKE_WIDTH and 0 <= next_head[1] < SNAKE_HEIGHT)
        hit_self = next_head in snake
        if hit_wall or hit_self:
            clear_console()
            draw_snake_board(snake, food, score, best_score, total_score)
            save_snake_scoreboard(max(best_score, score), total_score + score)
            print(t("game_over"))
            input(t("press_enter_continue"))
            break

        snake.insert(0, next_head)
        if next_head == food:
            score += 1
            food = spawn_snake_food(snake)
        else:
            snake.pop()

        time.sleep(max(0.06, 0.14 - score * 0.004))


def ensure_internet_or_offline_mode() -> bool:
    while not has_internet_connection():
        clear_console()
        print(t("no_connection"))
        print(t("need_internet_snake"))
        print()
        play_snake()
        if has_internet_connection():
            print(t("internet_back"))
            return True
        if not ask_yes_no(t("retry_internet")):
            return False
    return True


def set_blue_console() -> None:
    if os.name == "nt":
        os.system("color 1F")
    else:
        print("\033[44;97m", end="")
    clear_console()
    print(t("blue_enabled"))


def show_matrix_rain(lines: int = 18, width: int = 72) -> None:
    green = "\033[92m"
    reset = "\033[0m"
    print()
    print(f"{green}Wake up, Neo...{reset}")
    for _ in range(lines):
        row = "".join(random.choice(MATRIX_CHARS) for _ in range(width))
        if os.name == "nt":
            print(row)
        else:
            print(f"{green}{row}{reset}")
        time.sleep(0.035)
    print(f"{green}The Matrix has you.{reset}")


def start_gothic_music() -> None:
    opened = webbrowser.open(GOTHIC_URL, new=2)
    if opened:
        print(f"Gothic mode: {GOTHIC_URL}")
    else:
        print(f"Nie udalo sie otworzyc przegladarki. Link: {GOTHIC_URL}")


def ensure_hidden_file(path: Path) -> None:
    if os.name == "nt" and path.exists():
        subprocess.run(["attrib", "+h", str(path)], capture_output=True, **SUBPROCESS_TEXT_OPTIONS)


def clear_hidden_file(path: Path) -> None:
    if os.name == "nt" and path.exists():
        subprocess.run(["attrib", "-h", str(path)], capture_output=True, **SUBPROCESS_TEXT_OPTIONS)


def encode_download_count(value: int) -> str:
    safe_value = max(0, min(int(value), MAX_REASONABLE_DOWNLOAD_COUNT))
    return safe_value.to_bytes(4, byteorder="little", signed=False).hex()


def decode_download_count(raw_value: str) -> int | None:
    clean = raw_value.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{8}", clean):
        return None
    value = int.from_bytes(bytes.fromhex(clean), byteorder="little", signed=False)
    if value < 0 or value > MAX_REASONABLE_DOWNLOAD_COUNT:
        return None
    return value


def default_download_breakdown(total: int = 0) -> dict[str, int]:
    safe_total = max(0, min(int(total), MAX_REASONABLE_DOWNLOAD_COUNT))
    return {key: (safe_total if key == "total" else 0) for key in DOWNLOAD_STAT_KEYS}


def normalize_download_breakdown(data: dict[str, object] | None, fallback_total: int = 0) -> dict[str, int]:
    if not isinstance(data, dict):
        return default_download_breakdown(fallback_total)

    normalized: dict[str, int] = {}
    for key in DOWNLOAD_STAT_KEYS:
        raw_value = data.get(key, 0)
        if isinstance(raw_value, bool):
            value = 0
        else:
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                value = 0
        normalized[key] = max(0, min(value, MAX_REASONABLE_DOWNLOAD_COUNT))

    legacy_total = max(0, min(int(fallback_total), MAX_REASONABLE_DOWNLOAD_COUNT))
    naughty_detail_total = sum(normalized[key] for key in NAUGHTY_STAT_KEYS)
    normalized["naughties"] = max(normalized["naughties"], naughty_detail_total)
    category_total = (
        normalized["spotify"]
        + normalized["youtube"]
        + normalized["naughties"]
        + normalized["other"]
    )
    normalized["total"] = max(normalized["total"], legacy_total, category_total)
    return normalized


def encode_download_breakdown(data: dict[str, int]) -> str:
    normalized = normalize_download_breakdown(data)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return payload.encode("utf-8").hex()


def decode_download_breakdown(raw_value: str) -> dict[str, int] | None:
    clean = raw_value.strip().lower()
    if not clean or not re.fullmatch(r"[0-9a-f]+", clean) or len(clean) % 2:
        return None
    try:
        payload = bytes.fromhex(clean).decode("utf-8")
        decoded = json.loads(payload)
    except (ValueError, json.JSONDecodeError):
        return None
    return normalize_download_breakdown(decoded)


def encode_snake_scoreboard(best_score: int, total_score: int) -> str:
    best = max(0, min(int(best_score), MAX_REASONABLE_DOWNLOAD_COUNT))
    total = max(0, min(int(total_score), MAX_REASONABLE_DOWNLOAD_COUNT))
    return best.to_bytes(4, byteorder="little", signed=False).hex() + total.to_bytes(
        4, byteorder="little", signed=False
    ).hex()


def decode_snake_scoreboard(raw_value: str) -> tuple[int, int] | None:
    clean = raw_value.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{16}", clean):
        return None

    best = int.from_bytes(bytes.fromhex(clean[:8]), byteorder="little", signed=False)
    total = int.from_bytes(bytes.fromhex(clean[8:]), byteorder="little", signed=False)
    if best < 0 or total < 0 or best > MAX_REASONABLE_DOWNLOAD_COUNT or total > MAX_REASONABLE_DOWNLOAD_COUNT:
        return None
    return best, total


def load_embedded_snake_scoreboard() -> tuple[int, int] | None:
    return decode_snake_scoreboard(_SNEK_FF)


def save_embedded_snake_scoreboard(best_score: int, total_score: int) -> bool:
    global _SNEK_FF
    encoded = encode_snake_scoreboard(best_score, total_score)
    program_file = Path(__file__).resolve()
    try:
        clear_hidden_file(program_file)
        text = program_file.read_text(encoding="utf-8")
        new_text, replacements = re.subn(
            r'^_SNEK_FF = "[0-9a-fA-F]{16}"',
            f'_SNEK_FF = "{encoded}"',
            text,
            count=1,
            flags=re.MULTILINE,
        )
        if replacements != 1:
            return False
        program_file.write_text(new_text, encoding="utf-8")
        _SNEK_FF = encoded
        return True
    except OSError:
        return False


def get_existing_stats_config_file() -> Path:
    if STATS_CONFIG_FILE.exists():
        return STATS_CONFIG_FILE
    if LOCAL_STATS_CONFIG_FILE.exists():
        return LOCAL_STATS_CONFIG_FILE
    return STATS_CONFIG_FILE


def get_existing_snake_stats_file() -> Path:
    if LOCAL_SNAKE_STATS_FILE.exists():
        return LOCAL_SNAKE_STATS_FILE
    if SNAKE_STATS_FILE.exists():
        return SNAKE_STATS_FILE
    if FALLBACK_SNAKE_STATS_FILE.exists():
        return FALLBACK_SNAKE_STATS_FILE
    return LOCAL_SNAKE_STATS_FILE


def get_default_stats_config_data() -> dict[str, object]:
    return {
        "download_count": encode_download_count(0),
        "download_breakdown": encode_download_breakdown(default_download_breakdown(0)),
    }


def read_stats_config() -> dict[str, object]:
    db_stats = db_get_json("stats")
    if db_stats:
        return db_stats
    try:
        stats_file = get_existing_stats_config_file()
        if stats_file.exists():
            data = json.loads(stats_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (OSError, json.JSONDecodeError):
        pass
    return get_default_stats_config_data()


def write_stats_config(data: dict[str, object]) -> None:
    safe_data = {
        "download_count": encode_download_count(decode_download_count(str(data.get("download_count", ""))) or 0),
        "download_breakdown": encode_download_breakdown(
            decode_download_breakdown(str(data.get("download_breakdown", ""))) or default_download_breakdown(0)
        ),
    }
    db_set_json("stats", safe_data)


def load_legacy_user_stats_count() -> int:
    try:
        if LEGACY_DOWNLOAD_STATS_FILE.exists():
            raw_value = LEGACY_DOWNLOAD_STATS_FILE.read_text(encoding="utf-8").strip()
            if raw_value.isdigit():
                value = int(raw_value)
                if 0 <= value <= MAX_REASONABLE_DOWNLOAD_COUNT:
                    return value
    except OSError:
        pass
    return 0


def load_legacy_user_breakdown(fallback_total: int) -> dict[str, int]:
    try:
        if LEGACY_DOWNLOAD_BREAKDOWN_FILE.exists():
            value = decode_download_breakdown(LEGACY_DOWNLOAD_BREAKDOWN_FILE.read_text(encoding="utf-8"))
            if value is not None:
                return normalize_download_breakdown(value, fallback_total)
    except OSError:
        pass
    return default_download_breakdown(fallback_total)


def load_snake_stats_file() -> tuple[int, int]:
    try:
        stats_file = get_existing_snake_stats_file()
        if not stats_file.exists():
            return 0, 0

        value = decode_snake_scoreboard(stats_file.read_text(encoding="utf-8"))
        if value is None:
            save_snake_scoreboard(0, 0)
            return 0, 0
        return value
    except OSError:
        return 0, 0


def load_download_breakdown() -> dict[str, int]:
    data = read_stats_config()
    fallback_total = decode_download_count(str(data.get("download_count", ""))) or 0
    value = decode_download_breakdown(str(data.get("download_breakdown", "")))
    if value is None:
        value = load_legacy_user_breakdown(fallback_total)
        save_download_breakdown(value)
    return normalize_download_breakdown(value, fallback_total)


def load_download_count() -> int:
    data = read_stats_config()
    value = decode_download_count(str(data.get("download_count", "")))
    if value is None:
        value = load_legacy_user_stats_count()
        save_download_count(value)
    return value


def load_snake_scoreboard() -> tuple[int, int]:
    embedded_value = load_embedded_snake_scoreboard()
    file_best, file_total = load_snake_stats_file()
    if embedded_value is None:
        return file_best, file_total

    embedded_best, embedded_total = embedded_value
    return max(embedded_best, file_best), max(embedded_total, file_total)


def ensure_download_stats_file() -> None:
    count = load_download_count()
    breakdown = load_download_breakdown()
    breakdown["total"] = max(breakdown["total"], count)
    save_download_count(max(count, breakdown["total"]))
    save_download_breakdown(breakdown)


def ensure_snake_scoreboard_file() -> None:
    best_score, total_score = load_snake_scoreboard()
    save_snake_scoreboard(best_score, total_score)


def save_download_count(value: int) -> None:
    safe_value = max(0, min(int(value), MAX_REASONABLE_DOWNLOAD_COUNT))
    data = read_stats_config()
    data["download_count"] = encode_download_count(safe_value)
    if "download_breakdown" not in data:
        data["download_breakdown"] = encode_download_breakdown(default_download_breakdown(safe_value))
    write_stats_config(data)


def save_download_breakdown(data: dict[str, int]) -> None:
    normalized = normalize_download_breakdown(data, load_download_count())
    encoded = encode_download_breakdown(normalized)
    stats_data = read_stats_config()
    stats_data["download_count"] = encode_download_count(normalized["total"])
    stats_data["download_breakdown"] = encoded
    write_stats_config(stats_data)


def save_snake_scoreboard(best_score: int, total_score: int) -> None:
    safe_best = max(0, min(int(best_score), MAX_REASONABLE_DOWNLOAD_COUNT))
    safe_total = max(0, min(int(total_score), MAX_REASONABLE_DOWNLOAD_COUNT))
    if save_embedded_snake_scoreboard(safe_best, safe_total):
        return

    encoded = encode_snake_scoreboard(safe_best, safe_total)
    for stats_file in (LOCAL_SNAKE_STATS_FILE, SNAKE_STATS_FILE, FALLBACK_SNAKE_STATS_FILE):
        try:
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            clear_hidden_file(stats_file)
            stats_file.write_text(encoded, encoding="utf-8")
            ensure_hidden_file(stats_file)
            return
        except OSError:
            continue


def add_downloaded_files(amount: int = 1, category: str = "other") -> None:
    if amount <= 0:
        return
    clean_category = category if category in DOWNLOAD_STAT_KEYS else "other"
    if clean_category in NAUGHTY_STAT_KEYS:
        aggregate_category = "naughties"
    elif clean_category in {"spotify", "youtube", "naughties"}:
        aggregate_category = clean_category
    else:
        aggregate_category = "other"

    breakdown = load_download_breakdown()
    current_total = load_download_count()
    new_total = current_total + amount
    breakdown["total"] = max(breakdown["total"], current_total) + amount
    breakdown[aggregate_category] = breakdown.get(aggregate_category, 0) + amount
    if clean_category in NAUGHTY_STAT_KEYS:
        breakdown[clean_category] = breakdown.get(clean_category, 0) + amount
    save_download_count(new_total)
    save_download_breakdown(breakdown)


def get_rank_from_scale(count: int, scale: tuple[tuple[int, str], ...], default_key: str) -> str:
    if count > 9000:
        return "OVER 9000!"

    for threshold, rank_key in scale:
        if count < threshold:
            return t(rank_key)
    return t(default_key)


def get_overall_download_rank(count: int) -> str:
    return get_rank_from_scale(
        count,
        (
            (25, "rank_overall_starter"),
            (100, "rank_overall_downloader"),
            (300, "rank_overall_collector"),
            (1000, "rank_overall_archivist"),
            (3000, "rank_overall_master"),
            (9001, "rank_overall_legend"),
        ),
        "rank_overall_legend",
    )


def get_category_download_rank(count: int) -> str:
    return get_rank_from_scale(
        count,
        (
            (10, "rank_category_rookie"),
            (50, "rank_category_regular"),
            (150, "rank_category_fan"),
            (500, "rank_category_collector"),
            (1500, "rank_category_specialist"),
            (9001, "rank_category_legend"),
        ),
        "rank_category_legend",
    )


def get_download_counter_text() -> str:
    count = load_download_count()
    return t("stats", count=count, rank=get_overall_download_rank(count))


def format_duration(seconds: int | float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def get_total_usage_seconds(include_current_session: bool = True) -> int:
    session_seconds = int(time.time() - SESSION_STARTED_AT) if include_current_session else 0
    return max(0, int(TOTAL_USAGE_SECONDS) + session_seconds)


def save_usage_time() -> None:
    global TOTAL_USAGE_SECONDS, SESSION_STARTED_AT
    now = time.time()
    elapsed = max(0, int(now - SESSION_STARTED_AT))
    if elapsed:
        TOTAL_USAGE_SECONDS = max(0, int(TOTAL_USAGE_SECONDS)) + elapsed
        SESSION_STARTED_AT = now
        save_config()


def format_stats_line(label_key: str, count: int, overall: bool = False) -> str:
    return t(
        "stats_line",
        label=t(label_key),
        count=count,
        rank=get_overall_download_rank(count) if overall else get_category_download_rank(count),
    )


def show_download_stats(show_naughties: bool = False) -> None:
    breakdown = load_download_breakdown()
    print()
    print(t("stats_title"))
    if show_naughties:
        print(format_stats_line("stats_naughties", breakdown["naughties"]))
        for site_key in NAUGHTY_STAT_KEYS:
            if breakdown[site_key] > 0:
                print(format_stats_line(f"stats_{site_key}", breakdown[site_key]))
    else:
        print(format_stats_line("stats_total", breakdown["total"], overall=True))
        print(format_stats_line("stats_spotify", breakdown["spotify"]))
        print(format_stats_line("stats_youtube", breakdown["youtube"]))
        print(format_stats_line("stats_naughties", breakdown["naughties"]))
        print(format_stats_line("stats_other", breakdown["other"]))
        print(t("stats_usage_time", time=format_duration(get_total_usage_seconds())))
        print(t("stats_naughties_hint"))
    print()


def get_snake_scoreboard_text() -> str:
    best_score, total_score = load_snake_scoreboard()
    return t("snake_scoreboard", best=best_score, total=total_score)


def ask_url_or_quit(prompt: str) -> str | None:
    while True:
        value = ask_non_empty(prompt)
        if value.lower() in {"q", "quit", "koniec"}:
            return None

        value = normalize_user_url(value)
        error = validate_url(value)
        if error is None:
            return value

        print(t("invalid_url", error=error))


def ask_url(prompt: str) -> str:
    while True:
        value = normalize_user_url(ask_non_empty(prompt))
        error = validate_url(value)
        if error is None:
            return value

        print(t("invalid_url", error=error))


def ask_download_input() -> str | None:
    while True:
        value = input(t("auto_input_prompt")).strip().strip('"')
        if value.lower() in {"q", "quit", "koniec"}:
            return None
        if handle_easter_egg(value):
            continue
        if value:
            return value
        print(t("empty_field"))


def ask_yes_no(prompt: str) -> bool:
    while True:
        answer = input(f"{prompt}{t('yes_no_suffix')}").strip().lower()
        if answer in {"t", "tak", "y", "yes"}:
            return True
        if answer in {"n", "nie", "no"}:
            return False
        print(t("yes_no_hint"))


def read_urls_from_txt(file_path: str) -> list[str]:
    path = Path(file_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {path}")

    if not path.is_file():
        raise ValueError(f"To nie jest plik: {path}")

    urls = []
    try:
        text = path.read_text(encoding="utf-8")
    except PermissionError as exc:
        raise PermissionError(
            "Brak dostepu do pliku .txt. Przenies go np. do folderu Pobrane "
            "albo uruchom program z konta, ktore ma dostep do tego pliku."
        ) from exc

    for line in text.splitlines():
        clean = normalize_user_url(line.strip())
        if clean and not clean.startswith("#"):
            url_error = validate_url(clean)
            if url_error is not None:
                raise ValueError(f"Nieprawidlowy link w pliku .txt: {clean} ({url_error})")
            urls.append(clean)

    if not urls:
        raise ValueError("Plik .txt nie zawiera zadnych linkow.")

    return urls


def looks_like_url(value: str) -> bool:
    parsed = urlparse(normalize_user_url(value))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_user_url(value: str) -> str:
    clean = value.strip().strip('"')
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", clean):
        return clean
    lowered = clean.lower()
    known_prefixes = (
        "youtube.com/",
        "youtu.be/",
        "instagram.com/",
        "tiktok.com/",
        "facebook.com/",
        "fb.com/",
        "fb.watch/",
        "github.com/",
        "mega.nz/",
        "drive.google.com/",
        "open.spotify.com/",
        "pornhub.com/",
        "beeg.com/",
    )
    if lowered.startswith(known_prefixes) or lowered.startswith("www."):
        return "https://" + clean
    return clean


def is_youtube_watch_url(url: str) -> bool:
    parsed = urlparse(normalize_user_url(url))
    host = parsed.netloc.lower().replace("www.", "")
    return host in {"youtube.com", "m.youtube.com"} and parsed.path.lower() == "/watch"


def strip_youtube_playlist_from_watch_url(url: str) -> str:
    normalized = normalize_user_url(url)
    if not is_youtube_watch_url(normalized):
        return normalized

    parsed = urlparse(normalized)
    cleaned_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in {"list", "index", "start_radio"}
    ]
    return urlunparse(parsed._replace(query=urlencode(cleaned_query)))


def normalize_clipboard_download_url(url: str) -> str:
    normalized = normalize_user_url(url)
    mode = YOUTUBE_CLIPBOARD_LINK_MODE.lower()
    if mode in {"auto", "single"} and is_youtube_watch_url(normalized):
        return strip_youtube_playlist_from_watch_url(normalized)
    return normalized


def extract_links_from_html(html: str, base_url: str) -> list[str]:
    if BeautifulSoup is None:
        return []
    try:
        soup = BeautifulSoup(html, "lxml" if lxml is not None else "html.parser")
    except Exception:
        return []
    links: list[str] = []
    seen: set[str] = set()
    for tag in soup.find_all(["a", "source", "video", "img"]):
        for attribute in ("href", "src"):
            raw_value = tag.get(attribute)
            if not raw_value:
                continue
            link = str(raw_value).strip()
            if link.startswith("//"):
                link = urlparse(base_url).scheme + ":" + link
            elif link.startswith("/"):
                parsed = urlparse(base_url)
                link = f"{parsed.scheme}://{parsed.netloc}{link}"
            link = normalize_user_url(link)
            if looks_like_url(link) and link not in seen:
                seen.add(link)
                links.append(link)
    return links


def is_youtube_channel_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    if host not in {"youtube.com", "m.youtube.com"} and not host.endswith(".youtube.com"):
        return False
    path = parsed.path.strip("/")
    if not path:
        return False
    if path.startswith("watch") or path.startswith("playlist") or path.startswith("shorts/"):
        return False
    return path.startswith("@") or path.startswith(("channel/", "c/", "user/"))


def is_youtube_playlist_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    if host not in {"youtube.com", "m.youtube.com"} and not host.endswith(".youtube.com"):
        return False
    return parsed.path.strip("/").startswith("playlist") or "list=" in parsed.query


def parse_download_input(raw_value: str) -> tuple[list[str], str]:
    value = raw_value.strip().strip('"')
    if not value:
        raise ValueError(t("empty_field"))

    path = Path(value).expanduser()
    if path.exists() and path.is_file():
        urls = read_urls_from_txt(str(path))
    elif value.lower().endswith(".txt") and not looks_like_url(value):
        raise ValueError(f"Text file not found: {value}")
    else:
        tokens = [token.strip().strip(",;") for token in re.split(r"[\s,;]+", value) if token.strip().strip(",;")]
        urls = []
        invalid_tokens = []
        for token in tokens:
            token = normalize_user_url(token)
            url_error = validate_url(token)
            if url_error is None:
                urls.append(token)
            else:
                invalid_tokens.append(f"{token} ({url_error})")
        if invalid_tokens:
            raise ValueError("; ".join(invalid_tokens))
        if not urls:
            raise ValueError("No valid links detected.")

    if len(urls) == 1 and is_youtube_channel_url(urls[0]):
        return urls, "channel"
    if len(urls) == 1 and is_youtube_playlist_url(urls[0]):
        return urls, "playlist"
    return urls, "auto"


def ask_auto_download_urls(media_type: str) -> tuple[list[str], str] | None:
    while True:
        raw_value = ask_download_input()
        if raw_value is None:
            print(t("back_to_menu"))
            return None
        try:
            urls, source_type = parse_download_input(raw_value)
        except Exception as exc:
            print(t("auto_input_error", error=exc))
            print(t("auto_input_fix"))
            continue

        print(t("detected_links", count=len(urls)))
        if source_type == "channel":
            print(t("detected_channel"))
            if not preflight_channel_download(urls[0], media_type):
                print(t("channel_cancelled"))
                continue
        elif source_type == "playlist":
            print(t("detected_playlist"))
            if not preflight_playlist_download(urls[0], media_type):
                print(t("playlist_cancelled"))
                continue
        return urls, source_type


def is_large_file_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(extension) for extension in LARGE_FILE_EXTENSIONS)


def is_google_drive_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host == "drive.google.com" or host == "docs.google.com" or host.endswith(".googleusercontent.com")


def is_mega_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host in {"mega.nz", "mega.co.nz"} or host.endswith(".mega.nz") or host.endswith(".mega.co.nz")


def is_github_file_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path
    if host in {"raw.githubusercontent.com", "objects.githubusercontent.com"} or host.endswith(".githubusercontent.com"):
        return True
    if host != "github.com":
        return False
    return any(marker in path for marker in ("/releases/download/", "/archive/", "/raw/", "/blob/"))


def get_github_repo_from_url(url: str) -> tuple[str, str] | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    if host != "github.com":
        return None
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return None
    if len(parts) >= 3 and parts[2] in {"releases", "archive", "raw", "blob", "tree", "commit", "issues", "pulls"}:
        if parts[2] != "releases":
            return None
        if len(parts) >= 4 and parts[3] == "download":
            return None
    return parts[0], parts[1]


def is_github_repo_url(url: str) -> bool:
    return get_github_repo_from_url(url) is not None and not is_github_file_url(url)


def normalize_file_download_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    parts = parsed.path.strip("/").split("/")
    if host == "github.com" and len(parts) >= 5 and parts[2] == "blob":
        owner, repo, _blob, branch = parts[:4]
        file_path = "/".join(parts[4:])
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
    return url


def is_cloud_file_url(url: str) -> bool:
    return is_google_drive_url(url) or is_mega_url(url)


def is_supported_file_download_url(url: str) -> bool:
    return is_large_file_url(url) or is_cloud_file_url(url) or is_github_file_url(url) or is_github_repo_url(url)


def filename_from_response_or_url(url: str, response_headers: object | None = None) -> str:
    header = ""
    if response_headers is not None:
        try:
            header = response_headers.get("Content-Disposition", "")  # type: ignore[attr-defined]
        except AttributeError:
            header = ""
    match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', header)
    name = match.group(1) if match else Path(urlparse(url).path).name
    if not name:
        name = f"download_{int(time.time())}.bin"
    for char in WINDOWS_INVALID_PATH_CHARS:
        name = name.replace(char, "_")
    return name.strip(" .") or f"download_{int(time.time())}.bin"


def parse_large_file_input(raw_value: str) -> list[str]:
    value = raw_value.strip().strip('"')
    if not value:
        raise ValueError(t("empty_field"))
    path = Path(value).expanduser()
    if path.exists() and path.is_file():
        urls = read_urls_from_txt(str(path))
    else:
        urls = []
        invalid_tokens = []
        tokens = [item.strip().strip(",;") for item in re.split(r"[\s,;]+", value) if item.strip().strip(",;")]
        for token in tokens:
            token = normalize_user_url(token)
            url_error = validate_url(token)
            if url_error is not None:
                invalid_tokens.append(f"{token} ({url_error})")
            elif not is_supported_file_download_url(token):
                invalid_tokens.append(f"{token} ({t('file_invalid')})")
            else:
                urls.append(normalize_file_download_url(token))
        if invalid_tokens:
            raise ValueError("; ".join(invalid_tokens))
    unsupported = [url for url in urls if not is_supported_file_download_url(url)]
    if unsupported:
        raise ValueError(t("file_invalid"))
    if not urls:
        raise ValueError("No supported file links detected.")
    return [normalize_file_download_url(url) for url in urls]


def get_latest_github_release_assets(repo_url: str) -> list[dict[str, object]]:
    repo = get_github_repo_from_url(repo_url)
    if repo is None:
        return []
    owner, name = repo
    repo_label = f"{owner}/{name}"
    print(t("github_release_check", repo=repo_label))
    api_url = f"https://api.github.com/repos/{owner}/{name}/releases/latest"
    request = Request(api_url, headers={"User-Agent": "VideoDownloader"})
    with urlopen(request, timeout=30) as response:
        release = json.loads(response.read().decode("utf-8"))

    assets: list[dict[str, object]] = []
    for asset in release.get("assets", []):
        asset_name = str(asset.get("name") or "")
        asset_url = str(asset.get("browser_download_url") or "")
        if asset_name and asset_url:
            digest = str(asset.get("digest") or "")
            sha256 = normalize_hex_checksum(digest, "sha256")
            size = int(asset.get("size") or 0)
            register_remote_validation(asset_url, filename=asset_name, size=size, sha256=sha256)
            assets.append(
                {
                    "name": asset_name,
                    "url": asset_url,
                    "size": size,
                    "sha256": sha256 or "",
                }
            )
    return assets


def select_github_release_assets(repo_url: str) -> list[str]:
    try:
        assets = get_latest_github_release_assets(repo_url)
    except Exception as exc:
        print(t("github_release_error", error=exc))
        log_path = write_error_log(exc, f"GitHub latest release assets. URL: {repo_url}")
        print(t("details_saved", path=log_path))
        return []

    if not assets:
        print(t("github_release_no_assets"))
        return []

    print()
    print(t("github_release_assets"))
    for index, asset in enumerate(assets, start=1):
        size = format_gb_or_mb(asset.get("size") if isinstance(asset.get("size"), int) else None)
        print(f"{index}. {asset['name']} ({size})")

    while True:
        choice = input(t("github_release_select")).strip().lower()
        if handle_easter_egg(choice):
            continue
        if choice == t("github_release_all").lower() or choice == "all":
            return [str(asset["url"]) for asset in assets]
        try:
            selected_indexes = {
                int(part.strip())
                for part in re.split(r"[,;\s]+", choice)
                if part.strip()
            }
        except ValueError:
            print(t("invalid_choice"))
            continue
        selected_urls = [
            str(assets[index - 1]["url"])
            for index in sorted(selected_indexes)
            if 1 <= index <= len(assets)
        ]
        if selected_urls:
            return selected_urls
        print(t("invalid_choice"))


def expand_file_download_sources(urls: Iterable[str]) -> list[str]:
    expanded: list[str] = []
    for url in urls:
        if is_github_repo_url(url):
            expanded.extend(select_github_release_assets(url))
        else:
            expanded.append(normalize_file_download_url(url))
    return expanded


def get_large_file_queue_file() -> Path:
    if LOCAL_LARGE_FILE_QUEUE_FILE.exists():
        return LOCAL_LARGE_FILE_QUEUE_FILE
    if LARGE_FILE_QUEUE_FILE.exists():
        return LARGE_FILE_QUEUE_FILE
    return LOCAL_LARGE_FILE_QUEUE_FILE


def write_large_file_queue(download_dir: Path, current: str, queue: Iterable[str]) -> Path:
    queue_list = list(queue)
    db_set_json(
        "large_file_queue",
        {
            "download_dir": str(download_dir),
            "current": current,
            "queue": queue_list,
        },
    )
    lines = [
        "# VideoDownloader large-file queue",
        "# Do not edit while the app is downloading.",
        f"download_dir={download_dir}",
        f"current={current}",
    ]
    lines.extend(f"queue={url}" for url in queue_list)
    try:
        LARGE_FILE_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        LARGE_FILE_QUEUE_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return LARGE_FILE_QUEUE_FILE
    except OSError:
        return DATABASE_FILE


def clear_large_file_queue() -> None:
    db_delete_key("large_file_queue")
    for path in (LOCAL_LARGE_FILE_QUEUE_FILE, LARGE_FILE_QUEUE_FILE):
        try:
            if path.exists():
                path.unlink()
        except OSError:
            continue


def read_large_file_queue() -> tuple[Path, str, list[str]]:
    data = db_get_json("large_file_queue")
    if data:
        download_dir = Path(str(data.get("download_dir", DEFAULT_DOWNLOAD_DIR))).expanduser()
        current = str(data.get("current", "") or "")
        raw_queue = data.get("queue", [])
        queue = [str(item) for item in raw_queue] if isinstance(raw_queue, list) else []
        return download_dir, current, queue

    path = get_large_file_queue_file()
    if not path.exists():
        return DEFAULT_DOWNLOAD_DIR, "", []

    download_dir = DEFAULT_DOWNLOAD_DIR
    current = ""
    queue: list[str] = []
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().lower()
            value = value.strip()
            if key == "download_dir" and value:
                download_dir = Path(value).expanduser()
            elif key == "current":
                current = value
            elif key == "queue" and value:
                queue.append(value)
    except OSError:
        return DEFAULT_DOWNLOAD_DIR, "", []
    if current or queue:
        write_large_file_queue(download_dir, current, queue)
    return download_dir, current, queue


def get_pending_large_file_queue_count() -> int:
    _download_dir, current, queue = read_large_file_queue()
    return (1 if current else 0) + len(queue)


def get_remote_file_metadata(url: str) -> dict[str, object]:
    request = Request(url, method="HEAD", headers={"User-Agent": "VideoDownloader"})
    try:
        with urlopen(request, timeout=20) as response:
            length = response.headers.get("Content-Length")
            filename = filename_from_response_or_url(url, response.headers)
            size = int(length) if length and length.isdigit() else None
            checksums = extract_remote_checksums_from_headers(response.headers)
            metadata = register_remote_validation(
                url,
                filename=filename,
                size=size,
                md5=checksums.get("md5"),
                sha256=checksums.get("sha256"),
            )
            return metadata
    except Exception:
        return REMOTE_VALIDATION_BY_URL.get(url) or register_remote_validation(url)


def get_remote_file_info(url: str) -> tuple[int | None, str | None]:
    metadata = get_remote_file_metadata(url)
    size = metadata.get("size_bytes")
    filename = metadata.get("filename")
    return (
        size if isinstance(size, int) else None,
        str(filename) if filename else None,
    )


def ensure_enough_space(download_dir: Path, required_bytes: int | None, existing_bytes: int = 0) -> None:
    if required_bytes is None:
        return
    available = shutil.disk_usage(download_dir).free
    remaining = max(0, required_bytes - existing_bytes)
    if available < remaining:
        raise OSError(t("file_space_error", required=format_gb_or_mb(remaining), available=format_gb_or_mb(available)))


def is_disk_full_error(error: OSError) -> bool:
    return (
        getattr(error, "errno", None) == errno.ENOSPC
        or getattr(error, "winerror", None) == 112
        or "no space left" in str(error).lower()
        or "not enough space" in str(error).lower()
        or "disk full" in str(error).lower()
        or "za malo" in str(error).lower()
        or "brak miejsca" in str(error).lower()
        or "wolnego miejsca" in str(error).lower()
    )


def move_partial_to_new_download_dir(
    filename: str,
    old_partial: Path,
    old_download_dir: Path,
    total_size: int | None,
) -> tuple[Path, Path, Path, int]:
    print()
    print(t("file_disk_full"))
    print(t("file_choose_new_disk"))
    new_download_dir = ask_download_dir()
    new_download_dir.mkdir(parents=True, exist_ok=True)

    existing_bytes = old_partial.stat().st_size if old_partial.exists() else 0
    ensure_enough_space(new_download_dir, total_size, existing_bytes)

    new_partial = new_download_dir / old_partial.name
    new_target = new_download_dir / filename
    try:
        if old_partial.exists():
            if new_partial.exists():
                if new_partial.stat().st_size >= old_partial.stat().st_size:
                    old_partial.unlink(missing_ok=True)
                else:
                    new_partial.unlink()
                    shutil.move(str(old_partial), str(new_partial))
            else:
                shutil.move(str(old_partial), str(new_partial))
        print(t("file_part_moved", path=new_partial))
    except OSError as exc:
        print(t("file_part_move_failed", error=exc))
        raise

    moved_bytes = new_partial.stat().st_size if new_partial.exists() else 0
    return new_download_dir, new_partial, new_target, moved_bytes


def render_file_progress(name: str, downloaded: int, total: int | None, started_at: float) -> None:
    percent = downloaded / total * 100 if total else None
    speed = downloaded / max(0.001, time.perf_counter() - started_at)
    eta = (total - downloaded) / max(speed, 0.001) if total else None
    percent_text = f"{percent:.0f}%" if percent is not None else "--%"
    print_status_block(
        [
            shorten_text(name, STATUS_LINE_WIDTH),
            f"{make_progress_bar(percent, PROGRESS_BAR_WIDTH)} {percent_text}",
            f"{format_mb_compact(downloaded)}/{format_mb_compact(total)} {format_speed(speed)}",
            f"ETA {format_seconds(eta)}",
        ]
    )


def download_large_file(
    url: str,
    download_dir: Path,
    remaining_queue: Iterable[str] | None = None,
    persist_queue: bool = True,
) -> tuple[str, Path] | None:
    remote_metadata = get_remote_file_metadata(url)
    total_size = remote_metadata.get("size_bytes")
    total_size = total_size if isinstance(total_size, int) else None
    remote_name = remote_metadata.get("filename")
    remote_name = str(remote_name) if remote_name else None
    filename = remote_name or filename_from_response_or_url(url)
    target = download_dir / filename
    partial = download_dir / f"{filename}.part"
    download_dir.mkdir(parents=True, exist_ok=True)
    existing = partial.stat().st_size if partial.exists() else 0
    try:
        ensure_enough_space(download_dir, total_size, existing)
    except OSError as exc:
        if not is_disk_full_error(exc):
            raise
        download_dir, partial, target, existing = move_partial_to_new_download_dir(
            filename,
            partial,
            download_dir,
            total_size,
        )
        if persist_queue:
            write_large_file_queue(download_dir, url, remaining_queue or [])

    print()
    print(t("file_downloading", name=filename))
    if existing:
        print(t("file_resume", size=format_mb(existing)))

    started_at = time.perf_counter()
    downloaded = existing
    for attempt in range(1, LARGE_FILE_MAX_RETRIES + 1):
        headers = {"User-Agent": "VideoDownloader"}
        if downloaded:
            headers["Range"] = f"bytes={downloaded}-"
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                if downloaded and getattr(response, "status", None) != 206:
                    print()
                    print(t("file_no_range"))
                    downloaded = 0
                    partial.unlink(missing_ok=True)

                mode = "ab" if downloaded else "wb"
                with partial.open(mode) as output:
                    while True:
                        chunk = response.read(LARGE_FILE_CHUNK_SIZE)
                        if not chunk:
                            break
                        output.write(chunk)
                        downloaded += len(chunk)
                        render_file_progress(filename, downloaded, total_size, started_at)

            print()
            if total_size is not None and downloaded < total_size:
                raise URLError(f"Incomplete download: {downloaded}/{total_size}")
            partial.replace(target)
            register_downloaded_file_validation(target, remote_metadata)
            print(t("file_done", name=filename))
            return filename, download_dir
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            if isinstance(exc, OSError) and is_disk_full_error(exc):
                try:
                    download_dir, partial, target, downloaded = move_partial_to_new_download_dir(
                        filename,
                        partial,
                        download_dir,
                        total_size,
                    )
                    if persist_queue:
                        write_large_file_queue(download_dir, url, remaining_queue or [])
                    started_at = time.perf_counter()
                    continue
                except OSError as move_exc:
                    print_error_details(move_exc)
                    log_path = write_error_log(move_exc, f"Moving partial large file after disk-full error. URL: {url}")
                    print(t("details_saved", path=log_path))
                    return None
            if attempt >= LARGE_FILE_MAX_RETRIES:
                print()
                print_error_details(exc)
                log_path = write_error_log(exc, f"Large file download. URL: {url}")
                print(t("details_saved", path=log_path))
                return None
            print()
            print(t("file_retry", attempt=attempt + 1, total=LARGE_FILE_MAX_RETRIES))
            wait_for_internet()
            time.sleep(min(10, attempt * 2))
            downloaded = partial.stat().st_size if partial.exists() else 0
    return None


def download_cloud_file_with_ytdlp(url: str, download_dir: Path) -> tuple[str, Path] | None:
    if yt_dlp is None:
        print(t("cloud_missing"))
        log_path = write_error_log("Missing yt-dlp", f"Cloud file download. URL: {url}")
        print(t("details_saved", path=log_path))
        return None

    download_dir.mkdir(parents=True, exist_ok=True)
    print()
    print(t("cloud_downloading", site=detect_site(url)))

    options = {
        "outtmpl": str(download_dir / "%(title|download)s [%(id)s].%(ext)s"),
        "continuedl": True,
        "retries": LARGE_FILE_MAX_RETRIES,
        "fragment_retries": LARGE_FILE_MAX_RETRIES,
        "socket_timeout": 30,
        "progress_hooks": [progress_hook],
    }
    if not DEBUG:
        options.update(
            {
                "logger": QuietYtdlpLogger(),
                "no_warnings": True,
                "quiet": True,
            }
        )

    try:
        before_files = {path.name for path in download_dir.iterdir() if path.is_file()}
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        after_files = [path for path in download_dir.iterdir() if path.is_file() and path.name not in before_files]
        completed = [path for path in after_files if not path.name.endswith(".part")]
        if completed:
            return completed[0].name, download_dir
        return detect_site(url), download_dir
    except Exception as exc:
        print_error_details(exc)
        log_path = write_error_log(exc, f"Cloud file download through yt-dlp. URL: {url}")
        print(t("details_saved", path=log_path))
        return None


def download_large_files(urls: Iterable[str], download_dir: Path, persist_queue: bool = True) -> list[str]:
    saved_items: list[str] = []
    pending_urls = list(urls)
    failed = False
    if persist_queue and pending_urls:
        queue_path = write_large_file_queue(download_dir, "", pending_urls)
        print(t("queue_saved", path=queue_path))

    while pending_urls:
        url = pending_urls.pop(0)
        if persist_queue:
            write_large_file_queue(download_dir, url, pending_urls)
        if is_cloud_file_url(url):
            result = download_cloud_file_with_ytdlp(url, download_dir)
        else:
            result = download_large_file(url, download_dir, pending_urls, persist_queue)
        if result:
            saved, download_dir = result
            saved_items.append(saved)
            add_downloaded_files(1, "other")
            if persist_queue:
                write_large_file_queue(download_dir, "", pending_urls)
            continue
        if persist_queue:
            write_large_file_queue(download_dir, url, pending_urls)
        failed = True
        break
    if persist_queue and not pending_urls and not failed:
        clear_large_file_queue()
    return saved_items


def run_large_file_flow() -> None:
    download_dir = ask_download_dir()
    while True:
        raw_value = input(t("file_prompt")).strip().strip('"')
        if raw_value.lower() in {"q", "quit", "koniec"}:
            print(t("back_to_menu"))
            return
        if handle_easter_egg(raw_value):
            continue
        try:
            urls = parse_large_file_input(raw_value)
        except Exception as exc:
            print(t("auto_input_error", error=exc))
            print(t("auto_input_fix"))
            continue
        urls = expand_file_download_sources(urls)
        if not urls:
            continue
        print(t("detected_links", count=len(urls)))
        saved_items = download_large_files(urls, download_dir, persist_queue=True)
        if saved_items:
            add_history_entries(urls, "file", saved_items)
            print_saved_summary(download_dir, saved_items)


def resume_large_file_queue() -> None:
    download_dir, current, queue = read_large_file_queue()
    urls = ([current] if current else []) + queue
    if not urls:
        print(t("queue_empty"))
        return
    print(t("resume_start"))
    saved_items = download_large_files(urls, download_dir, persist_queue=True)
    if saved_items:
        add_history_entries(urls, "file", saved_items)
        print_saved_summary(download_dir, saved_items)


def get_clipboard_text() -> str:
    if tk is not None:
        root = None
        try:
            root = tk.Tk()
            root.withdraw()
            value = root.clipboard_get()
            return str(value or "")
        except Exception:
            pass
        finally:
            if root is not None:
                try:
                    root.destroy()
                except Exception:
                    pass

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
            capture_output=True,
            timeout=3,
            **SUBPROCESS_TEXT_OPTIONS,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        return ""
    return ""


def is_recognized_clipboard_url(url: str) -> bool:
    if validate_url(url) is not None:
        return False
    parsed = urlparse(normalize_user_url(url))
    host = parsed.netloc.lower().removeprefix("www.")
    for domain in SUPPORTED_SITE_HINTS:
        if host == domain or host.endswith(f".{domain}"):
            return True
    return False


def extract_clipboard_url(text: str) -> str | None:
    for token in re.findall(r"https?://[^\s<>()\[\]{}'\"|]+|www\.[^\s<>()\[\]{}'\"|]+", text or ""):
        clean = normalize_clipboard_download_url(token.strip().strip(",;"))
        if clean and is_recognized_clipboard_url(clean):
            return clean
    for token in re.split(r"[\s<>()\[\]{}'\"|]+", text or ""):
        clean = normalize_clipboard_download_url(token.strip().strip(",;"))
        if clean and is_recognized_clipboard_url(clean):
            return clean
    return None


def is_naughty_url(url: str) -> bool:
    parsed = urlparse(normalize_user_url(url))
    host = parsed.netloc.lower().removeprefix("www.")
    return any(host == domain or host.endswith(f".{domain}") for domain in NAUGHTY_SITE_HINTS)


def get_clipboard_media_type(url: str) -> str:
    return "mp4" if is_naughty_url(url) else DEFAULT_MEDIA_TYPE


def clear_clipboard_queue() -> None:
    db_delete_key("clipboard_queue")
    try:
        CLIPBOARD_QUEUE_FILE.unlink(missing_ok=True)
    except OSError:
        return


def read_clipboard_queue() -> list[str]:
    data = db_get_json("clipboard_queue")
    if data:
        raw_urls = data.get("urls", [])
        if isinstance(raw_urls, list):
            return [
                normalize_clipboard_download_url(str(url))
                for url in raw_urls
                if normalize_clipboard_download_url(str(url))
                and is_recognized_clipboard_url(normalize_clipboard_download_url(str(url)))
            ]

    try:
        if not CLIPBOARD_QUEUE_FILE.exists():
            return []
        urls: list[str] = []
        for line in CLIPBOARD_QUEUE_FILE.read_text(encoding="utf-8").splitlines():
            url = normalize_clipboard_download_url(line.strip())
            if url and is_recognized_clipboard_url(url) and url not in urls:
                urls.append(url)
        if urls:
            db_set_json("clipboard_queue", {"urls": urls})
        return urls
    except OSError:
        return []


def add_clipboard_queue_url(url: str) -> int:
    global CLIPBOARD_STATUS_LAST_URL, CLIPBOARD_STATUS_QUEUE_COUNT
    normalized = normalize_clipboard_download_url(url)
    urls = read_clipboard_queue()
    if normalized not in urls:
        urls.append(normalized)
    CLIPBOARD_STATUS_LAST_URL = normalized
    CLIPBOARD_STATUS_QUEUE_COUNT = len(urls)
    db_set_json("clipboard_queue", {"urls": urls})
    try:
        CLIPBOARD_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CLIPBOARD_QUEUE_FILE.write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")
    except OSError:
        return len(urls)
    return len(urls)


def confirm_clipboard_popup(url: str, media_type: str) -> bool | None:
    if tk is None:
        return None

    result: dict[str, bool | None] = {"value": None}
    root = None
    try:
        root = tk.Tk()
        root.title(t("clipboard_popup_title"))
        root.resizable(False, False)
        root.attributes("-topmost", True)

        frame = tk.Frame(root, padx=18, pady=14)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text=t("clipboard_popup_body", url=url, media=media_type.upper()),
            justify="left",
            wraplength=520,
        ).pack(anchor="w")
        tk.Label(
            frame,
            text=t("clipboard_popup_timeout", seconds=CLIPBOARD_POPUP_TIMEOUT_SECONDS),
            justify="left",
            wraplength=520,
        ).pack(anchor="w", pady=(8, 0))

        buttons = tk.Frame(frame)
        buttons.pack(anchor="e", pady=(14, 0))

        def finish(value: bool | None) -> None:
            result["value"] = value
            root.destroy()

        tk.Button(buttons, text=t("yes"), width=12, command=lambda: finish(True)).pack(side="left", padx=(0, 8))
        tk.Button(buttons, text=t("no"), width=12, command=lambda: finish(False)).pack(side="left", padx=(0, 8))
        tk.Button(buttons, text=t("decide_later"), width=18, command=lambda: finish(None)).pack(side="left")
        root.protocol("WM_DELETE_WINDOW", lambda: finish(None))
        root.after(CLIPBOARD_POPUP_TIMEOUT_SECONDS * 1000, lambda: finish(None))
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = max(0, (root.winfo_screenwidth() - width) // 2)
        y = max(0, (root.winfo_screenheight() - height) // 2)
        root.geometry(f"+{x}+{y}")
        root.mainloop()
        return result["value"]
    except Exception:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass
        return None


def confirm_clipboard_download(url: str, media_type: str) -> bool | None:
    if CLIPBOARD_POPUP:
        return confirm_clipboard_popup(url, media_type)

    answer = input(t("clipboard_console_prompt", url=url, media=media_type.upper())).strip().lower()
    if not answer:
        return None
    if answer in {"y", "yes", "t", "tak"}:
        return True
    return False


def download_clipboard_url(url: str, download_dir: Path) -> list[str]:
    media_type = get_clipboard_media_type(url)
    normalized = normalize_user_url(url)
    source_type = "auto"

    if is_spotify_url(normalized):
        saved_items = download_spotify_with_spotdl([normalized], download_dir)
        if saved_items:
            add_history_entries([normalized], "spotify", saved_items)
            print_saved_summary(download_dir / "Spotify", saved_items)
        return saved_items

    if is_youtube_channel_url(normalized):
        source_type = "channel"
        print(t("detected_channel"))
        if not preflight_channel_download(normalized, media_type):
            print(t("channel_cancelled"))
            return []
    elif is_youtube_playlist_url(normalized):
        source_type = "playlist"
        print(t("detected_playlist"))
        if not preflight_playlist_download(normalized, media_type):
            print(t("playlist_cancelled"))
            return []

    saved_items = download([normalized], media_type, source_type, download_dir)
    if saved_items:
        add_history_entries([normalized], media_type, saved_items)
        print_saved_summary(download_dir, saved_items)
    return saved_items


def download_clipboard_queue(download_dir: Path) -> None:
    urls = read_clipboard_queue()
    if not urls:
        print(t("clipboard_queue_empty"))
        return
    total_saved = 0
    for url in urls:
        saved_items = download_clipboard_url(url, download_dir)
        total_saved += len(saved_items)
    clear_clipboard_queue()
    print(t("clipboard_queue_done", count=total_saved))


def prompt_clipboard_queue(download_dir: Path) -> None:
    urls = read_clipboard_queue()
    if not urls:
        return
    print()
    print(t("clipboard_queue_pending", count=len(urls), path=CLIPBOARD_QUEUE_FILE))
    choice = ask_choice(
        t("clipboard_queue_action"),
        {
            "1": t("clipboard_queue_download_all"),
            "2": t("clipboard_queue_delete"),
            "3": t("clipboard_queue_later"),
        },
    )
    if choice == "1":
        download_clipboard_queue(download_dir)
    elif choice == "2":
        clear_clipboard_queue()
        print(t("clipboard_queue_deleted"))


def handle_clipboard_url(url: str, background: bool = False) -> None:
    global CLIPBOARD_STATUS_LAST_URL, CLIPBOARD_STATUS_QUEUE_COUNT
    url = normalize_clipboard_download_url(url)
    CLIPBOARD_STATUS_LAST_URL = url
    CLIPBOARD_STATUS_QUEUE_COUNT = len(read_clipboard_queue())
    media_type = get_clipboard_media_type(url)
    download_dir = DEFAULT_DOWNLOAD_DIR
    download_dir.mkdir(parents=True, exist_ok=True)

    if background and not CLIPBOARD_POPUP:
        count = add_clipboard_queue_url(url)
        CLIPBOARD_STATUS_QUEUE_COUNT = count
        return

    if background and not CLIPBOARD_PROMPT_LOCK.acquire(blocking=False):
        CLIPBOARD_STATUS_QUEUE_COUNT = add_clipboard_queue_url(url)
        return

    try:
        if not background:
            print(t("clipboard_detected", url=url))
        decision = confirm_clipboard_download(url, media_type)
        if decision is True:
            with CLIPBOARD_DOWNLOAD_LOCK:
                download_clipboard_url(url, download_dir)
            clear_clipboard_queue()
            CLIPBOARD_STATUS_QUEUE_COUNT = 0
        elif decision is None:
            count = add_clipboard_queue_url(url)
            CLIPBOARD_STATUS_QUEUE_COUNT = count
            if not background:
                print(t("clipboard_queued", count=count, path=CLIPBOARD_QUEUE_FILE))
            if not background:
                prompt_clipboard_queue(download_dir)
        else:
            if not background:
                print(t("clipboard_ignored"))
    finally:
        if background:
            try:
                CLIPBOARD_PROMPT_LOCK.release()
            except RuntimeError:
                pass


def clipboard_watcher_loop() -> None:
    global CLIPBOARD_WATCHER_LAST_URL

    CLIPBOARD_WATCHER_LAST_URL = extract_clipboard_url(get_clipboard_text()) or ""
    while not CLIPBOARD_WATCHER_STOP.is_set():
        text = get_clipboard_text()
        url = extract_clipboard_url(text)
        if url and url != CLIPBOARD_WATCHER_LAST_URL:
            CLIPBOARD_WATCHER_LAST_URL = url
            handle_clipboard_url(url, background=True)
        CLIPBOARD_WATCHER_STOP.wait(1)


def start_background_clipboard_watcher() -> None:
    global CLIPBOARD_WATCHER_THREAD
    if CLIPBOARD_WATCHER_THREAD is not None and CLIPBOARD_WATCHER_THREAD.is_alive():
        return
    CLIPBOARD_WATCHER_STOP.clear()
    CLIPBOARD_WATCHER_THREAD = threading.Thread(
        target=clipboard_watcher_loop,
        name="clipboard-watcher",
        daemon=True,
    )
    CLIPBOARD_WATCHER_THREAD.start()


def stop_background_clipboard_watcher() -> None:
    CLIPBOARD_WATCHER_STOP.set()
    thread = CLIPBOARD_WATCHER_THREAD
    if thread is not None and thread.is_alive():
        thread.join(timeout=2)


def run_clipboard_watcher() -> None:
    clear_console()
    print_app_header()
    print()
    print(t("clipboard_watcher_title"))
    print(t("clipboard_watcher_hint", media=DEFAULT_MEDIA_TYPE.upper(), folder=DEFAULT_DOWNLOAD_DIR))
    print(t("clipboard_watcher_stop"))
    print(t("clipboard_queue_autoclear"))

    last_text = get_clipboard_text()
    last_url = extract_clipboard_url(last_text) or ""
    download_dir = DEFAULT_DOWNLOAD_DIR
    download_dir.mkdir(parents=True, exist_ok=True)

    while True:
        if msvcrt is not None and msvcrt.kbhit():
            key = msvcrt.getwch().lower()
            if key == "q":
                print(t("clipboard_watcher_stopped"))
                return

        text = get_clipboard_text()
        url = extract_clipboard_url(text)
        if url and url != last_url:
            last_url = url
            handle_clipboard_url(url, background=False)
            print()
            print(t("clipboard_watcher_resume"))

        time.sleep(1)


def validate_url(value: str) -> str | None:
    clean = normalize_user_url(value)
    if not clean:
        return "link nie moze byc pusty."
    if any(char.isspace() for char in clean):
        return "link nie moze zawierac spacji."

    parsed = urlparse(clean)
    if parsed.scheme not in {"http", "https"}:
        return "link musi zaczynac sie od http:// albo https://."
    if not parsed.netloc or "." not in parsed.netloc:
        return "link musi zawierac poprawna domene."
    if parsed.netloc.startswith(".") or parsed.netloc.endswith("."):
        return "domena w linku wyglada niepoprawnie."

    return None


def detect_site(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    for domain, label in SUPPORTED_SITE_HINTS.items():
        if host == domain or host.endswith(f".{domain}"):
            return label
    return "automatycznie rozpoznana witryna"


def get_download_stat_category(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host == "open.spotify.com" or host.endswith(".spotify.com"):
        return "spotify"
    if host == "youtube.com" or host.endswith(".youtube.com") or host == "youtu.be":
        return "youtube"
    for domain, (site_key, _label) in NAUGHTY_SITE_HINTS.items():
        if host == domain or host.endswith(f".{domain}"):
            return site_key
    return "other"


def is_spotify_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host == "open.spotify.com" or host.endswith(".spotify.com")


def is_facebook_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host in {"facebook.com", "fb.com", "fb.watch"} or host.endswith(".facebook.com")


def is_facebook_reel_url(url: str) -> bool:
    parsed = urlparse(normalize_user_url(url))
    host = parsed.netloc.lower().removeprefix("www.")
    if host not in {"facebook.com", "m.facebook.com", "fb.com"} and not host.endswith(".facebook.com"):
        return False
    return parsed.path.strip("/").startswith("reel/")


def get_direct_media_extension(url: str) -> str | None:
    path = urlparse(url).path.lower()
    for extension in (".mp4", ".mov", ".m4v", ".webm", ".jpg", ".jpeg", ".png", ".gif", ".webp"):
        if path.endswith(extension):
            return extension
    return None


def is_direct_media_url(url: str) -> bool:
    return get_direct_media_extension(url) is not None


def safe_download_filename(url: str, fallback_prefix: str = "media") -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if not name:
        extension = get_direct_media_extension(url) or ".bin"
        name = f"{fallback_prefix}_{int(time.time())}{extension}"
    for char in WINDOWS_INVALID_PATH_CHARS:
        name = name.replace(char, "_")
    return name.strip(" .") or f"{fallback_prefix}_{int(time.time())}.bin"


def load_cookie_header_from_file(cookie_file: str, url: str) -> str:
    clean_file = cookie_file.strip().strip('"')
    if not clean_file:
        return ""

    path = Path(clean_file).expanduser()
    if not path.exists() or not path.is_file():
        return ""

    jar = MozillaCookieJar(str(path))
    jar.load(ignore_discard=True, ignore_expires=True)
    host = urlparse(url).netloc.lower()
    pairs: list[str] = []
    for cookie in jar:
        cookie_domain = cookie.domain.lower().lstrip(".")
        if host == cookie_domain or host.endswith(f".{cookie_domain}"):
            pairs.append(f"{cookie.name}={cookie.value}")
    return "; ".join(pairs)


def load_cookie_header_from_browser(browser: str, url: str) -> str:
    if browser_cookie3 is None or not browser:
        return ""
    loader = getattr(browser_cookie3, browser.lower(), None)
    if loader is None:
        return ""
    try:
        jar = loader(domain_name=urlparse(url).netloc)
    except Exception:
        try:
            jar = browser_cookie3.load(domain_name=urlparse(url).netloc)
        except Exception:
            return ""
    host = urlparse(url).netloc.lower()
    pairs: list[str] = []
    for cookie in jar:
        cookie_domain = str(getattr(cookie, "domain", "")).lower().lstrip(".")
        if cookie_domain and (host == cookie_domain or host.endswith(f".{cookie_domain}")):
            pairs.append(f"{cookie.name}={cookie.value}")
    return "; ".join(pairs)


def detect_default_browser() -> str:
    if winreg is None:
        return ""
    keys = [
        r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
        r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice",
    ]
    mapping = {
        "googlechrome": "chrome",
        "chromehtml": "chrome",
        "chrome": "chrome",
        "chromium": "chrome",
        "microsoftedge": "edge",
        "microsoft-edge": "edge",
        "msedge": "edge",
        "microsoft-edge-url": "edge",
        "edge": "edge",
        "firefoxurl": "firefox",
        "firefoxhtml": "firefox",
        "firefox": "firefox",
        "bravehtml": "brave",
        "brave": "brave",
        "operastable": "opera",
        "operagx": "opera",
        "opera": "opera",
        "vivaldihtm": "vivaldi",
        "vivaldi": "vivaldi",
    }
    for key in keys:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
                prog_id = str(winreg.QueryValueEx(handle, "ProgId")[0]).lower()
        except OSError:
            continue
        for needle, browser in mapping.items():
            if needle in prog_id:
                return browser
    return ""


def browser_loader(browser: str):
    if browser_cookie3 is None:
        return None
    return getattr(browser_cookie3, browser.lower(), None)


def browser_label(browser: str) -> str:
    return COOKIE_BROWSER_NAMES.get(browser.lower(), browser)


def load_browser_cookie_jar(browser: str):
    loader = browser_loader(browser)
    if loader is None:
        return None
    return loader()


def ensure_python_import(package_name: str, import_name: str) -> bool:
    try:
        globals()[import_name] = importlib.import_module(import_name)
        return True
    except ImportError:
        pass

    try:
        LOCAL_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
        if str(LOCAL_PACKAGE_DIR) not in sys.path:
            sys.path.insert(0, str(LOCAL_PACKAGE_DIR))
        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--target",
            str(LOCAL_PACKAGE_DIR),
            "--no-input",
            "--disable-pip-version-check",
            package_name,
        ]
        result = subprocess.run(command, capture_output=True, timeout=180, **SUBPROCESS_TEXT_OPTIONS)
        if result.returncode != 0:
            command = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--user",
                "--no-input",
                "--disable-pip-version-check",
                package_name,
            ]
            result = subprocess.run(command, capture_output=True, timeout=180, **SUBPROCESS_TEXT_OPTIONS)
            if result.returncode != 0:
                return False
        importlib.invalidate_caches()
        globals()[import_name] = importlib.import_module(import_name)
        return True
    except Exception:
        return False


def export_cookie_jar_to_netscape(jar, output_file: Path) -> int:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "# Netscape HTTP Cookie File",
        "# Generated by Video Downloader. Keep this file private.",
        "",
    ]
    count = 0
    for cookie in jar:
        domain = str(getattr(cookie, "domain", "") or "")
        name = str(getattr(cookie, "name", "") or "")
        value = str(getattr(cookie, "value", "") or "")
        path = str(getattr(cookie, "path", "") or "/")
        if not domain or not name:
            continue
        include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
        secure = "TRUE" if bool(getattr(cookie, "secure", False)) else "FALSE"
        expires = getattr(cookie, "expires", None)
        expiry = str(int(expires)) if expires else "0"
        rows.append("\t".join([domain, include_subdomains, path, secure, expiry, name, value]))
        count += 1
    output_file.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return count


def import_cookies_from_default_browser() -> tuple[bool, str, str]:
    global FACEBOOK_COOKIES_FROM_BROWSER, FACEBOOK_COOKIES_FILE
    global browser_cookie3

    if browser_cookie3 is None and not ensure_python_import("browser-cookie3", "browser_cookie3"):
        return False, "", t("cookies_import_missing_dependency")

    default_browser = detect_default_browser()
    browsers: list[str] = []
    if default_browser:
        browsers.append(default_browser)
    for browser in COOKIE_BROWSER_FALLBACKS:
        if browser not in browsers:
            browsers.append(browser)

    errors: list[str] = []
    for browser in browsers:
        try:
            jar = load_browser_cookie_jar(browser)
            label = browser_label(browser)
            if jar is None:
                errors.append(f"{label}: unsupported")
                continue
            output_file = APP_CONFIG_DIR / "cookies.txt"
            count = export_cookie_jar_to_netscape(jar, output_file)
            if count <= 0:
                errors.append(f"{label}: no cookies found")
                continue
            FACEBOOK_COOKIES_FROM_BROWSER = browser
            FACEBOOK_COOKIES_FILE = str(output_file)
            save_config()
            return True, browser, t("cookies_import_success", browser=label, count=count, path=output_file)
        except Exception as exc:
            errors.append(f"{browser_label(browser)}: {exc}")

    details = "; ".join(errors) if errors else "unknown error"
    return False, default_browser or "", t("cookies_import_failed", details=details)


def run_cookie_import_cli() -> int:
    load_config()
    ok, _browser, message = import_cookies_from_default_browser()
    print(message)
    if ok:
        return 0
    print(t("cookies_import_hint"))
    return 1


def has_invalid_windows_path_chars(value: str) -> bool:
    path = Path(value)
    parts = path.parts

    for index, part in enumerate(parts):
        if index == 0 and part.endswith(":\\"):
            continue
        if index == 0 and len(part) == 2 and part[1] == ":":
            continue
        if any(char in WINDOWS_INVALID_PATH_CHARS for char in part):
            return True

    return False


def has_reserved_windows_path_name(value: str) -> bool:
    for part in Path(value).parts:
        clean = part.rstrip(" .").split(".")[0].upper()
        if clean in WINDOWS_RESERVED_NAMES:
            return True
    return False


def has_bad_windows_path_ending(value: str) -> bool:
    for part in Path(value).parts:
        if part not in {".", ".."} and part.endswith((" ", ".")):
            return True
    return False


def validate_download_dir(raw_value: str) -> tuple[Path | None, str | None]:
    value = raw_value.strip().strip('"')
    if not value:
        path = DEFAULT_DOWNLOAD_DIR
    else:
        if looks_like_url(value):
            return None, "To wyglada jak link, a tutaj trzeba podac folder zapisu."
        if has_invalid_windows_path_chars(value):
            return None, "Sciezka zawiera znaki niedozwolone w nazwie folderu Windows."
        if has_reserved_windows_path_name(value):
            return None, "Sciezka zawiera zarezerwowana nazwe Windows, np. CON, PRN albo AUX."
        if has_bad_windows_path_ending(value):
            return None, "Folder nie moze konczyc sie spacja ani kropka."
        path = Path(value).expanduser()

    if path.exists() and not path.is_dir():
        return None, "Podana sciezka istnieje, ale jest plikiem, a nie folderem."

    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".youtube_downloader_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
    except PermissionError:
        return None, "Brak uprawnien do zapisu w tym folderze."
    except OSError as exc:
        return None, f"Nie mozna uzyc tego folderu: {exc}"

    return path, None


def ask_download_dir() -> Path:
    default = DEFAULT_DOWNLOAD_DIR
    while True:
        print()
        print(t("download_dir", path=default))
        custom = input(
            t("download_dir_prompt")
        )
        path, error = validate_download_dir(custom)
        if path is not None:
            return path

        print(t("invalid_save_path", error=error))


def classify_error(error_text: str) -> dict:
    error_lower = error_text.lower()
    for definition in ERROR_DEFINITIONS:
        if any(keyword in error_lower for keyword in definition["keywords"]):
            return definition

    return {
        "name": "Nieznany blad",
        "reason": "Program nie rozpoznal dokladnego typu bledu.",
        "repair": (
            "Sprobuj ponownie. Jesli problem wraca, ustaw DEBUG = 1 w pliku "
            "youtube_downloader.py i uruchom program jeszcze raz."
        ),
    }


def sanitize_error_text(error: object) -> str:
    text = str(error)
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    text = re.sub(r"\s+See\s+https?://\S+.*", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\s+Also see\s+https?://\S+.*", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = text.replace("ERROR: ERROR:", "ERROR:")
    return text.strip()


def format_user_error(error: object) -> str:
    clean = sanitize_error_text(error)
    details = classify_error(clean)
    if details["name"] != "Nieznany blad":
        return details["name"]
    return clean


def suggest_repair(error_text: str) -> str:
    return classify_error(error_text)["repair"]


def print_error_details(error: object) -> None:
    error_text = sanitize_error_text(error)
    details = classify_error(error_text)
    print(t("error_type", value=details["name"]))
    print(t("reason", value=details["reason"]))
    print(t("how_to_fix", value=details["repair"]))


def write_error_log(error: object, context: str = "") -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    error_text = str(error)
    details = classify_error(error_text)
    stack = ""
    if isinstance(error, BaseException):
        stack = "".join(traceback.format_exception(type(error), error, error.__traceback__))

    with ERROR_LOG_FILE.open("a", encoding="utf-8") as file:
        file.write("=" * 80 + "\n")
        file.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if context:
            file.write(f"Kontekst: {context}\n")
        file.write(f"Rodzaj bledu: {details['name']}\n")
        file.write(f"Opis bledu: {error_text}\n")
        file.write(f"Powod: {details['reason']}\n")
        file.write(f"Sposob naprawy: {details['repair']}\n")
        file.write("\nNajczestsze bledy i naprawy:\n")
        for hint in COMMON_ERROR_HINTS:
            file.write(f"- {hint}\n")
        if stack:
            file.write("\nSzczegoly techniczne:\n")
            file.write(stack)
        file.write("\n")

    return ERROR_LOG_FILE


class QuietYtdlpLogger:
    def debug(self, message: str) -> None:
        if DEBUG:
            print(message)

    def info(self, message: str) -> None:
        if DEBUG:
            print(message)

    def warning(self, message: str) -> None:
        if DEBUG:
            print(f"WARNING: {message}")

    def error(self, message: str) -> None:
        print(f"ERROR: {message}")


def format_seconds(seconds: float | int | None) -> str:
    if seconds is None:
        return "--:--"

    total_seconds = max(0, int(seconds))
    minutes, secs = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def shorten_text(value: str, max_length: int) -> str:
    if max_length <= 0:
        return ""
    if len(value) <= max_length:
        return value
    if max_length <= 3:
        return value[:max_length]
    return value[: max_length - 3] + "..."


def make_progress_bar(percent: float | None, width: int | None = None) -> str:
    bar_width = width or PROGRESS_BAR_WIDTH
    bar_width = max(MIN_PROGRESS_BAR_WIDTH, bar_width)
    try:
        "█░".encode(sys.stdout.encoding or "utf-8")
        filled_char = "█"
        empty_char = "░"
    except (LookupError, UnicodeEncodeError):
        filled_char = "#"
        empty_char = "-"

    if percent is None:
        return empty_char * bar_width

    done = int(bar_width * max(0, min(percent, 100)) / 100)
    return filled_char * done + empty_char * (bar_width - done)


def get_download_percent(progress: dict) -> float | None:
    total = progress.get("total_bytes") or progress.get("total_bytes_estimate")
    downloaded = progress.get("downloaded_bytes")
    if not total or downloaded is None:
        return None
    return downloaded / total * 100


def format_mb(bytes_value: float | int | None) -> str:
    if bytes_value is None:
        return "? MB"
    mb_value = bytes_value / (1024 * 1024)
    if mb_value >= 100 or mb_value.is_integer():
        return f"{mb_value:.0f} MB"
    return f"{mb_value:.1f} MB"


def format_mb_compact(bytes_value: float | int | None) -> str:
    return format_mb(bytes_value).replace(" ", "")


def format_gb_or_mb(bytes_value: float | int | None) -> str:
    if bytes_value is None:
        return "? MB"
    if bytes_value >= 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024 * 1024):.2f} GB"
    return format_mb(bytes_value)


def get_size_progress(progress: dict) -> str:
    downloaded = progress.get("downloaded_bytes")
    total = progress.get("total_bytes") or progress.get("total_bytes_estimate")
    return f"{format_mb_compact(downloaded)}/{format_mb_compact(total)}"


def format_speed(bytes_per_second: float | int | None) -> str:
    if bytes_per_second is None:
        return "? MB/s"
    return f"{bytes_per_second / (1024 * 1024):.1f} MB/s"


def get_eta_text(progress: dict) -> str:
    eta = progress.get("eta")
    if eta is not None:
        return format_seconds(eta)

    total = progress.get("total_bytes") or progress.get("total_bytes_estimate")
    downloaded = progress.get("downloaded_bytes")
    speed = progress.get("speed")
    if total and downloaded is not None and speed:
        return format_seconds((total - downloaded) / max(float(speed), 0.001))
    return "--:--"


def get_progress_title(progress: dict) -> str:
    info = progress.get("info_dict") or {}
    return info.get("title") or Path(progress.get("filename", "")).stem or t("download_label")


def get_collection_position(progress: dict) -> str:
    info = progress.get("info_dict") or {}
    index = (
        info.get("playlist_index")
        or progress.get("playlist_index")
        or info.get("__playlist_index")
        or progress.get("__playlist_index")
    )
    total = (
        info.get("playlist_count")
        or info.get("n_entries")
        or progress.get("playlist_count")
        or progress.get("n_entries")
    )
    if index is None and total is None:
        return ""
    try:
        index_text = str(int(index)) if index is not None else "?"
    except (TypeError, ValueError):
        index_text = str(index)
    try:
        total_text = str(int(total)) if total is not None else "?"
    except (TypeError, ValueError):
        total_text = str(total)
    return t("download_item_counter", current=index_text, total=total_text)


def is_collection_progress(progress: dict) -> bool:
    return bool(get_collection_position(progress))


def get_progress_title_line(progress: dict) -> str:
    title = get_progress_title(progress)
    position = get_collection_position(progress)
    if position:
        return f"{position} | {title}"
    return title


def reset_download_cancel() -> None:
    global DOWNLOAD_CANCEL_REQUESTED
    DOWNLOAD_CANCEL_REQUESTED = False


def request_download_cancel() -> None:
    global DOWNLOAD_CANCEL_REQUESTED
    DOWNLOAD_CANCEL_REQUESTED = True


def get_download_cancel_message() -> str:
    return t("download_stopped")


def check_download_cancel_key() -> None:
    if DOWNLOAD_CANCEL_REQUESTED:
        raise DownloadCancelled(get_download_cancel_message())

    if os.name != "nt" or msvcrt is None:
        return

    while msvcrt.kbhit():
        key = msvcrt.getwch()
        if key.lower() == "q":
            request_download_cancel()
            raise DownloadCancelled(get_download_cancel_message())


def get_completed_download_key(progress: dict) -> str:
    info = progress.get("info_dict") or {}
    return str(info.get("id") or progress.get("filename") or time.monotonic())


def record_completed_download(progress: dict) -> None:
    key = get_completed_download_key(progress)
    if key in COMPLETED_DOWNLOAD_KEYS:
        return

    COMPLETED_DOWNLOAD_KEYS.add(key)
    COMPLETED_DOWNLOAD_TITLES.append(get_progress_title(progress))
    filename = progress.get("filename")
    if filename:
        COMPLETED_DOWNLOAD_FILES.append(str(filename))


def print_status_block(lines: list[str], full_screen: bool = False) -> None:
    global STATUS_BLOCK_LINES

    with STATUS_LOCK:
        if full_screen:
            clear_console()
            print(t("download_stop_hint"))
            print()
            STATUS_BLOCK_LINES = 0
        if STATUS_BLOCK_LINES:
            print(f"\033[{STATUS_BLOCK_LINES}F", end="")

        rendered_lines = [shorten_text(line, STATUS_LINE_WIDTH) for line in lines]
        for line in rendered_lines:
            print(STATUS_CLEAR_SEQUENCE + line)

        if len(rendered_lines) < STATUS_BLOCK_LINES:
            for _ in range(STATUS_BLOCK_LINES - len(rendered_lines)):
                print(STATUS_CLEAR_SEQUENCE)

        STATUS_BLOCK_LINES = len(rendered_lines)
        print("", end="", flush=True)


def print_status_line(text: str) -> None:
    print_status_block([text])


def clear_status_line() -> None:
    global STATUS_BLOCK_LINES

    with STATUS_LOCK:
        if STATUS_BLOCK_LINES:
            print(f"\033[{STATUS_BLOCK_LINES}F", end="")
            for _ in range(STATUS_BLOCK_LINES):
                print(STATUS_CLEAR_SEQUENCE)
            STATUS_BLOCK_LINES = 0
        else:
            print(STATUS_CLEAR_SEQUENCE, end="")
        print("", end="", flush=True)


def print_progress_line(progress: dict) -> None:
    percent = get_download_percent(progress)
    speed = format_speed(progress.get("speed"))
    size_progress = get_size_progress(progress)
    percent_text = f"{percent:.0f}%" if percent is not None else "--%"
    bar = make_progress_bar(percent, PROGRESS_BAR_WIDTH)
    title = shorten_text(get_progress_title_line(progress), STATUS_LINE_WIDTH)
    print_status_block(
        [
            title,
            f"{bar} {percent_text}",
            f"{size_progress} {speed}",
            f"ETA {get_eta_text(progress)}",
        ],
        full_screen=is_collection_progress(progress),
    )


def print_conversion_line(progress: dict) -> None:
    print_status_block(
        [
            shorten_text(get_progress_title_line(progress), STATUS_LINE_WIDTH),
            f"{make_progress_bar(100, PROGRESS_BAR_WIDTH)} 100%",
            t("conversion"),
            "ETA 00:00",
        ],
        full_screen=is_collection_progress(progress),
    )


def print_conversion_status(title: str, started_at: float, frame: str, full_screen: bool = False) -> None:
    elapsed = int(time.monotonic() - started_at)
    print_status_block(
        [
            shorten_text(title, STATUS_LINE_WIDTH),
            f"{make_progress_bar(100, PROGRESS_BAR_WIDTH)} 100%",
            f"{frame} {t('conversion')} {format_seconds(elapsed)}",
            "ETA 00:00",
        ],
        full_screen=full_screen,
    )


def conversion_status_worker() -> None:
    started_at = time.monotonic()
    frames = "|/-\\"
    index = 0
    while not CONVERSION_STATUS_STOP.is_set():
        print_conversion_status(
            CONVERSION_STATUS_TITLE,
            started_at,
            frames[index % len(frames)],
            full_screen=CONVERSION_STATUS_FULLSCREEN,
        )
        index += 1
        CONVERSION_STATUS_STOP.wait(0.5)


def start_conversion_status(title: str, full_screen: bool = False) -> None:
    global CONVERSION_STATUS_THREAD, CONVERSION_STATUS_TITLE, CONVERSION_STATUS_FULLSCREEN
    if DEBUG:
        return
    if CONVERSION_STATUS_THREAD is not None and CONVERSION_STATUS_THREAD.is_alive():
        CONVERSION_STATUS_FULLSCREEN = CONVERSION_STATUS_FULLSCREEN or full_screen
        return

    CONVERSION_STATUS_TITLE = title or "Konwertowanie"
    CONVERSION_STATUS_FULLSCREEN = full_screen
    CONVERSION_STATUS_STOP.clear()
    CONVERSION_STATUS_THREAD = threading.Thread(target=conversion_status_worker, daemon=True)
    CONVERSION_STATUS_THREAD.start()


def stop_conversion_status() -> None:
    global CONVERSION_STATUS_THREAD, CONVERSION_STATUS_FULLSCREEN
    if DEBUG:
        return
    CONVERSION_STATUS_STOP.set()
    if CONVERSION_STATUS_THREAD is not None:
        CONVERSION_STATUS_THREAD.join(timeout=1)
        CONVERSION_STATUS_THREAD = None
    CONVERSION_STATUS_FULLSCREEN = False


def progress_hook(progress: dict) -> None:
    check_download_cancel_key()
    status = progress.get("status")
    if status == "finished":
        record_completed_download(progress)

    if DEBUG:
        return

    if status == "downloading":
        print_progress_line(progress)
    elif status == "finished":
        start_conversion_status(get_progress_title_line(progress), is_collection_progress(progress))


def postprocessor_hook(progress: dict) -> None:
    check_download_cancel_key()
    if progress.get("status") == "finished":
        record_completed_download(progress)

    if DEBUG:
        return

    status = progress.get("status")
    if status in {"started", "processing"}:
        start_conversion_status(get_progress_title_line(progress), is_collection_progress(progress))
    elif status == "finished":
        stop_conversion_status()
        clear_status_line()
        print_status_block(
            [
                shorten_text(get_progress_title_line(progress), STATUS_LINE_WIDTH),
                f"{make_progress_bar(100, PROGRESS_BAR_WIDTH)} 100%",
                t("saved_status"),
                "ETA 00:00",
            ],
            full_screen=is_collection_progress(progress),
        )


def get_cookie_file_candidates() -> list[Path]:
    candidates = [
        PROGRAM_DIR / "cookies.txt",
        CONFIG_DIR / "cookies.txt",
        APP_CONFIG_DIR / "cookies.txt",
        APP_DATA_DIR / "cookies.txt",
    ]
    if FACEBOOK_COOKIES_FILE.strip():
        candidates.insert(0, Path(FACEBOOK_COOKIES_FILE.strip().strip('"')).expanduser())
    return candidates


def get_existing_cookie_file() -> Path | None:
    for path in get_cookie_file_candidates():
        try:
            if path.exists() and path.is_file():
                return path
        except OSError:
            continue
    return None


def get_cookie_retry_strategies() -> list[dict]:
    strategies: list[dict] = []
    browsers: list[str] = ["chrome"]
    configured_browser = FACEBOOK_COOKIES_FROM_BROWSER.strip().lower()
    if configured_browser and configured_browser not in browsers:
        browsers.append(configured_browser)
    for browser in COOKIE_BROWSER_FALLBACKS:
        if browser not in browsers:
            browsers.append(browser)

    for browser in browsers:
        strategies.append(
            {
                "name": f"ponowienie z yt-dlp --cookies-from-browser {browser}",
                "options": {"cookiesfrombrowser": (browser, None, None, None)},
            }
        )

    cookie_file = get_existing_cookie_file()
    if cookie_file is not None:
        strategies.append(
            {
                "name": f"ponowienie z plikiem cookies.txt: {cookie_file}",
                "options": {"cookiefile": str(cookie_file)},
            }
        )

    return strategies


def get_workaround_strategies(media_type: str) -> list[dict]:
    fallback_format = "bestaudio/best" if media_type == "mp3" else "best/bv*+ba/b"
    strategies = [
        {
            "name": "standardowa konfiguracja",
            "options": {},
        },
        *get_cookie_retry_strategies(),
        {
            "name": "ponowienie z dluzszym timeoutem i mniejsza liczba polaczen",
            "options": {
                "retries": 10,
                "fragment_retries": 10,
                "extractor_retries": 5,
                "file_access_retries": 5,
                "socket_timeout": 30,
                "concurrent_fragment_downloads": 1,
            },
        },
        {
            "name": "awaryjny prostszy wybor formatu i alternatywny klient YouTube",
            "options": {
                "format": fallback_format,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"],
                    }
                },
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9,pl;q=0.8",
                    "Referer": "https://www.youtube.com/",
                },
            },
        },
    ]
    return strategies


def format_size_from_bitrate(format_data: dict, duration: float | int | None) -> int | None:
    bitrate = format_data.get("tbr") or format_data.get("abr") or format_data.get("vbr")
    if not bitrate or not duration:
        return None
    return int(float(bitrate) * 1000 * float(duration) / 8)


def estimate_format_size(format_data: dict, duration: float | int | None) -> int | None:
    size = format_data.get("filesize") or format_data.get("filesize_approx")
    if size:
        return int(size)
    return format_size_from_bitrate(format_data, duration)


def best_audio_format(formats: list[dict]) -> dict | None:
    audio_formats = [
        item
        for item in formats
        if item.get("acodec") != "none" and item.get("vcodec") == "none"
    ]
    return max(audio_formats, key=lambda item: item.get("abr") or item.get("tbr") or 0, default=None)


def best_video_format(formats: list[dict]) -> dict | None:
    video_formats = [
        item
        for item in formats
        if item.get("vcodec") != "none" and item.get("acodec") == "none"
    ]
    return max(
        video_formats,
        key=lambda item: (
            item.get("height") or 0,
            item.get("fps") or 0,
            item.get("vbr") or item.get("tbr") or 0,
        ),
        default=None,
    )


def best_combined_format(formats: list[dict]) -> dict | None:
    combined_formats = [
        item
        for item in formats
        if item.get("vcodec") != "none" and item.get("acodec") != "none"
    ]
    return max(
        combined_formats,
        key=lambda item: (
            item.get("height") or 0,
            item.get("fps") or 0,
            item.get("tbr") or 0,
        ),
        default=None,
    )


def estimate_entry_size(entry: dict, media_type: str) -> int | None:
    duration = entry.get("duration")
    formats = entry.get("formats") or []
    if not formats:
        return None

    if media_type == "mp3":
        audio = best_audio_format(formats) or best_combined_format(formats)
        return estimate_format_size(audio, duration) if audio else None

    video = best_video_format(formats)
    audio = best_audio_format(formats)
    if video and audio:
        video_size = estimate_format_size(video, duration)
        audio_size = estimate_format_size(audio, duration)
        if video_size is not None and audio_size is not None:
            return video_size + audio_size

    combined = best_combined_format(formats)
    return estimate_format_size(combined, duration) if combined else None


def get_metadata_options() -> dict:
    options = {
        "ignoreerrors": True,
        "skip_download": True,
        "extract_flat": False,
    }
    if not DEBUG:
        options.update(
            {
                "logger": QuietYtdlpLogger(),
                "no_warnings": True,
                "quiet": True,
            }
        )
    return options


def preflight_youtube_collection(url: str, media_type: str, collection_type: str) -> bool:
    if yt_dlp is None:
        message = "Brakuje biblioteki yt-dlp."
        print(message)
        log_path = write_error_log(message, f"Podglad {collection_type} przed pobraniem")
        print(t("details_saved", path=log_path))
        return False

    print()
    if collection_type == "playlist":
        print(t("checking_playlist"))
    else:
        print(t("checking_channel"))

    try:
        with yt_dlp.YoutubeDL(get_metadata_options()) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        print(t("check_collection_failed", type=collection_type, error=exc))
        print_error_details(exc)
        log_path = write_error_log(exc, f"Podglad {collection_type} przed pobraniem")
        print(t("details_saved", path=log_path))
        return False

    entries = list((info or {}).get("entries") or [])
    entries = [entry for entry in entries if entry]
    total_count = len(entries)
    if total_count == 0:
        print(t("no_collection_items"))
        return False

    known_count = 0
    unknown_count = 0
    estimated_bytes = 0

    for entry in entries:
        size = estimate_entry_size(entry, media_type)
        if size is None:
            unknown_count += 1
        else:
            known_count += 1
            estimated_bytes += size

    collection_title = (info or {}).get("title") or ("Playlista YouTube" if collection_type == "playlist" else "Kanal YouTube")
    media_label = t("preflight_mp3") if media_type == "mp3" else t("preflight_mp4")

    print()
    print(t("preflight_summary"))
    if collection_type == "playlist":
        print(t("preflight_playlist", title=collection_title))
    else:
        print(t("preflight_channel", title=collection_title))
    print(t("preflight_to_download", count=total_count, media=media_label))
    if known_count:
        print(t("preflight_size", size=format_gb_or_mb(estimated_bytes)))
    else:
        print(t("preflight_size_unknown"))
    if unknown_count:
        print(t("preflight_unknown_warning", unknown=unknown_count, total=total_count))
    print(t("preflight_size_note"))
    print()

    return ask_yes_no(t("continue_download"))


def preflight_channel_download(channel_url: str, media_type: str) -> bool:
    return preflight_youtube_collection(channel_url, media_type, "channel")


def preflight_playlist_download(playlist_url: str, media_type: str) -> bool:
    return preflight_youtube_collection(playlist_url, media_type, "playlist")


def is_collection_download(url: str, source_type: str) -> bool:
    return source_type in {"playlist", "channel"} or is_youtube_playlist_url(url) or is_youtube_channel_url(url)


def count_download_entries_from_info(info: dict | None) -> int:
    if not info:
        return 0

    entries = info.get("entries")
    if entries is None:
        return 1

    return sum(1 for entry in entries if entry)


def detect_expected_download_count(url: str, media_type: str, source_type: str, download_dir: Path) -> int:
    if yt_dlp is None:
        return 0

    effective_source_type = source_type
    if effective_source_type not in {"playlist", "channel"}:
        if is_youtube_channel_url(url):
            effective_source_type = "channel"
        elif is_youtube_playlist_url(url):
            effective_source_type = "playlist"

    if effective_source_type not in {"playlist", "channel"}:
        return 0

    try:
        options = build_download_options(
            media_type,
            effective_source_type,
            download_dir,
            {
                "extract_flat": "in_playlist",
                "quiet": True,
                "no_warnings": True,
                "logger": QuietYtdlpLogger(),
                "skip_download": True,
                "noplaylist": False,
                "simulate": True,
            },
            url,
        )
        options.pop("progress_hooks", None)
        options.pop("postprocessor_hooks", None)
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
        return count_download_entries_from_info(info)
    except Exception:
        return 0


def build_download_options(
    media_type: str,
    source_type: str,
    download_dir: Path,
    extra_options: dict | None = None,
    url: str | None = None,
) -> dict:
    try:
        download_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise PermissionError(
            f"Brak dostepu do folderu zapisu: {download_dir}. "
            "Sprawdz uprawnienia albo uruchom program z innego folderu."
        ) from exc

    output_template = str(
        download_dir / "%(playlist_title|Pobrane)s" / "%(title)s [%(id)s].%(ext)s"
    )
    if source_type == "link":
        output_template = str(download_dir / "%(title)s [%(id)s].%(ext)s")
    elif source_type == "channel":
        output_template = str(
            download_dir / "%(uploader|Kanal YouTube)s" / "%(title)s [%(id)s].%(ext)s"
        )
    elif source_type == "auto":
        output_template = str(
            download_dir / "%(extractor_key|Witryna)s" / "%(title)s [%(id)s].%(ext)s"
        )

    options = {
        "outtmpl": output_template,
        "ignoreerrors": False,
        "noplaylist": source_type == "link",
        "postprocessor_hooks": [postprocessor_hook],
        "progress_hooks": [progress_hook],
        "retries": 5,
        "fragment_retries": 5,
        "extractor_retries": 3,
        "file_access_retries": 3,
        "socket_timeout": 20,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,pl;q=0.8",
        },
    }

    if not DEBUG:
        options.update(
            {
                "logger": QuietYtdlpLogger(),
                "no_warnings": True,
                "quiet": True,
            }
        )

    if media_type == "mp3":
        options.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        )
    else:
        options.update(
            {
                "format": "bv*+ba/best",
                "merge_output_format": "mp4",
            }
        )

    apply_cookie_options(options, url)

    if extra_options:
        options.update(extra_options)

    return options


def apply_cookie_options(options: dict, url: str | None) -> None:
    if not url:
        return

    if is_facebook_url(url):
        cookie_file = FACEBOOK_COOKIES_FILE.strip().strip('"')
        if cookie_file:
            options["cookiefile"] = str(Path(cookie_file).expanduser())
            return

        browser = FACEBOOK_COOKIES_FROM_BROWSER.strip().lower()
        if browser:
            options["cookiesfrombrowser"] = (browser, None, None, None)
            cookie_header = load_cookie_header_from_browser(browser, url)
            if cookie_header:
                headers = dict(options.get("http_headers", {}))
                headers["Cookie"] = cookie_header
                options["http_headers"] = headers


def has_ffmpeg() -> bool:
    if (LOCAL_FFMPEG_BIN / "ffmpeg.exe").exists() and (LOCAL_FFMPEG_BIN / "ffprobe.exe").exists():
        os.environ["PATH"] = str(LOCAL_FFMPEG_BIN) + os.pathsep + os.environ.get("PATH", "")
    return which("ffmpeg") is not None and which("ffprobe") is not None


def show_ffmpeg_help() -> None:
    print()
    print("Brakuje FFmpeg albo FFprobe.")
    print("Bez tego program nie przekonwertuje audio do MP3 i moze nie scalic MP4.")
    print()
    print("Najprosciej zainstalowac FFmpeg poleceniem:")
    print("winget install Gyan.FFmpeg")
    print()
    print("Po instalacji zamknij to okno i uruchom program ponownie.")


def try_install_ffmpeg() -> bool:
    if which("winget") is None:
        print("Nie znaleziono winget, wiec nie moge automatycznie zainstalowac FFmpeg.")
        return False

    if not ask_yes_no("Brakuje FFmpeg. Czy sprobowac zainstalowac go automatycznie"):
        return False

    command = ["winget", "install", "-e", "--id", "Gyan.FFmpeg"]
    print("Instaluje FFmpeg...")
    if DEBUG:
        result = subprocess.run(command, **SUBPROCESS_TEXT_OPTIONS)
    else:
        result = subprocess.run(command, capture_output=True, **SUBPROCESS_TEXT_OPTIONS)

    if result.returncode == 0:
        print("FFmpeg zainstalowany. Jesli program dalej go nie widzi, zamknij okno i uruchom ponownie.")
        return True

    error_output = ""
    if not DEBUG:
        error_output = (result.stderr or result.stdout or "").strip()
    error = RuntimeError(error_output or f"winget zakonczyl prace kodem {result.returncode}")
    print("Nie udalo sie automatycznie zainstalowac FFmpeg.")
    print_error_details(error)
    log_path = write_error_log(error, "Automatyczna instalacja FFmpeg")
    print(f"Szczegoly zapisano w: {log_path}")
    return False


def has_gallery_dl() -> bool:
    return importlib.util.find_spec("gallery_dl") is not None


def has_spotdl() -> bool:
    return importlib.util.find_spec("spotdl") is not None


def show_gallery_dl_help() -> None:
    print()
    print("Brakuje gallery-dl.")
    print("To narzedzie jest potrzebne do pobierania zdjec z Instagram, TikTok i Facebook.")
    print()
    print("Zainstaluj je poleceniem:")
    print("python -m pip install --upgrade gallery-dl")


def show_spotdl_help() -> None:
    print()
    print(t("spotify_missing"))


def can_write_mp3_metadata() -> bool:
    return mutagen is not None


def download_photos(urls: Iterable[str], download_dir: Path) -> list[str]:
    saved_items: list[str] = []
    if not has_gallery_dl():
        message = "Brakuje biblioteki gallery-dl."
        show_gallery_dl_help()
        log_path = write_error_log(message, "Brak gallery-dl")
        print(f"Szczegoly zapisano w: {log_path}")
        return saved_items

    photos_dir = download_dir / "Zdjecia"
    photos_dir.mkdir(parents=True, exist_ok=True)

    for url in urls:
        clear_console()
        print(f"\nPobieranie zdjec ({detect_site(url)}): {url}")
        try:
            from gallery_dl import config, job

            config.set(("extractor",), "base-directory", str(photos_dir))
            gallery_job = job.DownloadJob(url)
            result = gallery_job.run()
            if result == 0 or result is True or result is None:
                print(t("status_success"))
                add_downloaded_files(1)
                saved_items.append(f"Zdjecia z: {url}")
                continue

            raise RuntimeError(f"gallery-dl zakonczyl prace wynikiem: {result}")
        except Exception as api_exc:
            if getattr(sys, "frozen", False):
                print(t("status_error"))
                print_error_details(api_exc)
                log_path = write_error_log(api_exc, f"Pobieranie zdjec. URL: {url}.")
                print(t("details_saved", path=log_path))
                continue

        command = [sys.executable, "-m", "gallery_dl", "--directory", str(photos_dir), url]
        if DEBUG:
            cli_result = subprocess.run(command, **SUBPROCESS_TEXT_OPTIONS)
        else:
            cli_result = subprocess.run(command, capture_output=True, **SUBPROCESS_TEXT_OPTIONS)

        if cli_result.returncode == 0:
            print(t("status_success"))
            add_downloaded_files(1)
            saved_items.append(f"Zdjecia z: {url}")
            continue

        error_output = ""
        if not DEBUG:
            error_output = (cli_result.stderr or cli_result.stdout or "").strip()
        error = RuntimeError(error_output or f"gallery-dl zakonczyl prace kodem {cli_result.returncode}")
        print(t("status_error"))
        print_error_details(error)
        log_path = write_error_log(error, f"Pobieranie zdjec. URL: {url}.")
        print(t("details_saved", path=log_path))
    return saved_items


def download_spotify_with_spotdl(urls: Iterable[str], download_dir: Path) -> list[str]:
    saved_items: list[str] = []
    spotify_dir = download_dir / "Spotify"
    spotify_dir.mkdir(parents=True, exist_ok=True)

    if not has_spotdl():
        show_spotdl_help()
        log_path = write_error_log("Missing spotDL package", "Spotify download requested.")
        print(t("details_saved", path=log_path))
        return saved_items

    env = os.environ.copy()
    if LOCAL_PACKAGE_DIR.exists():
        env["PYTHONPATH"] = str(LOCAL_PACKAGE_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    if LOCAL_FFMPEG_BIN.exists():
        env["PATH"] = str(LOCAL_FFMPEG_BIN) + os.pathsep + env.get("PATH", "")

    for url in urls:
        clear_console()
        print(t("spotify_downloading", url=url))

        if not is_spotify_url(url):
            print(t("invalid_url", error="Spotify URL required."))
            continue

        command = [
            sys.executable,
            "-m",
            "spotdl",
            "download",
            url,
            "--output",
            str(spotify_dir),
            "--format",
            "mp3",
        ]

        try:
            if DEBUG:
                result = subprocess.run(command, env=env, **SUBPROCESS_TEXT_OPTIONS)
            else:
                result = subprocess.run(command, capture_output=True, env=env, **SUBPROCESS_TEXT_OPTIONS)

            if result.returncode != 0:
                output = ""
                if not DEBUG:
                    output = (result.stderr or result.stdout or "").strip()
                raise RuntimeError(output or f"spotDL exited with code {result.returncode}")

            add_downloaded_files(1, "spotify")
            saved_items.append(f"Spotify: {url}")
            print(t("spotify_done"))
        except Exception as exc:
            print(t("status_error"))
            print_error_details(exc)
            log_path = write_error_log(exc, f"Spotify download through spotDL. URL: {url}.")
            print(t("details_saved", path=log_path))

    return saved_items


def download(
    urls: Iterable[str], media_type: str, source_type: str, download_dir: Path
) -> list[str]:
    saved_items: list[str] = []
    if yt_dlp is None:
        message = "Brakuje biblioteki yt-dlp."
        print(message)
        print("Zainstaluj ja poleceniem: python -m pip install --upgrade yt-dlp")
        log_path = write_error_log(message, "Brak zaleznosci Python")
        print(f"Szczegoly zapisano w: {log_path}")
        return saved_items

    if not has_ffmpeg():
        message = "Brakuje FFmpeg albo FFprobe."
        show_ffmpeg_help()
        try_install_ffmpeg()
        log_path = write_error_log(message, "Brak FFmpeg")
        print(f"Szczegoly zapisano w: {log_path}")
        return saved_items

    strategies = get_workaround_strategies(media_type)

    for url in urls:
        clear_console()
        print(f"\n{t('download_label')} ({detect_site(url)}): {url}")
        print(t("download_stop_hint"))
        last_error = None

        if is_spotify_url(url):
            print(t("spotify_not_supported"))
            continue

        for attempt, strategy in enumerate(strategies, start=1):
            if attempt > 1:
                print()
                print(
                    f"Proba obejscia problemu {attempt}/{len(strategies)}: {strategy['name']}..."
                )

            try:
                reset_download_cancel()
                COMPLETED_DOWNLOAD_KEYS.clear()
                COMPLETED_DOWNLOAD_TITLES.clear()
                COMPLETED_DOWNLOAD_FILES.clear()
                options = build_download_options(
                    media_type,
                    source_type,
                    download_dir,
                    strategy["options"],
                    url,
                )
                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.download([url])
                downloaded_titles = list(COMPLETED_DOWNLOAD_TITLES)
                if not downloaded_titles and not is_collection_download(url, source_type):
                    downloaded_titles = [detect_site(url)]
                if downloaded_titles:
                    add_downloaded_files(len(downloaded_titles), get_download_stat_category(url))
                    saved_items.extend(downloaded_titles)
                COMPLETED_DOWNLOAD_KEYS.clear()
                COMPLETED_DOWNLOAD_TITLES.clear()
                COMPLETED_DOWNLOAD_FILES.clear()
                if not DEBUG:
                    stop_conversion_status()
                    clear_status_line()
                    print(t("status_success"))
                last_error = None
                break
            except DownloadCancelled as exc:
                if not DEBUG:
                    stop_conversion_status()
                    clear_status_line()
                downloaded_titles = list(COMPLETED_DOWNLOAD_TITLES)
                if downloaded_titles:
                    add_downloaded_files(len(downloaded_titles), get_download_stat_category(url))
                    saved_items.extend(downloaded_titles)
                COMPLETED_DOWNLOAD_KEYS.clear()
                COMPLETED_DOWNLOAD_TITLES.clear()
                COMPLETED_DOWNLOAD_FILES.clear()
                print(f"\n{exc}")
                print(t("returning_to_menu"))
                return saved_items
            except Exception as exc:
                COMPLETED_DOWNLOAD_KEYS.clear()
                COMPLETED_DOWNLOAD_TITLES.clear()
                COMPLETED_DOWNLOAD_FILES.clear()
                if not DEBUG:
                    stop_conversion_status()
                    clear_status_line()
                last_error = exc
                if attempt < len(strategies):
                    print(f"\nNie udalo sie: {format_user_error(exc)}")
                    print_error_details(exc)
                    print("Aplikacja sprobuje kolejnego sposobu automatycznie.")
                else:
                    print(f"\nNie udalo sie po {len(strategies)} probach: {format_user_error(exc)}")
                    print_error_details(exc)

        if last_error is not None:
            context = (
                f"Nieudane pobieranie po {len(strategies)} probach. URL: {url}. "
                f"Typ: {media_type}. Zrodlo: {source_type}."
            )
            log_path = write_error_log(last_error, context)
            print(t("details_saved", path=log_path))
    return saved_items


def pause_before_exit() -> None:
    print()
    input(t("exit_prompt"))


def run_download_flow() -> None:
    media_choice = ask_download_type_choice()
    if media_choice == "0":
        return
    if media_choice == "1":
        media_type = "mp3"
    elif media_choice == "2":
        media_type = "mp4"
    elif media_choice == "3":
        media_type = "photos"
    elif media_choice == "4":
        media_type = "spotify"
    else:
        return

    if media_type == "photos":
        source_choice = ask_choice(
            t("photo_source"),
            {
                "0": t("back_to_menu").strip(),
                "1": t("single_photo_link"),
                "2": t("txt_file"),
            },
        )
        if source_choice == "0":
            return
        download_dir = ask_download_dir()

        if source_choice == "1":
            while True:
                url = ask_url_or_quit(t("photo_link_prompt"))
                if url is None:
                    print(t("back_to_menu"))
                    return
                if not looks_like_url(url):
                    print(t("bad_http_link"))
                    continue

                saved_items = download_photos([url], download_dir)
                if saved_items:
                    add_history_entries([url], "photos", saved_items)
                    print_saved_summary(download_dir / "Zdjecia", saved_items)
        else:
            txt_path = ask_non_empty(t("txt_path_prompt"))
            urls = read_urls_from_txt(txt_path)
            saved_items = download_photos(urls, download_dir)
            if saved_items:
                add_history_entries(urls, "photos", saved_items)
                print_saved_summary(download_dir / "Zdjecia", saved_items)
        return

    if media_type == "spotify":
        source_choice = ask_choice(
            t("spotify_source"),
            {
                "0": t("back_to_menu").strip(),
                "1": t("single_spotify_link"),
                "2": t("txt_file"),
            },
        )
        if source_choice == "0":
            return
        download_dir = ask_download_dir()

        if source_choice == "1":
            while True:
                url = ask_url_or_quit(t("spotify_link_prompt"))
                if url is None:
                    print(t("back_to_menu"))
                    return
                if not is_spotify_url(url):
                    print(t("invalid_url", error="Spotify URL required."))
                    continue

                saved_items = download_spotify_with_spotdl([url], download_dir)
                if saved_items:
                    add_history_entries([url], "spotify", saved_items)
                    print_saved_summary(download_dir / "Spotify", saved_items)
        else:
            txt_path = ask_non_empty(t("txt_path_prompt"))
            urls = read_urls_from_txt(txt_path)
            saved_items = download_spotify_with_spotdl(urls, download_dir)
            if saved_items:
                add_history_entries(urls, "spotify", saved_items)
                print_saved_summary(download_dir / "Spotify", saved_items)
        return

    download_dir = ask_download_dir()
    while True:
        detected = ask_auto_download_urls(media_type)
        if detected is None:
            return
        urls, source_type = detected
        saved_items = download(urls, media_type, source_type, download_dir)
        if saved_items:
            add_history_entries(urls, media_type, saved_items)
            print_saved_summary(download_dir, saved_items)


def main() -> None:
    load_config()
    init_database()
    ensure_download_stats_file()
    ensure_snake_scoreboard_file()
    clear_clipboard_queue()
    print_app_header()
    if not ensure_internet_or_offline_mode():
        print(t("program_no_internet"))
        return
    start_background_clipboard_watcher()

    try:
        while True:
            save_usage_time()
            clear_console()
            print_app_header()
            print()
            print(get_download_counter_text())
            pending_queue_count = get_pending_large_file_queue_count()
            if pending_queue_count:
                print(t("queue_pending", count=pending_queue_count))
            clipboard_queue_count = len(read_clipboard_queue())
            if clipboard_queue_count:
                print(t("clipboard_queue_menu", count=clipboard_queue_count))
            if CLIPBOARD_STATUS_LAST_URL:
                print(
                    t(
                        "clipboard_last_status",
                        url=shorten_text(CLIPBOARD_STATUS_LAST_URL, 54),
                        count=CLIPBOARD_STATUS_QUEUE_COUNT or clipboard_queue_count,
                    )
                )
            action = ask_choice(
                t("main_action"),
                {
                    "1": t("main_download"),
                    "2": t("main_file_download"),
                    "3": t("main_clipboard"),
                    "4": t("main_stats"),
                    "5": t("main_settings"),
                    "6": t("main_exit"),
                },
            )

            if action == "6":
                print(t("goodbye"))
                break
            if action == "2":
                run_large_file_flow()
                continue
            if action == "3":
                prompt_clipboard_queue(DEFAULT_DOWNLOAD_DIR)
                input(t("continue_prompt"))
                continue
            if action == "4":
                clear_console()
                print_app_header()
                show_download_stats()
                input(t("continue_prompt"))
                continue
            if action == "5":
                clear_console()
                print_app_header()
                show_settings_menu()
                continue

            run_download_flow()
    except KeyboardInterrupt:
        print(t("interrupted"))
    except Exception as exc:
        print(t("unexpected_error", error=exc))
        print_error_details(exc)
        log_path = write_error_log(exc, "Nieoczekiwany blad programu")
        print(t("details_saved", path=log_path))
    finally:
        stop_background_clipboard_watcher()
        save_usage_time()
        if not SKIP_EXIT_PAUSE:
            pause_before_exit()


if __name__ == "__main__":
    if "--import-cookies" in sys.argv:
        raise SystemExit(run_cookie_import_cli())
    main()
