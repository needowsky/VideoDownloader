@echo off
cd /d "%~dp0"

if exist "%~dp0tools\ffmpeg\bin\ffmpeg.exe" (
    set "PATH=%~dp0tools\ffmpeg\bin;%PATH%"
)

if exist "%~dp0python_packages" (
    set "PYTHONPATH=%~dp0python_packages;%PYTHONPATH%"
)

if exist "%~dp0tools\python312\python.exe" (
    "%~dp0tools\python312\python.exe" youtube_downloader.py
    pause
    exit /b
)

where py >nul 2>nul
if not errorlevel 1 (
    for %%V in (3.14 3.13 3.12 3.11 3.10) do (
        py -%%V -c "import sys; raise SystemExit(0)" >nul 2>nul
        if not errorlevel 1 (
            py -%%V youtube_downloader.py
            pause
            exit /b
        )
    )
)

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    "%LocalAppData%\Programs\Python\Python312\python.exe" youtube_downloader.py
    pause
    exit /b
)

where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info[:2] in [(3,10),(3,11),(3,12),(3,13),(3,14)] else 1)" >nul 2>nul
    if not errorlevel 1 (
        python youtube_downloader.py
        pause
        exit /b
    )
)

for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2] in [(3,10),(3,11),(3,12),(3,13),(3,14)] else 1)" >nul 2>nul
        if not errorlevel 1 (
            "%%D\python.exe" youtube_downloader.py
            pause
            exit /b
        )
    )
)

for /d %%D in ("%LocalAppData%\Python\pythoncore-*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2] in [(3,10),(3,11),(3,12),(3,13),(3,14)] else 1)" >nul 2>nul
        if not errorlevel 1 (
            "%%D\python.exe" youtube_downloader.py
            pause
            exit /b
        )
    )
)

echo Nie znaleziono zgodnego Pythona 3.10-3.14 ani lokalnego Pythona aplikacji.
echo Uruchom ponownie zainstaluj_wszystko.bat jako administrator.
pause
