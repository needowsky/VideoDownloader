@echo off
cd /d "%~dp0"

if exist "%~dp0tools\ffmpeg\bin\ffmpeg.exe" (
    set "PATH=%~dp0tools\ffmpeg\bin;%PATH%"
)

if exist "%~dp0python_packages" (
    set "PYTHONPATH=%~dp0python_packages;%PYTHONPATH%"
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 youtube_downloader.py
    pause
    exit /b
)

where python >nul 2>nul
if not errorlevel 1 (
    python youtube_downloader.py
    pause
    exit /b
)

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    "%LocalAppData%\Programs\Python\Python312\python.exe" youtube_downloader.py
    pause
    exit /b
)

for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" youtube_downloader.py
        pause
        exit /b
    )
)

echo Nie znaleziono Pythona.
echo Uruchom najpierw zainstaluj_wszystko.bat
pause
