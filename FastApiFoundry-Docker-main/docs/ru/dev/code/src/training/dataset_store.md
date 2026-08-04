# Dataset Store

**Файл:** `src/training/dataset_store.py`  
**Тип:** `.py`

---

### `QAPairStatus` — Класс

```python
class QAPairStatus(str, Enum)
```

Lifecycle status of a QA training pair.

### `QAPair` — Класс

```python
class QAPair
```

A single question-answer training example.

Attributes:
    id: Unique identifier (UUID4).
    question: The input question or user utterance.
    answer_correct: The ideal / ground-truth answer.
    answer_wrong: An example of a bad answer (used for preference training).
    status: Review status — pending / approved / rejected.
    source: Optional tag describing where this pair came from
            (e.g. "helpdesk", "manual", "synthetic").
    created_at: ISO-8601 creation timestamp.
    metadata: Arbitrary extra fields (model used, score, etc.).

Example:
    >>> pair = QAPair(
    ...     question="Как сбросить пароль?",
    ...     answer_correct="Перейдите в Настройки → Безопасность → Сбросить пароль.",
    ...     answer_wrong="Не знаю.",
    ...     source="helpdesk",
    ... )
    >>> pair.status
    <QAPairStatus.PENDING: 'pending'>

### `DatasetStore` — Класс

```python
class DatasetStore
```

Persistent store for QA training pairs.

Pairs are stored as JSONL (one JSON object per line) in
``<data_dir>/qa_pairs.jsonl``.  The file is read once on first access
and written on every mutation.

Args:
    data_dir: Directory where ``qa_pairs.jsonl`` is stored.
              Defaults to ``./training_data``.

Example:
    >>> store = DatasetStore()
    >>> pair = store.add("Что такое RAG?", "RAG — поиск + генерация.", "Не знаю.")
    >>> store.approve(pair.id)
    >>> approved = store.list(status=QAPairStatus.APPROVED)
    >>> len(approved)
    1

### `__init__` — Функция

```python
def __init__(self, question: str, answer_correct: str, answer_wrong: str='', source: str='manual', status: QAPairStatus=QAPairStatus.PENDING, id: Optional[str]=None, created_at: Optional[str]=None, metadata: Optional[dict]=None) -> None
```

### `to_dict` — Функция

```python
def to_dict(self) -> dict
```

Serialize to a plain dict (for JSONL storage).

### `from_dict` — Функция

```python
@classmethod
```

Deserialize from a plain dict.

### `__init__` — Функция

```python
def __init__(self, data_dir: Optional[Path]=None) -> None
```

### `_load` — Функция

```python
def _load(self) -> None
```

Load pairs from JSONL file (lazy, called once).

### `_save` — Функция

```python
def _save(self) -> None
```

Persist all pairs to JSONL file.

### `add` — Функция

```python
def add(self, question: str, answer_correct: str, answer_wrong: str='', source: str='manual', metadata: Optional[dict]=None) -> QAPair
```

Add a new QA pair with PENDING status.

Args:
    question: User question or prompt.
    answer_correct: Ground-truth / ideal answer.
    answer_wrong: Example of a bad answer (optional but recommended).
    source: Origin tag — "helpdesk", "manual", "synthetic", etc.
    metadata: Arbitrary extra fields.

Returns:
    QAPair: The newly created pair.

### `get` — Функция

```python
def get(self, pair_id: str) -> Optional[QAPair]
```

Get a pair by ID.

Args:
    pair_id: UUID of the pair.

Returns:
    QAPair or None if not found.

### `list` — Функция

```python
def list(self, status: Optional[QAPairStatus]=None, source: Optional[str]=None, limit: int=1000, offset: int=0) -> List[QAPair]
```

List pairs with optional filtering.

Args:
    status: Filter by status (pending / approved / rejected).
    source: Filter by source tag.
    limit: Maximum number of results.
    offset: Skip first N results.

Returns:
    List[QAPair]: Matching pairs.

### `_set_status` — Функция

```python
def _set_status(self, pair_id: str, status: QAPairStatus) -> bool
```

Internal: change status of a pair by ID.

### `approve` — Функция

```python
def approve(self, pair_id: str) -> bool
```

Mark a pair as approved (ready for training).

Args:
    pair_id: UUID of the pair.

Returns:
    bool: True if found and updated.

### `reject` — Функция

```python
def reject(self, pair_id: str) -> bool
```

Mark a pair as rejected (excluded from training).

Args:
    pair_id: UUID of the pair.

Returns:
    bool: True if found and updated.

### `delete` — Функция

```python
def delete(self, pair_id: str) -> bool
```

Permanently delete a pair.

Args:
    pair_id: UUID of the pair.

Returns:
    bool: True if found and deleted.

### `stats` — Функция

```python
def stats(self) -> dict
```

Return counts by status.

Returns:
    dict: {"total": N, "pending": N, "approved": N, "rejected": N}

### `export_approved` — Функция

```python
def export_approved(self) -> List[dict]
```

Export all approved pairs as plain dicts (for training pipeline).

Returns:
    List[dict]: Approved QA pairs serialized as dicts.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
