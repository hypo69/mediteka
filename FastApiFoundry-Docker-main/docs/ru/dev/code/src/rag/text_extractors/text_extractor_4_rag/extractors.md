# Extractors

**Файл:** `src/rag/text_extractors/text_extractor_4_rag/extractors.py`  
**Тип:** `.py`

---

### `TextExtractor` — Класс

```python
class TextExtractor
```

Класс для извлечения текста из файлов различных форматов.

### `__init__` — Функция

```python
def __init__(self)
```

Инициализация экстрактора текста.

### `extract_text` — Функция

```python
def extract_text(self, file_content: bytes, filename: str) -> List[Dict[str, Any]]
```

Основной метод извлечения текста (теперь синхронный для выполнения в threadpool).

### `_extract_text_by_format` — Функция

```python
def _extract_text_by_format(self, content: bytes, extension: str, filename: str) -> str
```

Извлечение текста в зависимости от формата (синхронная версия).

### `_get_extraction_methods_mapping` — Функция

```python
def _get_extraction_methods_mapping(self) -> dict
```

Получение словаря сопоставления расширений с методами извлечения.

### `_get_group_extraction_methods` — Функция

```python
def _get_group_extraction_methods(self) -> list
```

Получение списка групп расширений с соответствующими методами.

### `_extract_from_pdf_sync` — Функция

```python
def _extract_from_pdf_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из PDF.

### `_extract_pdf_page_content` — Функция

```python
def _extract_pdf_page_content(self, page, page_num: int) -> list
```

Извлечение содержимого страницы PDF.

### `_extract_pdf_page_images` — Функция

```python
def _extract_pdf_page_images(self, page) -> list
```

Извлечение текста из изображений на странице PDF.

### `_cleanup_temp_file` — Функция

```python
def _cleanup_temp_file(self, temp_file_path: str) -> None
```

Безопасное удаление временного файла.

### `_extract_from_docx_sync` — Функция

```python
def _extract_from_docx_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из DOCX с полным извлечением согласно п.3.3 ТЗ.

### `_extract_docx_paragraphs` — Функция

```python
def _extract_docx_paragraphs(self, doc) -> list
```

Извлечение основного текста из параграфов DOCX.

### `_extract_docx_tables` — Функция

```python
def _extract_docx_tables(self, doc) -> list
```

Извлечение текста из таблиц DOCX.

### `_extract_docx_headers_footers` — Функция

```python
def _extract_docx_headers_footers(self, doc) -> list
```

Извлечение текста из колонтитулов DOCX.

### `_extract_section_text` — Функция

```python
def _extract_section_text(self, paragraphs) -> list
```

Извлечение текста из параграфов секции.

### `_extract_docx_footnotes` — Функция

```python
def _extract_docx_footnotes(self, doc) -> list
```

Извлечение сносок из DOCX.

### `_extract_docx_comments` — Функция

```python
def _extract_docx_comments(self, doc) -> list
```

Извлечение комментариев из DOCX.

### `_extract_from_doc_sync` — Функция

```python
def _extract_from_doc_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из DOC через конвертацию в DOCX с помощью LibreOffice.

### `_extract_from_excel_sync` — Функция

```python
def _extract_from_excel_sync(self, content: bytes) -> str
```

Синхронное извлечение данных из Excel файлов.

### `_extract_from_csv_sync` — Функция

```python
def _extract_from_csv_sync(self, content: bytes) -> str
```

Синхронное извлечение данных из CSV файлов.

### `_extract_from_pptx_sync` — Функция

```python
def _extract_from_pptx_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из PPTX с полным извлечением согласно п.3.3 ТЗ.

### `_extract_from_ppt_sync` — Функция

```python
def _extract_from_ppt_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из PPT через конвертацию в PPTX с помощью LibreOffice.

### `_extract_from_txt_sync` — Функция

```python
def _extract_from_txt_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из TXT файлов.

### `_decode_text_content` — Функция

```python
def _decode_text_content(self, content: bytes) -> str
```

Декодирование содержимого с автоопределением кодировки.

### `_get_encoding_list` — Функция

```python
def _get_encoding_list(self) -> list
```

Получение списка кодировок для проверки.

### `_try_decode_with_encoding` — Функция

```python
def _try_decode_with_encoding(self, content: bytes, encoding: str) -> str
```

Попытка декодирования с проверкой качества.

### `_is_decoding_quality_good` — Функция

```python
def _is_decoding_quality_good(self, text: str) -> bool
```

Проверка качества декодирования по количеству заменяющих символов.

### `_is_mac_cyrillic_valid` — Функция

```python
def _is_mac_cyrillic_valid(self, text: str, encoding: str) -> bool
```

Дополнительная валидация для mac-cyrillic кодировки.

### `_has_suspicious_start_chars` — Функция

```python
def _has_suspicious_start_chars(self, text: str) -> bool
```

Проверка на подозрительные символы в начале текста.

### `_has_valid_cyrillic_ratio` — Функция

```python
def _has_valid_cyrillic_ratio(self, text: str) -> bool
```

Проверка соотношения кириллицы и латиницы.

### `_extract_from_source_code_sync` — Функция

```python
def _extract_from_source_code_sync(self, content: bytes, extension: str, filename: str) -> str
```

Синхронное извлечение текста из файлов исходного кода.

### `_format_source_code_output` — Функция

```python
def _format_source_code_output(self, text: str, extension: str, filename: str) -> str
```

Форматирование вывода для файлов исходного кода.

### `_get_programming_language` — Функция

```python
def _get_programming_language(self, extension: str) -> str
```

Определение языка программирования по расширению файла.

### `_get_language_map` — Функция

```python
def _get_language_map(self) -> dict
```

Получение словаря соответствия расширений языкам программирования.

### `_create_source_code_header` — Функция

```python
def _create_source_code_header(self, language: str, filename: str, text: str) -> str
```

Создание заголовка для файла исходного кода.

### `_extract_from_html_sync` — Функция

```python
def _extract_from_html_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из HTML.

### `_extract_from_markdown_sync` — Функция

```python
def _extract_from_markdown_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из Markdown.

### `_extract_from_json_sync` — Функция

```python
def _extract_from_json_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из JSON.

### `_extract_from_rtf_sync` — Функция

```python
def _extract_from_rtf_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из RTF.

### `_extract_from_xml_sync` — Функция

```python
def _extract_from_xml_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из XML.

### `_extract_from_yaml_sync` — Функция

```python
def _extract_from_yaml_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из YAML.

### `_extract_yaml_strings` — Функция

```python
def _extract_yaml_strings(self, obj, path='') -> list
```

Рекурсивное извлечение всех строковых значений из YAML.

### `_extract_yaml_dict_strings` — Функция

```python
def _extract_yaml_dict_strings(self, obj_dict: dict, path: str) -> list
```

Извлечение строк из словаря YAML.

### `_extract_yaml_list_strings` — Функция

```python
def _extract_yaml_list_strings(self, obj_list: list, path: str) -> list
```

Извлечение строк из списка YAML.

### `_extract_from_odt_sync` — Функция

```python
def _extract_from_odt_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из ODT.

### `_extract_from_epub_sync` — Функция

```python
def _extract_from_epub_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из EPUB.

### `_should_stop_epub_extraction` — Функция

```python
def _should_stop_epub_extraction(self, current_size: int, file_size: int) -> bool
```

Проверка лимита размера для EPUB.

### `_is_epub_html_file` — Функция

```python
def _is_epub_html_file(self, filename: str) -> bool
```

Проверка является ли файл HTML для EPUB.

### `_extract_epub_html_text` — Функция

```python
def _extract_epub_html_text(self, zip_ref, file_info) -> tuple
```

Извлечение текста из HTML файла EPUB.

### `_extract_from_eml_sync` — Функция

```python
def _extract_from_eml_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из EML.

### `_decode_eml_content` — Функция

```python
def _decode_eml_content(self, content: bytes) -> str
```

Декодирование содержимого EML файла.

### `_extract_eml_headers` — Функция

```python
def _extract_eml_headers(self, msg) -> list
```

Извлечение заголовков из EML.

### `_decode_eml_header` — Функция

```python
def _decode_eml_header(self, value: str, decode_header_func) -> str
```

Декодирование заголовка EML.

### `_extract_eml_body_multipart` — Функция

```python
def _extract_eml_body_multipart(self, msg) -> list
```

Извлечение тела многочастного EML письма.

### `_extract_eml_body_simple` — Функция

```python
def _extract_eml_body_simple(self, msg) -> list
```

Извлечение тела простого EML письма.

### `_extract_eml_part_text` — Функция

```python
def _extract_eml_part_text(self, part, content_type: str) -> str
```

Извлечение текста из части EML.

### `_decode_payload` — Функция

```python
def _decode_payload(self, payload: bytes, charset: str) -> str
```

Декодирование payload с обработкой ошибок.

### `_extract_from_msg_sync` — Функция

```python
def _extract_from_msg_sync(self, content: bytes) -> str
```

Синхронное извлечение текста из MSG.

### `_extract_utf16_text_from_msg` — Функция

```python
def _extract_utf16_text_from_msg(self, content: bytes) -> list
```

Извлечение UTF-16 текста из MSG файла.

### `_clean_msg_lines` — Функция

```python
def _clean_msg_lines(self, lines: list) -> list
```

Очистка строк MSG от управляющих символов.

### `_is_valid_msg_line` — Функция

```python
def _is_valid_msg_line(self, line: str) -> bool
```

Проверка валидности строки MSG.

### `_filter_unique_lines` — Функция

```python
def _filter_unique_lines(self, lines: list, min_length: int=5) -> list
```

Фильтрация уникальных строк с минимальной длиной.

### `_extract_ascii_text_from_msg` — Функция

```python
def _extract_ascii_text_from_msg(self, content: bytes, existing_text_parts: list) -> list
```

Извлечение ASCII текста из MSG файла.

### `_is_valid_ascii_line` — Функция

```python
def _is_valid_ascii_line(self, line: str, existing_parts: list) -> bool
```

Проверка валидности ASCII строки.

### `_safe_tesseract_ocr` — Функция

```python
def _safe_tesseract_ocr(self, image, temp_image_path: str=None) -> str
```

Безопасный вызов Tesseract с ограничениями ресурсов.

Args:
    image: PIL Image объект
    temp_image_path: Путь к временному файлу (если None, создается автоматически)

Returns:
    str: Распознанный текст

### `_extract_from_image_sync` — Функция

```python
def _extract_from_image_sync(self, content: bytes) -> str
```

Синхронный OCR изображения.

### `_check_mime_type` — Функция

```python
def _check_mime_type(self, content: bytes, filename: str) -> bool
```

Проверка MIME-типа файла для предотвращения подделки расширений.

### `_extract_from_archive` — Функция

```python
def _extract_from_archive(self, content: bytes, filename: str, nesting_level: int=0) -> List[Dict[str, Any]]
```

Безопасное извлечение файлов из архива.

### `_extract_zip_files` — Функция

```python
def _extract_zip_files(self, archive_path: Path, extract_dir: Path, archive_name: str, nesting_level: int) -> List[Dict[str, Any]]
```

Извлечение файлов из ZIP-архива.

### `_validate_zip_size` — Функция

```python
def _validate_zip_size(self, zip_ref) -> None
```

Проверка размера файлов в ZIP-архиве для защиты от zip bomb.

### `_process_zip_files` — Функция

```python
def _process_zip_files(self, zip_ref, extract_dir: Path, archive_name: str, nesting_level: int) -> List[Dict[str, Any]]
```

Обработка всех файлов в ZIP-архиве.

### `_extract_single_zip_file` — Функция

```python
def _extract_single_zip_file(self, info, zip_ref, extract_dir: Path, archive_name: str, nesting_level: int) -> List[Dict[str, Any]]
```

Извлечение и обработка одного файла из ZIP-архива.

### `_extract_tar_files` — Функция

```python
def _extract_tar_files(self, archive_path: Path, extract_dir: Path, archive_name: str, nesting_level: int) -> List[Dict[str, Any]]
```

Извлечение файлов из TAR-архива.

### `_extract_rar_files` — Функция

```python
def _extract_rar_files(self, archive_path: Path, extract_dir: Path, archive_name: str, nesting_level: int) -> List[Dict[str, Any]]
```

Извлечение файлов из RAR-архива.

### `_extract_7z_files` — Функция

```python
def _extract_7z_files(self, archive_path: Path, extract_dir: Path, archive_name: str, nesting_level: int) -> List[Dict[str, Any]]
```

Извлечение файлов из 7Z-архива.

### `_process_extracted_file` — Функция

```python
def _process_extracted_file(self, content: bytes, filename: str, basename: str, archive_name: str, nesting_level: int) -> Optional[List[Dict[str, Any]]]
```

Обработка извлеченного файла.

### `_sanitize_archive_filename` — Функция

```python
def _sanitize_archive_filename(self, filename: str) -> str
```

Санитизация имени файла из архива.

### `_is_system_file` — Функция

```python
def _is_system_file(self, filename: str) -> bool
```

Проверка, является ли файл системным.

### `_ocr_from_pdf_image_sync` — Функция

```python
def _ocr_from_pdf_image_sync(self, page, img_info) -> str
```

Синхронный OCR изображения из PDF.

### `_extract_page_with_playwright` — Функция

```python
def _extract_page_with_playwright(self, url: str, user_agent: Optional[str]=None, extraction_options: Optional[Any]=None) -> tuple[str, str]
```

Извлечение HTML контента страницы с помощью Playwright (с поддержкой JS, обновлено в v1.10.2).

Args:
    url: URL страницы
    user_agent: Пользовательский User-Agent
    extraction_options: Настройки извлечения

Returns:
    tuple[str, str]: (html_content, final_url)

### `_safe_scroll_for_lazy_loading` — Функция

```python
def _safe_scroll_for_lazy_loading(self, page, extraction_options: Optional[Any]=None) -> None
```

Безопасный скролл страницы для активации lazy loading с защитой от бесконечности (обновлено в v1.10.2).

Args:
    page: Playwright page объект
    extraction_options: Настройки извлечения

### `_determine_content_type` — Функция

```python
def _determine_content_type(self, url: str, user_agent: Optional[str]=None, extraction_options: Optional[Any]=None) -> tuple[str, str]
```

Определение типа контента через HEAD запрос (новое в v1.10.3).

Args:
    url: URL для проверки
    user_agent: Пользовательский User-Agent
    extraction_options: Настройки извлечения

Returns:
    tuple[str, str]: (content_type, final_url) - тип контента и финальный URL после редиректов

### `_is_html_content` — Функция

```python
def _is_html_content(self, content_type: str, url: str) -> bool
```

Определение является ли контент HTML страницей (новое в v1.10.3).

Args:
    content_type: MIME тип из заголовков
    url: URL для анализа расширения как fallback

Returns:
    bool: True если это HTML страница

### `_download_and_extract_file` — Функция

```python
def _download_and_extract_file(self, url: str, user_agent: Optional[str]=None, extraction_options: Optional[Any]=None) -> List[Dict[str, Any]]
```

Скачивание файла по URL и его обработка как обычного файла (новое в v1.10.3).

Args:
    url: URL файла для скачивания
    user_agent: Пользовательский User-Agent
    extraction_options: Настройки извлечения

Returns:
    List[Dict[str, Any]]: Результат извлечения текста как от /v1/extract/file

### `_extract_filename_from_response` — Функция

```python
def _extract_filename_from_response(self, response, url: str) -> str
```

Извлечение имени файла из HTTP ответа (новое в v1.10.3).

Args:
    response: HTTP ответ requests
    url: Исходный URL

Returns:
    str: Имя файла

### `_get_extension_from_content_type` — Функция

```python
def _get_extension_from_content_type(self, content_type: str) -> Optional[str]
```

Определение расширения файла по Content-Type (новое в v1.10.3).

Args:
    content_type: MIME тип

Returns:
    Optional[str]: Расширение файла или None

### `extract_from_url` — Функция

```python
def extract_from_url(self, url: str, user_agent: Optional[str]=None, extraction_options: Optional[Any]=None) -> List[Dict[str, Any]]
```

Извлечение текста с веб-страницы или файла по URL (обновлено в v1.10.3).

### `_extract_html_page` — Функция

```python
def _extract_html_page(self, url: str, user_agent: Optional[str]=None, extraction_options: Optional[Any]=None) -> List[Dict[str, Any]]
```

Извлечение текста с HTML страницы (выделено из extract_from_url в v1.10.3).

Args:
    url: URL HTML страницы
    user_agent: Пользовательский User-Agent
    extraction_options: Настройки извлечения

Returns:
    List[Dict[str, Any]]: Результат извлечения текста со страницы

### `_extract_page_with_requests` — Функция

```python
def _extract_page_with_requests(self, url: str, user_agent: Optional[str]=None, extraction_options: Optional[Any]=None) -> tuple[str, str]
```

Извлечение HTML контента страницы с помощью requests (без JS, обновлено в v1.10.2).

Args:
    url: URL страницы
    user_agent: Пользовательский User-Agent
    extraction_options: Настройки извлечения

Returns:
    tuple[str, str]: (html_content, final_url)

### `_is_safe_url` — Функция

```python
def _is_safe_url(self, url: str) -> bool
```

Проверка безопасности URL (защита от SSRF).

### `_check_url_scheme` — Функция

```python
def _check_url_scheme(self, scheme: str) -> bool
```

Проверка схемы URL.

### `_check_hostname_not_blocked` — Функция

```python
def _check_hostname_not_blocked(self, hostname: str, url: str) -> bool
```

Проверка, что hostname не заблокирован.

### `_resolve_hostname_ips` — Функция

```python
def _resolve_hostname_ips(self, hostname: str) -> list
```

Разрешение IP-адресов для hostname.

### `_check_all_ips_safe` — Функция

```python
def _check_all_ips_safe(self, ips: list, url: str) -> bool
```

Проверка безопасности всех IP-адресов.

### `_check_single_ip_safe` — Функция

```python
def _check_single_ip_safe(self, ip_str: str, url: str) -> bool
```

Проверка безопасности одного IP-адреса.

### `_is_special_ip_unsafe` — Функция

```python
def _is_special_ip_unsafe(self, ip_obj, ip_str: str, url: str) -> bool
```

Проверка на специальные небезопасные IP.

### `_is_ip_in_blocked_ranges` — Функция

```python
def _is_ip_in_blocked_ranges(self, ip_obj, ip_str: str, url: str) -> bool
```

Проверка IP на принадлежность заблокированным диапазонам.

### `_is_metadata_service_ip` — Функция

```python
def _is_metadata_service_ip(self, ip_obj, ip_str: str, url: str) -> bool
```

Проверка на metadata service IP.

### `_is_docker_bridge_ip` — Функция

```python
def _is_docker_bridge_ip(self, ip_obj, ip_str: str, url: str) -> bool
```

Проверка на Docker bridge gateway IP.

### `_extract_text_from_html` — Функция

```python
def _extract_text_from_html(self, html_content: str) -> str
```

Извлечение текста из HTML контента.

### `_extract_images_from_html` — Функция

```python
def _extract_images_from_html(self, html_content: str, base_url: str, extraction_options: Optional[Any]=None) -> List[Dict[str, Any]]
```

Извлечение и обработка изображений со страницы (обновлено в v1.10.2).

### `_setup_image_extraction_options` — Функция

```python
def _setup_image_extraction_options(self, extraction_options: Optional[Any]) -> dict
```

Настройка параметров извлечения изображений.

### `_parse_images_from_html` — Функция

```python
def _parse_images_from_html(self, html_content: str, max_images: int) -> list
```

Парсинг изображений из HTML контента.

### `_categorize_images` — Функция

```python
def _categorize_images(self, img_tags: list, enable_base64: bool) -> tuple
```

Категоризация изображений на base64 и URL.

### `_process_base64_images` — Функция

```python
def _process_base64_images(self, base64_images: list, extraction_options: Optional[Any]) -> list
```

Обработка base64 изображений.

### `_process_url_images` — Функция

```python
def _process_url_images(self, url_images: list, base_url: str, extraction_options: Optional[Any]) -> list
```

Обработка URL изображений.

### `_process_images_batch` — Функция

```python
def _process_images_batch(self, batch: list, base_url: str, extraction_options: Optional[Any], timeout: int) -> list
```

Обработка группы изображений параллельно.

### `_process_single_image` — Функция

```python
def _process_single_image(self, img_tag, base_url: str, extraction_options: Optional[Any]=None) -> Optional[Dict[str, Any]]
```

Обработка одного изображения (обновлено в v1.10.2).

### `_process_base64_image` — Функция

```python
def _process_base64_image(self, img_tag, extraction_options: Optional[Any]=None) -> Optional[Dict[str, Any]]
```

Обработка base64 изображения из data URI (обновлено в v1.10.2).

### `extract_strings` — Функция

```python
def extract_strings(obj, path='')
```

### `extract_from_element` — Функция

```python
def extract_from_element(elem, path='')
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
