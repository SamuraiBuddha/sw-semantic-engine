#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Developer install script for SolidWorks Semantic Engine.

.DESCRIPTION
    Performs all setup steps:
      1. Check prerequisites (Python 3.10+, SolidWorks, Ollama, MSBuild, RegAsm)
      2. Create Python venv and install requirements
      3. NuGet restore + MSBuild Release build
      4. RegAsm /codebase on output DLL
      5. Create Ollama model (if not already present)
      6. Generate swse-config.json next to the DLL
      7. Print summary

.NOTES
    Run from an elevated PowerShell prompt at the project root.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$AddinDir    = Join-Path $ProjectRoot "addin"
$OutputDir   = Join-Path $AddinDir "bin\Release"
$DllName     = "SolidWorksSemanticEngine.dll"
$DllPath     = Join-Path $OutputDir $DllName

# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------

function Write-Step {
    param([int]$Number, [string]$Message)
    Write-Host ""
    Write-Host "=== Step $Number : $Message ===" -ForegroundColor Cyan
}

function Find-OllamaExe {
    # Check common install location first
    $localApp = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    if (Test-Path $localApp) { return $localApp }

    # Fall back to PATH
    $found = Get-Command "ollama" -ErrorAction SilentlyContinue
    if ($found) { return $found.Source }

    return $null
}

function Find-MSBuild {
    # VS 2022 (all editions)
    $vs2022Paths = @(
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
    )
    foreach ($p in $vs2022Paths) {
        if (Test-Path $p) { return $p }
    }

    # VS 2019
    $vs2019Paths = @(
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
    )
    foreach ($p in $vs2019Paths) {
        if (Test-Path $p) { return $p }
    }

    # PATH fallback
    $found = Get-Command "MSBuild.exe" -ErrorAction SilentlyContinue
    if ($found) { return $found.Source }

    return $null
}

function Find-RegAsm {
    # .NET Framework 4.x RegAsm
    $fxDir = Join-Path $env:windir "Microsoft.NET\Framework64\v4.0.30319"
    $regasm = Join-Path $fxDir "RegAsm.exe"
    if (Test-Path $regasm) { return $regasm }

    # 32-bit fallback
    $fxDir32 = Join-Path $env:windir "Microsoft.NET\Framework\v4.0.30319"
    $regasm32 = Join-Path $fxDir32 "RegAsm.exe"
    if (Test-Path $regasm32) { return $regasm32 }

    return $null
}

function Find-NuGet {
    $found = Get-Command "nuget" -ErrorAction SilentlyContinue
    if ($found) { return $found.Source }

    # Check common download location
    $local = Join-Path $ProjectRoot "nuget.exe"
    if (Test-Path $local) { return $local }

    return $null
}

# --------------------------------------------------------------------------
# Step 1: Check prerequisites
# --------------------------------------------------------------------------
Write-Step 1 "Checking prerequisites"

$failures = @()

# Python 3.10+
$pythonCmd = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $failures += "Python not found in PATH"
} else {
    $pyVer = & python --version 2>&1
    if ($pyVer -match "(\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            $failures += "Python 3.10+ required (found $pyVer)"
        } else {
            Write-Host "[OK] Python $pyVer" -ForegroundColor Green
        }
    }
}

# SolidWorks
$swPath = "${env:ProgramFiles}\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe"
if (Test-Path $swPath) {
    Write-Host "[OK] SolidWorks found" -ForegroundColor Green
} else {
    $failures += "SolidWorks not found at expected location"
}

# Ollama
$ollamaExe = Find-OllamaExe
if ($ollamaExe) {
    Write-Host "[OK] Ollama found: $ollamaExe" -ForegroundColor Green
} else {
    $failures += "Ollama not found. Install from https://ollama.com"
}

# MSBuild
$msbuild = Find-MSBuild
if ($msbuild) {
    Write-Host "[OK] MSBuild found: $msbuild" -ForegroundColor Green
} else {
    $failures += "MSBuild not found. Install Visual Studio or Build Tools"
}

# RegAsm
$regasm = Find-RegAsm
if ($regasm) {
    Write-Host "[OK] RegAsm found: $regasm" -ForegroundColor Green
} else {
    $failures += "RegAsm not found (.NET Framework 4.x required)"
}

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "[FAIL] Missing prerequisites:" -ForegroundColor Red
    foreach ($f in $failures) {
        Write-Host "  - $f" -ForegroundColor Red
    }
    exit 1
}

# --------------------------------------------------------------------------
# Step 2: Create Python venv and install requirements
# --------------------------------------------------------------------------
Write-Step 2 "Creating Python virtual environment"

$venvDir = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $venvDir)) {
    & python -m venv $venvDir
    Write-Host "[OK] Created venv at $venvDir" -ForegroundColor Green
} else {
    Write-Host "[OK] Venv already exists at $venvDir" -ForegroundColor Green
}

$venvPip = Join-Path $venvDir "Scripts\pip.exe"
$reqFile = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path $reqFile) {
    Write-Host "Installing requirements..."
    & $venvPip install -r $reqFile --quiet
    Write-Host "[OK] Requirements installed" -ForegroundColor Green
} else {
    Write-Host "[WARN] No requirements.txt found, skipping pip install" -ForegroundColor Yellow
}

# --------------------------------------------------------------------------
# Step 3: NuGet restore + MSBuild Release build
# --------------------------------------------------------------------------
Write-Step 3 "Building add-in (Release)"

$csproj = Join-Path $AddinDir "SolidWorksSemanticEngine.csproj"

# Attempt NuGet restore
$nuget = Find-NuGet
if ($nuget) {
    Write-Host "Running NuGet restore..."
    & $nuget restore $csproj -NonInteractive
} else {
    Write-Host "[WARN] nuget.exe not found -- skipping explicit restore." -ForegroundColor Yellow
    Write-Host "  MSBuild PackageReference restore should handle it." -ForegroundColor Yellow
}

Write-Host "Building with MSBuild..."
& $msbuild $csproj /p:Configuration=Release /p:Platform=AnyCPU /t:Build /v:minimal /restore
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] MSBuild failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Build succeeded" -ForegroundColor Green

# --------------------------------------------------------------------------
# Step 4: RegAsm /codebase
# --------------------------------------------------------------------------
Write-Step 4 "Registering COM add-in with RegAsm"

if (-not (Test-Path $DllPath)) {
    Write-Host "[FAIL] DLL not found at $DllPath" -ForegroundColor Red
    exit 1
}

& $regasm /codebase $DllPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] RegAsm failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] COM registration succeeded" -ForegroundColor Green

# --------------------------------------------------------------------------
# Step 5: Create Ollama model
# --------------------------------------------------------------------------
Write-Step 5 "Creating Ollama model"

$modelfile = Join-Path $ProjectRoot "Modelfile"
if (-not (Test-Path $modelfile)) {
    Write-Host "[WARN] No Modelfile found, skipping model creation" -ForegroundColor Yellow
} else {
    # Check if model already exists
    $existingModels = & $ollamaExe list 2>&1
    if ($existingModels -match "sw-semantic-7b") {
        Write-Host "[OK] Model sw-semantic-7b already exists" -ForegroundColor Green
    } else {
        Write-Host "Creating model sw-semantic-7b (this may take a while)..."
        & $ollamaExe create sw-semantic-7b -f $modelfile
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARN] ollama create returned non-zero exit code" -ForegroundColor Yellow
        } else {
            Write-Host "[OK] Model created" -ForegroundColor Green
        }
    }
}

# --------------------------------------------------------------------------
# Step 6: Generate swse-config.json
# --------------------------------------------------------------------------
Write-Step 6 "Generating swse-config.json"

$config = @{
    projectRoot      = $ProjectRoot
    pythonVenvPath    = ".venv"
    ollamaExePath    = $ollamaExe
    backendPort      = 8000
    ollamaPort       = 11434
    autoLaunchBackend = $true
    autoLaunchOllama  = $true
    killOnDisconnect  = $true
    startupTimeoutMs  = 15000
}

$configJson = $config | ConvertTo-Json -Depth 4
$configPath = Join-Path $OutputDir "swse-config.json"
Set-Content -Path $configPath -Value $configJson -Encoding UTF8
Write-Host "[OK] Config written to $configPath" -ForegroundColor Green

# --------------------------------------------------------------------------
# Step 7: Summary
# --------------------------------------------------------------------------
Write-Step 7 "Installation complete"

Write-Host ""
Write-Host "  Project root  : $ProjectRoot" -ForegroundColor White
Write-Host "  Python venv   : $venvDir" -ForegroundColor White
Write-Host "  DLL           : $DllPath" -ForegroundColor White
Write-Host "  Config        : $configPath" -ForegroundColor White
Write-Host "  Ollama        : $ollamaExe" -ForegroundColor White
Write-Host ""
Write-Host "Open SolidWorks -- the Semantic Engine add-in should load" -ForegroundColor Green
Write-Host "automatically and start the backend services." -ForegroundColor Green
Write-Host ""
