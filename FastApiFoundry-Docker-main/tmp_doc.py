# -*- coding: utf-8 -*-
path = 'src/rag/document_ingestor.py'
c = open(path, encoding='utf-8').read()

# 1. Class docstring
old_cls = '''class DocumentIngestor:
    """!
    Класс, отвечающий за подготовку данных к RAG.
    Инкапсулирует логику выбора инструментов и первичной обработки.
    """'''

new_cls = '''class DocumentIngestor:
    """Подготовка документов к индексации в RAG.

    Инкапсулирует выбор инструментов извлечения текста и первичную обработку.

    Архитектурное ограничение — временные файлы:
        Все внутренние методы (_process_file_recursive, MarkItDown, zipfile,
        tarfile, py7zr, rarfile) работают с путями к файлам на диске, а не
        с байтами в памяти. Поэтому process_upload() обязан сохранить
        содержимое UploadFile во временный файл перед обработкой.

        Временный файл создаётся через tempfile.mkstemp() в системной
        temp-директории (например C:\\Users\\user\\AppData\\Local\\Temp\\).
        Суффикс берётся из basename(filename), чтобы избежать ошибок
        при именах вида "ru/about.md" (webkitdirectory upload).
        Файл гарантированно удаляется в блоке finally.

        TODO: рефакторинг на работу с io.BytesIO позволит убрать temp-файлы,
        но требует переписать все зависимые экстракторы.
    """'''

assert old_cls in c, 'class docstring NOT FOUND'
c = c.replace(old_cls, new_cls, 1)

# 2. process_upload docstring
old_pu = '    async def process_upload(self, file: UploadFile) -> Tuple[str, str, str, Dict[str, Any]]:\r\n        """Обработка загруженного файла."""'
new_pu = '''    async def process_upload(self, file: UploadFile) -> Tuple[str, str, str, Dict[str, Any]]:
        """Обработка загруженного файла через временный файл на диске.

        Почему используется временный файл:
            FastAPI передаёт содержимое как UploadFile (SpooledTemporaryFile
            в памяти), но все нижележащие экстракторы (MarkItDown, zipfile,
            tarfile, py7zr, rarfile) требуют путь к файлу на диске.
            Поэтому байты сначала сбрасываются в tempfile.mkstemp(), а после
            обработки файл удаляется.

        Почему mkstemp, а не f"temp_{filename}":
            file.filename при загрузке директории через <input webkitdirectory>
            содержит относительный путь (например "ru/about.md"). Конкатенация
            "temp_" + "ru/about.md" даёт несуществующий путь "temp_ru/about.md".
            mkstemp создаёт файл в системной temp-директории, используя только
            расширение из basename(filename).

        Args:
            file (UploadFile): Загруженный файл. filename может содержать
                относительный путь (webkitdirectory), используется только
                как source_name для метаданных индекса.

        Returns:
            Tuple[str, str, str, Dict]: (text, source_name, method, metadata).
        """'''

if old_pu not in c:
    old_pu = old_pu.replace('\r\n', '\n')

assert old_pu in c, 'process_upload docstring NOT FOUND'
c = c.replace(old_pu, new_pu, 1)

open(path, 'w', encoding='utf-8').write(c)
print('OK')
