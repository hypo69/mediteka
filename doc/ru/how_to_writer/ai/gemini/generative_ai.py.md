### Инструкции для генерации документации к коду

=========================================================================================

**Описание**
-------------------------
Этот модуль `generative_ai.py` предоставляет класс `GoogleGenerativeAI` для интеграции с моделями Google Gemini AI. Он включает методы для текстовых запросов, диалога, описания изображений и загрузки файлов. Модуль обрабатывает ошибки, связанные с API, сетью, аутентификацией и др., а также имеет функции для сохранения и загрузки истории чата.

**Шаги выполнения**
-------------------------
1.  Импортируются необходимые библиотеки и модули, включая `codecs`, `re`, `asyncio`, `time`, `json`, `IOBase`, `Path`, `Optional`, `Dict`, `List`, `Any`, `dataclass`, `field`, `base64`, `google.generativeai`, `requests`, `grpc`, исключения из `google.api_core.exceptions`, `header`, `logger`, `gs`, и вспомогательные утилиты `read_text_file`, `save_text_file`, `TimeoutCheck`, `j_loads`, `j_dumps`, `get_image_bytes`, `pprint`.
2.  Определена функция `normalize_text` для декодирования Unicode escape-последовательностей и замены `\
` на `
`.
3.  Определена функция `remove_html_blocks` для удаления блоков HTML-кода, начинающихся с ```.
4.  Создан класс `GoogleGenerativeAI` с аннотациями типов и значениями по умолчанию для работы с Google Gemini AI API.
    -   `api_key` - ключ API для доступа к Google Gemini AI.
    -   `model_name` - имя модели (по умолчанию "gemini-2.0-flash-exp").
    -   `generation_config` - конфигурация генерации (по умолчанию {"response_mime_type": "text/plain"}).
    -   `system_instruction` - системная инструкция для модели (опционально).
    -   `dialogue_log_path`, `dialogue_txt_path`, `history_dir`, `history_txt_file`, `history_json_file` - пути к файлам для сохранения логов и истории.
    -   `chat_history` - история чата.
    -   `model` - экземпляр модели `genai.GenerativeModel`.
    -   `_chat` - объект чата.
    -   `MODELS` - список доступных моделей.
5.  Метод `__post_init__` выполняет инициализацию объекта `GoogleGenerativeAI` после создания экземпляра класса. Он настраивает пути к файлам, инициализирует модель и начинает чат.
6.  Метод `_start_chat` запускает чат с начальной настройкой, включая системную инструкцию.
7.  Метод `clear_history` очищает историю чата в памяти и удаляет файл истории.
8.  Метод `_save_chat_history` сохраняет историю чата в JSON-файл.
9.  Метод `_load_chat_history` загружает историю чата из JSON-файла.
10. Метод `chat` управляет диалогом с моделью, обрабатывает режимы сохранения и очистки истории чата, отправляет запрос в модель и возвращает ответ.
11. Метод `ask` отправляет текстовый запрос модели и возвращает ответ, обрабатывая различные исключения (сетевые, аутентификационные, квотные и т.д.).
12. Метод `describe_image` отправляет изображение в Gemini Pro Vision для получения текстового описания.
13. Метод `upload_file` загружает файл в Gemini API.
14. Функция `main` демонстрирует примеры использования класса `GoogleGenerativeAI`:
    -   Создание экземпляра `GoogleGenerativeAI`.
    -   Вызов `describe_image` с JSON и без JSON формата.
    -   Вызов `upload_file` для загрузки текстового файла.
    -   Запуск чата с моделью в цикле.
15. Условный запуск `main` при исполнении скрипта.

**Пример использования**
-------------------------
```python
import asyncio
from pathlib import Path
from src.ai.gemini.generative_ai import GoogleGenerativeAI

async def main():
    # Замените на свой ключ API
    api_key = "YOUR_API_KEY"  
    system_instruction = "Ты - полезный ассистент. Отвечай на все вопросы кратко"
    ai = GoogleGenerativeAI(api_key=api_key, system_instruction=system_instruction)

    # Пример вызова describe_image с промптом
    image_path = Path("test.jpg")  # Замените на путь к вашему изображению

    if not image_path.is_file():
        print(
            f"Файл {image_path} не существует. Поместите в корневую папку с программой файл с названием test.jpg"
        )
    else:
        prompt = """Проанализируй это изображение. Выдай ответ в формате JSON,
        где ключом будет имя объекта, а значением его описание.
         Если есть люди, опиши их действия."""

        description = await ai.describe_image(image_path, prompt=prompt)
        if description:
            print("Описание изображения (с JSON форматом):")
            print(description)
            try:
                import json
                parsed_description = json.loads(description)
                print(parsed_description)

            except Exception as ex:
                print("Не удалось распарсить JSON. Получен текст:")
                print(description)

        else:
            print("Не удалось получить описание изображения.")

        # Пример без JSON вывода
        prompt = "Проанализируй это изображение. Перечисли все объекты, которые ты можешь распознать."
        description = await ai.describe_image(image_path, prompt=prompt)
        if description:
            print("Описание изображения (без JSON формата):")
            print(description)

    file_path = Path('test.txt')
    with open(file_path, "w") as f:
        f.write("Hello, Gemini!")

    file_upload = await ai.upload_file(file_path, 'test_file.txt')
    print(file_upload)

    # Пример чата
    while True:
        user_message = input("You: ")
        if user_message.lower() == 'exit':
            break
        ai_message = await ai.chat(user_message, chat_data_folder=None)
        if ai_message:
            print(f"Gemini: {ai_message}")
        else:
            print("Gemini: Ошибка получения ответа")

if __name__ == "__main__":
    asyncio.run(main())
```