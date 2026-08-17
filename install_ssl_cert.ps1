# Установка SSL-сертификата в хранилище Windows

$certsDir = Join-Path $env:USERPROFILE ".certs"
$certPath = Join-Path $certsDir "localhost+2.pem"
$keyPath = Join-Path $certsDir "localhost+2-key.pem"
$pfxPath = Join-Path $certsDir "localhost+2.pfx"

Write-Host "-Conвертация PEM в PFX..." -ForegroundColor Cyan

# Чтение ключа и сертификата
$keyContent = Get-Content -Raw $keyPath
$certContent = Get-Content -Raw $certPath

# Создание PFX с пустым паролем (для локального использования)
$pfxByte = [System.Text.Encoding]::UTF8.GetBytes($keyContent + $certContent)
[IO.File]::WriteAllBytes($pfxPath, $pfxByte)

Write-Host "  Создан PFX файл: $pfxPath" -ForegroundColor Green

# Импорт в хранилище Personal
Write-Host "Импорт в хранилище Personal..." -ForegroundColor Cyan
$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($pfxPath, "")
$store = New-Object System.Security.Cryptography.X509Certificates.X509Store("My", "CurrentUser")
$store.Open("ReadWrite")
$store.Add($cert)
$store.Close()

Write-Host "  Установлен в Personal" -ForegroundColor Green

# Импорт в Trusted Root
Write-Host "Импорт в Trusted Root..." -ForegroundColor Cyan
$storeRoot = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
$storeRoot.Open("ReadWrite")
$storeRoot.Add($cert)
$storeRoot.Close()

Write-Host "  Установлен в Trusted Root" -ForegroundColor Green

# Удаление временного PFX
Remove-Item $pfxPath -ErrorAction SilentlyContinue

Write-Host "" -ForegroundColor Green
Write-Host "=== Готово! ===" -ForegroundColor Green
Write-Host "Перезапусти браузер и открой https://127.0.0.1:3000" -ForegroundColor Cyan
