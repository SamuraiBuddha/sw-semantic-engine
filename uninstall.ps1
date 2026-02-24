#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Uninstall script for SolidWorks Semantic Engine.

.DESCRIPTION
    Removes the COM registration and optionally deletes the Python venv.
      1. RegAsm /u on the DLL
      2. Remove SolidWorks registry key
      3. Optionally remove .venv

.PARAMETER RemoveVenv
    If specified, also removes the .venv directory.

.NOTES
    Run from an elevated PowerShell prompt at the project root.
#>

[CmdletBinding()]
param(
    [switch]$RemoveVenv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$OutputDir   = Join-Path $ProjectRoot "addin\bin\Release"
$DllPath     = Join-Path $OutputDir "SolidWorksSemanticEngine.dll"

# --------------------------------------------------------------------------
# Find RegAsm
# --------------------------------------------------------------------------
function Find-RegAsm {
    $fxDir = Join-Path $env:windir "Microsoft.NET\Framework64\v4.0.30319"
    $regasm = Join-Path $fxDir "RegAsm.exe"
    if (Test-Path $regasm) { return $regasm }

    $fxDir32 = Join-Path $env:windir "Microsoft.NET\Framework\v4.0.30319"
    $regasm32 = Join-Path $fxDir32 "RegAsm.exe"
    if (Test-Path $regasm32) { return $regasm32 }

    return $null
}

# --------------------------------------------------------------------------
# Step 1: RegAsm /u
# --------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Step 1 : Unregister COM add-in ===" -ForegroundColor Cyan

$regasm = Find-RegAsm
if (-not $regasm) {
    Write-Host "[WARN] RegAsm not found, cannot unregister" -ForegroundColor Yellow
} elseif (-not (Test-Path $DllPath)) {
    Write-Host "[WARN] DLL not found at $DllPath" -ForegroundColor Yellow
} else {
    & $regasm /u $DllPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] COM unregistration succeeded" -ForegroundColor Green
    } else {
        Write-Host "[WARN] RegAsm /u returned non-zero exit code" -ForegroundColor Yellow
    }
}

# --------------------------------------------------------------------------
# Step 2: Remove SolidWorks registry key
# --------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Step 2 : Remove SolidWorks registry key ===" -ForegroundColor Cyan

$addinGuid = "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"
$regKeyPath = "HKLM:\SOFTWARE\SolidWorks\Addins\{$addinGuid}"

if (Test-Path $regKeyPath) {
    Remove-Item -Path $regKeyPath -Force
    Write-Host "[OK] Registry key removed" -ForegroundColor Green
} else {
    Write-Host "[OK] Registry key not present (already clean)" -ForegroundColor Green
}

# --------------------------------------------------------------------------
# Step 3: Remove swse-config.json
# --------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Step 3 : Remove config file ===" -ForegroundColor Cyan

$configPath = Join-Path $OutputDir "swse-config.json"
if (Test-Path $configPath) {
    Remove-Item -Path $configPath -Force
    Write-Host "[OK] Removed $configPath" -ForegroundColor Green
} else {
    Write-Host "[OK] Config file not present" -ForegroundColor Green
}

# --------------------------------------------------------------------------
# Step 4: Optionally remove .venv
# --------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Step 4 : Virtual environment ===" -ForegroundColor Cyan

$venvDir = Join-Path $ProjectRoot ".venv"
if ($RemoveVenv) {
    if (Test-Path $venvDir) {
        Remove-Item -Path $venvDir -Recurse -Force
        Write-Host "[OK] Removed $venvDir" -ForegroundColor Green
    } else {
        Write-Host "[OK] Venv not present" -ForegroundColor Green
    }
} else {
    if (Test-Path $venvDir) {
        Write-Host "[OK] Venv preserved at $venvDir (use -RemoveVenv to delete)" -ForegroundColor Green
    } else {
        Write-Host "[OK] No venv to clean up" -ForegroundColor Green
    }
}

# --------------------------------------------------------------------------
# Done
# --------------------------------------------------------------------------
Write-Host ""
Write-Host "Uninstall complete." -ForegroundColor Green
Write-Host ""
