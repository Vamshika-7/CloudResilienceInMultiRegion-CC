# Script to run all unit and integration test suites
Write-Host "========================================="
Write-Host " Running E-Commerce Microservices Test Suite "
Write-Host "========================================="

$ErrorActionPreference = "Continue"
$failed = 0

$suites = @(
    @{ Name = "Product Service"; Path = "services\product-service\tests" },
    @{ Name = "Order Service"; Path = "services\order-service\tests" },
    @{ Name = "Payment Service"; Path = "services\payment-service\tests" },
    @{ Name = "API Gateway"; Path = "gateway\tests" }
)

foreach ($suite in $suites) {
    Write-Host "`n>>> Testing $($suite.Name)..." -ForegroundColor Cyan
    .\venv\Scripts\python.exe -m pytest $suite.Path -v
    if ($LASTEXITCODE -ne 0) {
        $failed++
    }
}

Write-Host "`n========================================="
if ($failed -eq 0) {
    Write-Host " ALL TEST SUITES PASSED SUCCESSFULLY! " -ForegroundColor Green
} else {
    Write-Host " $failed test suite(s) failed." -ForegroundColor Red
    exit 1
}
Write-Host "========================================="
