# Training

**Файл:** `src/api/endpoints/training.py`  
**Тип:** `.py`

---

### `add_qa_pair` — Функция

```python
@router.post('/training/pairs')
```

Add a new QA training pair.

Args:
    request (dict): Fields:
        - question (str): User question.
        - answer_correct (str): Ideal answer.
        - answer_wrong (str, optional): Example of a bad answer.
        - source (str, optional): Origin tag. Default: "manual".
        - metadata (dict, optional): Extra fields.

Returns:
    dict: ``{success, pair}``

### `approve_pair` — Функция

```python
@router.patch('/training/pairs/{pair_id}/approve')
```

Approve a QA pair — mark it ready for training.

Args:
    pair_id (str): UUID of the pair.

Returns:
    dict: ``{success}``

### `reject_pair` — Функция

```python
@router.patch('/training/pairs/{pair_id}/reject')
```

Reject a QA pair — exclude it from training.

Args:
    pair_id (str): UUID of the pair.

Returns:
    dict: ``{success}``

### `delete_pair` — Функция

```python
@router.delete('/training/pairs/{pair_id}')
```

Permanently delete a QA pair.

Args:
    pair_id (str): UUID of the pair.

Returns:
    dict: ``{success}``

### `list_pairs` — Функция

```python
@router.get('/training/pairs')
```

List QA pairs with optional filtering.

Args:
    status (str, optional): pending / approved / rejected.
    source (str, optional): Filter by source tag.
    limit (int): Max results. Default 100.
    offset (int): Skip first N. Default 0.

Returns:
    dict: ``{success, pairs, total}``

### `get_pair` — Функция

```python
@router.get('/training/pairs/{pair_id}')
```

Get a single QA pair by ID.

Args:
    pair_id (str): UUID of the pair.

Returns:
    dict: ``{success, pair}``

### `training_stats` — Функция

```python
@router.get('/training/stats')
```

Return dataset statistics.

Returns:
    dict: ``{success, stats}`` where stats has total/pending/approved/rejected.

### `export_approved` — Функция

```python
@router.get('/training/export')
```

Export all approved QA pairs as JSON.

Returns:
    dict: ``{success, pairs, total}``

### `run_training` — Функция

```python
@router.post('/training/run')
```

Launch a fine-tuning run over approved QA pairs.

Args:
    request (dict): Fields:
        - strategy (str): "sft" / "dpo" / "lora". Default: "sft".
        - model_id (str, optional): Base model to fine-tune.
        - output_dir (str, optional): Output directory. Default: "training_output".
        - max_pairs (int, optional): Max approved pairs to use. Default: 10000.

Returns:
    dict: ``{success, result}``

Example:
    >>> # POST /api/v1/training/run
    >>> # {"strategy": "dpo", "model_id": "hf::mistral-7b-instruct"}


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
