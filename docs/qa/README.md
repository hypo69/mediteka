# QA Engineer Guide for ai-mediteka

## Введение

Это руководство для QA инженеров, работающих над проектом ai-mediteka - AI-ассистентом с медиаплеером, Telegram Mini App, пультом дистанционного управления и голосовым вводом.

## Структура документации

- **[Стратегия тестирования](testing-strategy.md)** - подход к тестированию проекта
- **[Тест-кейсы](test-cases.md)** - подробные тест-кейсы по модулям
- **[Чеклист QA](qa-checklist.md)** - контрольный список для QA проверок
- **[API тестирование](api-testing.md)** - руководство по тестированию API
- **[Интеграционное тестирование](integration-testing.md)** - интеграционные сценарии
- **[Инструменты QA](qa-tools.md)** - список используемых инструментов

## Быстрый старт

### Установка зависимостей

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=src --cov=plugins --cov-report=html:htmlcov

# Конкретный файл
pytest tests/test_ai.py

# Конкретный тест
pytest tests/test_ai.py::TestGoogleGenerativeAI::test_chat_with_mock
```

### Просмотр отчетов

```bash
# Открыть HTML отчет о покрытии
start htmlcov/index.html
```

## Типы тестов

| Тип | Описание | Доля |
|-----|----------|------|
| Unit | Модульное тестирование | 40% |
| Integration | Интеграционное тестирование | 30% |
| API | Тестирование API endpoints | 20% |
| Smoke | Быстрое тестирование | 10% |

## CI/CD

Тесты автоматически запускаются при каждом push и pull request:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-test.txt
      - name: Run tests
        run: pytest --cov=src --cov=plugins --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: coverage.xml
```

## Контакты

- **Project Lead**: hypo69
- **QA Lead**: [Ваше имя]
- **Slack**: #ai-mediteka-qa

---

[← Назад к документации](../index.md)