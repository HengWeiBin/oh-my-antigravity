<#
.SYNOPSIS
    oh-my-antigravity Installer (Windows PowerShell)
.DESCRIPTION
    Installs or updates oh-my-antigravity plugin for Google Antigravity 2.0 with
    Python 3.13+ runtime pre-flight checks and idempotent git logic.
.LINK
    https://github.com/HengWeiBin/oh-my-antigravity
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/HengWeiBin/oh-my-antigravity.git"

function Write-Info {
    param([string]$Message)
    Write-Host "-> $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[+] $Message" -ForegroundColor Green
}

function Write-WarningMsg {
    param([string]$Message)
    Write-Host "[!] $Message" -ForegroundColor Yellow
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[x] $Message" -ForegroundColor Red
}

function Show-Banner {
    $bannerText = @'
   ___  __               __  __           ___         __  _                       __  __     
  / _ \/ /_  ____ __ _  / / / /_ _____   / _ | ___  / /_(_)__ ________ __  _____ / /_/ /_  __
 / // / _ \ /___// '  \/ /_/ / // /___/ / __ |/ _ \/ __/ / _ `/ __/ _ `/ |/ / // / __/ // / 
 \___/_//_/     /_/_/_/\____/\_, /     /_/ |_/_//_/\__/_/\_, /_/  \_,_/|___/\_, /\__/\_, /  
                            /___/                       /___/              /___/    /___/   
'@
    Write-Host $bannerText -ForegroundColor Cyan
    Write-Host "oh-my-antigravity - Release Readiness Installer" -ForegroundColor White
    Write-Host "Orchestration, Skills & Lifecycle Hooks for Google Antigravity 2.0" -ForegroundColor DarkGray
    Write-Host ""
}

function Resolve-TargetDir {
    if ($env:ANTIGRAVITY_PLUGINS_DIR) {
        if ($env:ANTIGRAVITY_PLUGINS_DIR.EndsWith("oh-my-antigravity", [System.StringComparison]::OrdinalIgnoreCase)) {
            return $env:ANTIGRAVITY_PLUGINS_DIR
        } else {
            return (Join-Path $env:ANTIGRAVITY_PLUGINS_DIR "oh-my-antigravity")
        }
    }

    $UserHome = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
    return (Join-Path $UserHome ".gemini\config\plugins\oh-my-antigravity")
}

function Test-Prerequisites {
    Write-Info "Running pre-flight environment checks..."

    # Check Git
    $gitCmd = Get-Command "git" -ErrorAction SilentlyContinue
    if (-not $gitCmd) {
        Write-ErrorMsg "git is required but was not found in PATH."
        Write-Host "  Please install Git for Windows before proceeding:" -ForegroundColor White
        Write-Host "    winget install Git.Git" -ForegroundColor Cyan
        Write-Host "    or download from https://git-scm.com/download/win" -ForegroundColor Cyan
        Write-Host ""
        exit 1
    }
    $gitVersion = (git --version 2>&1).Trim()
    Write-Success "Found git: $gitVersion"

    # Check Python >= 3.13 or uv
    $runtimeFound = $false
    $runtimeDesc = ""

    # Check uv
    $uvCmd = Get-Command "uv" -ErrorAction SilentlyContinue
    if ($uvCmd) {
        $uvVersion = (uv --version 2>&1).Trim()
        $runtimeFound = $true
        $runtimeDesc = $uvVersion
    }

    # Check py launcher (py -3.13)
    $pyCmd = Get-Command "py" -ErrorAction SilentlyContinue
    if ($pyCmd) {
        try {
            $pyOutput = & py -3.13 -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $pyOutput) {
                $runtimeFound = $true
                $desc = "py -3.13 (v$($pyOutput.Trim()))"
                $runtimeDesc = if ($runtimeDesc) { "$runtimeDesc + $desc" } else { $desc }
            }
        } catch {}
    }

    # Check python in PATH
    $pythonCmd = Get-Command "python" -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        try {
            $isV313 = & python -c "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $pyOutput = (& python -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}')" 2>$null).Trim()
                $runtimeFound = $true
                $desc = "python (v$pyOutput)"
                $runtimeDesc = if ($runtimeDesc) { "$runtimeDesc + $desc" } else { $desc }
            }
        } catch {}
    }

    # Check python3 in PATH
    $python3Cmd = Get-Command "python3" -ErrorAction SilentlyContinue
    if ($python3Cmd -and -not $runtimeFound) {
        try {
            $isV313 = & python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $pyOutput = (& python3 -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}')" 2>$null).Trim()
                $runtimeFound = $true
                $runtimeDesc = "python3 (v$pyOutput)"
            }
        } catch {}
    }

    if (-not $runtimeFound) {
        Write-ErrorMsg "Python >= 3.13 or uv is required to run oh-my-antigravity hooks."

        # Detect current version if present
        $currentPy = ""
        try {
            $currentPy = (python --version 2>&1).Trim()
        } catch {}

        if ($currentPy) {
            Write-Host "  Currently detected: $currentPy (requires >= 3.13)" -ForegroundColor DarkGray
            Write-Host ""
        } else {
            Write-Host "  No Python installation found in PATH." -ForegroundColor DarkGray
            Write-Host ""
        }

        Write-Host "  Recommended resolution:" -ForegroundColor White
        Write-Host "    1. Install uv (ultra-fast package & tool manager):" -ForegroundColor White
        Write-Host "       winget install astral-sh.uv" -ForegroundColor Cyan
        Write-Host '       or: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"' -ForegroundColor Cyan
        Write-Host "    2. Or install Python 3.13+ directly:" -ForegroundColor White
        Write-Host "       winget install Python.Python.3.13" -ForegroundColor Cyan
        Write-Host "       or download from https://www.python.org/downloads/" -ForegroundColor Cyan
        Write-Host ""
        exit 1
    }

    Write-Success "Found runtime prerequisite: $runtimeDesc"
}

function Install-OrUpdate {
    param([string]$TargetDir)

    if (Test-Path $TargetDir) {
        $gitDir = Join-Path $TargetDir ".git"
        if (Test-Path $gitDir) {
            Write-Info "Existing installation detected at: $TargetDir"
            $hasRemote = (git -C "$TargetDir" remote 2>$null)
            if ($hasRemote) {
                Write-Info "Updating repository via git pull --ff-only..."
                $prevEAP = $ErrorActionPreference
                $ErrorActionPreference = "SilentlyContinue"
                git -C "$TargetDir" pull --ff-only
                $pullExitCode = $LASTEXITCODE
                $ErrorActionPreference = $prevEAP

                if ($pullExitCode -eq 0) {
                    Write-Success "Repository updated successfully."
                } else {
                    Write-WarningMsg "git pull --ff-only returned exit code $pullExitCode. Local modifications or diverge may exist."
                }
            } else {
                Write-Info "Local repository detected. Skipping remote pull."
            }
        } else {
            Write-ErrorMsg "Target directory already exists but is not a Git repository:"
            Write-Host "  $TargetDir" -ForegroundColor White
            Write-Host "  Please remove or back up this directory, then run the installer again." -ForegroundColor Yellow
            Write-Host ""
            exit 1
        }
    } else {
        $parentDir = Split-Path $TargetDir -Parent
        if (-not (Test-Path $parentDir)) {
            Write-Info "Creating plugin directory tree: $parentDir"
            New-Item -ItemType Directory -Force -Path $parentDir | Out-Null
        }

        Write-Info "Cloning oh-my-antigravity repository into:"
        Write-Host "  $TargetDir" -ForegroundColor White
        git clone $RepoUrl "$TargetDir"
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMsg "git clone failed. Please check network connection and permissions."
            exit 1
        }
        Write-Success "Repository cloned successfully."
    }
}

function Verify-Installation {
    param([string]$TargetDir)

    Write-Info "Verifying plugin integrity..."

    $pluginJson = Join-Path $TargetDir "plugin.json"
    $hooksJson = Join-Path $TargetDir "hooks.json"

    $missing = @()
    if (-not (Test-Path $pluginJson)) { $missing += "plugin.json" }
    if (-not (Test-Path $hooksJson)) { $missing += "hooks.json" }

    if ($missing.Count -gt 0) {
        Write-ErrorMsg "Integrity check failed! Missing essential files: $($missing -join ', ')"
        exit 1
    }

    Write-Success "Integrity check passed (plugin.json and hooks.json present)."
}

function Show-Success {
    param([string]$TargetDir)

    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host "  * oh-my-antigravity is successfully installed! *" -ForegroundColor Green
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Install Location: $TargetDir" -ForegroundColor White
    Write-Host "  Version:          0.1.0" -ForegroundColor White
    Write-Host "  Status:           Ready for Google Antigravity 2.0" -ForegroundColor White
    Write-Host ""

    Write-Host "Next Steps:" -ForegroundColor White
    Write-Host "  1. Start or restart Google Antigravity to load the plugin." -ForegroundColor White
    Write-Host "  2. Verify installed plugins via Antigravity CLI:" -ForegroundColor White
    Write-Host "     agy plugin list" -ForegroundColor Cyan
    Write-Host "  3. Or inspect in GUI: Settings -> Customizations -> Plugins" -ForegroundColor White
    Write-Host '  4. Try invoking subagents (e.g. @Atlas, @Prometheus, @Hephaestus)' -ForegroundColor White
    Write-Host "     or explore bundled skills in skills/." -ForegroundColor White
    Write-Host ""

    Write-Host "Repository & Docs: https://github.com/HengWeiBin/oh-my-antigravity" -ForegroundColor DarkGray
    Write-Host ""
}

function Main {
    Show-Banner
    $targetDir = Resolve-TargetDir
    Test-Prerequisites
    Install-OrUpdate -TargetDir $targetDir
    Verify-Installation -TargetDir $targetDir
    Show-Success -TargetDir $targetDir
}

Main
