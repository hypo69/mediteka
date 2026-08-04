# Rag Profile Manager

**Файл:** `src/rag/rag_profile_manager.py`  
**Тип:** `.py`

---

### `RAGProfileManager` — Класс

```python
class RAGProfileManager
```

Manages named RAG index profiles under the base rag directory.

### `parse_rag_readme` — Функция

```python
def parse_rag_readme(profile_dir: Path) -> Dict[str, str]
```

Read README.md metadata for a RAG profile.

The first Markdown H1 is the title. The first non-empty paragraph after it
is the short purpose/description shown in the API and UI.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `list_profiles` — Функция

```python
def list_profiles(self) -> List[Dict]
```

Return all available RAG profiles with metadata.

Returns:
    List[Dict]: Each item has keys: name, path, has_index, description.

### `get_profile_path` — Функция

```python
def get_profile_path(self, name: str) -> Optional[Path]
```

Return path for a named profile, or None if it doesn't exist.

Args:
    name (str): Profile name (directory name under ~/.ai-assist/rag/).

Returns:
    Optional[Path]: Path to profile directory or None.

### `create_profile` — Функция

```python
def create_profile(self, name: str, description: str='') -> Path
```

Create a new profile directory.

Args:
    name (str): Profile name.
    description (str): Optional description saved to description.txt.

Returns:
    Path: Created profile directory.

### `delete_profile` — Функция

```python
def delete_profile(self, name: str) -> bool
```

Rename profile directory with ~ suffix (soft delete).

Args:
    name (str): Profile name to delete.

Returns:
    bool: True if renamed, False if not found.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
