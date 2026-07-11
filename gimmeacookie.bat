@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

if not exist "%~dp0youtube_downloader.py" (
    echo Nie wykryto plikow aplikacji Video Downloader.
    echo Najpierw zainstaluj aplikacje, a potem uruchom gimmeacookie.bat z folderu programu.
    pause
    exit /b 1
)

net session >nul 2>nul
if errorlevel 1 (
    echo Requesting administrator permission...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -WorkingDirectory '%~dp0' -Verb RunAs"
    exit /b
)

if exist "%~dp0tools\ffmpeg\bin" (
    set "PATH=%~dp0tools\ffmpeg\bin;%PATH%"
)

if exist "%~dp0python_packages" (
    set "PYTHONPATH=%~dp0python_packages;%PYTHONPATH%"
)

set "PYTHON_EXE="
if exist "%~dp0tools\python312\python.exe" set "PYTHON_EXE=%~dp0tools\python312\python.exe"

if not defined PYTHON_EXE (
    where py >nul 2>nul
    if not errorlevel 1 (
        for %%V in (3.14 3.13 3.12 3.11 3.10) do (
            py -%%V -c "import sys; raise SystemExit(0)" >nul 2>nul
            if not errorlevel 1 (
                py -%%V youtube_downloader.py --import-cookies
                set "EXIT_CODE=%ERRORLEVEL%"
                if not "!EXIT_CODE!"=="0" (
                    echo.
                    echo Import cookies nie powiodl sie.
                    echo Sprawdz, czy jestes zalogowany w Chrome, Microsoft Edge albo Firefox i czy przegladarka jest calkowicie zamknieta.
                )
                pause
                exit /b !EXIT_CODE!
            )
        )
    )
)

if not defined PYTHON_EXE (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_EXE=python"
)

if not defined PYTHON_EXE (
    for /d %%D in ("%LocalAppData%\Python\pythoncore-*") do (
        if exist "%%D\python.exe" (
            set "PYTHON_EXE=%%D\python.exe"
        )
    )
)

if not defined PYTHON_EXE (
    echo Compatible Python was not found.
    echo Najpierw zainstaluj aplikacje przez zainstaluj_wszystko.bat albo instalator EXE.
    pause
    exit /b 1
)

"%PYTHON_EXE%" youtube_downloader.py --import-cookies
set "EXIT_CODE=%ERRORLEVEL%"
if not "!EXIT_CODE!"=="0" (
    echo.
    echo Import cookies nie powiodl sie.
    echo Sprawdz, czy jestes zalogowany w Chrome, Microsoft Edge albo Firefox i czy przegladarka jest calkowicie zamknieta.
)
pause
exit /b !EXIT_CODE!
