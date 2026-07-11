@echo off

setlocal

set "SOURCE_DIR=%~dp0"

:: DEBUG=0 ukrywa techniczne logi instalacji. DEBUG=1 pokazuje pelne szczegoly.

set "DEBUG=0"

:: LANG=en shows English UI. LANG=pl shows Polish UI.

set "LANG=en"

:: Default installation folder. Requires administrator rights.

if not defined INSTALL_DIR set "INSTALL_DIR=%ProgramFiles%\VideoDownloader"

:: GitHub source used to download the newest application files.

if not defined GITHUB_UPDATES set "GITHUB_UPDATES=1"

set "GITHUB_REPO=needowsky/VideoDownloader"

set "GITHUB_DOWNLOAD_MODE=release"

set "GITHUB_BRANCH=main"

set "TOTAL_STEPS=11"

echo ================================================

echo  Video Downloader AIO Installer

echo ================================================

echo.

if "%DEBUG%"=="1" echo Debug mode: %DEBUG%

if "%DEBUG%"=="1" echo Language: %LANG%

if "%DEBUG%"=="1" echo Install folder: %INSTALL_DIR%

call :EnsureAdmin

if defined ELEVATION_STARTED exit /b 0

if errorlevel 1 exit /b 1

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%" >nul 2>nul

cd /d "%INSTALL_DIR%"

if errorlevel 1 (

    echo Error type: Cannot enter install folder.

    echo Reason: The installer has no write permission for %INSTALL_DIR%.

    echo How to fix: Run the installer as administrator or change INSTALL_DIR.

    pause

    exit /b 1

)

set "APP_DIR=%CD%"

if not exist "logs" mkdir "logs" >nul 2>nul

set "LOCAL_PYTHON_DIR=%APP_DIR%\tools\python312"

set "INSTALL_LOG=%APP_DIR%\logs\install_debug_log.txt"

> "%INSTALL_LOG%" echo Video Downloader GitHub Installer

>> "%INSTALL_LOG%" echo Date: %DATE% %TIME%

>> "%INSTALL_LOG%" echo DEBUG=%DEBUG%

>> "%INSTALL_LOG%" echo GITHUB_REPO=%GITHUB_REPO%

>> "%INSTALL_LOG%" echo GITHUB_DOWNLOAD_MODE=%GITHUB_DOWNLOAD_MODE%

>> "%INSTALL_LOG%" echo GITHUB_BRANCH=%GITHUB_BRANCH%

echo.

call :StepStart 1 "Downloading application files"

if /i "%GITHUB_UPDATES%"=="1" (

    call :DownloadProgramFiles

    if errorlevel 1 (

        call :StepFail "github files"

        pause

        exit /b 1

    )

    call :DownloadAppAssets

    call :ApplyProgramLanguage

    call :StepOk 1

) else (

    >> "%INSTALL_LOG%" echo GITHUB_UPDATES=0 - using local installer files.

    call :ApplyProgramLanguage

    call :StepAlready 1 "GitHub download skipped - using local files"

)

set "PYTHON_PACKAGE_DIR=%APP_DIR%\python_packages"

if not exist "%PYTHON_PACKAGE_DIR%" mkdir "%PYTHON_PACKAGE_DIR%" >nul 2>nul

set "PYTHONPATH=%PYTHON_PACKAGE_DIR%;%PYTHONPATH%"

call :StepStart 2 "Python"

call :LongStepNotice "Python"

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

call :EnsurePortablePythonPackagePath

if defined PYTHON_WAS_INSTALLED (

    call :StepInstalled 2 "Python installed"

) else (

    call :StepAlready 2 "Python already installed"

)

call :StepStart 3 "pip"

"%PYTHON_EXE%" -m pip --version >> "%INSTALL_LOG%" 2>&1

if errorlevel 1 (

    call :RunPythonCommand "pip" "-m ensurepip --upgrade"

    if errorlevel 1 (

        call :StepFail "pip"

        pause

        exit /b 1

    )

    call :StepInstalled 3 "pip installed"

) else (

    call :UpdatePip

    if errorlevel 1 (

        call :StepFail "pip"

        pause

        exit /b 1

    )

    if defined PIP_WAS_UPDATED (

        call :StepUpdated 3 "pip checked and updated if needed"

    ) else (

        call :StepAlready 3 "pip already installed and current"

    )

)

call :StepStart 4 "Microsoft C++ Build Tools"

call :LongStepNotice "Microsoft C++ Build Tools"

call :FindVcBuildTools

if not defined VC_BUILD_TOOLS_FOUND (

    call :InstallVcBuildTools

    call :FindVcBuildTools

)

if not defined VC_BUILD_TOOLS_FOUND (

    call :StepFail "vc build tools"

    pause

    exit /b 1

)

if defined VC_BUILD_TOOLS_WAS_INSTALLED (

    call :StepInstalled 4 "Microsoft C++ Build Tools installed"

) else (

    call :StepAlready 4 "Microsoft C++ Build Tools already installed"

)

call :StepStart 5 "FFmpeg"

call :FindFfmpeg

if not defined FFMPEG_FOUND (

    call :InstallLocalFfmpeg

    call :FindFfmpeg

)

if not defined FFMPEG_FOUND (

    call :InstallWithWinget "Gyan.FFmpeg"

    if not errorlevel 1 set "FFMPEG_WAS_INSTALLED=1"

    call :FindFfmpeg

)

if not defined FFMPEG_FOUND (

    call :StepFail "ffmpeg"

    pause

    exit /b 1

)

if defined FFMPEG_WAS_INSTALLED (

    call :StepInstalled 5 "FFmpeg installed"

) else (

    call :StepAlready 5 "FFmpeg already installed"

)

call :StepStart 6 "yt-dlp"

call :EnsurePipPackage 6 "yt-dlp" "yt_dlp"

if errorlevel 1 (

    call :StepFail "yt-dlp"

    pause

    exit /b 1

)

call :StepStart 7 "gallery-dl"

call :EnsurePipPackage 7 "gallery-dl" "gallery_dl"

if errorlevel 1 (

    call :StepFail "gallery-dl"

    pause

    exit /b 1

)

call :StepStart 8 "spotDL"

call :EnsurePipPackage 8 "spotdl" "spotdl"

if errorlevel 1 (

    call :StepFail "spotdl"

    pause

    exit /b 1

)

call :StepStart 9 "UI and helper libraries"

call :EnsureHelperPackages 9

if errorlevel 1 (

    call :StepFail "helper packages"

    pause

    exit /b 1

)

call :StepStart 10 "Final check"

call :FindPython

if not defined PYTHON_EXE (

    call :StepFail "python not visible"

    pause

    exit /b 1

)

"%PYTHON_EXE%" -c "import yt_dlp, gallery_dl, spotdl, rich, textual, browser_cookie3, bs4, lxml, mutagen, selenium, sqlite3" >> "%INSTALL_LOG%" 2>&1

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

call :GrantAppReadPermissions

call :StepOk 10

call :StepStart 11 "Shortcuts"

call :CreateAppShortcuts

if errorlevel 1 (

    call :StepFail "shortcuts"

    pause

    exit /b 1

)

call :SetShortcutIcons

call :StepOk 11

echo.

echo ================================================

echo  Done - 100%% success

echo  Installed in: %APP_DIR%

echo  Shortcuts: Desktop and Start Menu

echo ================================================

echo.

pause

exit /b 0

:LongStepNotice

set "LONG_STEP_NAME=%~1"

if /i "%LANG%"=="pl" (

    echo Ten etap moze potrwac dluzej: %LONG_STEP_NAME%.

    echo Prosimy o cierpliwosc - instalator nadal pracuje.

) else (

    echo This step may take longer: %LONG_STEP_NAME%.

    echo Please be patient - the installer is still working.

)

echo.

exit /b 0

:EnsureAdmin

set "INSTALL_REQUIRES_ADMIN=0"

echo(%INSTALL_DIR%| findstr /i /b /c:"%ProgramFiles%" >nul 2>nul && set "INSTALL_REQUIRES_ADMIN=1"

if defined ProgramFiles(x86) echo(%INSTALL_DIR%| findstr /i /b /c:"%ProgramFiles(x86)%" >nul 2>nul && set "INSTALL_REQUIRES_ADMIN=1"

if not "%INSTALL_REQUIRES_ADMIN%"=="1" exit /b 0

net session >nul 2>nul

if not errorlevel 1 exit /b 0

echo Administrator permission is required for Program Files.

echo Requesting administrator permission...

set "ELEVATE_VBS=%TEMP%\vd_elevate_installer.vbs"

> "%ELEVATE_VBS%" echo Set UAC = CreateObject^("Shell.Application"^)

>> "%ELEVATE_VBS%" echo UAC.ShellExecute "%~f0", "", "%SOURCE_DIR%", "runas", 1

cscript //nologo "%ELEVATE_VBS%" >nul 2>nul

if errorlevel 1 exit /b 1

set "ELEVATION_STARTED=1"

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

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; function Get-Numbers($v){ $n=@([regex]::Matches([string]$v,'\d+') | ForEach-Object {[int]$_.Value}); if($n.Count -eq 0){ return @(0) }; return $n }; function Compare-Version($a,$b){ $av=Get-Numbers $a; $bv=Get-Numbers $b; $max=[Math]::Max($av.Count,$bv.Count); for($i=0;$i -lt $max;$i++){ $ai=0; $bi=0; if($i -lt $av.Count){ $ai=$av[$i] }; if($i -lt $bv.Count){ $bi=$bv[$i] }; if($ai -gt $bi){ return 1 }; if($ai -lt $bi){ return -1 } }; return 0 }; $repo='%GITHUB_REPO%'; $api='https://api.github.com/repos/' + $repo + '/releases/latest'; $release=Invoke-RestMethod -Uri $api -Headers @{'User-Agent'='VideoDownloaderInstaller'}; $releaseName=([string]$release.name).Trim(); $releaseTag=([string]$release.tag_name).Trim(); if($releaseName -match '\d'){ $latest=$releaseName } else { $latest=$releaseTag }; if(-not $latest){ $latest=$releaseName }; if(-not $latest){ throw 'No release version in latest release' }; $current=''; if(Test-Path 'youtube_downloader.py'){ $line=Select-String -Path 'youtube_downloader.py' -Pattern 'APP_VERSION' | Select-Object -First 1; if($line){ $m=[regex]::Match($line.Line,'v?\d+(\.\d+)*'); if($m.Success){ $current=$m.Value.Trim() } } }; if($current -and ((Compare-Version $latest $current) -le 0)){ Write-Host ('Current version ' + $current + ' is up to date. Latest: ' + $latest); exit 0 }; Write-Host ('Installing app version ' + $latest + ($(if($current){ ' over ' + $current } else { '' }))); $zipUrl=$release.zipball_url; if(-not $zipUrl){ throw 'No zipball_url in latest release' }; $zip=Join-Path $env:TEMP 'vd_latest_release.zip'; $tmp=Join-Path $env:TEMP ('vd_release_'+[guid]::NewGuid().ToString()); Invoke-WebRequest -UseBasicParsing -Uri $zipUrl -Headers @{'User-Agent'='VideoDownloaderInstaller'} -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $tmp; $root=Get-ChildItem -Path $tmp -Directory | Select-Object -First 1; if(-not $root){ throw 'Release archive is empty' }; $files=@('youtube_downloader.py','uruchom_downloader.bat','gimmeacookie.bat','README.md','CHANGELOG.md','LICENSE','install.ps1','zainstaluj_wszystko.bat','update.bat','config/config.json','config/stats.json','config/lang/en.lang','config/lang/pl.lang','assets/video_downloader.ico','assets/video_downloader.png','aio_installer/VideoDownloader_AIO_Installer.py','aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.exe','aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.zip'); foreach($file in $files){ $src=Join-Path $root.FullName $file; if(Test-Path $src){ $dest=$file; $destDir=Split-Path -Parent $dest; if($destDir){ New-Item -ItemType Directory -Force -Path $destDir | Out-Null }; Copy-Item -Force -LiteralPath $src -Destination $dest } else { Write-Host ('Skipped missing file: ' + $file) } }; exit 0"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; function Get-Numbers($v){ $n=@([regex]::Matches([string]$v,'\d+') | ForEach-Object {[int]$_.Value}); if($n.Count -eq 0){ return @(0) }; return $n }; function Compare-Version($a,$b){ $av=Get-Numbers $a; $bv=Get-Numbers $b; $max=[Math]::Max($av.Count,$bv.Count); for($i=0;$i -lt $max;$i++){ $ai=0; $bi=0; if($i -lt $av.Count){ $ai=$av[$i] }; if($i -lt $bv.Count){ $bi=$bv[$i] }; if($ai -gt $bi){ return 1 }; if($ai -lt $bi){ return -1 } }; return 0 }; $repo='%GITHUB_REPO%'; $api='https://api.github.com/repos/' + $repo + '/releases/latest'; $release=Invoke-RestMethod -Uri $api -Headers @{'User-Agent'='VideoDownloaderInstaller'}; $releaseName=([string]$release.name).Trim(); $releaseTag=([string]$release.tag_name).Trim(); if($releaseName -match '\d'){ $latest=$releaseName } else { $latest=$releaseTag }; if(-not $latest){ $latest=$releaseName }; if(-not $latest){ throw 'No release version in latest release' }; $current=''; if(Test-Path 'youtube_downloader.py'){ $line=Select-String -Path 'youtube_downloader.py' -Pattern 'APP_VERSION' | Select-Object -First 1; if($line){ $m=[regex]::Match($line.Line,'v?\d+(\.\d+)*'); if($m.Success){ $current=$m.Value.Trim() } } }; if($current -and ((Compare-Version $latest $current) -le 0)){ Write-Output ('Current version ' + $current + ' is up to date. Latest: ' + $latest); exit 0 }; Write-Output ('Installing app version ' + $latest + ($(if($current){ ' over ' + $current } else { '' }))); $zipUrl=$release.zipball_url; if(-not $zipUrl){ throw 'No zipball_url in latest release' }; $zip=Join-Path $env:TEMP 'vd_latest_release.zip'; $tmp=Join-Path $env:TEMP ('vd_release_'+[guid]::NewGuid().ToString()); Invoke-WebRequest -UseBasicParsing -Uri $zipUrl -Headers @{'User-Agent'='VideoDownloaderInstaller'} -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $tmp; $root=Get-ChildItem -Path $tmp -Directory | Select-Object -First 1; if(-not $root){ throw 'Release archive is empty' }; $files=@('youtube_downloader.py','uruchom_downloader.bat','gimmeacookie.bat','README.md','CHANGELOG.md','LICENSE','install.ps1','zainstaluj_wszystko.bat','update.bat','config/config.json','config/stats.json','config/lang/en.lang','config/lang/pl.lang','assets/video_downloader.ico','assets/video_downloader.png','aio_installer/VideoDownloader_AIO_Installer.py','aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.exe','aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.zip'); foreach($file in $files){ $src=Join-Path $root.FullName $file; if(Test-Path $src){ $dest=$file; $destDir=Split-Path -Parent $dest; if($destDir){ New-Item -ItemType Directory -Force -Path $destDir | Out-Null }; Copy-Item -Force -LiteralPath $src -Destination $dest } }; exit 0" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

:DownloadProgramFilesFromBranch

set "DOWNLOAD_BRANCH=%~1"

if "%DEBUG%"=="1" (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $repo='%GITHUB_REPO%'; $branch='%DOWNLOAD_BRANCH%'; $zip=Join-Path $env:TEMP ('vd_branch_' + [guid]::NewGuid().ToString('N') + '.zip'); $tmp=Join-Path $env:TEMP ('vd_branch_' + [guid]::NewGuid().ToString('N')); $url='https://codeload.github.com/' + $repo + '/zip/refs/heads/' + $branch; Write-Host ('Downloading repository zip from ' + $branch); Invoke-WebRequest -UseBasicParsing -Headers @{'User-Agent'='VideoDownloaderInstaller'} -Uri $url -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $tmp; $root=Get-ChildItem -Path $tmp -Directory | Select-Object -First 1; if(-not $root){ throw 'Branch archive is empty' }; $files=@('youtube_downloader.py','uruchom_downloader.bat','gimmeacookie.bat','README.md','CHANGELOG.md','LICENSE','install.ps1','zainstaluj_wszystko.bat','update.bat','config/config.json','config/stats.json','config/lang/en.lang','config/lang/pl.lang','assets/video_downloader.ico','assets/video_downloader.png','aio_installer/VideoDownloader_AIO_Installer.py','aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.exe','aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.zip'); foreach($file in $files){ $src=Join-Path $root.FullName $file; if(Test-Path $src){ $dest=$file; $destDir=Split-Path -Parent $dest; if($destDir){ New-Item -ItemType Directory -Force -Path $destDir | Out-Null }; Copy-Item -Force -LiteralPath $src -Destination $dest; Write-Host ('Updated ' + $file) } else { Write-Host ('Skipped missing file: ' + $file) } }; exit 0"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $repo='%GITHUB_REPO%'; $branch='%DOWNLOAD_BRANCH%'; $zip=Join-Path $env:TEMP ('vd_branch_' + [guid]::NewGuid().ToString('N') + '.zip'); $tmp=Join-Path $env:TEMP ('vd_branch_' + [guid]::NewGuid().ToString('N')); $url='https://codeload.github.com/' + $repo + '/zip/refs/heads/' + $branch; Invoke-WebRequest -UseBasicParsing -Headers @{'User-Agent'='VideoDownloaderInstaller'} -Uri $url -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $tmp; $root=Get-ChildItem -Path $tmp -Directory | Select-Object -First 1; if(-not $root){ throw 'Branch archive is empty' }; $files=@('youtube_downloader.py','uruchom_downloader.bat','gimmeacookie.bat','README.md','CHANGELOG.md','LICENSE','install.ps1','zainstaluj_wszystko.bat','update.bat','config/config.json','config/stats.json','config/lang/en.lang','config/lang/pl.lang','assets/video_downloader.ico','assets/video_downloader.png','aio_installer/VideoDownloader_AIO_Installer.py','aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.exe','aio_exe_release/VideoDownloader_AIO_Installer_EXE_3_5.zip'); foreach($file in $files){ $src=Join-Path $root.FullName $file; if(Test-Path $src){ $dest=$file; $destDir=Split-Path -Parent $dest; if($destDir){ New-Item -ItemType Directory -Force -Path $destDir | Out-Null }; Copy-Item -Force -LiteralPath $src -Destination $dest } }; exit 0" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

:StepStart

set "CURRENT_STEP=%~1"

set "CURRENT_STEP_NAME=%~2"

set /a OVERALL_PERCENT=(%1-1)*100/%TOTAL_STEPS%

echo.

echo Step %1 of %TOTAL_STEPS% - %~2

call :ProgressLine 0 %OVERALL_PERCENT% "in progress"

exit /b 0

:StepOk

set /a OVERALL_PERCENT=%1*100/%TOTAL_STEPS%

call :ProgressLine 100 %OVERALL_PERCENT% "success"

exit /b 0

:StepAlready

set /a OVERALL_PERCENT=%1*100/%TOTAL_STEPS%

call :ProgressLine 100 %OVERALL_PERCENT% "%~2"

exit /b 0

:StepInstalled

set /a OVERALL_PERCENT=%1*100/%TOTAL_STEPS%

call :ProgressLine 100 %OVERALL_PERCENT% "%~2"

exit /b 0

:StepUpdated

set /a OVERALL_PERCENT=%1*100/%TOTAL_STEPS%

call :ProgressLine 100 %OVERALL_PERCENT% "%~2"

exit /b 0

:ProgressLine

set "STEP_BAR=----------"

if %~1 GEQ 10 set "STEP_BAR==---------"

if %~1 GEQ 20 set "STEP_BAR===--------"

if %~1 GEQ 30 set "STEP_BAR====-------"

if %~1 GEQ 40 set "STEP_BAR=====------"

if %~1 GEQ 50 set "STEP_BAR======-----"

if %~1 GEQ 60 set "STEP_BAR=======----"

if %~1 GEQ 70 set "STEP_BAR========---"

if %~1 GEQ 80 set "STEP_BAR=========--"

if %~1 GEQ 90 set "STEP_BAR==========-"

if %~1 GEQ 100 set "STEP_BAR=========="

set "OVERALL_BAR=----------"

if %~2 GEQ 10 set "OVERALL_BAR==---------"

if %~2 GEQ 20 set "OVERALL_BAR===--------"

if %~2 GEQ 30 set "OVERALL_BAR====-------"

if %~2 GEQ 40 set "OVERALL_BAR=====------"

if %~2 GEQ 50 set "OVERALL_BAR======-----"

if %~2 GEQ 60 set "OVERALL_BAR=======----"

if %~2 GEQ 70 set "OVERALL_BAR========---"

if %~2 GEQ 80 set "OVERALL_BAR=========--"

if %~2 GEQ 90 set "OVERALL_BAR==========-"

if %~2 GEQ 100 set "OVERALL_BAR=========="

echo step    %~1%%  %STEP_BAR%
echo overall %~2%%  %OVERALL_BAR%  %~3

exit /b 0

:AlreadyInstalled

if "%DEBUG%"=="1" echo %~1: juz zainstalowane - pomijam pobieranie

exit /b 0

:ApplyProgramLanguage

if /i not "%LANG%"=="pl" set "LANG=en"

if "%DEBUG%"=="1" (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$dir='config'; New-Item -ItemType Directory -Force -Path $dir | Out-Null; $path=Join-Path $dir 'config.json'; $lang='%LANG%'; $config=@{}; if(Test-Path $path){ try{ $raw=Get-Content -Raw $path | ConvertFrom-Json; foreach($p in $raw.PSObject.Properties){ $config[$p.Name]=$p.Value } } catch { $config=@{} } }; $config['lang']=$lang; if(-not $config.ContainsKey('debug')){ $config['debug']=[int]'%DEBUG%' }; $config | ConvertTo-Json -Depth 5 | Set-Content -Path $path -Encoding UTF8"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$dir='config'; New-Item -ItemType Directory -Force -Path $dir | Out-Null; $path=Join-Path $dir 'config.json'; $lang='%LANG%'; $config=@{}; if(Test-Path $path){ try{ $raw=Get-Content -Raw $path | ConvertFrom-Json; foreach($p in $raw.PSObject.Properties){ $config[$p.Name]=$p.Value } } catch { $config=@{} } }; $config['lang']=$lang; if(-not $config.ContainsKey('debug')){ $config['debug']=[int]'%DEBUG%' }; $config | ConvertTo-Json -Depth 5 | Set-Content -Path $path -Encoding UTF8" >nul 2>nul

)

exit /b 0

:DownloadAppAssets

if not exist "assets" mkdir "assets" >nul 2>nul

if exist "assets\video_downloader.ico" if exist "assets\video_downloader.png" exit /b 0

if not defined DOWNLOAD_BRANCH set "DOWNLOAD_BRANCH=%GITHUB_BRANCH%"

if "%DEBUG%"=="1" (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Continue'; $ProgressPreference='SilentlyContinue'; $base='https://raw.githubusercontent.com/%GITHUB_REPO%/%DOWNLOAD_BRANCH%/assets'; New-Item -ItemType Directory -Force -Path 'assets' | Out-Null; foreach($file in @('video_downloader.ico','video_downloader.png')){ $dest=Join-Path 'assets' $file; if(-not (Test-Path $dest)){ Invoke-WebRequest -UseBasicParsing -Uri ($base + '/' + $file) -OutFile $dest } }; exit 0"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Continue'; $ProgressPreference='SilentlyContinue'; $base='https://raw.githubusercontent.com/%GITHUB_REPO%/%DOWNLOAD_BRANCH%/assets'; New-Item -ItemType Directory -Force -Path 'assets' | Out-Null; foreach($file in @('video_downloader.ico','video_downloader.png')){ $dest=Join-Path 'assets' $file; if(-not (Test-Path $dest)){ Invoke-WebRequest -UseBasicParsing -Uri ($base + '/' + $file) -OutFile $dest } }; exit 0" >> "%INSTALL_LOG%" 2>&1

)

exit /b 0

:CreateAppShortcuts

if "%DEBUG%"=="1" (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $app='%APP_DIR%'; $target=Join-Path $app 'uruchom_downloader.bat'; $py=Join-Path $app 'youtube_downloader.py'; if((-not (Test-Path $target)) -and (Test-Path $py)){ $lines=@('@echo off','cd /d ""%%~dp0""','if exist ""tools\python312\python.exe"" (','    ""tools\python312\python.exe"" youtube_downloader.py',') else (','    python youtube_downloader.py',')','pause'); Set-Content -Path $target -Value $lines -Encoding ASCII }; if(-not (Test-Path $target)){ throw 'Launcher not found: ' + $target }; $shell=New-Object -ComObject WScript.Shell; function New-Link($dir){ if([string]::IsNullOrWhiteSpace($dir)){ return $false }; New-Item -ItemType Directory -Force -Path $dir | Out-Null; $path=Join-Path $dir 'Video Downloader.lnk'; $s=$shell.CreateShortcut($path); $s.TargetPath=$target; $s.WorkingDirectory=$app; $s.Description='Video Downloader'; $s.IconLocation=$env:SystemRoot + '\System32\shell32.dll,220'; $s.Save(); return (Test-Path $path) }; $desktop=[Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory); $publicDesktop=[Environment]::GetFolderPath([Environment+SpecialFolder]::CommonDesktopDirectory); $programs=[Environment]::GetFolderPath([Environment+SpecialFolder]::Programs); $commonPrograms=[Environment]::GetFolderPath([Environment+SpecialFolder]::CommonPrograms); $desktopOk=(New-Link $desktop) -or (New-Link $publicDesktop); $startDir=if($programs){ Join-Path $programs 'Video Downloader' } else { Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Video Downloader' }; $commonStartDir=if($commonPrograms){ Join-Path $commonPrograms 'Video Downloader' } else { $null }; $startOk=(New-Link $startDir) -or (New-Link $commonStartDir); if((-not $desktopOk) -or (-not $startOk)){ throw ('Shortcut creation failed. Desktop=' + $desktopOk + ' StartMenu=' + $startOk) }; exit 0"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $app='%APP_DIR%'; $target=Join-Path $app 'uruchom_downloader.bat'; $py=Join-Path $app 'youtube_downloader.py'; if((-not (Test-Path $target)) -and (Test-Path $py)){ $lines=@('@echo off','cd /d ""%%~dp0""','if exist ""tools\python312\python.exe"" (','    ""tools\python312\python.exe"" youtube_downloader.py',') else (','    python youtube_downloader.py',')','pause'); Set-Content -Path $target -Value $lines -Encoding ASCII }; if(-not (Test-Path $target)){ throw 'Launcher not found: ' + $target }; $shell=New-Object -ComObject WScript.Shell; function New-Link($dir){ if([string]::IsNullOrWhiteSpace($dir)){ return $false }; New-Item -ItemType Directory -Force -Path $dir | Out-Null; $path=Join-Path $dir 'Video Downloader.lnk'; $s=$shell.CreateShortcut($path); $s.TargetPath=$target; $s.WorkingDirectory=$app; $s.Description='Video Downloader'; $s.IconLocation=$env:SystemRoot + '\System32\shell32.dll,220'; $s.Save(); return (Test-Path $path) }; $desktop=[Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory); $publicDesktop=[Environment]::GetFolderPath([Environment+SpecialFolder]::CommonDesktopDirectory); $programs=[Environment]::GetFolderPath([Environment+SpecialFolder]::Programs); $commonPrograms=[Environment]::GetFolderPath([Environment+SpecialFolder]::CommonPrograms); $desktopOk=(New-Link $desktop) -or (New-Link $publicDesktop); $startDir=if($programs){ Join-Path $programs 'Video Downloader' } else { Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Video Downloader' }; $commonStartDir=if($commonPrograms){ Join-Path $commonPrograms 'Video Downloader' } else { $null }; $startOk=(New-Link $startDir) -or (New-Link $commonStartDir); if((-not $desktopOk) -or (-not $startOk)){ throw ('Shortcut creation failed. Desktop=' + $desktopOk + ' StartMenu=' + $startOk) }; exit 0" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

:SetShortcutIcons

if not exist "%APP_DIR%\assets\video_downloader.ico" exit /b 0

if "%DEBUG%"=="1" (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Continue'; $app='%APP_DIR%'; $icon=Join-Path $app 'assets\video_downloader.ico'; if(-not (Test-Path $icon)){ exit 0 }; $paths=@(); $desktop=[Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory); $publicDesktop=[Environment]::GetFolderPath([Environment+SpecialFolder]::CommonDesktopDirectory); $programs=[Environment]::GetFolderPath([Environment+SpecialFolder]::Programs); $commonPrograms=[Environment]::GetFolderPath([Environment+SpecialFolder]::CommonPrograms); foreach($dir in @($desktop,$publicDesktop,(Join-Path $programs 'Video Downloader'),(Join-Path $commonPrograms 'Video Downloader'))){ if($dir){ $paths += (Join-Path $dir 'Video Downloader.lnk') } }; $shell=New-Object -ComObject WScript.Shell; foreach($path in $paths){ if(Test-Path $path){ $s=$shell.CreateShortcut($path); $s.IconLocation=$icon; $s.Save() } }; exit 0"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Continue'; $app='%APP_DIR%'; $icon=Join-Path $app 'assets\video_downloader.ico'; if(-not (Test-Path $icon)){ exit 0 }; $paths=@(); $desktop=[Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory); $publicDesktop=[Environment]::GetFolderPath([Environment+SpecialFolder]::CommonDesktopDirectory); $programs=[Environment]::GetFolderPath([Environment+SpecialFolder]::Programs); $commonPrograms=[Environment]::GetFolderPath([Environment+SpecialFolder]::CommonPrograms); foreach($dir in @($desktop,$publicDesktop,(Join-Path $programs 'Video Downloader'),(Join-Path $commonPrograms 'Video Downloader'))){ if($dir){ $paths += (Join-Path $dir 'Video Downloader.lnk') } }; $shell=New-Object -ComObject WScript.Shell; foreach($path in $paths){ if(Test-Path $path){ $s=$shell.CreateShortcut($path); $s.IconLocation=$icon; $s.Save() } }; exit 0" >> "%INSTALL_LOG%" 2>&1

)

exit /b 0

:GrantAppReadPermissions

>> "%INSTALL_LOG%" echo Granting read permissions for standard users in %APP_DIR%.

icacls "%APP_DIR%" /grant "*S-1-5-32-545:(OI)(CI)RX" /T /C >> "%INSTALL_LOG%" 2>&1

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

    echo Error type: Cannot create application files.

    echo Reason: The installer has no write permission in this folder or a file is locked.

    echo How to fix: Move the installer to Downloads/Desktop and run it again.

    exit /b 0

)

if /i "%ERR_STAGE%"=="github files" (

    echo Error type: Cannot download application files from GitHub.

    echo Reason: No internet, GitHub is blocked, the repository is private, or the branch/file names are different.

    echo How to fix: Check internet, make the repository public, or verify GITHUB_REPO and GITHUB_BRANCH in this installer.

    exit /b 0

)

if /i "%ERR_STAGE%"=="desktop shortcut" (

    echo Error type: Cannot create desktop shortcut.

    echo Reason: The Desktop folder is unavailable, the launcher is missing, or Windows blocked shortcut creation.

    echo How to fix: Start the app manually from %APP_DIR%\uruchom_downloader.bat or run the installer again as administrator.

    exit /b 0

)

if /i "%ERR_STAGE%"=="shortcuts" (

    echo Error type: Cannot create app shortcuts.

    echo Reason: Desktop or Start Menu folder is unavailable, the launcher is missing, or Windows blocked shortcut creation.

    echo How to fix: Start the app manually from %APP_DIR%\uruchom_downloader.bat or run the installer again as administrator.

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

if /i "%ERR_STAGE%"=="vc build tools" (

    echo Error type: Microsoft C++ Build Tools setup failed.

    echo Reason: winget/direct Microsoft installer failed, internet is blocked, or Visual Studio installer needs a restart.

    echo How to fix: Restart Windows and run this installer again. If it returns, install Microsoft Visual Studio 2022 Build Tools with C++ workload manually.

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

if /i "%ERR_STAGE%"=="spotdl" (

    echo Error type: spotDL installation failed.

    echo Reason: No internet, PyPI unavailable, pip blocked, incompatible Python version, or folder write permissions missing.

    echo How to fix: Use Python 3.11-3.13, run as administrator, or unblock Python in firewall. Python 3.14 may require build tools for some dependencies.

    exit /b 0

)

if /i "%ERR_STAGE%"=="helper packages" (

    echo Error type: UI/helper libraries installation failed.

    echo Reason: pip could not install Rich/Textual/browser-cookie3/BeautifulSoup/lxml/mutagen/Selenium, usually because PyPI is blocked, Python is broken, or build wheels are unavailable.

    echo How to fix: Check internet, run as administrator, unblock Python in firewall, then run the installer again.

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

>> "%INSTALL_LOG%" echo FindPython: PATH=%PATH%

>> "%INSTALL_LOG%" echo FindPython: LocalAppData=%LocalAppData%

>> "%INSTALL_LOG%" echo FindPython: ProgramFiles=%ProgramFiles%

if exist "%LOCAL_PYTHON_DIR%\python.exe" call :UsePythonCandidate "%LOCAL_PYTHON_DIR%\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%ProgramFiles%\Python312\python.exe" call :UsePythonCandidate "%ProgramFiles%\Python312\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%ProgramFiles(x86)%\Python312\python.exe" call :UsePythonCandidate "%ProgramFiles(x86)%\Python312\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" call :UsePythonCandidate "%LocalAppData%\Programs\Python\Python312\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%ProgramFiles%\Python313\python.exe" call :UsePythonCandidate "%ProgramFiles%\Python313\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%ProgramFiles(x86)%\Python313\python.exe" call :UsePythonCandidate "%ProgramFiles(x86)%\Python313\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%LocalAppData%\Programs\Python\Python313\python.exe" call :UsePythonCandidate "%LocalAppData%\Programs\Python\Python313\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%ProgramFiles%\Python311\python.exe" call :UsePythonCandidate "%ProgramFiles%\Python311\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%ProgramFiles(x86)%\Python311\python.exe" call :UsePythonCandidate "%ProgramFiles(x86)%\Python311\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%LocalAppData%\Programs\Python\Python311\python.exe" call :UsePythonCandidate "%LocalAppData%\Programs\Python\Python311\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%ProgramFiles%\Python310\python.exe" call :UsePythonCandidate "%ProgramFiles%\Python310\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%ProgramFiles(x86)%\Python310\python.exe" call :UsePythonCandidate "%ProgramFiles(x86)%\Python310\python.exe"

if defined PYTHON_EXE exit /b 0

if exist "%LocalAppData%\Programs\Python\Python310\python.exe" call :UsePythonCandidate "%LocalAppData%\Programs\Python\Python310\python.exe"

if defined PYTHON_EXE exit /b 0

if "%DEBUG%"=="1" (

    where py >nul 2>nul

    if not errorlevel 1 (

        >> "%INSTALL_LOG%" echo FindPython: py launcher found.

        for %%V in (3.13 3.12 3.11 3.10) do (

            if not defined PYTHON_EXE (

                for /f "delims=" %%P in ('py -%%V -c "import sys; print(sys.executable)" 2^>nul') do call :UsePythonCandidate "%%P"

            )

        )

    )

)

if defined PYTHON_EXE exit /b 0

where python >nul 2>nul

if not errorlevel 1 (

    >> "%INSTALL_LOG%" echo FindPython: python command found.

    for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do call :UsePythonCandidate "%%P"

)

if defined PYTHON_EXE exit /b 0

for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (

    if not defined PYTHON_EXE if exist "%%~fD\python.exe" call :UsePythonCandidate "%%~fD\python.exe"

)

if defined PYTHON_EXE exit /b 0

for /d %%D in ("%ProgramFiles%\Python3*") do (

    if not defined PYTHON_EXE if exist "%%~fD\python.exe" call :UsePythonCandidate "%%~fD\python.exe"

)

exit /b 0

:UsePythonCandidate

set "PY_CANDIDATE=%~1"

>> "%INSTALL_LOG%" echo Checking Python candidate: %PY_CANDIDATE%

if not exist "%PY_CANDIDATE%" exit /b 1

"%PY_CANDIDATE%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] in [(3,10),(3,11),(3,12),(3,13)] else 1)" >nul 2>nul

if not errorlevel 1 (

    set "PYTHON_EXE=%PY_CANDIDATE%"

    if "%DEBUG%"=="1" "%PY_CANDIDATE%" -c "import sys; print('Using Python ' + sys.version.split()[0] + ' at ' + sys.executable)"

    exit /b 0

)

if "%DEBUG%"=="1" (

    "%PY_CANDIDATE%" -c "import sys; print('Skipping incompatible Python ' + sys.version.split()[0] + ' at ' + sys.executable)" 2>nul

)

exit /b 1

:EnsurePortablePythonPackagePath

if not exist "%LOCAL_PYTHON_DIR%\python312._pth" exit /b 0

findstr /x /c:"%PYTHON_PACKAGE_DIR%" "%LOCAL_PYTHON_DIR%\python312._pth" >nul 2>nul

if errorlevel 1 (

    >> "%LOCAL_PYTHON_DIR%\python312._pth" echo %PYTHON_PACKAGE_DIR%

    >> "%INSTALL_LOG%" echo Added python package folder to portable Python path: %PYTHON_PACKAGE_DIR%

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

:FindVcBuildTools

set "VC_BUILD_TOOLS_FOUND="

where cl >nul 2>nul

if not errorlevel 1 (

    set "VC_BUILD_TOOLS_FOUND=path"

    exit /b 0

)

set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"

if exist "%VSWHERE%" (

    for /f "usebackq delims=" %%V in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2^>nul`) do (

        if exist "%%V\VC\Tools\MSVC" (

            set "VC_BUILD_TOOLS_FOUND=vswhere"

            exit /b 0

        )

    )

)

if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC" (

    set "VC_BUILD_TOOLS_FOUND=buildtools2022"

    exit /b 0

)

if exist "%ProgramFiles%\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC" (

    set "VC_BUILD_TOOLS_FOUND=buildtools2022"

    exit /b 0

)

exit /b 0

:InstallPython

call :InstallPythonPortable

if not errorlevel 1 call :FindPython

if defined PYTHON_EXE (

    set "PYTHON_WAS_INSTALLED=1"

    exit /b 0

)

exit /b 1

:InstallWithWinget

set "WINGET_PACKAGE=%~1"

if "%DEBUG%"=="1" (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; $w=(Get-Command winget -ErrorAction SilentlyContinue).Source; if(-not $w){exit 127}; & $w install --id '%WINGET_PACKAGE%' --exact --silent --disable-interactivity --accept-package-agreements --accept-source-agreements"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; $w=(Get-Command winget -ErrorAction SilentlyContinue).Source; if(-not $w){exit 127}; & $w install --id '%WINGET_PACKAGE%' --exact --silent --disable-interactivity --accept-package-agreements --accept-source-agreements" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

:InstallWithWingetForce

set "WINGET_PACKAGE=%~1"

if "%DEBUG%"=="1" (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; $w=(Get-Command winget -ErrorAction SilentlyContinue).Source; if(-not $w){exit 127}; & $w install --id '%WINGET_PACKAGE%' --exact --silent --force --disable-interactivity --accept-package-agreements --accept-source-agreements"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; $w=(Get-Command winget -ErrorAction SilentlyContinue).Source; if(-not $w){exit 127}; & $w install --id '%WINGET_PACKAGE%' --exact --silent --force --disable-interactivity --accept-package-agreements --accept-source-agreements" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

:InstallVcBuildTools

call :InstallVcBuildToolsWinget

if not errorlevel 1 (

    set "VC_BUILD_TOOLS_WAS_INSTALLED=1"

    exit /b 0

)

call :InstallVcBuildToolsDirect

if not errorlevel 1 set "VC_BUILD_TOOLS_WAS_INSTALLED=1"

exit /b %ERRORLEVEL%

:InstallVcBuildToolsWinget

if "%DEBUG%"=="1" (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; $w=(Get-Command winget -ErrorAction SilentlyContinue).Source; if(-not $w){exit 127}; & $w install --id 'Microsoft.VisualStudio.2022.BuildTools' --exact --silent --disable-interactivity --accept-package-agreements --accept-source-agreements --override '--wait --quiet --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended'"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; $w=(Get-Command winget -ErrorAction SilentlyContinue).Source; if(-not $w){exit 127}; & $w install --id 'Microsoft.VisualStudio.2022.BuildTools' --exact --silent --disable-interactivity --accept-package-agreements --accept-source-agreements --override '--wait --quiet --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended'" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

:InstallVcBuildToolsDirect

if "%DEBUG%"=="1" (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://aka.ms/vs/17/release/vs_BuildTools.exe'; $exe=Join-Path $env:TEMP 'vd_vs_buildtools.exe'; Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $exe; $args=@('--quiet','--wait','--norestart','--nocache','--add','Microsoft.VisualStudio.Workload.VCTools','--includeRecommended'); $p=Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden -Wait -PassThru; if($p.ExitCode -eq 3010){ exit 0 }; exit $p.ExitCode"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://aka.ms/vs/17/release/vs_BuildTools.exe'; $exe=Join-Path $env:TEMP 'vd_vs_buildtools.exe'; Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $exe; $args=@('--quiet','--wait','--norestart','--nocache','--add','Microsoft.VisualStudio.Workload.VCTools','--includeRecommended'); $p=Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden -Wait -PassThru; if($p.ExitCode -eq 3010){ exit 0 }; exit $p.ExitCode" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

:InstallPythonDirect

if "%DEBUG%"=="1" (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe'; $exe=Join-Path $env:TEMP 'vd_python_installer.exe'; Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $exe; $target='%LOCAL_PYTHON_DIR%'; New-Item -ItemType Directory -Force -Path $target | Out-Null; $log=Join-Path '%APP_DIR%' 'logs\python_installer.log'; $args=@('/quiet','InstallAllUsers=0','PrependPath=0','Include_pip=1','Include_launcher=0','Include_test=0','SimpleInstall=1',('TargetDir=' + $target),('/log ' + $log)); $p=Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden -Wait -PassThru; exit $p.ExitCode"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe'; $exe=Join-Path $env:TEMP 'vd_python_installer.exe'; Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $exe; $target='%LOCAL_PYTHON_DIR%'; New-Item -ItemType Directory -Force -Path $target | Out-Null; $log=Join-Path '%APP_DIR%' 'logs\python_installer.log'; $args=@('/quiet','InstallAllUsers=0','PrependPath=0','Include_pip=1','Include_launcher=0','Include_test=0','SimpleInstall=1',('TargetDir=' + $target),('/log ' + $log)); $p=Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden -Wait -PassThru; exit $p.ExitCode" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

:RepairPythonDirect
if "%DEBUG%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe'; $exe=Join-Path $env:TEMP 'vd_python_installer.exe'; if(-not (Test-Path $exe)){ Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $exe }; $target='%LOCAL_PYTHON_DIR%'; New-Item -ItemType Directory -Force -Path $target | Out-Null; $log=Join-Path '%APP_DIR%' 'logs\python_installer_repair.log'; $args=@('/quiet','/repair','InstallAllUsers=0','PrependPath=0','Include_pip=1','Include_launcher=0','Include_test=0','SimpleInstall=1',('TargetDir=' + $target),('/log ' + $log)); $p=Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden -Wait -PassThru; exit $p.ExitCode"
) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe'; $exe=Join-Path $env:TEMP 'vd_python_installer.exe'; if(-not (Test-Path $exe)){ Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $exe }; $target='%LOCAL_PYTHON_DIR%'; New-Item -ItemType Directory -Force -Path $target | Out-Null; $log=Join-Path '%APP_DIR%' 'logs\python_installer_repair.log'; $args=@('/quiet','/repair','InstallAllUsers=0','PrependPath=0','Include_pip=1','Include_launcher=0','Include_test=0','SimpleInstall=1',('TargetDir=' + $target),('/log ' + $log)); $p=Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden -Wait -PassThru; exit $p.ExitCode" >> "%INSTALL_LOG%" 2>&1

)
exit /b %ERRORLEVEL%

:InstallPythonPortable
if "%DEBUG%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $target='%LOCAL_PYTHON_DIR%'; if(Test-Path $target){ Remove-Item -Recurse -Force $target }; New-Item -ItemType Directory -Force -Path $target | Out-Null; $zip=Join-Path $env:TEMP 'vd_python_3.12.10_embed.zip'; Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip' -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $target; $pth=Join-Path $target 'python312._pth'; if(Test-Path $pth){ (Get-Content $pth) -replace '#import site','import site' | Set-Content -Encoding ASCII $pth }; $gp=Join-Path $target 'get-pip.py'; Invoke-WebRequest -UseBasicParsing -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile $gp; & (Join-Path $target 'python.exe') $gp --no-warn-script-location; exit $LASTEXITCODE"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $target='%LOCAL_PYTHON_DIR%'; if(Test-Path $target){ Remove-Item -Recurse -Force $target }; New-Item -ItemType Directory -Force -Path $target | Out-Null; $zip=Join-Path $env:TEMP 'vd_python_3.12.10_embed.zip'; Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip' -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $target; $pth=Join-Path $target 'python312._pth'; if(Test-Path $pth){ (Get-Content $pth) -replace '#import site','import site' | Set-Content -Encoding ASCII $pth }; $gp=Join-Path $target 'get-pip.py'; Invoke-WebRequest -UseBasicParsing -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile $gp; & (Join-Path $target 'python.exe') $gp --no-warn-script-location; exit $LASTEXITCODE" >> "%INSTALL_LOG%" 2>&1
)
exit /b %ERRORLEVEL%

:InstallLocalFfmpeg
if "%DEBUG%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'; $zip=Join-Path $env:TEMP 'vd_ffmpeg.zip'; $tmp=Join-Path $env:TEMP ('vd_ffmpeg_'+[guid]::NewGuid().ToString()); $dest=Join-Path (Get-Location) 'tools\ffmpeg\bin'; New-Item -ItemType Directory -Force -Path $dest | Out-Null; Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $tmp; $ff=Get-ChildItem -Path $tmp -Recurse -Filter ffmpeg.exe | Select-Object -First 1; if(-not $ff){throw 'ffmpeg.exe not found'}; Copy-Item -Force -Recurse -Path (Join-Path $ff.Directory.FullName '*') -Destination $dest; exit 0"

) else (

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'; $zip=Join-Path $env:TEMP 'vd_ffmpeg.zip'; $tmp=Join-Path $env:TEMP ('vd_ffmpeg_'+[guid]::NewGuid().ToString()); $dest=Join-Path (Get-Location) 'tools\ffmpeg\bin'; New-Item -ItemType Directory -Force -Path $dest | Out-Null; Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $zip; Expand-Archive -Force -Path $zip -DestinationPath $tmp; $ff=Get-ChildItem -Path $tmp -Recurse -Filter ffmpeg.exe | Select-Object -First 1; if(-not $ff){throw 'ffmpeg.exe not found'}; Copy-Item -Force -Recurse -Path (Join-Path $ff.Directory.FullName '*') -Destination $dest; exit 0" >> "%INSTALL_LOG%" 2>&1

)

if not errorlevel 1 set "FFMPEG_WAS_INSTALLED=1"

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

:UpdatePip

set "PIP_WAS_UPDATED="

if "%DEBUG%"=="1" (

    "%PYTHON_EXE%" -m pip install --upgrade pip --disable-pip-version-check

) else (

    "%PYTHON_EXE%" -m pip install --upgrade pip --quiet --disable-pip-version-check >> "%INSTALL_LOG%" 2>&1

)

if not errorlevel 1 set "PIP_WAS_UPDATED=1"

exit /b %ERRORLEVEL%

:EnsurePipPackage

set "STEP_NUMBER=%~1"

set "PIP_PACKAGE=%~2"

set "IMPORT_NAME=%~3"

set "PACKAGE_WAS_INSTALLED="

set "PACKAGE_WAS_UPDATED="

"%PYTHON_EXE%" -c "import %IMPORT_NAME%" >> "%INSTALL_LOG%" 2>&1

if errorlevel 1 (

    echo %PIP_PACKAGE% not installed - installing...

    call :InstallPipPackageWithFallback "%PIP_PACKAGE%"

    if errorlevel 1 exit /b 1

    "%PYTHON_EXE%" -c "import %IMPORT_NAME%" >> "%INSTALL_LOG%" 2>&1

    if errorlevel 1 exit /b 1

    call :StepInstalled "%STEP_NUMBER%" "%PIP_PACKAGE% installed"

    exit /b 0

)

echo %PIP_PACKAGE% already installed - checking updates...

call :InstallPipPackageWithFallback "%PIP_PACKAGE%"

if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -c "import %IMPORT_NAME%" >> "%INSTALL_LOG%" 2>&1

if errorlevel 1 exit /b 1

call :StepUpdated "%STEP_NUMBER%" "%PIP_PACKAGE% checked and updated if needed"

exit /b 0

:EnsureOptionalPipPackage

set "STEP_NUMBER=%~1"

set "PIP_PACKAGE=%~2"

set "IMPORT_NAME=%~3"

set "OPTIONAL_MESSAGE=%~4"

set "PACKAGE_WAS_INSTALLED="

set "PACKAGE_WAS_UPDATED="

"%PYTHON_EXE%" -c "import %IMPORT_NAME%" >> "%INSTALL_LOG%" 2>&1

if errorlevel 1 (

    echo %PIP_PACKAGE% not installed - installing...

    call :InstallPipPackageWithFallback "%PIP_PACKAGE%"

    if not errorlevel 1 (

        "%PYTHON_EXE%" -c "import %IMPORT_NAME%" >> "%INSTALL_LOG%" 2>&1

        if not errorlevel 1 (

            call :StepInstalled "%STEP_NUMBER%" "%PIP_PACKAGE% installed"

            exit /b 0

        )

    )

    >> "%INSTALL_LOG%" echo Optional package %PIP_PACKAGE% could not be installed after all fallback methods.

    set "OPTIONAL_PACKAGE_SKIPPED=1"

    call :StepUpdated "%STEP_NUMBER%" "%OPTIONAL_MESSAGE%"

    exit /b 0

)

echo %PIP_PACKAGE% already installed - checking updates...

call :InstallPipPackageWithFallback "%PIP_PACKAGE%"

if errorlevel 1 (

    >> "%INSTALL_LOG%" echo Optional package %PIP_PACKAGE% update failed. Keeping existing installation.

    call :StepAlready "%STEP_NUMBER%" "%PIP_PACKAGE% already installed - update failed, kept current"

    exit /b 0

)

"%PYTHON_EXE%" -c "import %IMPORT_NAME%" >> "%INSTALL_LOG%" 2>&1

if errorlevel 1 (

    >> "%INSTALL_LOG%" echo Optional package %PIP_PACKAGE% is no longer importable after update attempt.

    set "OPTIONAL_PACKAGE_SKIPPED=1"

    call :StepUpdated "%STEP_NUMBER%" "%OPTIONAL_MESSAGE%"

    exit /b 0

)

call :StepUpdated "%STEP_NUMBER%" "%PIP_PACKAGE% already installed - update checked"

exit /b 0

:EnsureHelperPackages

set "STEP_NUMBER=%~1"

call :InstallPipPackageWithFallback "rich"

if errorlevel 1 exit /b 1

call :InstallPipPackageWithFallback "textual"

if errorlevel 1 exit /b 1

call :InstallPipPackageWithFallback "browser-cookie3"

if errorlevel 1 exit /b 1

call :InstallPipPackageWithFallback "beautifulsoup4"

if errorlevel 1 exit /b 1

call :InstallPipPackageWithFallback "lxml"

if errorlevel 1 exit /b 1

call :InstallPipPackageWithFallback "mutagen"

if errorlevel 1 exit /b 1

call :InstallPipPackageWithFallback "selenium"

if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -c "import rich, textual, browser_cookie3, bs4, lxml, mutagen, selenium, sqlite3" >> "%INSTALL_LOG%" 2>&1

if errorlevel 1 exit /b 1

call :StepUpdated "%STEP_NUMBER%" "UI/helper libraries checked and updated"

exit /b 0

:InstallPipPackageWithFallback

set "PIP_PACKAGE=%~1"

call :InstallPipPackage "%PIP_PACKAGE%"

if not errorlevel 1 exit /b 0

echo %PIP_PACKAGE% primary install failed - trying fallback method 1...

>> "%INSTALL_LOG%" echo Fallback 1 for %PIP_PACKAGE%: prepare Python/VC++ and prefer binary wheels.

call :PreparePipFallback

if errorlevel 1 exit /b 1

call :InstallPipPackagePreferBinary "%PIP_PACKAGE%"

if not errorlevel 1 exit /b 0

echo %PIP_PACKAGE% fallback method 1 failed - trying fallback method 2...

>> "%INSTALL_LOG%" echo Fallback 2 for %PIP_PACKAGE%: user-site install with prefer-binary.

call :InstallPipPackageUser "%PIP_PACKAGE%"

if not errorlevel 1 exit /b 0

echo %PIP_PACKAGE% fallback method 2 failed - trying fallback method 3...

>> "%INSTALL_LOG%" echo Fallback 3 for %PIP_PACKAGE%: prefer binary wheels without target folder.

call :InstallPipPackageUserOnlyBinary "%PIP_PACKAGE%"

if not errorlevel 1 exit /b 0

>> "%INSTALL_LOG%" echo All fallback install methods failed for %PIP_PACKAGE%.

exit /b 1

:PreparePipFallback

call :EnsureFallbackPython

if errorlevel 1 exit /b 1

call :FindVcBuildTools

if not defined VC_BUILD_TOOLS_FOUND (

    call :InstallVcBuildTools

    call :FindVcBuildTools

)

call :UpdatePip

exit /b 0

:EnsureFallbackPython

if defined PYTHON_EXE (

    "%PYTHON_EXE%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] in [(3,10),(3,11),(3,12),(3,13)] else 1)" >nul 2>nul

    if not errorlevel 1 exit /b 0

)

>> "%INSTALL_LOG%" echo Current Python is incompatible for fallback. Installing/searching Python 3.12.

set "PYTHON_EXE="

call :InstallPython

call :FindPython

if defined PYTHON_EXE exit /b 0

exit /b 1

:InstallPipPackage

set "PIP_PACKAGE=%~1"

if "%DEBUG%"=="1" (

    "%PYTHON_EXE%" -m pip install --upgrade --target "%PYTHON_PACKAGE_DIR%" --no-input --disable-pip-version-check "%PIP_PACKAGE%"

) else (

    "%PYTHON_EXE%" -m pip install --upgrade --target "%PYTHON_PACKAGE_DIR%" --no-input --quiet --disable-pip-version-check "%PIP_PACKAGE%" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

:InstallPipPackagePreferBinary

set "PIP_PACKAGE=%~1"

if "%DEBUG%"=="1" (

    "%PYTHON_EXE%" -m pip install --upgrade --prefer-binary --target "%PYTHON_PACKAGE_DIR%" --no-input --disable-pip-version-check "%PIP_PACKAGE%"

) else (

    "%PYTHON_EXE%" -m pip install --upgrade --prefer-binary --target "%PYTHON_PACKAGE_DIR%" --no-input --quiet --disable-pip-version-check "%PIP_PACKAGE%" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

:InstallPipPackageUser

set "PIP_PACKAGE=%~1"

if "%DEBUG%"=="1" (

    "%PYTHON_EXE%" -m pip install --upgrade --prefer-binary --user --no-input --disable-pip-version-check "%PIP_PACKAGE%"

) else (

    "%PYTHON_EXE%" -m pip install --upgrade --prefer-binary --user --no-input --quiet --disable-pip-version-check "%PIP_PACKAGE%" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

:InstallPipPackageUserOnlyBinary

set "PIP_PACKAGE=%~1"

if "%DEBUG%"=="1" (

    "%PYTHON_EXE%" -m pip install --upgrade --prefer-binary --only-binary=:all: --user --no-input --disable-pip-version-check "%PIP_PACKAGE%"

) else (

    "%PYTHON_EXE%" -m pip install --upgrade --prefer-binary --only-binary=:all: --user --no-input --quiet --disable-pip-version-check "%PIP_PACKAGE%" >> "%INSTALL_LOG%" 2>&1

)

exit /b %ERRORLEVEL%

