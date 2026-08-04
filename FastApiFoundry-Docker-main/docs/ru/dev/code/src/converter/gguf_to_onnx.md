# Gguf To Onnx

**Файл:** `src/converter/gguf_to_onnx.py`  
**Тип:** `.py`

---

### `ConversionResult` — Класс

```python
@dataclass
```

### `GGUFConverter` — Класс

```python
class GGUFConverter
```

Конвертер GGUF → ONNX с опциональной оптимизацией

### `convert` — Функция

```python
async def convert(self, gguf_path: str, output_dir: str, model_type: str='gpt2', opset: int=17, optimize: bool=True) -> ConversionResult
```

Конвертировать .gguf файл в ONNX.

Args:
    gguf_path: Путь к .gguf файлу
    output_dir: Директория для сохранения результата
    model_type: Тип модели для оптимизатора ('gpt2', 'bert', 'bart')
    opset: Версия ONNX opset
    optimize: Запустить оптимизацию после экспорта

Returns:
    ConversionResult с путями и статусом

### `_export` — Функция

```python
def _export(self, gguf_path: str, output_dir: str, opset: int) -> ConversionResult
```

Экспорт модели через optimum (синхронный, запускается в executor)

### `_optimize` — Функция

```python
def _optimize(self, onnx_path: str, model_type: str) -> str
```

Оптимизация ONNX модели (синхронная, запускается в executor)

### `is_available` — Функция

```python
@staticmethod
```

Проверить доступность зависимостей


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
