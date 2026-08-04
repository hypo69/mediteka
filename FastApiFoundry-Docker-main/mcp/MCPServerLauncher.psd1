## \
# -*- coding: utf-8 -*-
#! .pyenv/bin/pwsh

<#
.SYNOPSIS
    Module manifest for MCP PowerShell Server Launcher
    
.DESCRIPTION
    Манифест модуля для автоматического запуска и управления MCP серверами
    
.NOTES
    File MCPServerLauncher.psd1
    Version: 1.0.1
    Author: hypo69
    License: MIT (https://opensource.org/licenses/MIT)
    Copyright: © 2024 - 2026 hypo69
#>

@{
    # Версия модуля
    ModuleVersion = '1.0.1'
    
    # Поддерживаемая версия PSEdition
    CompatiblePSEditions = @('Core', 'Desktop')
    
    # GUID модуля
    GUID = 'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d'
    
    # Автор модуля
    Author = 'hypo69'
    
    # Компания или поставщик модуля
    CompanyName = 'hypo69'
    
    # Авторские права
    Copyright = '© 2024 - 2026 hypo69. All rights reserved.'
    
    # Описание функциональности модуля
    Description = 'Модуль для автоматического запуска и управления MCP PowerShell серверами. Поддерживает STDIO, HTTPS и WordPress CLI серверы.'
    
    # Минимальная версия PowerShell
    PowerShellVersion = '7.0'
    
    # Корневой модуль
    RootModule = 'MCPServerLauncher.psm1'
    
    # Функции для экспорта из этого модуля
    FunctionsToExport = @(
        'Start-MCPServerLauncher',
        'Stop-MCPServers',
        'Get-MCPServerStatus',
        'Restart-MCPServers',
        'Test-MCPServerRunning',
        'Get-MCPServerLog'
    )
    
    # Командлеты для экспорта из этого модуля
    CmdletsToExport = @()
    
    # Переменные для экспорта из этого модуля
    VariablesToExport = @()
    
    # Псевдонимы для экспорта из этого модуля
    AliasesToExport = @(
        'Start-MCP',
        'Stop-MCP',
        'Get-MCPStatus',
        'Restart-MCP'
    )
    
    # Список всех файлов, упакованных с этим модулем
    FileList = @(
        'MCPServerLauncher.psd1',
        'MCPServerLauncher.psm1',
        'README.md'
    )
    
    # Приватные данные для передачи в модуль
    PrivateData = @{
        PSData = @{
            # Теги для поиска модуля в онлайн-галереях
            Tags = @('MCP', 'Server', 'Launcher', 'PowerShell', 'STDIO', 'HTTPS', 'WordPress', 'CLI')
            
            # URL-адрес лицензии для этого модуля
            LicenseUri = 'https://opensource.org/licenses/MIT'
            
            # URL-адрес главного веб-сайта для этого проекта
            ProjectUri = 'https://github.com/hypo69/hypo'
            
            # Примечания к выпуску этого модуля
            ReleaseNotes = @'
## Version 1.0.1
- Автоматический запуск MCP серверов
- Управление жизненным циклом серверов
- Поддержка STDIO, HTTPS и WordPress CLI серверов
- Подробное логирование
- Мониторинг статуса серверов
'@
        }
    }
}