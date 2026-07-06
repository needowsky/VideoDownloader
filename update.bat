@echo off
setlocal
set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"
set "GITHUB_REPO=needowsky/VideoDownloader"
set "LOG_DIR=%APP_DIR%\logs"
set "UPDATE_LOG=%LOG_DIR%\update_log.txt"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>nul

net session >nul 2>nul
if errorlevel 1 (
    echo Administrator permission is required to update files in this folder.
    echo Requesting administrator permission...
    set "ELEVATE_VBS=%TEMP%\vd_elevate_update.vbs"
    > "%ELEVATE_VBS%" echo Set UAC = CreateObject^("Shell.Application"^)
    >> "%ELEVATE_VBS%" echo UAC.ShellExecute "%~f0", "", "%APP_DIR%", "runas", 1
    cscript //nologo "%ELEVATE_VBS%" >nul 2>nul
    exit /b 0
)

cd /d "%APP_DIR%"
if errorlevel 1 (
    echo Cannot enter app folder: %APP_DIR%
    pause
    exit /b 1
)

echo ================================================
echo  Video Downloader updater
echo ================================================
echo.
echo Closing app lock window...
timeout /t 2 /nobreak >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $repo='%GITHUB_REPO%'; $appDir=(Get-Location).Path; $log='%UPDATE_LOG%'; function Write-Log($m){ Add-Content -LiteralPath $log -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' ' + $m) }; Write-Log 'Update started'; $api='https://api.github.com/repos/' + $repo + '/releases/latest'; Write-Host '[ 10%%] Checking latest release...'; $release=Invoke-RestMethod -Uri $api -Headers @{'User-Agent'='VideoDownloaderUpdater'}; $latest=([string]$release.name).Trim(); if(-not ($latest -match '\d')){ $latest=([string]$release.tag_name).Trim() }; if(-not $latest){ throw 'Latest release has no version name or tag.' }; Write-Host ('Latest release: ' + $latest); $zipUrl=$release.zipball_url; if(-not $zipUrl){ throw 'Latest release does not contain source zip.' }; $work=Join-Path $env:TEMP ('vd_update_' + [guid]::NewGuid().ToString('N')); $zip=Join-Path $work 'release.zip'; $extract=Join-Path $work 'release'; New-Item -ItemType Directory -Force -Path $work | Out-Null; Write-Host '[ 30%%] Downloading update...'; Invoke-WebRequest -UseBasicParsing -Uri $zipUrl -Headers @{'User-Agent'='VideoDownloaderUpdater'} -OutFile $zip; Write-Host '[ 55%%] Extracting files...'; Expand-Archive -Force -Path $zip -DestinationPath $extract; $root=Get-ChildItem -Path $extract -Directory | Select-Object -First 1; if(-not $root){ throw 'Release archive is empty.' }; $files=@('youtube_downloader.py','uruchom_downloader.bat','README.md','CHANGELOG.md','LICENSE','install.ps1','zainstaluj_wszystko.bat','config/config.json','config/stats.json','config/lang/en.lang','config/lang/pl.lang'); Write-Host '[ 75%%] Updating application files...'; foreach($file in $files){ $src=Join-Path $root.FullName $file; if(Test-Path $src){ $dest=Join-Path $appDir $file; $destDir=Split-Path -Parent $dest; if($destDir){ New-Item -ItemType Directory -Force -Path $destDir | Out-Null }; Copy-Item -Force -LiteralPath $src -Destination $dest; Write-Log ('Updated ' + $file) } else { Write-Log ('Skipped missing file in release: ' + $file) } }; Write-Host '[100%%] Update complete.'; Write-Log ('Update complete: ' + $latest); Start-Sleep -Seconds 1"

if errorlevel 1 (
    echo.
    echo Update failed. Details:
    echo %UPDATE_LOG%
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Continue'; $ProgressPreference='SilentlyContinue'; $base='https://raw.githubusercontent.com/%GITHUB_REPO%/main/assets'; New-Item -ItemType Directory -Force -Path 'assets' | Out-Null; foreach($file in @('video_downloader.ico','video_downloader.png')){ Invoke-WebRequest -UseBasicParsing -Uri ($base + '/' + $file) -OutFile (Join-Path 'assets' $file) }" >> "%UPDATE_LOG%" 2>&1

echo.
echo Update complete.
echo You can start Video Downloader again.
pause
exit /b 0
