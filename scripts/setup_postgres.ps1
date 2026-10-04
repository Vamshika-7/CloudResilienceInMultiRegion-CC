# Script to download, configure, and run portable PostgreSQL locally (no admin rights needed)
param (
    [string]$PgsqlDir = "$HOME\.pgsql",
    [int]$Port = 5432,
    [string]$Database = "ecommerce"
)

$ErrorActionPreference = "Stop"

$BinDir = "$PgsqlDir\pgsql\bin"
$DataDir = "$PgsqlDir\data"
$LogFile = "$PgsqlDir\postgres.log"

# Check if pg_isready is already accessible in PATH or BinDir
$pgIsReady = if (Test-Path "$BinDir\pg_isready.exe") { "$BinDir\pg_isready.exe" } elseif (Get-Command pg_isready.exe -ErrorAction SilentlyContinue) { (Get-Command pg_isready.exe).Source } else { $null }

if ($pgIsReady) {
    & $pgIsReady -p $Port -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PostgreSQL is already running on port $Port."
        exit 0
    }
}

if (-not (Test-Path "$BinDir\initdb.exe")) {
    Write-Host "PostgreSQL binaries not found. Downloading portable PostgreSQL..."
    if (-not (Test-Path $PgsqlDir)) {
        New-Item -ItemType Directory -Path $PgsqlDir -Force | Out-Null
    }
    
    $ZipPath = "$PgsqlDir\postgresql-windows-x64-binaries.zip"
    $DownloadUrl = "https://get.enterprisedb.com/postgresql/postgresql-16.15-5-windows-x64-binaries.zip"
    
    Write-Host "Downloading from $DownloadUrl..."
    curl.exe -L -o $ZipPath $DownloadUrl
    
    Write-Host "Extracting archive to $PgsqlDir..."
    python -c "import zipfile; zipfile.ZipFile(r'$ZipPath').extractall(r'$PgsqlDir')"
    Remove-Item -Path $ZipPath -Force
    Write-Host "Extraction complete."
}

if (-not (Test-Path "$DataDir\PG_VERSION")) {
    Write-Host "Initializing PostgreSQL cluster at $DataDir..."
    & "$BinDir\initdb.exe" -D $DataDir -U postgres -A trust -E UTF8
}

Write-Host "Starting PostgreSQL server on port $Port..."
& "$BinDir\pg_ctl.exe" -D $DataDir -o "-p $Port" -l $LogFile start

# Wait for server to be ready
Start-Sleep -Seconds 2
& "$BinDir\pg_isready.exe" -p $Port -U postgres
if ($LASTEXITCODE -ne 0) {
    Write-Host "Waiting for PostgreSQL to be ready..."
    Start-Sleep -Seconds 3
}

# Create database if not exists
Write-Host "Creating database '$Database' if not present..."
& "$BinDir\createdb.exe" -h localhost -p $Port -U postgres $Database 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Database '$Database' created successfully."
} else {
    Write-Host "Database '$Database' already exists or created."
}

Write-Host "PostgreSQL setup complete and running on localhost:$Port."
