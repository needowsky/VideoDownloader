@echo off
setlocal
cd /d "%~dp0"

:: DEBUG=0 ukrywa techniczne logi instalacji. DEBUG=1 pokazuje pelne szczegoly.
set "DEBUG=0"
:: LANG=en shows English UI. LANG=pl shows Polish UI.
set "LANG=en"
:: GitHub source used to download the newest program files.
set "GITHUB_UPDATES=1"
set "GITHUB_REPO=needowsky/VideoDownloader"
set "GITHUB_DOWNLOAD_MODE=release"
set "GITHUB_BRANCH=main"
set "APP_DIR=%CD%"
set "TOTAL_STEPS=7"

echo ================================================
echo  Video Downloader AIO Installer
echo ================================================
echo.
if "%DEBUG%"=="1" echo Debug mode: %DEBUG%
if "%DEBUG%"=="1" echo Language: %LANG%
if not exist "logs" mkdir "logs" >nul 2>nul
set "INSTALL_LOG=%APP_DIR%\logs\install_debug_log.txt"
> "%INSTALL_LOG%" echo Video Downloader GitHub Installer
>> "%INSTALL_LOG%" echo Date: %DATE% %TIME%
>> "%INSTALL_LOG%" echo DEBUG=%DEBUG%
>> "%INSTALL_LOG%" echo GITHUB_REPO=%GITHUB_REPO%
>> "%INSTALL_LOG%" echo GITHUB_DOWNLOAD_MODE=%GITHUB_DOWNLOAD_MODE%
>> "%INSTALL_LOG%" echo GITHUB_BRANCH=%GITHUB_BRANCH%
echo.
call :StepStart 1 "Downloading program files"
call :DownloadProgramFiles
if errorlevel 1 (
    call :StepFail "github files"
    pause
    exit /b 1
)
call :ApplyProgramLanguage
call :StepOk 1

set "PYTHON_PACKAGE_DIR=%APP_DIR%\python_packages"
if not exist "%PYTHON_PACKAGE_DIR%" mkdir "%PYTHON_PACKAGE_DIR%" >nul 2>nul
set "PYTHONPATH=%PYTHON_PACKAGE_DIR%;%PYTHONPATH%"

call :StepStart 2 "Python"
call :FindPython
if not defined PYTHON_EXE (
    call :InstallPython
    if errorlevel 1 (
        call :StepFail "python"
        pause
        exit /b 1
    )
    call :FindPython
)
if not defined PYTHON_EXE (
    call :StepFail "python not visible"
    pause
    exit /b 1
)
call :StepOk 2

call :StepStart 3 "pip"
"%PYTHON_EXE%" -m pip --version >> "%INSTALL_LOG%" 2>&1
if errorlevel 1 (
    call :RunPythonCommand "pip" "-m ensurepip --upgrade"
    if errorlevel 1 (
        call :StepFail "pip"
        pause
        exit /b 1
    )
)
call :StepOk 3

call :StepStart 4 "FFmpeg"
call :FindFfmpeg
if not defined FFMPEG_FOUND (
    call :InstallLocalFfmpeg
    call :FindFfmpeg
)
if not defined FFMPEG_FOUND (
    call :InstallWithWinget "Gyan.FFmpeg"
    call :FindFfmpeg
)
if not defined FFMPEG_FOUND (
    call :StepFail "ffmpeg"
    pause
    exit /b 1
)
call :StepOk 4

call :StepStart 5 "yt-dlp"
"%PYTHON_EXE%" -c "import yt_dlp" >> "%INSTALL_LOG%" 2>&1
if errorlevel 1 (
    call :InstallPipPackage "yt-dlp"
    if errorlevel 1 (
        call :StepFail "yt-dlp"
        pause
        exit /b 1
    )
)
call :StepOk 5

call :StepStart 6 "gallery-dl"
"%PYTHON_EXE%" -c "import gallery_dl" >> "%INSTALL_LOG%" 2>&1
if errorlevel 1 (
    call :InstallPipPackage "gallery-dl"
    if errorlevel 1 (
        call :StepFail "gallery-dl"
        pause
        exit /b 1
    )
)
call :StepOk 6

call :StepStart 7 "Final check"
call :FindPython
if not defined PYTHON_EXE (
    call :StepFail "python not visible"
    pause
    exit /b 1
)
"%PYTHON_EXE%" -c "import yt_dlp, gallery_dl" >> "%INSTALL_LOG%" 2>&1
if errorlevel 1 (
    call :StepFail "python packages"
    pause
    exit /b 1
)
call :FindFfmpeg
if not defined FFMPEG_FOUND (
    call :StepFail "ffmpeg"
    pause
    exit /b 1
)
call :StepOk 7

echo.
echo ================================================
echo  Done - 100%% success
echo  Run: uruchom_downloader.bat
echo ================================================
echo.
pause
exit /b 0

:DownloadProgramFiles
if /i not "%GITHUB_UPDATES%"=="1" exit /b 1
if /i "%GITHUB_DOWNLOAD_MODE%"=="release" (
    call :DownloadProgramFilesFromLatestRelease
    if not errorlevel 1 exit /b 0
)
call :DownloadProgramFilesFromBranch "%GITHUB_BRANCH%"
if not errorlevel 1 exit /b 0
if /i not "%GITHUB_BRANCH%"=="master" (
    call :DownloadProgramFilesFromBranch "master"
    if not errorlevel 1 exit /b 0
)
exit /b 1

:DownloadProgramFilesFromLatestRelease
if "%DEBUG%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $repo='%GITHUB_REPO%'; $api='https://api.github.com/repos/' + $repo + '/releases/latest'; $release=Invoke-RestMethod -Uri $api -Headers @{'User-Agent'='VideoDownloaderInstaller'}; $zipUrl=$release.zipball_url; if(-not $zipUrl){ throw 'No zipball_url in latest release' }; $zip=Join-Path $env:TEMP 'vd_latest_release.zip'; $tmp=Join-Path $env:TEMP ('vd_release_'+[guid]::NewGuid().ToString()); Invoke-WebRequest -UseBasicParsing -Uri $zipUrl -Headers @{'User-Agent'='VideoDownloaderInstaller'} -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $tmp; $root=Get-ChildItem -Path $tmp -Directory | Select-Object -First 1; if(-not $root){ throw 'Release archive is empty' }; $files=@('youtube_downloader.py','uruchom_downloader.bat','README.md','LICENSE'); foreach($file in $files){ $src=Join-Path $root.FullName $file; if(-not (Test-Path $src)){ throw ('Missing file in release: ' + $file) }; Copy-Item -Force -LiteralPath $src -Destination $file }; exit 0"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $repo='%GITHUB_REPO%'; $api='https://api.github.com/repos/' + $repo + '/releases/latest'; $release=Invoke-RestMethod -Uri $api -Headers @{'User-Agent'='VideoDownloaderInstaller'}; $zipUrl=$release.zipball_url; if(-not $zipUrl){ throw 'No zipball_url in latest release' }; $zip=Join-Path $env:TEMP 'vd_latest_release.zip'; $tmp=Join-Path $env:TEMP ('vd_release_'+[guid]::NewGuid().ToString()); Invoke-WebRequest -UseBasicParsing -Uri $zipUrl -Headers @{'User-Agent'='VideoDownloaderInstaller'} -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $tmp; $root=Get-ChildItem -Path $tmp -Directory | Select-Object -First 1; if(-not $root){ throw 'Release archive is empty' }; $files=@('youtube_downloader.py','uruchom_downloader.bat','README.md','LICENSE'); foreach($file in $files){ $src=Join-Path $root.FullName $file; if(-not (Test-Path $src)){ throw ('Missing file in release: ' + $file) }; Copy-Item -Force -LiteralPath $src -Destination $file }; exit 0" >> "%INSTALL_LOG%" 2>&1
)
exit /b %ERRORLEVEL%

:DownloadProgramFilesFromBranch
set "DOWNLOAD_BRANCH=%~1"
if "%DEBUG%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $base='https://raw.githubusercontent.com/%GITHUB_REPO%/%DOWNLOAD_BRANCH%'; $files=@('youtube_downloader.py','uruchom_downloader.bat','README.md','LICENSE'); foreach($file in $files){ $url=($base.TrimEnd('/') + '/' + $file); Write-Host ('Downloading ' + $file); Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $file }; exit 0"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $base='https://raw.githubusercontent.com/%GITHUB_REPO%/%DOWNLOAD_BRANCH%'; $files=@('youtube_downloader.py','uruchom_downloader.bat','README.md','LICENSE'); foreach($file in $files){ $url=($base.TrimEnd('/') + '/' + $file); Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $file }; exit 0" >> "%INSTALL_LOG%" 2>&1
)
exit /b %ERRORLEVEL%

:StepStart
set /a PERCENT=(%1-1)*100/%TOTAL_STEPS%
echo.
echo Step %1 of %TOTAL_STEPS% - %~2
call :ProgressLine %PERCENT% "in progress"
exit /b 0

:StepOk
set /a PERCENT=%1*100/%TOTAL_STEPS%
call :ProgressLine %PERCENT% "success"
exit /b 0

:ProgressLine
set "BAR=[..........]"
if %~1 GEQ 10 set "BAR=[#.........]"
if %~1 GEQ 20 set "BAR=[##........]"
if %~1 GEQ 30 set "BAR=[###.......]"
if %~1 GEQ 40 set "BAR=[####......]"
if %~1 GEQ 50 set "BAR=[#####.....]"
if %~1 GEQ 60 set "BAR=[######....]"
if %~1 GEQ 70 set "BAR=[#######...]"
if %~1 GEQ 80 set "BAR=[########..]"
if %~1 GEQ 90 set "BAR=[#########.]"
if %~1 GEQ 100 set "BAR=[##########]"
echo %BAR% %~1%% - %~2
exit /b 0

:AlreadyInstalled
if "%DEBUG%"=="1" echo %~1: juz zainstalowane - pomijam pobieranie
exit /b 0

:ApplyProgramLanguage
if /i not "%LANG%"=="pl" set "LANG=en"
if "%DEBUG%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$p='youtube_downloader.py'; $lang='%LANG%'; $text=Get-Content -Raw $p; $text=$text -replace 'LANG = \"(en|pl)\"', ('LANG = \"' + $lang + '\"'); Set-Content -Path $p -Value $text -Encoding UTF8"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$p='youtube_downloader.py'; $lang='%LANG%'; $text=Get-Content -Raw $p; $text=$text -replace 'LANG = \"(en|pl)\"', ('LANG = \"' + $lang + '\"'); Set-Content -Path $p -Value $text -Encoding UTF8" >nul 2>nul
)
exit /b 0

:StepFail
echo.
echo [..........] error
echo Progress: error
call :ExplainInstallError "%~1"
echo Technical log: %INSTALL_LOG%
echo To see full installer details, set DEBUG=1 in zainstaluj_wszystko.bat and run it again.
exit /b 0

:ExplainInstallError
set "ERR_STAGE=%~1"
echo Failed stage: %ERR_STAGE%
if /i "%ERR_STAGE%"=="creating files" (
    echo Error type: Cannot create program files.
    echo Reason: The installer has no write permission in this folder or a file is locked.
    echo How to fix: Move the installer to Downloads/Desktop and run it again.
    exit /b 0
)
if /i "%ERR_STAGE%"=="github files" (
    echo Error type: Cannot download program files from GitHub.
    echo Reason: No internet, GitHub is blocked, the repository is private, or the branch/file names are different.
    echo How to fix: Check internet, make the repository public, or verify GITHUB_REPO and GITHUB_BRANCH in this installer.
    exit /b 0
)
if /i "%ERR_STAGE%"=="winget" (
    echo Error type: winget not available.
    echo Reason: Windows cannot see winget in this window.
    echo How to fix: The installer will try direct downloads. If this returns, run as administrator or install App Installer.
    exit /b 0
)
if /i "%ERR_STAGE%"=="python" (
    echo Error type: Python installation failed.
    echo Reason: No internet, download blocked, antivirus, or no permission to start the Python installer.
    echo How to fix: Run the installer as administrator or check internet/firewall.
    exit /b 0
)
if /i "%ERR_STAGE%"=="python not visible" (
    echo Error type: Python is not visible after installation.
    echo Reason: PATH did not refresh or Python installation was interrupted.
    echo How to fix: Close this window and run zainstaluj_wszystko.bat again.
    exit /b 0
)
if /i "%ERR_STAGE%"=="ffmpeg" (
    echo Error type: FFmpeg setup failed.
    echo Reason: Local download and winget failed, usually because of no internet, blocked download, or folder permissions.
    echo How to fix: Move the installer to Downloads/Desktop and run again, or run as administrator.
    exit /b 0
)
if /i "%ERR_STAGE%"=="pip" (
    echo Error type: pip setup failed.
    echo Reason: Python installation is broken, pip is blocked, or permissions are missing.
    echo How to fix: Run the installer again or repair Python.
    exit /b 0
)
if /i "%ERR_STAGE%"=="yt-dlp" (
    echo Error type: yt-dlp installation failed.
    echo Reason: No internet, PyPI unavailable, pip blocked, or folder write permissions missing.
    echo How to fix: Check internet, run as administrator, or unblock Python in firewall.
    exit /b 0
)
if /i "%ERR_STAGE%"=="gallery-dl" (
    echo Error type: gallery-dl installation failed.
    echo Reason: No internet, PyPI unavailable, pip blocked, or folder write permissions missing.
    echo How to fix: Check internet, run as administrator, or unblock Python in firewall.
    exit /b 0
)
if /i "%ERR_STAGE%"=="python packages" (
    echo Error type: Python packages are not visible after installation.
    echo Reason: pip installed packages in another profile or installation was interrupted.
    echo How to fix: Run the installer again. If it returns, set DEBUG=1 and check the log.
    exit /b 0
)
echo Error type: Unknown installer error.
echo Reason: Installer did not recognize the exact failed stage.
echo How to fix: Set DEBUG=1 and run again to see full logs.
exit /b 0

:FindPython
set "PYTHON_EXE="
where py >nul 2>nul
if not errorlevel 1 (
    for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
)
if defined PYTHON_EXE exit /b 0
where python >nul 2>nul
if not errorlevel 1 (
    for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
)
if defined PYTHON_EXE exit /b 0
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if defined PYTHON_EXE exit /b 0
for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
    if exist "%%~fD\python.exe" set "PYTHON_EXE=%%~fD\python.exe"
)
if defined PYTHON_EXE exit /b 0
for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%~fD\python.exe" set "PYTHON_EXE=%%~fD\python.exe"
)
exit /b 0

:FindFfmpeg
set "FFMPEG_FOUND="
where ffmpeg >nul 2>nul
if not errorlevel 1 (
    set "FFMPEG_FOUND=system"
    exit /b 0
)
if exist "%APP_DIR%\tools\ffmpeg\bin\ffmpeg.exe" (
    set "PATH=%APP_DIR%\tools\ffmpeg\bin;%PATH%"
    set "FFMPEG_FOUND=local"
)
exit /b 0

:InstallPython
call :InstallPythonDirect
if not errorlevel 1 exit /b 0
call :InstallWithWinget "Python.Python.3.12"
exit /b %ERRORLEVEL%

:InstallWithWinget
set "WINGET_PACKAGE=%~1"
if "%DEBUG%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; $w=(Get-Command winget -ErrorAction SilentlyContinue).Source; if(-not $w){exit 127}; & $w install --id '%WINGET_PACKAGE%' --exact --silent --disable-interactivity --accept-package-agreements --accept-source-agreements"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; $w=(Get-Command winget -ErrorAction SilentlyContinue).Source; if(-not $w){exit 127}; & $w install --id '%WINGET_PACKAGE%' --exact --silent --disable-interactivity --accept-package-agreements --accept-source-agreements" >> "%INSTALL_LOG%" 2>&1
)
exit /b %ERRORLEVEL%

:InstallPythonDirect
if "%DEBUG%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe'; $exe=Join-Path $env:TEMP 'vd_python_installer.exe'; Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $exe; $p=Start-Process -FilePath $exe -ArgumentList @('/quiet','InstallAllUsers=0','PrependPath=1','Include_pip=1','Include_launcher=1','Include_test=0','SimpleInstall=1') -WindowStyle Hidden -Wait -PassThru; exit $p.ExitCode"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe'; $exe=Join-Path $env:TEMP 'vd_python_installer.exe'; Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $exe; $p=Start-Process -FilePath $exe -ArgumentList @('/quiet','InstallAllUsers=0','PrependPath=1','Include_pip=1','Include_launcher=1','Include_test=0','SimpleInstall=1') -WindowStyle Hidden -Wait -PassThru; exit $p.ExitCode" >> "%INSTALL_LOG%" 2>&1
)
exit /b %ERRORLEVEL%

:InstallLocalFfmpeg
if "%DEBUG%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'; $zip=Join-Path $env:TEMP 'vd_ffmpeg.zip'; $tmp=Join-Path $env:TEMP ('vd_ffmpeg_'+[guid]::NewGuid().ToString()); $dest=Join-Path (Get-Location) 'tools\ffmpeg\bin'; New-Item -ItemType Directory -Force -Path $dest | Out-Null; Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $tmp; $ff=Get-ChildItem -Path $tmp -Recurse -Filter ffmpeg.exe | Select-Object -First 1; if(-not $ff){throw 'ffmpeg.exe not found'}; Copy-Item -Force -Recurse -Path (Join-Path $ff.Directory.FullName '*') -Destination $dest; exit 0"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'; $zip=Join-Path $env:TEMP 'vd_ffmpeg.zip'; $tmp=Join-Path $env:TEMP ('vd_ffmpeg_'+[guid]::NewGuid().ToString()); $dest=Join-Path (Get-Location) 'tools\ffmpeg\bin'; New-Item -ItemType Directory -Force -Path $dest | Out-Null; Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $tmp; $ff=Get-ChildItem -Path $tmp -Recurse -Filter ffmpeg.exe | Select-Object -First 1; if(-not $ff){throw 'ffmpeg.exe not found'}; Copy-Item -Force -Recurse -Path (Join-Path $ff.Directory.FullName '*') -Destination $dest; exit 0" >> "%INSTALL_LOG%" 2>&1
)
exit /b %ERRORLEVEL%

:RunPythonCommand
set "PY_STAGE=%~1"
set "PY_ARGS=%~2"
if "%DEBUG%"=="1" (
    "%PYTHON_EXE%" %PY_ARGS%
) else (
    "%PYTHON_EXE%" %PY_ARGS% >> "%INSTALL_LOG%" 2>&1
)
exit /b %ERRORLEVEL%

:InstallPipPackage
set "PIP_PACKAGE=%~1"
if "%DEBUG%"=="1" (
    "%PYTHON_EXE%" -m pip install --upgrade --target "%PYTHON_PACKAGE_DIR%" --no-input --disable-pip-version-check "%PIP_PACKAGE%"
) else (
    "%PYTHON_EXE%" -m pip install --upgrade --target "%PYTHON_PACKAGE_DIR%" --no-input --quiet --disable-pip-version-check "%PIP_PACKAGE%" >> "%INSTALL_LOG%" 2>&1
)
exit /b %ERRORLEVEL%
