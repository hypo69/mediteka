### Инструкции для генерации документации к коду

=========================================================================================

**Описание**
-------------------------
Этот блок кода является файлом инициализации (`__init__.py`) для модуля `src.ai.gemini`. Он импортирует класс `GoogleGenerativeAI` из модуля `generative_ai` внутри пакета `src.ai.gemini`. Это позволяет использовать класс `GoogleGenerativeAI` при импорте пакета `src.ai.gemini`.

**Шаги выполнения**
-------------------------
1. Объявляется файл инициализации модуля `src.ai.gemini`.
2. Импортируется класс `GoogleGenerativeAI` из модуля `generative_ai` внутри того же пакета.

**Пример использования**
-------------------------
```python
# Предполагая, что структура проекта выглядит так:
# src/
#   ai/
#     gemini/
#       __init__.py
#       generative_ai.py

# Теперь при импорте пакета:
from src.ai.gemini import GoogleGenerativeAI

# Теперь класс GoogleGenerativeAI доступен через пакет src.ai.gemini:
# model = GoogleGenerativeAI(api_key="your_api_key")
# response = model.generate_content("some_prompt")
# print(response)
```