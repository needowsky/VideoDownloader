from __future__ import annotations

from datetime import datetime
import importlib.util
import os
from pathlib import Path
import random
import re
from shutil import which
import socket
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from typing import Iterable
from urllib.parse import quote, urlparse

PROGRAM_DIR = Path(__file__).resolve().parent
LOCAL_PACKAGE_DIR = PROGRAM_DIR / "python_packages"
LOCAL_FFMPEG_BIN = PROGRAM_DIR / "tools" / "ffmpeg" / "bin"

if LOCAL_PACKAGE_DIR.exists():
    sys.path.insert(0, str(LOCAL_PACKAGE_DIR))

if (LOCAL_FFMPEG_BIN / "ffmpeg.exe").exists():
    os.environ["PATH"] = str(LOCAL_FFMPEG_BIN) + os.pathsep + os.environ.get("PATH", "")

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


DEFAULT_DOWNLOAD_DIR = Path.home() / "Downloads" / "YouTube Downloader"
APP_DATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / "VideoDownloader"
LOCAL_DOWNLOAD_STATS_FILE = PROGRAM_DIR / ".download_stats"
DOWNLOAD_STATS_FILE = APP_DATA_DIR / ".download_stats"
FALLBACK_DOWNLOAD_STATS_FILE = Path(".download_stats")
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
LANG = "en"  # en/pl
_N0R_FF = "00000000"
_SNEK_FF = "0000000000000000"
PROGRESS_BAR_WIDTH = 10
MIN_PROGRESS_BAR_WIDTH = 10
STATUS_LINE_WIDTH = 72
STATUS_TITLE_WIDTH = 22
STATUS_CLEAR_SEQUENCE = "\033[2K\r"
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

TEXTS = {
    "en": {
        "choose_option": "Choose option: ",
        "invalid_choice": "Invalid choice. Try again.",
        "empty_field": "This field cannot be empty.",
        "commands_title": "Special commands:",
        "help_help": "help       - shows this list",
        "help_matrix": "iamtheone  - starts the Matrix effect",
        "help_blue": "imblue     - changes console color to blue",
        "help_gothic": "gothic     - opens Gothic music in the browser",
        "help_lang": "lang=en/pl - switches language for the current session",
        "language_changed": "Language changed to English.",
        "finished_title": "=== Download finished ===",
        "saved_items": "Saved:",
        "saved_files": "Downloaded files were saved.",
        "saved_more": "- ... and {count} more files",
        "location": "Location",
        "offline_snake": "No internet - offline Snake | score: {score} | best: {best} | total: {total} | WASD/arrows, Q quits",
        "snake_scoreboard": "Snake: best {best} | total {total}",
        "snake_windows_only": "Offline Snake currently works only in Windows console.",
        "press_enter_continue": "Press Enter to continue...",
        "game_over": "Game over.",
        "no_connection": "No internet connection.",
        "need_internet_snake": "Downloading needs internet, so I am starting offline Snake.",
        "internet_back": "Internet is back. Returning to the program.",
        "retry_internet": "Still no internet. Check again",
        "blue_enabled": "Console color changed to blue.",
        "stats": "Downloaded files: {count} | Rank: {rank}",
        "invalid_url": "Invalid URL: {error}",
        "yes_no_hint": "Type y/n.",
        "yes_no_suffix": " [y/n]: ",
        "download_dir": "Save folder: {path}",
        "download_dir_prompt": "Press Enter to keep default, or enter another folder: ",
        "invalid_save_path": "Invalid save path: {error}",
        "error_type": "Error type: {value}",
        "reason": "Reason: {value}",
        "how_to_fix": "How to fix: {value}",
        "download_label": "Downloading",
        "status_success": "Status: success",
        "status_error": "Status: error",
        "details_saved": "Details saved in: {path}",
        "exit_prompt": "Press Enter to close the window...",
        "what_download": "What do you want to download?",
        "mp3": "MP3 - audio only",
        "mp4": "MP4 - video in the highest available quality",
        "photos": "Photos - Instagram, TikTok, Facebook",
        "photo_source": "Where should photos be downloaded from?",
        "single_photo_link": "Single link - Instagram, TikTok, Facebook",
        "txt_file": "Text file with links",
        "photo_link_prompt": "\nPaste photo link or type q to go back: ",
        "back_to_menu": "\nBack to menu.",
        "bad_http_link": "This does not look like a valid http/https link.",
        "txt_path_prompt": "Enter path to .txt file: ",
        "source": "Where should we download from?",
        "single_link": "Single link - auto: YouTube, Instagram, TikTok, Pornhub, Beeg etc.",
        "playlist": "YouTube playlist",
        "channel": "All songs from a YouTube channel",
        "url_prompt": "\nPaste link or type q to go back: ",
        "playlist_prompt": "Paste YouTube playlist link: ",
        "channel_intro": "Paste channel link, preferably to videos or music tab.",
        "examples": "Examples:",
        "channel_prompt": "Paste YouTube channel link: ",
        "channel_cancelled": "\nChannel download cancelled.",
        "app_title": "=== Video Downloader ===",
        "program_no_internet": "\nProgram closed - no internet connection.",
        "main_action": "What do you want to do?",
        "main_download": "Download link, playlist, channel or .txt file",
        "main_exit": "Exit program",
        "goodbye": "\nDone.",
        "interrupted": "\nInterrupted by user.",
        "unexpected_error": "\nAn error occurred: {error}",
        "conversion": "Converting...",
        "saved_status": "Saved",
    },
    "pl": {
        "choose_option": "Wybierz opcje: ",
        "invalid_choice": "Nieprawidlowy wybor. Sprobuj ponownie.",
        "empty_field": "To pole nie moze byc puste.",
        "commands_title": "Dostepne komendy specjalne:",
        "help_help": "help       - pokazuje te liste",
        "help_matrix": "iamtheone  - uruchamia efekt Matrix",
        "help_blue": "imblue     - zmienia kolor konsoli na niebieski",
        "help_gothic": "gothic     - otwiera muzyke Gothic w przegladarce",
        "help_lang": "lang=en/pl - zmienia jezyk w obecnej sesji",
        "language_changed": "Zmieniono jezyk na polski.",
        "finished_title": "=== Zakonczono pobieranie ===",
        "saved_items": "Zapisano:",
        "saved_files": "Zapisano pobrane pliki.",
        "saved_more": "- ... oraz {count} kolejnych plikow",
        "location": "Lokalizacja",
        "offline_snake": "Brak internetu - Snake offline | wynik: {score} | rekord: {best} | suma: {total} | WASD/strzalki, Q konczy",
        "snake_scoreboard": "Snake: rekord {best} | suma {total}",
        "snake_windows_only": "Snake offline dziala obecnie tylko w konsoli Windows.",
        "press_enter_continue": "Nacisnij Enter, aby kontynuowac...",
        "game_over": "Koniec gry.",
        "no_connection": "Brak polaczenia z internetem.",
        "need_internet_snake": "Pobieranie wymaga internetu, wiec wlaczam mini-gre Snake offline.",
        "internet_back": "Internet wrocil. Wracam do programu.",
        "retry_internet": "Nadal brak internetu. Sprawdzic ponownie",
        "blue_enabled": "Kolor konsoli zmieniony na niebieski.",
        "stats": "Pobrane pliki: {count} | Ranga: {rank}",
        "invalid_url": "Nieprawidlowy URL: {error}",
        "yes_no_hint": "Wpisz t/n.",
        "yes_no_suffix": " [t/n]: ",
        "download_dir": "Folder zapisu: {path}",
        "download_dir_prompt": "Nacisnij Enter, aby zostawic domyslny, albo podaj inny folder: ",
        "invalid_save_path": "Nieprawidlowa sciezka zapisu: {error}",
        "error_type": "Rodzaj bledu: {value}",
        "reason": "Powod: {value}",
        "how_to_fix": "Jak naprawic: {value}",
        "download_label": "Pobieranie",
        "status_success": "Status: sukces",
        "status_error": "Status: blad",
        "details_saved": "Szczegoly zapisano w: {path}",
        "exit_prompt": "Nacisnij Enter, aby zamknac okno...",
        "what_download": "Co chcesz pobrac?",
        "mp3": "MP3 - tylko dzwiek",
        "mp4": "MP4 - wideo w najwyzszej dostepnej jakosci",
        "photos": "Zdjecia - Instagram, TikTok, Facebook",
        "photo_source": "Skad pobieramy zdjecia?",
        "single_photo_link": "Pojedynczy link - Instagram, TikTok, Facebook",
        "txt_file": "Plik .txt z linkami",
        "photo_link_prompt": "\nWklej link ze zdjeciami albo wpisz q, aby wrocic: ",
        "back_to_menu": "\nPowrot do menu.",
        "bad_http_link": "To nie wyglada jak poprawny link http/https.",
        "txt_path_prompt": "Podaj sciezke do pliku .txt: ",
        "source": "Skad pobieramy?",
        "single_link": "Pojedynczy link - auto: YouTube, Instagram, TikTok, Pornhub, Beeg itd.",
        "playlist": "Playlista YouTube",
        "channel": "Wszystkie piosenki z kanalu YouTube",
        "url_prompt": "\nWklej link albo wpisz q, aby wrocic: ",
        "playlist_prompt": "Wklej link do playlisty YouTube: ",
        "channel_intro": "Wklej link do kanalu, najlepiej do zakladki z filmami albo muzyka.",
        "examples": "Przyklady:",
        "channel_prompt": "Wklej link do kanalu YouTube: ",
        "channel_cancelled": "\nPobieranie kanalu anulowane.",
        "app_title": "=== Pobieranie filmow z YouTube ===",
        "program_no_internet": "\nProgram zakonczony - brak polaczenia z internetem.",
        "main_action": "Co chcesz zrobic?",
        "main_download": "Pobrac link, playliste, kanal albo plik .txt",
        "main_exit": "Zakonczyc program",
        "goodbye": "\nKoniec pracy.",
        "interrupted": "\nPrzerwano przez uzytkownika.",
        "unexpected_error": "\nWystapil blad: {error}",
        "conversion": "Konwertowanie...",
        "saved_status": "Zapisano",
    },
}


def t(key: str, **kwargs: object) -> str:
    lang = LANG.lower()
    if lang not in TEXTS:
        lang = "en"
    value = TEXTS[lang].get(key, TEXTS["en"].get(key, key))
    return value.format(**kwargs)
ERROR_DEFINITIONS = [
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
SUPPORTED_SITE_HINTS = {
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "fb.watch": "Facebook",
    "pornhub.com": "Pornhub",
    "beeg.com": "Beeg",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
}
MATRIX_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ#$%&*+-/<=>?"
MAX_REASONABLE_DOWNLOAD_COUNT = 10_000_000
SNAKE_WIDTH = 30
SNAKE_HEIGHT = 14
GOTHIC_URL = "https://www.youtube.com/watch?v=DLyqSQhS6E0"
CONVERSION_STATUS_STOP = threading.Event()
CONVERSION_STATUS_THREAD: threading.Thread | None = None
CONVERSION_STATUS_TITLE = "Konwertowanie"
COMPLETED_DOWNLOAD_KEYS: set[str] = set()
COMPLETED_DOWNLOAD_TITLES: list[str] = []


def ask_choice(prompt: str, options: dict[str, str]) -> str:
    while True:
        print()
        print(prompt)
        for key, label in options.items():
            print(f"{key}. {label}")

        choice = input(t("choose_option")).strip()
        if choice in options:
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
    if command in {"lang=en", "lang=pl"}:
        LANG = command.split("=", 1)[1]
        print(t("language_changed"))
        return True
    if command == "help":
        show_command_help()
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
    print()


def clear_console() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def terminal_supports_hyperlinks() -> bool:
    return bool(os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"))


def make_folder_hyperlink(path: Path) -> str:
    resolved = path.expanduser().resolve()
    label = str(resolved)
    if not terminal_supports_hyperlinks():
        return label

    try:
        uri = resolved.as_uri()
    except ValueError:
        uri = "file:///" + quote(resolved.as_posix(), safe="/:")
    return f"\033]8;;{uri}\033\\{label}\033]8;;\033\\"


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
    print(f"{t('location')}: {make_folder_hyperlink(saved_path)}")
    print()


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
        subprocess.run(["attrib", "+h", str(path)], capture_output=True, text=True)


def clear_hidden_file(path: Path) -> None:
    if os.name == "nt" and path.exists():
        subprocess.run(["attrib", "-h", str(path)], capture_output=True, text=True)


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


def load_embedded_download_count() -> int | None:
    return decode_download_count(_N0R_FF)


def save_embedded_download_count(value: int) -> bool:
    global _N0R_FF
    encoded = encode_download_count(value)
    program_file = Path(__file__).resolve()
    try:
        clear_hidden_file(program_file)
        text = program_file.read_text(encoding="utf-8")
        new_text, replacements = re.subn(
            r'^_N0R_FF = "[0-9a-fA-F]{8}"',
            f'_N0R_FF = "{encoded}"',
            text,
            count=1,
            flags=re.MULTILINE,
        )
        if replacements != 1:
            return False
        program_file.write_text(new_text, encoding="utf-8")
        _N0R_FF = encoded
        return True
    except OSError:
        return False


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


def get_existing_stats_file() -> Path:
    if LOCAL_DOWNLOAD_STATS_FILE.exists():
        return LOCAL_DOWNLOAD_STATS_FILE
    if DOWNLOAD_STATS_FILE.exists():
        return DOWNLOAD_STATS_FILE
    if FALLBACK_DOWNLOAD_STATS_FILE.exists():
        return FALLBACK_DOWNLOAD_STATS_FILE
    return LOCAL_DOWNLOAD_STATS_FILE


def get_existing_snake_stats_file() -> Path:
    if LOCAL_SNAKE_STATS_FILE.exists():
        return LOCAL_SNAKE_STATS_FILE
    if SNAKE_STATS_FILE.exists():
        return SNAKE_STATS_FILE
    if FALLBACK_SNAKE_STATS_FILE.exists():
        return FALLBACK_SNAKE_STATS_FILE
    return LOCAL_SNAKE_STATS_FILE


def load_stats_file_count() -> int:
    try:
        stats_file = get_existing_stats_file()
        if not stats_file.exists():
            return 0

        raw_value = stats_file.read_text(encoding="utf-8").strip()
        if not raw_value.isdigit():
            save_download_count(0)
            return 0

        value = int(raw_value)
        if value < 0 or value > MAX_REASONABLE_DOWNLOAD_COUNT:
            save_download_count(0)
            return 0

        return value
    except OSError:
        return 0


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


def load_download_count() -> int:
    embedded_count = load_embedded_download_count()
    stats_count = load_stats_file_count()
    if embedded_count is None:
        return stats_count
    return max(embedded_count, stats_count)


def load_snake_scoreboard() -> tuple[int, int]:
    embedded_value = load_embedded_snake_scoreboard()
    file_best, file_total = load_snake_stats_file()
    if embedded_value is None:
        return file_best, file_total

    embedded_best, embedded_total = embedded_value
    return max(embedded_best, file_best), max(embedded_total, file_total)


def ensure_download_stats_file() -> None:
    count = load_download_count()
    save_download_count(count)


def ensure_snake_scoreboard_file() -> None:
    best_score, total_score = load_snake_scoreboard()
    save_snake_scoreboard(best_score, total_score)


def save_download_count(value: int) -> None:
    safe_value = max(0, min(int(value), MAX_REASONABLE_DOWNLOAD_COUNT))
    if save_embedded_download_count(safe_value):
        return

    for stats_file in (LOCAL_DOWNLOAD_STATS_FILE, DOWNLOAD_STATS_FILE, FALLBACK_DOWNLOAD_STATS_FILE):
        try:
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            clear_hidden_file(stats_file)
            stats_file.write_text(str(safe_value), encoding="utf-8")
            ensure_hidden_file(stats_file)
            return
        except OSError:
            continue


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


def add_downloaded_files(amount: int = 1) -> None:
    if amount <= 0:
        return
    save_download_count(load_download_count() + amount)


def get_download_rank(count: int) -> str:
    if count > 9000:
        return "OVER 9000!"

    if LANG.lower() == "pl":
        ranks = (
            (10, "swiezak"),
            (100, "nowicjusz"),
            (500, "regular"),
            (1000, "kolekcjoner"),
            (5000, "weteran"),
        )
        default_rank = "legenda"
    else:
        ranks = (
            (10, "rookie"),
            (100, "novice"),
            (500, "regular"),
            (1000, "collector"),
            (5000, "veteran"),
        )
        default_rank = "legend"

    for threshold, rank in ranks:
        if count < threshold:
            return rank
    return default_rank


def get_download_counter_text() -> str:
    count = load_download_count()
    return t("stats", count=count, rank=get_download_rank(count))


def get_snake_scoreboard_text() -> str:
    best_score, total_score = load_snake_scoreboard()
    return t("snake_scoreboard", best=best_score, total=total_score)


def ask_url_or_quit(prompt: str) -> str | None:
    while True:
        value = ask_non_empty(prompt)
        if value.lower() in {"q", "quit", "koniec"}:
            return None

        error = validate_url(value)
        if error is None:
            return value

        print(t("invalid_url", error=error))


def ask_url(prompt: str) -> str:
    while True:
        value = ask_non_empty(prompt)
        error = validate_url(value)
        if error is None:
            return value

        print(t("invalid_url", error=error))


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
        clean = line.strip()
        if clean and not clean.startswith("#"):
            url_error = validate_url(clean)
            if url_error is not None:
                raise ValueError(f"Nieprawidlowy link w pliku .txt: {clean} ({url_error})")
            urls.append(clean)

    if not urls:
        raise ValueError("Plik .txt nie zawiera zadnych linkow.")

    return urls


def looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_url(value: str) -> str | None:
    clean = value.strip().strip('"')
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


def suggest_repair(error_text: str) -> str:
    return classify_error(error_text)["repair"]


def print_error_details(error: object) -> None:
    error_text = str(error)
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
    if percent is None:
        return "[" + "." * bar_width + "]"

    done = int(bar_width * max(0, min(percent, 100)) / 100)
    return "[" + "#" * done + "." * (bar_width - done) + "]"


def get_download_percent(progress: dict) -> float | None:
    total = progress.get("total_bytes") or progress.get("total_bytes_estimate")
    downloaded = progress.get("downloaded_bytes")
    if not total or downloaded is None:
        return None
    return downloaded / total * 100


def format_mb(bytes_value: float | int | None) -> str:
    if bytes_value is None:
        return "? MB"
    return f"{bytes_value / (1024 * 1024):.2f} MB"


def format_gb_or_mb(bytes_value: float | int | None) -> str:
    if bytes_value is None:
        return "? MB"
    if bytes_value >= 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024 * 1024):.2f} GB"
    return format_mb(bytes_value)


def get_size_progress(progress: dict) -> str:
    downloaded = progress.get("downloaded_bytes")
    total = progress.get("total_bytes") or progress.get("total_bytes_estimate")
    return f"{format_mb(downloaded)}/{format_mb(total)}"


def format_speed(bytes_per_second: float | int | None) -> str:
    if bytes_per_second is None:
        return "? MB/s"
    return f"{bytes_per_second / (1024 * 1024):.2f} MB/s"


def get_progress_title(progress: dict) -> str:
    info = progress.get("info_dict") or {}
    return info.get("title") or Path(progress.get("filename", "")).stem or t("download_label")


def get_completed_download_key(progress: dict) -> str:
    info = progress.get("info_dict") or {}
    return str(info.get("id") or progress.get("filename") or time.monotonic())


def record_completed_download(progress: dict) -> None:
    key = get_completed_download_key(progress)
    if key in COMPLETED_DOWNLOAD_KEYS:
        return

    COMPLETED_DOWNLOAD_KEYS.add(key)
    COMPLETED_DOWNLOAD_TITLES.append(get_progress_title(progress))


def print_status_line(text: str) -> None:
    line = shorten_text(text, STATUS_LINE_WIDTH)
    print(STATUS_CLEAR_SEQUENCE + line, end="", flush=True)


def clear_status_line() -> None:
    print(STATUS_CLEAR_SEQUENCE, end="", flush=True)


def print_progress_line(progress: dict) -> None:
    percent = get_download_percent(progress)
    speed = format_speed(progress.get("speed"))
    size_progress = get_size_progress(progress)
    percent_text = f"{percent:5.1f}%" if percent is not None else "--.-%"
    bar = make_progress_bar(percent, PROGRESS_BAR_WIDTH)
    suffix = f" {bar} {percent_text} {size_progress} {speed}"
    title = shorten_text(get_progress_title(progress), STATUS_TITLE_WIDTH)
    line = f"{title:<{STATUS_TITLE_WIDTH}}{suffix}"
    print_status_line(line)


def print_conversion_line(progress: dict) -> None:
    suffix = f" {make_progress_bar(100, PROGRESS_BAR_WIDTH)} 100.0% Konwertowanie..."
    title = shorten_text(get_progress_title(progress), STATUS_TITLE_WIDTH)
    line = f"{title:<{STATUS_TITLE_WIDTH}}{suffix}"
    print_status_line(line)


def print_conversion_status(title: str, started_at: float, frame: str) -> None:
    elapsed = int(time.monotonic() - started_at)
    suffix = f" {frame} {t('conversion')} {format_seconds(elapsed)}"
    line = f"{shorten_text(title, STATUS_TITLE_WIDTH):<{STATUS_TITLE_WIDTH}}{suffix}"
    print_status_line(line)


def conversion_status_worker() -> None:
    started_at = time.monotonic()
    frames = "|/-\\"
    index = 0
    while not CONVERSION_STATUS_STOP.is_set():
        print_conversion_status(CONVERSION_STATUS_TITLE, started_at, frames[index % len(frames)])
        index += 1
        CONVERSION_STATUS_STOP.wait(0.5)


def start_conversion_status(title: str) -> None:
    global CONVERSION_STATUS_THREAD, CONVERSION_STATUS_TITLE
    if DEBUG:
        return
    if CONVERSION_STATUS_THREAD is not None and CONVERSION_STATUS_THREAD.is_alive():
        return

    CONVERSION_STATUS_TITLE = title or "Konwertowanie"
    CONVERSION_STATUS_STOP.clear()
    CONVERSION_STATUS_THREAD = threading.Thread(target=conversion_status_worker, daemon=True)
    CONVERSION_STATUS_THREAD.start()


def stop_conversion_status() -> None:
    global CONVERSION_STATUS_THREAD
    if DEBUG:
        return
    CONVERSION_STATUS_STOP.set()
    if CONVERSION_STATUS_THREAD is not None:
        CONVERSION_STATUS_THREAD.join(timeout=1)
        CONVERSION_STATUS_THREAD = None


def progress_hook(progress: dict) -> None:
    status = progress.get("status")
    if status == "finished":
        record_completed_download(progress)

    if DEBUG:
        return

    if status == "downloading":
        print_progress_line(progress)
    elif status == "finished":
        start_conversion_status(get_progress_title(progress))


def postprocessor_hook(progress: dict) -> None:
    if DEBUG:
        return

    status = progress.get("status")
    if status in {"started", "processing"}:
        start_conversion_status(get_progress_title(progress))
    elif status == "finished":
        stop_conversion_status()
        suffix = f" 100.0% {t('saved_status')}"
        title = shorten_text(get_progress_title(progress), STATUS_TITLE_WIDTH)
        print_status_line(f"{title:<{STATUS_TITLE_WIDTH}}{suffix}")


def get_workaround_strategies(media_type: str) -> list[dict]:
    fallback_format = "bestaudio/best" if media_type == "mp3" else "best/bv*+ba/b"
    return [
        {
            "name": "standardowa konfiguracja",
            "options": {},
        },
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
            "name": "awaryjny prostszy wybor formatu",
            "options": {
                "format": fallback_format,
            },
        },
    ]


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


def preflight_channel_download(channel_url: str, media_type: str) -> bool:
    if yt_dlp is None:
        message = "Brakuje biblioteki yt-dlp."
        print(message)
        log_path = write_error_log(message, "Podglad kanalu przed pobraniem")
        print(f"Szczegoly zapisano w: {log_path}")
        return False

    print()
    print("Sprawdzam kanal przed pobieraniem. To moze chwile potrwac...")

    try:
        with yt_dlp.YoutubeDL(get_metadata_options()) as ydl:
            info = ydl.extract_info(channel_url, download=False)
    except Exception as exc:
        print(f"Nie udalo sie sprawdzic kanalu: {exc}")
        print_error_details(exc)
        log_path = write_error_log(exc, "Podglad kanalu przed pobraniem")
        print(f"Szczegoly zapisano w: {log_path}")
        return False

    entries = list((info or {}).get("entries") or [])
    entries = [entry for entry in entries if entry]
    total_count = len(entries)
    if total_count == 0:
        print("Nie znaleziono materialow do pobrania na podanym linku kanalu.")
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

    channel_title = (info or {}).get("title") or "Kanal YouTube"
    media_label = "plikow MP3" if media_type == "mp3" else "filmow MP4"

    print()
    print("Podsumowanie przed pobieraniem:")
    print(f"Kanal: {channel_title}")
    print(f"Do pobrania: {total_count} materialow / {media_label}")
    if known_count:
        print(f"Szacowany rozmiar: {format_gb_or_mb(estimated_bytes)}")
    else:
        print("Szacowany rozmiar: nieznany")
    if unknown_count:
        print(
            f"Uwaga: dla {unknown_count} z {total_count} materialow nie udalo sie "
            "odczytac rozmiaru, wiec realny rozmiar moze byc wiekszy."
        )
    print("Rozmiar jest szacunkowy, bo YouTube czasem nie podaje pelnych danych.")
    print()

    return ask_yes_no("Kontynuowac pobieranie")


def build_download_options(
    media_type: str,
    source_type: str,
    download_dir: Path,
    extra_options: dict | None = None,
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

    if extra_options:
        options.update(extra_options)

    return options


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
        result = subprocess.run(command, text=True)
    else:
        result = subprocess.run(command, capture_output=True, text=True)

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


def show_gallery_dl_help() -> None:
    print()
    print("Brakuje gallery-dl.")
    print("To narzedzie jest potrzebne do pobierania zdjec z Instagram, TikTok i Facebook.")
    print()
    print("Zainstaluj je poleceniem:")
    print("python -m pip install --upgrade gallery-dl")


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
            cli_result = subprocess.run(command, text=True)
        else:
            cli_result = subprocess.run(command, capture_output=True, text=True)

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
        last_error = None

        for attempt, strategy in enumerate(strategies, start=1):
            if attempt > 1:
                print()
                print(
                    f"Proba obejscia problemu {attempt}/3: {strategy['name']}..."
                )

            try:
                COMPLETED_DOWNLOAD_KEYS.clear()
                COMPLETED_DOWNLOAD_TITLES.clear()
                options = build_download_options(
                    media_type,
                    source_type,
                    download_dir,
                    strategy["options"],
                )
                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.download([url])
                downloaded_titles = list(COMPLETED_DOWNLOAD_TITLES) or [detect_site(url)]
                downloaded_count = len(downloaded_titles)
                add_downloaded_files(downloaded_count)
                saved_items.extend(downloaded_titles)
                COMPLETED_DOWNLOAD_KEYS.clear()
                COMPLETED_DOWNLOAD_TITLES.clear()
                if not DEBUG:
                    stop_conversion_status()
                    clear_status_line()
                    print(t("status_success"))
                last_error = None
                break
            except Exception as exc:
                COMPLETED_DOWNLOAD_KEYS.clear()
                COMPLETED_DOWNLOAD_TITLES.clear()
                if not DEBUG:
                    stop_conversion_status()
                    clear_status_line()
                last_error = exc
                if attempt < len(strategies):
                    print(f"\nNie udalo sie: {exc}")
                    print_error_details(exc)
                    print("Aplikacja sprobuje kolejnego sposobu automatycznie.")
                else:
                    print(f"\nNie udalo sie po 3 probach: {exc}")
                    print_error_details(exc)

        if last_error is not None:
            context = (
                f"Nieudane pobieranie po 3 probach. URL: {url}. "
                f"Typ: {media_type}. Zrodlo: {source_type}."
            )
            log_path = write_error_log(last_error, context)
            print(t("details_saved", path=log_path))
    return saved_items


def pause_before_exit() -> None:
    print()
    input(t("exit_prompt"))


def run_download_flow() -> None:
    media_choice = ask_choice(
        t("what_download"),
        {
            "1": t("mp3"),
            "2": t("mp4"),
            "3": t("photos"),
        },
    )
    if media_choice == "1":
        media_type = "mp3"
    elif media_choice == "2":
        media_type = "mp4"
    else:
        media_type = "photos"

    if media_type == "photos":
        source_choice = ask_choice(
            t("photo_source"),
            {
                "1": t("single_photo_link"),
                "2": t("txt_file"),
            },
        )
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
                    print_saved_summary(download_dir / "Zdjecia", saved_items)
        else:
            txt_path = ask_non_empty(t("txt_path_prompt"))
            urls = read_urls_from_txt(txt_path)
            saved_items = download_photos(urls, download_dir)
            if saved_items:
                print_saved_summary(download_dir / "Zdjecia", saved_items)
        return

    source_choice = ask_choice(
        t("source"),
        {
            "1": t("single_link"),
            "2": t("playlist"),
            "3": t("txt_file"),
            "4": t("channel"),
        },
    )

    download_dir = ask_download_dir()

    if source_choice == "1":
        source_type = "auto"
        while True:
            url = ask_url_or_quit(t("url_prompt"))
            if url is None:
                print(t("back_to_menu"))
                return
            if not looks_like_url(url):
                print(t("bad_http_link"))
                continue

            saved_items = download([url], media_type, source_type, download_dir)
            if saved_items:
                print_saved_summary(download_dir, saved_items)
    elif source_choice == "2":
        source_type = "playlist"
        urls = [ask_url(t("playlist_prompt"))]
    elif source_choice == "3":
        source_type = "txt"
        txt_path = ask_non_empty(t("txt_path_prompt"))
        urls = read_urls_from_txt(txt_path)
    else:
        source_type = "channel"
        print()
        print(t("channel_intro"))
        print(t("examples"))
        print("https://www.youtube.com/@nazwa_kanalu/videos")
        print("https://www.youtube.com/@nazwa_kanalu/releases")
        urls = [ask_url(t("channel_prompt"))]
        if not preflight_channel_download(urls[0], media_type):
            print(t("channel_cancelled"))
            return

    saved_items = download(urls, media_type, source_type, download_dir)
    if saved_items:
        print_saved_summary(download_dir, saved_items)


def main() -> None:
    ensure_download_stats_file()
    ensure_snake_scoreboard_file()
    print(t("app_title"))
    if not ensure_internet_or_offline_mode():
        print(t("program_no_internet"))
        return

    try:
        while True:
            print()
            print(get_download_counter_text())
            print(get_snake_scoreboard_text())
            action = ask_choice(
                t("main_action"),
                {
                    "1": t("main_download"),
                    "2": t("main_exit"),
                },
            )

            if action == "2":
                print(t("goodbye"))
                break

            run_download_flow()
    except KeyboardInterrupt:
        print(t("interrupted"))
    except Exception as exc:
        print(t("unexpected_error", error=exc))
        print_error_details(exc)
        log_path = write_error_log(exc, "Nieoczekiwany blad programu")
        print(t("details_saved", path=log_path))
    finally:
        pause_before_exit()


if __name__ == "__main__":
    main()
