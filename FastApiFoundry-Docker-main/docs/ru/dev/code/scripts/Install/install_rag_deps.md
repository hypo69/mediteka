# Install Rag Deps

**Файл:** `scripts/Install/install_rag_deps.py`  
**Тип:** `.py`

---

### `check_cuda` — Функция

```python
def check_cuda() -> bool
```

Простая проверка наличия NVIDIA GPU через nvidia-smi.

### `check_disk_space` — Функция

```python
def check_disk_space(required_gb: int=5) -> bool
```

Проверка свободного места (по умолчанию нужно 5 ГБ).

### `get_rag_packages_from_file` — Функция

```python
def get_rag_packages_from_file(req_path: Path) -> dict
```

Читает требования из requirements.txt и адаптирует под GPU/CPU.

### `get_import_name` — Функция

```python
def get_import_name(pkg_name: str) -> str
```

Сопоставление имени пакета pip с именем для import.

### `is_installed` — Функция

```python
def is_installed(import_name: str) -> bool
```

Проверка наличия пакета через импорт.

### `install_package` — Функция

```python
def install_package(package: str) -> bool
```

Установка пакета через pip со стримингом вывода.

### `main` — Функция

```python
def main() -> None
```

Основной цикл проверки и установки RAG-зависимостей.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
