### Инструкции для генерации документации к коду

=========================================================================================

**Описание**
-------------------------
Этот блок кода импортирует класс `GoogleGenerativeAI` из модуля `gemini` в текущем пакете. Это позволяет использовать функциональность, предоставляемую классом `GoogleGenerativeAI`, в текущем модуле.

**Шаги выполнения**
-------------------------
1. Импортируется класс `GoogleGenerativeAI` из модуля `gemini` внутри текущего пакета.

**Пример использования**
-------------------------
```python
# Предположим, что структура проекта выглядит так:
# your_package/
#   __init__.py
#   gemini.py  (содержит класс GoogleGenerativeAI)
#   some_module.py

# Содержимое some_module.py:
from your_package.gemini import GoogleGenerativeAI

# Теперь вы можете создавать экземпляры и использовать методы класса GoogleGenerativeAI:
# model = GoogleGenerativeAI(api_key="your_api_key")
# response = model.generate_content("some_prompt")
# print(response)
```