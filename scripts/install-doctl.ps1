# Install doctl CLI for DigitalOcean
# Run this script as Administrator in PowerShell

Write-Host "======================================"
Write-Host "Installing doctl CLI for DigitalOcean"
Write-Host "======================================"
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Define version and paths
$version = "1.146.0"
$downloadUrl = "https://github.com/digitalocean/doctl/releases/download/v$version/doctl-$version-windows-amd64.zip"
$downloadPath = "$env:TEMP\doctl-$version-windows-amd64.zip"
$extractPath = "$env:TEMP\doctl-$version-windows-amd64"
$installPath = "$env:ProgramFiles\doctl"

Write-Host "Step 1: Downloading doctl v$version..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $downloadPath -UseBasicParsing
    Write-Host "✓ Download complete" -ForegroundColor Green
} catch {
    Write-Host "✗ Download failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Extracting archive..." -ForegroundColor Cyan
try {
    if (Test-Path $extractPath) {
        Remove-Item -Path $extractPath -Recurse -Force
    }
    Expand-Archive -Path $downloadPath -DestinationPath $extractPath -Force
    Write-Host "✓ Extraction complete" -ForegroundColor Green
} catch {
    Write-Host "✗ Extraction failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 3: Installing doctl..." -ForegroundColor Cyan
try {
    # Create installation directory
    if (-not (Test-Path $installPath)) {
        New-Item -ItemType Directory -Path $installPath -Force | Out-Null
    }

    # Copy executable
    $exePath = Join-Path $extractPath "doctl.exe"
    if (-not (Test-Path $exePath)) {
        Write-Host "✗ doctl.exe not found in extracted archive" -ForegroundColor Red
        exit 1
    }

    Copy-Item -Path $exePath -Destination $installPath -Force
    Write-Host "✓ Installation complete" -ForegroundColor Green
} catch {
    Write-Host "✗ Installation failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 4: Adding to system PATH..." -ForegroundColor Cyan
try {
    $currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine)

    if ($currentPath -notlike "*$installPath*") {
        [Environment]::SetEnvironmentVariable(
            "Path",
            "$currentPath;$installPath",
            [EnvironmentVariableTarget]::Machine
        )
        Write-Host "✓ Added to system PATH" -ForegroundColor Green
    } else {
        Write-Host "✓ Already in system PATH" -ForegroundColor Green
    }

    # Refresh current session PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
} catch {
    Write-Host "✗ Failed to update PATH: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 5: Cleaning up temporary files..." -ForegroundColor Cyan
try {
    Remove-Item -Path $downloadPath -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $extractPath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✓ Cleanup complete" -ForegroundColor Green
} catch {
    Write-Host "⚠ Cleanup failed (non-critical): $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================"
Write-Host "✓ doctl installation complete!" -ForegroundColor Green
Write-Host "======================================"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Close and reopen your terminal"
Write-Host "  2. Run: doctl version"
Write-Host "  3. Run: doctl auth init"
Write-Host "  4. Paste your DigitalOcean API token when prompted"
Write-Host ""
Write-Host "To get an API token:"
Write-Host "  1. Go to: https://cloud.digitalocean.com/account/api/tokens"
Write-Host "  2. Click 'Generate New Token'"
Write-Host "  3. Name it 'todo-app-deployment'"
Write-Host "  4. Select 'Read & Write' scopes"
Write-Host "  5. Copy the token (you won't see it again!)"
Write-Host ""
Write-Host "For full Phase V guide, see: PHASE_V_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
