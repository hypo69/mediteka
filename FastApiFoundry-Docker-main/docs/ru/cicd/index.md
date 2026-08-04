# 🔄 CI/CD — Непрерывная интеграция и доставка

**Проект:** AI Assistant
**Автор:** hypo69
**Copyright:** © 2024 - 2026 hypo69
**Лицензия:** MIT

Этот раздел описывает систему непрерывной интеграции и доставки для проекта AI Assistant.

---

## Архитектура CI/CD

```
Developer Push
      │
      ▼
GitHub Actions Workflow (qa.yml)
      │
      ├─→ Checkout Repository
      ├─→ Setup Python 3.11
      ├─→ Install Dependencies
      ├─→ Security Audit (pip-audit)
      ├─→ Run Full QA Cycle
      │     ├─ Ruff (Linter)
      │     ├─ Mypy (Type Checking)
      │     ├─ Pytest (Tests)
      │     ├─ Coverage (HTML Report)
      │     ├─ Secrets Scan (detect-secrets)
      │     └─ JUnit Report
      │
      ▼
Status Report (Pass/Fail)
```

---

## GitHub Actions Workflow

**Конфигурация:** `.github/workflows/qa.yml`

### Триггеры

| Событие | Ветки | Описание |
|---------|-------|----------|
| `pull_request` | `main`, `master` | Запуск при создании PR |

### Этапы выполнения

#### 1. Checkout Repository
```yaml
- uses: actions/checkout@v4
```
Получение кода репозитория.

#### 2. Setup Python 3.11
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'
```
Установка Python и кэширование зависимостей.

#### 3. Install Dependencies
```yaml
- name: Install base dependencies
  run: |
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python -m pip install -r requirements-qa.txt
```
Установка основных и QA-зависимостей.

#### 4. Security Audit
```yaml
- name: Security Audit
  id: security-audit
  continue-on-error: true
  run: |
    python -m pip_audit --desc on --format json --output tests/reports/audit-ci.json
```
Проверка зависимостей на известные уязвимости.

#### 5. Create Security Issue
```yaml
- name: Create Security Issue on Vulnerabilities
  if: steps.security-audit.outcome == 'failure'
  uses: peter-evans/create-issue@v6
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    title: '🚨 Security Vulnerabilities Detected...'
    body: ${{ steps.read-audit-report.outputs.audit_report_json }}
    labels: security
```
Создание Issue при обнаружении уязвимостей.

#### 6. Run Full QA Cycle
```yaml
- name: Run Full QA Cycle
  shell: pwsh
  run: |
    ./scripts/Invoke-Qa.ps1 -SkipCoverageReport
```
Полный цикл контроля качества.

---

## Локальная разработка

### Установка Git-хуков

```powershell
.\scripts\Setup-GitHooks.ps1
```

**Что делает:**
- Копирует `scripts/pre-commit` в `.git/hooks/pre-commit`
- Активирует проверку на секреты перед каждым коммитом

### Запуск полного QA

```powershell
.\scripts\Invoke-Qa.ps1
```

**Этапы:**
1. Активация виртуального окружения
2. Проверка обновлений пакетов
3. Аудит безопасности (pip-audit)
4. Поиск секретов (detect-secrets)
5. Линтинг (Ruff)
6. Проверка типов (Mypy)
7. Тесты (Pytest)
8. Генерация отчета о покрытии
9. Визуализация производительности

### Исправление уязвимостей

```powershell
.\scripts\Fix-Vulnerabilities.ps1
```

**Что делает:**
- Создает ветку `security-fix`
- Применяет патчи к уязвимым пакетам
- Автоматически создает коммит

---

## Структура отчетов

```
tests/reports/
├── coverage/          # HTML отчет о покрытии
│   └── index.html
├── junit.xml          # JUnit отчет для GitHub
├── audit.json         # Отчет pip-audit (локально)
├── audit-ci.json      # Отчет pip-audit (CI)
├── secrets.json       # Результаты detect-secrets
└── qa_management_report.pdf  # PDF отчет для руководства
```

---

## Инструменты

| Инструмент | Назначение | Конфигурация |
|------------|------------|--------------|
| **Ruff** | Линтинг Python | `pyproject.toml` / `ruff.toml` |
| **Mypy** | Проверка типов | `mypy.ini` |
| **Pytest** | Тестирование | `pytest.ini` |
| **Coverage** | Покрытие кода | `setup.cfg` / `pyproject.toml` |
| **pip-audit** | Безопасность | — |
| **detect-secrets** | Секреты | `.detect-secrets.yaml` |

---

## Рекомендации

### Для разработчиков

1. **Перед коммитом:**
   ```powershell
   .\scripts\Invoke-Qa.ps1
   ```

2. **При добавлении зависимостей:**
   - Обновите `requirements.txt`
   - Запустите `.\scripts\Invoke-Qa.ps1`
   - Проверьте отчет о покрытии

3. **При обнаружении уязвимостей:**
   ```powershell
   .\scripts\Fix-Vulnerabilities.ps1
   ```

### Для CI/CD

1. **GitHub Actions автоматически запускает QA при:**
   - Создании Pull Request
   - Изменениях в ветках `main` и `master`

2. **При обнаружении уязвимостей:**
   - Создается Issue с меткой `security`
   - Workflow продолжает выполнение
   - Разработчик получает уведомление

---

## Связанные файлы

- `.github/workflows/qa.yml` — GitHub Actions workflow
- `scripts/Setup-GitHooks.ps1` — установка Git-хуков
- `scripts/Invoke-Qa.ps1` — полный цикл QA
- `scripts/Fix-Vulnerabilities.ps1` — исправление уязвимостей
- `scripts/pre-commit` — шаблон хука
- `.git/hooks/pre-commit` — установленный хук
- `.detect-secrets.yaml` — конфигурация detect-secrets
