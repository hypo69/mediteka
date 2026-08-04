import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import io
import zipfile
import tarfile
from datetime import datetime
from src.rag.document_ingestor import DocumentIngestor

# Импортируем app. В зависимости от структуры проекта это может быть:
# from src.api.main import app или из app.py
from src.api.app import app 

client = TestClient(app)

@pytest.mark.asyncio
async def test_index_pdf_with_table_integration():
    """
    Интеграционный тест: загрузка PDF с таблицей.
    Проверяет, что MarkItDown вызывается корректно и данные попадают в RAG.
    """
    # 1. Подготовка мока для результата MarkItDown
    mock_result = MagicMock()
    # Имитируем извлеченную таблицу в формате Markdown
    mock_markdown = (
        "# Отчет\n\n"
        "| Название | Сумма |\n"
        "|---|---|\n"
        "| Услуги ИИ | 5000 |\n"
        "| Лицензии | 1200 |"
    )
    mock_result.text_content = mock_markdown

    # 2. Патчим MarkItDown и метод добавления в RAG
    # Важно: патчим там, где эти объекты ИСПОЛЬЗУЮТСЯ (в эндпоинте rag.py)
    with patch("src.api.endpoints.rag.markitdown_engine.convert", return_value=mock_result) as mock_convert, \
         patch("src.api.endpoints.rag.rag_system.add_text", new_callable=AsyncMock) as mock_add_text:
        
        # Симулируем бинарный контент PDF
        file_content = b"%PDF-1.4 mock pdf content"
        files = {"file": ("test_table.pdf", io.BytesIO(file_content), "application/pdf")}
        
        # 3. Выполнение запроса
        response = client.post("/api/v1/rag/index", files=files)
        
        # 4. Проверки
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["method"] == "MarkItDown"
        
        # Проверяем, что MarkItDown был вызван
        mock_convert.assert_called_once()
        
        # Проверяем, что в RAG систему был передан именно наш Markdown с таблицей
        mock_add_text.assert_called_once()
        called_kwargs = mock_add_text.call_args.kwargs
        assert "| Название | Сумма |" in called_kwargs["text"]
        assert called_kwargs["metadata"]["source"] == "test_table.pdf"

@pytest.mark.asyncio
async def test_index_pdf_fallback_to_extractor():
    """
    Проверка фолбэка: если MarkItDown падает, должен сработать TextExtractor.
    """
    # 1. Мокаем ошибку в MarkItDown
    # 2. Мокаем успешный ответ от кастомного экстрактора
    mock_fallback_content = "Текст, извлеченный кастомным экстрактором после ошибки Microsoft"
    
    # Патчим convert, чтобы он кидал исключение
    with patch("src.rag.document_ingestor.MarkItDown.convert", side_effect=RuntimeError("MID Crash")), \
         patch("src.rag.document_ingestor.TextExtractor.extract_from_file", new_callable=AsyncMock) as mock_custom, \
        mock_custom.return_value = mock_fallback_content
        
        file_content = b"%PDF-1.4 binary data"
        files = {"file": ("broken.pdf", io.BytesIO(file_content), "application/pdf")}
        
        # 3. Вызов API
        response = client.post("/api/v1/rag/index", files=files)
        
        # 4. Проверки
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Метод должен определиться как CustomExtractor из-за ошибки в MarkItDown
        assert data["method"] == "CustomExtractor"
        # Проверяем, что кастомный экстрактор действительно вызывался
        mock_custom.assert_called_once()

@pytest.mark.asyncio
async def test_index_pdf_with_form_and_annotations_integration():
    """
    Проверка корректности извлечения данных из PDF формы и аннотаций.
    """
    # MarkItDown не будет извлекать данные формы и аннотации, поэтому мокаем его пустой строкой
    mock_mid_result = MagicMock()
    mock_mid_result.text_content = "Основной текст PDF документа."

    with patch("src.rag.document_ingestor.MarkItDown.convert", return_value=mock_mid_result), \
         patch("src.api.endpoints.rag.rag_system.add_text", new_callable=AsyncMock) as mock_add_text:
        
        file_content = b"%PDF-1.4 mock pdf content with form and annotations"
        files = {"file": ("form_and_annotations.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = client.post("/api/v1/rag/index", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        mock_add_text.assert_called_once()
        final_content = mock_add_text.call_args.kwargs["text"]
        
        # Проверка основного текста
        assert "Основной текст PDF документа." in final_content
        # Проверка данных формы
        assert "--- PDF Form Data ---" in final_content
        assert "NameField: John Doe" in final_content
        assert "EmailField: john.doe@example.com" in final_content
        assert "AgeField: 30" in final_content
        assert "EmptyField:" not in final_content
        # Проверка аннотаций
        assert "--- PDF Annotations ---" in final_content
        assert "Comment by Author1: Comment 1 text" in final_content
        assert "Text Box: Free text box content" in final_content
        # Проверка метаданных
        assert data["metadata"]["author"] == "Test Author"
def test_document_ingestor_clean_text_logic():
    """Проверка очистки Markdown-ссылок и HTML-тегов."""
    ingestor = DocumentIngestor(settings={})
    raw_text = "Check [this link](https://example.com) and <br> <b>HTML</b>. Also ![image](img.png)"
    
    cleaned = ingestor._clean_text(raw_text)
    
    # Текст ссылки должен остаться, а URL и теги - исчезнуть
    assert "this link" in cleaned
    assert "https://example.com" not in cleaned
    assert "HTML" in cleaned
    assert "<b>" not in cleaned
    assert "img.png" not in cleaned

@pytest.mark.asyncio
async def test_document_ingestor_size_validation():
    """Проверка валидации размера файла (HTTP 413)."""
    ingestor = DocumentIngestor(settings={"max_file_size_mb": 1})
    
    mock_file = MagicMock()
    mock_file.filename = "large.pdf"
    mock_file.size = 2 * 1024 * 1024  # 2MB при лимите 1MB
    
    with pytest.raises(HTTPException) as excinfo:
        await ingestor.process_upload(mock_file)
    assert excinfo.value.status_code == 413

def test_document_ingestor_recursive_empty_lines_cleaning():
    """Проверка рекурсивной очистки текста от множественных пустых строк."""
    ingestor = DocumentIngestor(settings={})
    raw_text = "Line 1\n\n\n\nLine 2\n\n\nLine 3\n\n"
    
    cleaned = ingestor._clean_text(raw_text)
    
    # Должно быть не более двух пустых строк между абзацами
    expected_text = "Line 1\n\nLine 2\n\nLine 3"
    assert cleaned == expected_text

@pytest.mark.asyncio
async def test_index_zip_archive_integration():
    """
    Интеграционный тест: загрузка ZIP-архива.
    Проверяет, что DocumentIngestor корректно распаковывает и объединяет контент.
    """
    # 1. Создаем временный ZIP-файл
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        zf.writestr("file1.txt", "Content of file 1.")
        zf.writestr("nest/level1.txt", "Level 1 content.")
        zf.writestr("nest/sub/level2.md", "Level 2 content.")
        zf.writestr("empty.txt", "")
    zip_buffer.seek(0)

    # 2. Патчим rag_system.add_text
    with patch("src.api.endpoints.rag.rag_system.add_text", new_callable=AsyncMock) as mock_add_text:
        files = {"file": ("archive.zip", zip_buffer, "application/zip")}
        
        # 3. Выполнение запроса
        response = client.post("/api/v1/rag/index", files=files)
        
        # 4. Проверки
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["method"] == "ZipProcessor"
        
        mock_add_text.assert_called_once()
        called_kwargs = mock_add_text.call_args.kwargs
        
        # Проверяем наличие путей к вложенным файлам
        assert "--- File: file1.txt ---" in called_kwargs["text"]
        assert "--- File: nest/level1.txt ---" in called_kwargs["text"]
        assert "--- File: nest/sub/level2.md ---" in called_kwargs["text"]
        assert "Level 2 content." in called_kwargs["text"]
        assert called_kwargs["metadata"]["source"] == "archive.zip"
        assert called_kwargs["metadata"]["lang"] == "en" # Default mock language

@pytest.mark.asyncio
async def test_index_tar_gz_archive_integration():
    """
    Интеграционный тест: загрузка .tar.gz архива.
    Проверяет поддержку tar-форматов и корректность обработки DocumentIngestor.
    """
    # 1. Создаем временный tar.gz файл в памяти
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        content_bytes = b"Hello from inside a tarball"
        tarinfo = tarfile.TarInfo(name="inside/note.txt")
        tarinfo.size = len(content_bytes)
        tar.addfile(tarinfo, io.BytesIO(content_bytes))
    tar_buffer.seek(0)

    # 2. Патчим rag_system.add_text
    with patch("src.api.endpoints.rag.rag_system.add_text", new_callable=AsyncMock) as mock_add_text:
        files = {"file": ("data.tar.gz", tar_buffer, "application/gzip")}
        
        # 3. Выполнение запроса
        response = client.post("/api/v1/rag/index", files=files)
        
        # 4. Проверки
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["method"] == "TarProcessor"
        
        mock_add_text.assert_called_once()
        text_sent_to_rag = mock_add_text.call_args.kwargs["text"]
        assert "--- File: inside/note.txt ---" in text_sent_to_rag
        assert "Hello from inside a tarball" in text_sent_to_rag

@pytest.mark.asyncio
async def test_document_ingestor_ignores_technical_folders_in_archive():
    """
    Проверка того, что DocumentIngestor действительно игнорирует __pycache__
    и другие технические файлы/папки при распаковке архива.
    """
    # 1. Создаем ZIP-архив с валидным и невалидным контентом
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        zf.writestr("src/main.py", "print('hello')")
        zf.writestr("src/__pycache__/main.pyc", "compiled_garbage_content")
        zf.writestr(".git/config", "git_config_content")
        zf.writestr("docs/.DS_Store", "binary_noise")
    zip_buffer.seek(0)

    # 2. Патчим добавление в RAG
    with patch("src.api.endpoints.rag.rag_system.add_text", new_callable=AsyncMock) as mock_add_text:
        files = {"file": ("project.zip", zip_buffer, "application/zip")}

        # 3. Выполняем запрос к API
        response = client.post("/api/v1/rag/index", files=files)

        # 4. Проверки
        assert response.status_code == 200
        mock_add_text.assert_called_once()
        final_text = mock_add_text.call_args.kwargs["text"]

        # Валидный файл должен быть найден
        assert "src/main.py" in final_text
        assert "print('hello')" in final_text

        # Технический мусор должен отсутствовать
        assert "compiled_garbage_content" not in final_text
        assert "git_config_content" not in final_text
        assert "binary_noise" not in final_text
        assert "__pycache__" not in final_text

@pytest.mark.asyncio
async def test_index_password_protected_zip_behavior():
    """
    Проверка поведения при загрузке запароленного ZIP-архива.
    Ожидается, что система не сможет его распаковать и вернет ошибку обработки контента.
    """
    # 1. Создаем ZIP-архив с паролем. 
    # В стандартном zipfile установка пароля через setpassword() влияет на чтение, 
    # но для создания шифрованного архива требуются дополнительные усилия.
    # Мы имитируем ситуацию, когда extractall падает из-за отсутствия пароля.
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        # Добавляем файл, который потребует пароль при чтении (имитация)
        zf.writestr("secret.txt", "This is a secret message")
    
    zip_buffer.seek(0)
    
    # Патчим метод открытия ZIP так, чтобы он имитировал требование пароля при извлечении
    with patch("zipfile.ZipFile.extractall", side_effect=RuntimeError("Password required")):
        files = {"file": ("encrypted.zip", zip_buffer, "application/zip")}
        response = client.post("/api/v1/rag/index", files=files)
        
        # Так как extractall упал, контент пуст, и возвращается 422
        assert response.status_code == 422
        assert "Не удалось извлечь текст" in response.json()["detail"]

@pytest.mark.asyncio
async def test_document_ingestor_max_files_limit_hit():
    """
    Проверка блокировки архива при превышении параметра max_files_per_archive.
    """
    # 1. Создаем ZIP-архив с 5 файлами
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for i in range(5):
            zf.writestr(f"file_{i}.txt", f"Content {i}")
    zip_buffer.seek(0)

    # 2. Инициализируем инжектор с лимитом в 3 файла
    # Мы патчим настройки прямо в DocumentIngestor, который используется в эндпоинте
    with patch("src.api.endpoints.rag.ingestor.settings", {"max_files_per_archive": 3, "max_file_size_mb": 20}):
        files = {"file": ("many_files.zip", zip_buffer, "application/zip")}
        
        # 3. Выполняем запрос
        response = client.post("/api/v1/rag/index", files=files)
        
        # 4. Проверка
        # Ожидаем 413, так как 5 файлов > лимита 3
        assert response.status_code == 413
        assert "Слишком много файлов" in response.json()["detail"]

@pytest.mark.asyncio
async def test_document_ingestor_uncompressed_size_limit_hit():
    """
    Проверка блокировки Zip-бомбы по суммарному размеру распакованных файлов.
    """
    # 1. Создаем ZIP-архив с одним файлом размером 2МБ
    large_content = "X" * (2 * 1024 * 1024)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        zf.writestr("large.txt", large_content)
    zip_buffer.seek(0)

    # 2. Имитируем лимит в 1МБ
    patch_settings = {
        "max_uncompressed_size_mb": 1,
        "max_file_size_mb": 20,
        "max_files_per_archive": 1000
    }
    with patch("src.api.endpoints.rag.ingestor.settings", patch_settings):
        files = {"file": ("bomb.zip", zip_buffer, "application/zip")}
        response = client.post("/api/v1/rag/index", files=files)
        
        assert response.status_code == 413
        assert "Распакованный размер слишком велик" in response.json()["detail"]

@pytest.mark.asyncio
async def test_index_docx_with_ocr_integration():
    """
    Проверка извлечения текста из DOCX, включая OCR изображений.
    """
    # 1. Подготовка мока для MarkItDown (основной текст)
    mock_mid_result = MagicMock()
    mock_mid_result.text_content = "Основной текст документа Word."
    
    # 2. Текст, который мы ожидаем получить от OCR
    mock_ocr_text = "Текст, считанный с картинки внутри Word."
    
    # 3. Настройка патчей
    # Патчим MarkItDown и внутренний метод OCR ингестора
    with patch("src.rag.document_ingestor.MarkItDown.convert", return_value=mock_mid_result), \
         patch("src.rag.document_ingestor.DocumentIngestor._ocr_images_in_docx", new_callable=AsyncMock) as mock_ocr_func, \
         patch("src.api.endpoints.rag.rag_system.add_text", new_callable=AsyncMock) as mock_add_text:
        
        mock_ocr_func.return_value = f"--- OCR from image: image1.png ---\n{mock_ocr_text}"
        
        # Симуляция DOCX файла
        file_content = b"PK\x03\x04 fake docx"
        files = {"file": ("document_with_images.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        
        # 4. Выполнение запроса
        response = client.post("/api/v1/rag/index", files=files)
        
        # 5. Верификация
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Проверка объединения текстов в вызове RAG
        mock_add_text.assert_called_once()
        final_content = mock_add_text.call_args.kwargs["text"]
        assert "Основной текст документа Word." in final_content
        assert "Текст, считанный с картинки внутри Word." in final_content

@pytest.mark.asyncio
async def test_index_docx_with_comments_integration():
    """
    Проверка извлечения комментариев из DOCX файла.
    """
    mock_mid_result = MagicMock()
    mock_mid_result.text_content = "Основной контент документа."
    
    # Имитируем XML комментариев Word
    mock_comments_xml = b"""<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:comment w:author="Petr">
            <w:p><w:r><w:t>Это важное примечание</w:t></w:r></w:p>
        </w:comment>
    </w:comments>"""
    
    with patch("src.rag.document_ingestor.MarkItDown.convert", return_value=mock_mid_result), \
         patch("zipfile.ZipFile") as mock_zip_class, \
         patch("src.api.endpoints.rag.rag_system.add_text", new_callable=AsyncMock) as mock_add_text:
        
        mock_zip = mock_zip_class.return_value.__enter__.return_value
        mock_zip.namelist.return_value = ['word/comments.xml']
        mock_zip.read.return_value = mock_comments_xml
        
        file_content = b"PK\x03\x04 fake docx"
        files = {"file": ("doc_with_comments.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        
        response = client.post("/api/v1/rag/index", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        mock_add_text.assert_called_once()
        final_content = mock_add_text.call_args.kwargs["text"]
        assert "Comment by Petr: Это важное примечание" in final_content

@pytest.mark.asyncio
async def test_index_pdf_form_fields_extraction_logic():
    """
    Проверка корректности извлечения данных из PDF формы с несколькими заполненными полями.
    """
    # 1. Подготовка моков
    mock_mid_result = MagicMock()
    mock_mid_result.text_content = "Текст документа."
    
    # 2. Настройка патчей
    with patch("src.rag.document_ingestor.MarkItDown.convert", return_value=mock_mid_result), \
         patch("src.api.endpoints.rag.rag_system.add_text", new_callable=AsyncMock) as mock_add_text:
        
        # Симуляция PDF файла
        file_content = b"%PDF-1.4 mock content"
        files = {"file": ("form_test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        # 3. Выполнение запроса
        response = client.post("/api/v1/rag/index", files=files)
        
        # 4. Проверки
        assert response.status_code == 200
        mock_add_text.assert_called_once()
        final_content = mock_add_text.call_args.kwargs["text"]
        
        # Проверяем извлечение нескольких полей (используя данные из mock_pypdf2 фикстуры)
        assert "--- PDF Form Data ---" in final_content
        assert "NameField: John Doe" in final_content
        assert "EmailField: john.doe@example.com" in final_content
        assert "AgeField: 30" in final_content