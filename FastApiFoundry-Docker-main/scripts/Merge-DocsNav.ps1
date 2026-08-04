<#
.SYNOPSIS
    Интегрирует сгенерированный фрагмент навигации в mkdocs.yml.
#>
param (
    [string]$MkdocsConfig = "mkdocs.yml",
    [string]$NavFragment  = "docs/ru/dev/powershell/nav_fragment.yml"
)

if (-not (Test-Path $NavFragment)) {
    Write-Error "Фрагмент навигации не найден: $NavFragment"
    exit 1
}

$FragmentContent = Get-Content $NavFragment -Raw
$ConfigContent   = Get-Content $MkdocsConfig -Raw

# Регулярное выражение для поиска блока между маркерами
$Pattern = "(?s)# AUTO_GENERATED_PS_DOCS_START.*?# AUTO_GENERATED_PS_DOCS_END"
$Replacement = "# AUTO_GENERATED_PS_DOCS_START`n$FragmentContent`n        # AUTO_GENERATED_PS_DOCS_END"

$NewConfig = $ConfigContent -replace $Pattern, $Replacement

$NewConfig | Set-Content $MkdocsConfig -Encoding UTF8
Write-Host "✅ Навигация успешно интегрирована в $MkdocsConfig" -ForegroundColor Green