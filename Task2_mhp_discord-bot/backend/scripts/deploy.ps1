<#
.SYNOPSIS
    Package Lambda function code into a ZIP for manual upload via AWS Console.

.EXAMPLE
    .\scripts\deploy.ps1
#>

$ErrorActionPreference = "Stop"
$BackendDir = Split-Path -Parent $PSScriptRoot
$PackageDir = Join-Path $BackendDir "package"
$ZipFile = Join-Path $BackendDir "deployment.zip"

Write-Host "=== MHP Discord Bot - Lambda Packager ===" -ForegroundColor Cyan
Write-Host ""

# Clean previous build
if (Test-Path $PackageDir) {
    Write-Host "Cleaning previous package..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $PackageDir
}
if (Test-Path $ZipFile) {
    Remove-Item -Force $ZipFile
}

# Install dependencies targeting Lambda Linux x86_64 runtime
Write-Host "Installing dependencies (Linux x86_64 for Lambda)..." -ForegroundColor Yellow
$ReqFile = Join-Path $BackendDir "requirements-lambda.txt"
pip install -r $ReqFile -t $PackageDir --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 --only-binary=:all: --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "Cross-platform install failed!" -ForegroundColor Red
    exit 1
}

# Copy source code
Write-Host "Copying source code..." -ForegroundColor Yellow
Copy-Item -Recurse (Join-Path $BackendDir "src") (Join-Path $PackageDir "src")

# Remove __pycache__ dirs from source copy
Get-ChildItem -Path $PackageDir -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Create ZIP
Write-Host "Creating deployment.zip..." -ForegroundColor Yellow
Push-Location $PackageDir
Compress-Archive -Path * -DestinationPath $ZipFile -Force
Pop-Location

$zipSize = [math]::Round((Get-Item $ZipFile).Length / 1MB, 2)
Write-Host ""
Write-Host "Package created: deployment.zip - $zipSize MB" -ForegroundColor Green

# Clean up package dir (keep zip)
Remove-Item -Recurse -Force $PackageDir

Write-Host ""
Write-Host "Done! Upload deployment.zip to Lambda via AWS Console:" -ForegroundColor Cyan
Write-Host "  Lambda > Functions > trainee-2026-niloy-mhp-discord-dev > Code > Upload from > .zip file"
