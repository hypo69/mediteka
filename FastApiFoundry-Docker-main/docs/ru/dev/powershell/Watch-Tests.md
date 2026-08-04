# Watch-Tests

> Test Watcher — запуск тестов при изменении кода

## Description

Следит за изменениями в src/ и tests/.
При изменении файла *.py автоматически запускает связанные тесты.
Результат выводится в консоль с цветовой индикацией.
Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\watch_tests.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\watch_tests.ps1 -Path src/api/endpoints
powershell -ExecutionPolicy Bypass -File .\scripts\watch_tests.ps1 -All
File: scripts/watch_tests.ps1
Project: AI Assistant
Version: 0.7.1
Author: hypo69
Copyright: © 2024 - 2026 hypo69
Licence: MIT
=============================================================================

## Examples

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\watch_tests.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\watch_tests.ps1 -Path src/api/endpoints
powershell -ExecutionPolicy Bypass -File .\scripts\watch_tests.ps1 -All
File: scripts/watch_tests.ps1
Project: AI Assistant
Version: 0.7.1
Author: hypo69
Copyright: © 2024 - 2026 hypo69
Licence: MIT
=============================================================================
```

## Source

`scripts/Watch-Tests.ps1`

