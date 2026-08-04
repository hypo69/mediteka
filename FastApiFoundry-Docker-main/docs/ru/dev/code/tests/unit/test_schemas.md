# Test Schemas

**Файл:** `tests/unit/test_schemas.py`  
**Тип:** `.py`

---

### `_is_valid_uuid4` — Функция

```python
def _is_valid_uuid4(s: str) -> bool
```

Return True if *s* is a valid UUID v4 string.

### `test_message_record_round_trip` — Функция

```python
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
```

**Validates: Requirements 2.1, 9.5**

Property 1: Round-trip сериализации Pydantic-схем.

For any valid MessageRecord, serialising via model_dump() and then
deserialising via model_validate() must produce an equivalent object.

### `test_session_record_round_trip` — Функция

```python
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
```

**Validates: Requirements 2.2**

Property 2: Round-trip сериализации SessionRecord.

For any valid SessionRecord, serialising via model_dump() and then
deserialising via model_validate() must produce an equivalent object.

### `test_whitespace_content_raises_validation_error` — Функция

```python
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
```

**Validates: Requirements 2.7**

Property 3: Валидация пустого content.

For any string consisting solely of whitespace characters (including the
empty string), creating a SaveMessageRequest with that content must raise
a Pydantic ValidationError.

### `test_non_uuid_session_id_raises_validation_error` — Функция

```python
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
```

**Validates: Requirements 2.8**

Property 4: Валидация session_id не-UUID.

For any string that is not a valid UUID v4, creating a SaveMessageRequest
with that session_id must raise a Pydantic ValidationError.

### `TestSaveMessageRequestEdgeCases` — Класс

```python
class TestSaveMessageRequestEdgeCases
```

Unit tests for SaveMessageRequest boundary values.

### `test_empty_content_raises_validation_error` — Функция

```python
def test_empty_content_raises_validation_error(self) -> None
```

Empty string content must raise ValidationError.

### `test_whitespace_only_content_raises_validation_error` — Функция

```python
def test_whitespace_only_content_raises_validation_error(self) -> None
```

Content consisting only of spaces must raise ValidationError.

### `test_tab_newline_content_raises_validation_error` — Функция

```python
def test_tab_newline_content_raises_validation_error(self) -> None
```

Content consisting only of tabs and newlines must raise ValidationError.

### `test_invalid_role_raises_validation_error` — Функция

```python
def test_invalid_role_raises_validation_error(self) -> None
```

An unrecognised role value must raise ValidationError.

### `test_invalid_session_id_format_raises_validation_error` — Функция

```python
def test_invalid_session_id_format_raises_validation_error(self) -> None
```

A non-UUID session_id must raise ValidationError.

### `test_uuid_v1_session_id_raises_validation_error` — Функция

```python
def test_uuid_v1_session_id_raises_validation_error(self) -> None
```

A UUID v1 (not v4) session_id must raise ValidationError.

### `test_content_10000_chars_succeeds` — Функция

```python
def test_content_10000_chars_succeeds(self) -> None
```

Content of exactly 10,000 characters must be accepted.

### `test_valid_request_succeeds` — Функция

```python
def test_valid_request_succeeds(self) -> None
```

A fully valid SaveMessageRequest must be created without errors.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
