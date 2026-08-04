# Trainer

**Файл:** `src/training/trainer.py`  
**Тип:** `.py`

---

### `TrainingStrategy` — Класс

```python
class TrainingStrategy(str, Enum)
```

Available fine-tuning strategies.

Attributes:
    SFT:  Supervised Fine-Tuning — trains on (question, correct_answer) pairs.
    DPO:  Direct Preference Optimization — trains on
          (question, correct_answer, wrong_answer) triples.
    LORA: LoRA adapter training — parameter-efficient, low VRAM.

### `TrainingResult` — Класс

```python
class TrainingResult
```

Result returned by a training run.

Attributes:
    success: Whether the run completed without fatal errors.
    strategy: Which strategy was used.
    pairs_used: Number of QA pairs included in training.
    message: Human-readable status or error description.
    artifacts: Paths to output files (adapter weights, logs, etc.).

### `FineTuner` — Класс

```python
class FineTuner
```

Orchestrates fine-tuning runs over the QA dataset.

Selects approved pairs from DatasetStore and dispatches to the
appropriate training strategy.  All strategies are currently stubs
that log intent and return a placeholder result — they will be
implemented in future versions.

Args:
    store: DatasetStore instance. Defaults to the module singleton.

Example:
    >>> tuner = FineTuner()
    >>> result = tuner.run(strategy=TrainingStrategy.DPO, model_id="hf::mistral-7b")
    >>> result.success
    True
    >>> result.message
    'DPO training scheduled (not yet implemented)'

### `__init__` — Функция

```python
def __init__(self, success: bool, strategy: TrainingStrategy, pairs_used: int, message: str, artifacts: Optional[dict]=None) -> None
```

### `to_dict` — Функция

```python
def to_dict(self) -> dict
```

### `__init__` — Функция

```python
def __init__(self, store: Optional[DatasetStore]=None) -> None
```

### `run` — Функция

```python
def run(self, strategy: TrainingStrategy=TrainingStrategy.SFT, model_id: str='', output_dir: str='training_output', max_pairs: int=10000) -> TrainingResult
```

Launch a training run.

Loads approved QA pairs and dispatches to the selected strategy.

Args:
    strategy: Training method — sft / dpo / lora.
    model_id: Base model to fine-tune (e.g. ``hf::mistral-7b-instruct``).
    output_dir: Directory for saving adapter weights and logs.
    max_pairs: Maximum number of approved pairs to use.

Returns:
    TrainingResult: Outcome of the run.

### `_run_sft` — Функция

```python
def _run_sft(self, pairs: List[QAPair], model_id: str, output_dir: str) -> TrainingResult
```

Supervised Fine-Tuning stub.

Trains on (question → correct_answer) pairs using cross-entropy loss.
Will use HuggingFace Trainer in the full implementation.

### `_run_dpo` — Функция

```python
def _run_dpo(self, pairs: List[QAPair], model_id: str, output_dir: str) -> TrainingResult
```

Direct Preference Optimization stub.

Trains on (question, correct_answer, wrong_answer) triples.
Requires answer_wrong to be non-empty.
Will use TRL DPOTrainer in the full implementation.

### `_run_lora` — Функция

```python
def _run_lora(self, pairs: List[QAPair], model_id: str, output_dir: str) -> TrainingResult
```

LoRA adapter training stub.

Parameter-efficient fine-tuning via Low-Rank Adaptation.
Requires much less VRAM than full fine-tuning.
Will use PEFT + HuggingFace Trainer in the full implementation.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
