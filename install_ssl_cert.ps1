<#
.SYNOPSIS
    Проверка, генерация и установка локальных SSL-сертификатов для Mediteka.

.DESCRIPTION
    1. Проверяет наличие сертификатов в $env:USERPROFILE\.certs (localhost+2.pem, localhost+2-key.pem).
    2. Если отсутствуют — генерирует их через mkcert (если установлен) или встроенным генератором (Python/PowerShell).
    3. Импортирует сертификат в хранилища Windows (CurrentUser\My и CurrentUser\Root), чтобы браузер доверял HTTPS.
#>

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$certsDir  = Join-Path $env:USERPROFILE ".certs"
$certPath  = Join-Path $certsDir "localhost+2.pem"
$keyPath   = Join-Path $certsDir "localhost+2-key.pem"
$pfxPath   = Join-Path $certsDir "localhost+2.pfx"
$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"

if (-not (Test-Path $certsDir)) {
    New-Item -ItemType Directory -Force -Path $certsDir | Out-Null
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              MEDITEKA — НАСТРОЙКА SSL СЕРТИФИКАТОВ            ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 1. Проверка / Генерация сертификатов
if (-not ((Test-Path $certPath) -and (Test-Path $keyPath))) {
    Write-Host "[1/3] SSL-сертификаты не найдены. Генерация..." -ForegroundColor Cyan

    $mkcertCmd = Get-Command mkcert -ErrorAction SilentlyContinue
    if ($mkcertCmd) {
        Write-Host "    Использование mkcert для генерации доверенного сертификата..." -ForegroundColor DarkGray
        try {
            & mkcert -install
            & mkcert -cert-file $certPath -key-file $keyPath "localhost" "127.0.0.1" "::1"
            Write-Host "    [OK] Сертификаты успешно сгенерированы через mkcert" -ForegroundColor Green
        } catch {
            Write-Host "    [WARN] Ошибка mkcert: $_. Попытка создания через Python..." -ForegroundColor Yellow
        }
    }

    # Если mkcert не создал файлы, генерируем через Python (cryptography)
    if (-not ((Test-Path $certPath) -and (Test-Path $keyPath))) {
        Write-Host "    Генерация самоподписанного сертификата через Python cryptography..." -ForegroundColor DarkGray
        $pyTarget = if (Test-Path $pythonExe) { $pythonExe } else { "python" }
        
        $genScript = @"
import os, ipaddress
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, 'localhost'),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Mediteka Local Dev'),
])
cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.now(timezone.utc))
    .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1825))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName('localhost'),
            x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),
            x509.IPAddress(ipaddress.IPv6Address('::1')),
        ]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)

cert_pem = cert.public_bytes(serialization.Encoding.PEM)
key_pem = key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()
)

certs_dir = r'$certsDir'
os.makedirs(certs_dir, exist_ok=True)
with open(r'$certPath', 'wb') as f:
    f.write(cert_pem)
with open(r'$keyPath', 'wb') as f:
    f.write(key_pem)
print('OK')
"@
        try {
            $genRes = & $pyTarget -c $genScript 2>&1
            if ($genRes -match 'OK') {
                Write-Host "    [OK] Сертификаты успешно созданы:" -ForegroundColor Green
                Write-Host "        $certPath" -ForegroundColor Gray
                Write-Host "        $keyPath"  -ForegroundColor Gray
            } else {
                Write-Host "    [WARN] Не удалось сгенерировать сертификат через Python: $genRes" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "    [WARN] Ошибка вызова Python: $_" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "[1/3] SSL-сертификаты уже существуют:" -ForegroundColor Green
    Write-Host "    $certPath" -ForegroundColor Gray
    Write-Host "    $keyPath"  -ForegroundColor Gray
}

# 2. Экспорт / Импорт в хранилища сертификатов Windows
if ((Test-Path $certPath) -and (Test-Path $keyPath)) {
    Write-Host ""
    Write-Host "[2/3] Добавление сертификата в доверенные сертификаты Windows..." -ForegroundColor Cyan
    try {
        $certObj = [System.Security.Cryptography.X509Certificates.X509Certificate2]::CreateFromPemFile($certPath, $keyPath)
        
        # Импорт в Personal (My)
        $storeMy = New-Object System.Security.Cryptography.X509Certificates.X509Store("My", "CurrentUser")
        $storeMy.Open("ReadWrite")
        $storeMy.Add($certObj)
        $storeMy.Close()
        Write-Host "    [OK] Сертификат добавлен в CurrentUser\Personal" -ForegroundColor Green

        # Импорт в Trusted Root
        $storeRoot = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
        $storeRoot.Open("ReadWrite")
        $storeRoot.Add($certObj)
        $storeRoot.Close()
        Write-Host "    [OK] Сертификат добавлен в CurrentUser\Trusted Root" -ForegroundColor Green
    } catch {
        Write-Host "    [WARN] Не удалось автоматически импортировать в хранилище Windows: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "    [WARN] Файлы сертификатов отсутствуют — запуск сервера будет без SSL." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3/3] Завершение настройки SSL" -ForegroundColor Cyan
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  SSL-СЕРТИФИКАТЫ ГОТОВЫ!                                      ║" -ForegroundColor Green
Write-Host "║  Адрес: https://localhost:3000                                ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
