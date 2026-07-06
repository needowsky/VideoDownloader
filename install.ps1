param(
    [string]$InstallDir = "$env:ProgramFiles\VideoDownloader",
    [string]$Repo = "needowsky/VideoDownloader",
    [string]$Branch = "main",
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
$LogRoot = Join-Path $env:TEMP "VideoDownloaderInstallLogs"
$LogPath = Join-Path $LogRoot ("install_ps1_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
$LatestLogPath = Join-Path $LogRoot "install_ps1_latest.log"
$RunningFromFile = [bool]$PSCommandPath
$WorkDir = Join-Path $env:TEMP ("VideoDownloaderInstall_" + [guid]::NewGuid().ToString("N"))
$InstallerPath = Join-Path $WorkDir $InstallerName

New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

function Write-Log {
    param([string]$Message)

    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
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

function Try-DownloadLatestReleaseInstaller {
    try {
        $apiUrl = "https://api.github.com/repos/$Repo/releases/latest"
        Write-Log "Checking latest GitHub release: $apiUrl"
        $release = Invoke-RestMethod -Headers @{ "User-Agent" = "VideoDownloaderPowerShellInstaller" } -Uri $apiUrl

        $asset = $release.assets | Where-Object { $_.name -ieq $InstallerName } | Select-Object -First 1
        if ($asset) {
            Invoke-Download -Url $asset.browser_download_url -OutFile $InstallerPath
            return $true
        }

        if (-not $release.zipball_url) {
            throw "Latest release does not contain $InstallerName or source zip."
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
        return $true
    } catch {
        Write-ScreenLog "Raw branch '$RawBranch' failed: $($_.Exception.Message)"
        return $false
    }
}

function Update-InstallerSettings {
    $text = Get-Content -Raw -LiteralPath $InstallerPath
    $debugValue = if ($Debug) { "1" } else { "0" }
    $text = $text -replace 'set "DEBUG=[01]"', ('set "DEBUG=' + $debugValue + '"')
    $text = $text -replace 'set "LANG=(en|pl)"', ('set "LANG=' + $Lang + '"')
    $text = $text -replace 'set "GITHUB_REPO=[^"]+"', ('set "GITHUB_REPO=' + $Repo + '"')
    $text = $text -replace 'set "GITHUB_DOWNLOAD_MODE=[^"]+"', 'set "GITHUB_DOWNLOAD_MODE=branch"'
    $text = $text -replace 'set "GITHUB_BRANCH=[^"]+"', ('set "GITHUB_BRANCH=' + $Branch + '"')
    $text = $text -replace 'if not defined INSTALL_DIR set "INSTALL_DIR=[^"]+"', ('if not defined INSTALL_DIR set "INSTALL_DIR=' + $InstallDir + '"')

    Set-Content -LiteralPath $InstallerPath -Value $text -Encoding UTF8
}

function Start-AioInstaller {
    $env:INSTALL_DIR = $InstallDir

    if ($NoRun) {
        Write-ScreenLog "NoRun enabled. Installer downloaded to: $InstallerPath"
        return
    }

    Write-ScreenLog "Starting AIO installer..."
    & cmd.exe /c "`"$InstallerPath`""
    Write-Log ("AIO installer exited with code: " + $LASTEXITCODE)
}

$hadError = $false
try {
    Write-Log "Video Downloader PowerShell Installer started."
    Write-ScreenLog "==============================================="
    Write-ScreenLog " Video Downloader PowerShell Installer"
    Write-ScreenLog "==============================================="
    Write-ScreenLog "Repository: $Repo"
    Write-ScreenLog "Target:     $InstallDir"
    Write-ScreenLog "Language:   $Lang"
    Write-ScreenLog "Log:        $LogPath"
    Write-ScreenLog ""

    New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

    Write-Step 1 4 "Preparing installer workspace"
    Write-ScreenLog "Workspace: $WorkDir"

    Write-Step 2 4 "Downloading AIO installer from GitHub"
    $downloaded = Try-DownloadLatestReleaseInstaller
    if (-not $downloaded) {
        $downloaded = Try-DownloadRawInstaller -RawBranch $Branch
    }
    if (-not $downloaded -and $Branch -ine "master") {
        $downloaded = Try-DownloadRawInstaller -RawBranch "master"
    }
    if (-not $downloaded) {
        throw "Cannot download $InstallerName from GitHub. Check internet connection, repository visibility and release files."
    }

    Write-Step 3 4 "Applying installer settings"
    Update-InstallerSettings

    Write-Step 4 4 "Launching full installer"
    Start-AioInstaller
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
