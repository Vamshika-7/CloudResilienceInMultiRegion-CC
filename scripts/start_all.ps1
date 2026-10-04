# Script to start all microservices, API Gateway, and Frontend locally
param (
    [switch]$NoFrontend
)

$ErrorActionPreference = "Continue"

Write-Host "=========================================================="
Write-Host "  Starting E-Commerce Microservices & Resilience Testbed  "
Write-Host "=========================================================="

# 1. Verify / Start PostgreSQL
$pgBin = "$HOME\.pgsql\pgsql\bin\pg_isready.exe"
if (Test-Path $pgBin) {
    & $pgBin -p 5432 -q
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PostgreSQL is not running. Starting local PostgreSQL..."
        & "$PSScriptRoot\setup_postgres.ps1"
    } else {
        Write-Host "[OK] PostgreSQL is active on localhost:5432."
    }
} else {
    Write-Host "Ensuring PostgreSQL is initialized..."
    & "$PSScriptRoot\setup_postgres.ps1"
}

# 2. Start Product Service (Port 8001)
Write-Host "Starting Product Service on port 8001..."
$prodProc = Start-Process -FilePath "..\venv\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8001" -WorkingDirectory "$PSScriptRoot\..\services\product-service" -PassThru

# 3. Start Order Service (Port 8002)
Write-Host "Starting Order Service on port 8002..."
$orderProc = Start-Process -FilePath "..\venv\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8002" -WorkingDirectory "$PSScriptRoot\..\services\order-service" -PassThru

# 4. Start Payment Service (Port 8003)
Write-Host "Starting Payment Service on port 8003..."
$payProc = Start-Process -FilePath "..\venv\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8003" -WorkingDirectory "$PSScriptRoot\..\services\payment-service" -PassThru

# 5. Start API Gateway (Port 8000)
Write-Host "Starting API Gateway on port 8000..."
$gwProc = Start-Process -FilePath "..\venv\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000" -WorkingDirectory "$PSScriptRoot\..\gateway" -PassThru

# 6. Start React Frontend (Port 5173)
if (-not $NoFrontend) {
    Write-Host "Starting Frontend (Vite) on port 5173..."
    $feProc = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory "$PSScriptRoot\..\frontend" -PassThru
}

Write-Host "`nAll services have been launched:"
Write-Host "  - API Gateway:    http://localhost:8000 (Swagger: http://localhost:8000/docs)"
Write-Host "  - Product Service:http://localhost:8001 (Swagger: http://localhost:8001/docs)"
Write-Host "  - Order Service:  http://localhost:8002 (Swagger: http://localhost:8002/docs)"
Write-Host "  - Payment Service:http://localhost:8003 (Swagger: http://localhost:8003/docs)"
Write-Host "  - React Frontend: http://localhost:5173"
Write-Host "=========================================================="
