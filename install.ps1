param(
    [string]$InstallDir = "$env:ProgramFiles\VideoDownloader",
    [string]$Repo = "needowsky/VideoDownloader",
    [string]$Branch = "main",
    [ValidateSet("exe", "branch", "release")]
    [string]$DownloadMode = "exe",
    [ValidateSet("en", "pl")]
    [string]$Lang = "en",
    [switch]$Debug,
    [switch]$NoRun,
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$InstallerName = "zainstaluj_wszystko.bat"
$ExeInstallerNamePattern = "VideoDownloader_AIO_Installer*.exe"
$LogRoot = Join-Path $env:TEMP "VideoDownloaderInstallLogs"
$LogPath = Join-Path $LogRoot ("install_ps1_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
$LatestLogPath = Join-Path $LogRoot "install_ps1_latest.log"
$RunningFromFile = [bool]$PSCommandPath
$WorkDir = Join-Path $env:TEMP ("VideoDownloaderInstall_" + [guid]::NewGuid().ToString("N"))
$InstallerPath = Join-Path $WorkDir $InstallerName
$ExeInstallerPath = Join-Path $WorkDir "VideoDownloader_AIO_Installer.exe"

New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

function Write-Log {
    param([string]$Message)

    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::AppendAllText($LogPath, $line + [Environment]::NewLine, $utf8NoBom)
    Copy-Item -Force -LiteralPath $LogPath -Destination $LatestLogPath -ErrorAction SilentlyContinue
}

function Write-ScreenLog {
    param([string]$Message)

    Write-Host $Message
    Write-Log $Message
}

function Write-Step {
    param(
        [int]$Step,
        [int]$Total,
        [string]$Message
    )

    $percent = [int](($Step / [Math]::Max($Total, 1)) * 100)
    Write-ScreenLog ("[{0,3}%] Step {1}/{2} - {3}" -f $percent, $Step, $Total, $Message)
}

function Save-LogCopyToInstallDir {
    try {
        $targetLogDir = Join-Path $InstallDir "logs"
        New-Item -ItemType Directory -Force -Path $targetLogDir | Out-Null
        Copy-Item -Force -LiteralPath $LogPath -Destination (Join-Path $targetLogDir "install_ps1_latest.log")
    } catch {
        Write-Log ("Could not copy bootstrap log to install folder: " + $_.Exception.Message)
    }
}

function Wait-IfFileLaunch {
    param([bool]$HadError)

    if ($NoPause -or -not $RunningFromFile) {
        return
    }

    Write-Host ""
    if ($HadError) {
        Write-Host "Installer failed. Log saved in: $LogPath"
    } else {
        Write-Host "Installer finished. Log saved in: $LogPath"
    }
    Read-Host "Press Enter to close this window"
}

function Invoke-Download {
    param(
        [string]$Url,
        [string]$OutFile
    )

    try {
        Invoke-WebRequest `
            -UseBasicParsing `
            -Headers @{ "User-Agent" = "VideoDownloaderPowerShellInstaller" } `
            -Uri $Url `
            -OutFile $OutFile
    } catch {
        Write-Log ("Invoke-WebRequest failed for $Url. Trying WebClient fallback. Error: " + $_.Exception.Message)
        $client = New-Object Net.WebClient
        $client.Headers.Add("User-Agent", "VideoDownloaderPowerShellInstaller")
        $client.DownloadFile($Url, $OutFile)
    }
}

function Copy-InstallerFromDirectory {
    param([string]$SourceDir)

    $source = Get-ChildItem -Path $SourceDir -Recurse -File -Filter $InstallerName | Select-Object -First 1
    if (-not $source) {
        throw "Missing $InstallerName in downloaded package."
    }
    Copy-Item -Force -LiteralPath $source.FullName -Destination $InstallerPath
}

function Get-VersionNumbers {
    param([string]$Value)

    $numbers = @([regex]::Matches([string]$Value, "\d+") | ForEach-Object { [int]$_.Value })
    if ($numbers.Count -eq 0) {
        return @()
    }
    return $numbers
}

function Get-VersionKey {
    param([string]$Value)

    $numbers = Get-VersionNumbers $Value
    if ($numbers.Count -eq 0) {
        return $null
    }
    return (($numbers | ForEach-Object { $_.ToString("D8") }) -join ".")
}

function Test-AppRelease {
    param($Release)

    $tag = [string]$Release.tag_name
    $name = [string]$Release.name
    return (($tag -notmatch "^\s*EXE[\s_-]+v?\d") -and ($name -notmatch "^\s*EXE[\s_-]+v?\d"))
}

function Test-ExeRelease {
    param($Release)

    $tag = [string]$Release.tag_name
    $name = [string]$Release.name
    return (($tag -match "^\s*EXE[\s_-]+v?\d") -or ($name -match "^\s*EXE[\s_-]+v?\d"))
}

function Get-HighestVersionRelease {
    param(
        $Releases,
        [switch]$Exe
    )

    $candidates = @()
    foreach ($release in $Releases) {
        if ($release.draft -or $release.prerelease) {
            continue
        }
        $matchesType = if ($Exe) { Test-ExeRelease $release } else { Test-AppRelease $release }
        if (-not $matchesType) {
            continue
        }

        $label = [string]$release.tag_name
        if ($label -notmatch "\d") {
            $label = [string]$release.name
        }
        $key = Get-VersionKey $label
        if ($key) {
            $candidates += [pscustomobject]@{
                Key = $key
                Release = $release
            }
        }
    }

    if (-not $candidates) {
        return $null
    }
    return ($candidates | Sort-Object Key -Descending | Select-Object -First 1).Release
}

function Get-BestExeAsset {
    param($Release)

    $assets = @($Release.assets)
    if (-not $assets) {
        return $null
    }

    $ranked = foreach ($asset in $assets) {
        $name = [string]$asset.name
        if (-not $asset.browser_download_url) {
            continue
        }
        $score = 0
        if ($name -like "*.exe") { $score += 100 }
        if ($name -like "*.zip") { $score += 70 }
        if ($name -match "AIO") { $score += 20 }
        if ($name -match "Installer") { $score += 20 }
        if ($name -match "VideoDownloader") { $score += 10 }
        if ($score -gt 0) {
            [pscustomobject]@{
                Score = $score
                Asset = $asset
            }
        }
    }

    return ($ranked | Sort-Object Score -Descending | Select-Object -First 1).Asset
}

function Expand-ExeAssetIfNeeded {
    param([string]$AssetPath)

    if ($AssetPath.ToLowerInvariant().EndsWith(".exe")) {
        return $AssetPath
    }
    if (-not $AssetPath.ToLowerInvariant().EndsWith(".zip")) {
        throw "Downloaded installer asset is not an EXE or ZIP: $AssetPath"
    }

    $extractPath = Join-Path $WorkDir "exe_asset"
    if (Test-Path $extractPath) {
        Remove-Item -Recurse -Force -LiteralPath $extractPath
    }
    New-Item -ItemType Directory -Force -Path $extractPath | Out-Null
    Expand-Archive -Force -Path $AssetPath -DestinationPath $extractPath
    $exe = Get-ChildItem -Path $extractPath -Recurse -File -Filter "*.exe" |
        Where-Object { $_.Name -like $ExeInstallerNamePattern -or $_.Name -match "AIO|Installer|VideoDownloader" } |
        Sort-Object @{ Expression = { if ($_.Name -like $ExeInstallerNamePattern) { 0 } else { 1 } } }, Length -Descending |
        Select-Object -First 1
    if (-not $exe) {
        throw "Downloaded EXE ZIP does not contain a Video Downloader installer."
    }
    return $exe.FullName
}

function Try-DownloadLatestExeInstaller {
    try {
        $apiUrl = "https://api.github.com/repos/$Repo/releases?per_page=50"
        Write-Log "Checking GitHub EXE releases by version: $apiUrl"
        $releases = Invoke-RestMethod -Headers @{ "User-Agent" = "VideoDownloaderPowerShellInstaller" } -Uri $apiUrl
        $release = Get-HighestVersionRelease -Releases $releases -Exe
        if (-not $release) {
            throw "No versioned EXE installer release found."
        }

        $asset = Get-BestExeAsset -Release $release
        if (-not $asset) {
            throw "Selected EXE release has no installer EXE/ZIP asset."
        }

        $assetName = [string]$asset.name
        $assetPath = Join-Path $WorkDir $assetName
        Write-ScreenLog "Installer release: $($release.tag_name)"
        Write-ScreenLog "Installer asset:   $assetName"
        Invoke-Download -Url $asset.browser_download_url -OutFile $assetPath
        $resolvedExe = Expand-ExeAssetIfNeeded -AssetPath $assetPath
        Copy-Item -Force -LiteralPath $resolvedExe -Destination $ExeInstallerPath
        return $true
    } catch {
        Write-ScreenLog "EXE release download failed: $($_.Exception.Message)"
        return $false
    }
}

function Try-DownloadLatestReleaseInstaller {
    try {
        $apiUrl = "https://api.github.com/repos/$Repo/releases?per_page=50"
        Write-Log "Checking GitHub releases by version: $apiUrl"
        $releases = Invoke-RestMethod -Headers @{ "User-Agent" = "VideoDownloaderPowerShellInstaller" } -Uri $apiUrl
        $release = Get-HighestVersionRelease $releases
        if (-not $release) {
            throw "No versioned application release found."
        }

        $asset = $release.assets | Where-Object { $_.name -ieq $InstallerName } | Select-Object -First 1
        if ($asset) {
            Invoke-Download -Url $asset.browser_download_url -OutFile $InstallerPath
            return $true
        }

        if (-not $release.zipball_url) {
            throw "Selected release does not contain $InstallerName or source zip."
        }

        $zipPath = Join-Path $WorkDir "release.zip"
        $extractPath = Join-Path $WorkDir "release"
        Invoke-Download -Url $release.zipball_url -OutFile $zipPath
        Expand-Archive -Force -Path $zipPath -DestinationPath $extractPath
        Copy-InstallerFromDirectory -SourceDir $extractPath
        return $true
    } catch {
        Write-ScreenLog "Release download failed: $($_.Exception.Message)"
        return $false
    }
}

function Try-DownloadRawInstaller {
    param([string]$RawBranch)

    try {
        $url = "https://raw.githubusercontent.com/$Repo/$RawBranch/$InstallerName"
        Write-Log "Downloading raw installer: $url"
        Invoke-Download -Url $url -OutFile $InstallerPath
        $head = Get-Content -LiteralPath $InstallerPath -TotalCount 1 -ErrorAction Stop
        if ($head -notmatch '(@echo off|setlocal|::)') {
            throw "Downloaded file does not look like a batch installer."
        }
        return $true
    } catch {
        Write-ScreenLog "Raw branch '$RawBranch' failed: $($_.Exception.Message)"
        return $false
    }
}

function Start-ExeInstaller {
    $env:INSTALL_DIR = $InstallDir
    $env:GITHUB_REPO = $Repo
    $env:GITHUB_BRANCH = $Branch
    $env:DEBUG = if ($Debug) { "1" } else { "0" }
    $env:LANG = $Lang

    if ($NoRun) {
        Write-ScreenLog "NoRun enabled. EXE installer downloaded to: $ExeInstallerPath"
        return
    }

    Write-ScreenLog "Opening preferred EXE installer..."
    Write-ScreenLog "Continue installation in the installer window."
    Write-Log "Starting EXE installer: $ExeInstallerPath"
    Start-Process -FilePath $ExeInstallerPath -WorkingDirectory $WorkDir | Out-Null
    Write-Log "EXE installer started."
}

function Update-InstallerSettings {
    $text = Get-Content -Raw -LiteralPath $InstallerPath
    $debugValue = if ($Debug) { "1" } else { "0" }
    $text = $text -replace 'set "DEBUG=[01]"', ('set "DEBUG=' + $debugValue + '"')
    $text = $text -replace 'set "LANG=(en|pl)"', ('set "LANG=' + $Lang + '"')
    $text = $text -replace 'set "GITHUB_REPO=[^"]+"', ('set "GITHUB_REPO=' + $Repo + '"')
    $text = $text -replace 'set "GITHUB_DOWNLOAD_MODE=[^"]+"', ('set "GITHUB_DOWNLOAD_MODE=' + $DownloadMode + '"')
    $text = $text -replace 'set "GITHUB_BRANCH=[^"]+"', ('set "GITHUB_BRANCH=' + $Branch + '"')
    $text = $text -replace 'if not defined INSTALL_DIR set "INSTALL_DIR=[^"]+"', ('if not defined INSTALL_DIR set "INSTALL_DIR=' + $InstallDir + '"')

    $text = $text -replace "`r?`n", "`r`n"
    $encoding = New-Object System.Text.ASCIIEncoding
    [System.IO.File]::WriteAllText($InstallerPath, $text, $encoding)
}

function Start-AioInstaller {
    $env:INSTALL_DIR = $InstallDir
    $env:GITHUB_REPO = $Repo
    $env:GITHUB_BRANCH = $Branch

    if ($NoRun) {
        Write-ScreenLog "NoRun enabled. Installer downloaded to: $InstallerPath"
        return
    }

    $needsAdmin = ($InstallDir -like "$env:ProgramFiles*") -and -not (Test-IsAdministrator)
    if ($needsAdmin) {
        Write-ScreenLog "Opening AIO installer in administrator window..."
        Write-ScreenLog "Continue installation in the new administrator window."
        Write-Log "Starting AIO installer with UAC elevation."
        $arguments = "/c `"$InstallerPath`""
        Start-Process -FilePath "cmd.exe" -ArgumentList $arguments -WorkingDirectory $WorkDir -Verb RunAs | Out-Null
        Write-Log "AIO installer was handed off to administrator window."
        return
    }

    Write-ScreenLog "Starting AIO installer..."
    & cmd.exe /c "`"$InstallerPath`""
    Write-Log ("AIO installer exited with code: " + $LASTEXITCODE)
    if ($LASTEXITCODE -ne 0) {
        throw "AIO installer failed with exit code $LASTEXITCODE."
    }
}

function Test-IsAdministrator {
    try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($identity)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        Write-Log ("Administrator check failed: " + $_.Exception.Message)
        return $false
    }
}

$hadError = $false
try {
    Write-Log "Video Downloader PowerShell Installer started."
    Write-ScreenLog "==============================================="
    Write-ScreenLog " Video Downloader PowerShell Installer"
    Write-ScreenLog "==============================================="
    Write-ScreenLog "Repository: $Repo"
    Write-ScreenLog "Source:     $DownloadMode"
    Write-ScreenLog "Target:     $InstallDir"
    Write-ScreenLog "Language:   $Lang"
    Write-ScreenLog "Log:        $LogPath"
    if ($InstallDir -like "$env:ProgramFiles*") {
        if (Test-IsAdministrator) {
            Write-ScreenLog "Permission: Administrator"
        } else {
            Write-ScreenLog "Permission: Standard user - Windows may ask for administrator permission."
        }
    }
    Write-ScreenLog ""

    New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

    Write-Step 1 4 "Preparing installer workspace"
    Write-ScreenLog "Workspace: $WorkDir"

    Write-Step 2 4 "Downloading installer from GitHub"
    $downloaded = $false
    $usingExe = $false
    if ($DownloadMode -ieq "exe") {
        $downloaded = Try-DownloadLatestExeInstaller
        $usingExe = $downloaded
        if (-not $downloaded) {
            Write-ScreenLog "Falling back to batch installer from main branch..."
            $downloaded = Try-DownloadRawInstaller -RawBranch $Branch
        }
        if (-not $downloaded -and $Branch -ine "master") {
            $downloaded = Try-DownloadRawInstaller -RawBranch "master"
        }
        if (-not $downloaded) {
            $downloaded = Try-DownloadLatestReleaseInstaller
        }
    } elseif ($DownloadMode -ieq "branch") {
        $downloaded = Try-DownloadRawInstaller -RawBranch $Branch
        if (-not $downloaded -and $Branch -ine "master") {
            $downloaded = Try-DownloadRawInstaller -RawBranch "master"
        }
        if (-not $downloaded) {
            $downloaded = Try-DownloadLatestReleaseInstaller
        }
    } else {
        $downloaded = Try-DownloadLatestReleaseInstaller
        if (-not $downloaded) {
            $downloaded = Try-DownloadRawInstaller -RawBranch $Branch
        }
        if (-not $downloaded -and $Branch -ine "master") {
            $downloaded = Try-DownloadRawInstaller -RawBranch "master"
        }
    }
    if (-not $downloaded) {
        throw "Cannot download installer from GitHub. Check internet connection, repository visibility and release files."
    }

    if ($usingExe) {
        Write-Step 3 4 "Preparing EXE installer settings"
        Write-Log "EXE installer will receive settings through environment variables."

        Write-Step 4 4 "Opening preferred EXE installer"
        Start-ExeInstaller
    } else {
        Write-Step 3 4 "Applying batch installer settings"
        Update-InstallerSettings

        Write-Step 4 4 "Opening full batch installer"
        Start-AioInstaller
    }
    Save-LogCopyToInstallDir
} catch {
    $hadError = $true
    Write-Host ""
    Write-Host "[ERROR] $($_.Exception.Message)"
    Write-Log ("ERROR: " + $_.Exception.Message)
    Write-Log ($_.ScriptStackTrace | Out-String)
    Save-LogCopyToInstallDir
    exit 1
} finally {
    Copy-Item -Force -LiteralPath $LogPath -Destination $LatestLogPath -ErrorAction SilentlyContinue
    Wait-IfFileLaunch -HadError $hadError
}
