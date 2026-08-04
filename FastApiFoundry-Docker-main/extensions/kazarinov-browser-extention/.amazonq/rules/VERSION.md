# FastApiFoundry (Docker) - Version Control

**Текущая версия:** 0.7.1
**Проект:** AI Assistant (ai_assist)

---

## ПРАВИЛА ВЕРСИОНИРОВАНИЯ

### ОБЯЗАТЕЛЬНО ДЛЯ ВСЕХ ФАЙЛОВ:

При изменении любого файла в проекте AI Assistant (ai_assist):

1. **Обновить версию до 0.7.1** в заголовке файла
2. **Указать проект:** AI Assistant (ai_assist)
3. **Изменения в версии:** описать что изменилось относительно предыдущей версии

### ФОРМАТ ЗАГОЛОВКА (Python):

```python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: <Description>
# =============================================================================
# Description:
#   <Details>
#
# File: <filename>
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - <what changed>
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
```

### ФОРМАТ ЗАГОЛОВКА (PowerShell):

```powershell
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: <Description>
# =============================================================================
# Description:
#   <Details>
#
# File: <filename>
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - <what changed>
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
```

### БЕЙДЖ ВЕРСИИ В ДОКУМЕНТАЦИИ:

Каждая страница документации `docs/ru/index.md` содержит бейджи:

```markdown
![Version](https://img.shields.io/badge/version-0.7.1-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Docker-informational)
```

При смене версии — обновлять бейдж в `docs/ru/index.md` и `extra.ai_assist_version` в `mkdocs.yml`.

### CHANGELOG:

Каждое изменение фиксируется в `CHANGELOG.md` в корне проекта.
Формат записи:

```markdown
## [0.7.1] - YYYY-MM-DD

### Added
- `path/to/file.py` — описание добавленного

### Changed
- `path/to/file.py` — описание изменения

### Fixed
- `path/to/file.py` — описание исправления
```

### ПРИМЕНЕНИЕ:

- ✅ Все Python файлы (.py)
- ✅ Все конфигурационные файлы (.json, .yaml, .env)
- ✅ Все документационные файлы (.md)
- ✅ Все скрипты (.sh, .bat, .ps1)
- ✅ Все веб-файлы (.html, .js, .css)
