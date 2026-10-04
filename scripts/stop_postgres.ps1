# Script to cleanly stop the local PostgreSQL instance
param (
    [string]$PgsqlDir = "$HOME\.pgsql"
)

$BinDir = "$PgsqlDir\pgsql\bin"
$DataDir = "$PgsqlDir\data"

if (Test-Path "$BinDir\pg_ctl.exe") {
    Write-Host "Stopping PostgreSQL server..."
    & "$BinDir\pg_ctl.exe" -D $DataDir stop
} else {
    Write-Host "PostgreSQL binaries not found at $BinDir"
}
