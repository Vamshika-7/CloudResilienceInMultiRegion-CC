# Script to stop all running Python microservices, Frontend, and PostgreSQL
Write-Host "Stopping microservice processes (ports 8000, 8001, 8002, 8003, 5173)..."

Get-Process -Name "python", "node" -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*CC*" -or $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*vite*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop PostgreSQL if requested
& "$PSScriptRoot\stop_postgres.ps1"

Write-Host "All services stopped."
