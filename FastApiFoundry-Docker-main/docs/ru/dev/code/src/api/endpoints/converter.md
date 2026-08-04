# Converter

**Файл:** `src/api/endpoints/converter.py`  
**Тип:** `.py`

---

### `ConvertRequest` — Класс

```python
class ConvertRequest(BaseModel)
```

### `converter_status` — Функция

```python
@router.get('/status')
```

Проверить доступность зависимостей конвертера

### `convert_gguf` — Функция

```python
@router.post('/convert')
```

Конвертировать .gguf файл в ONNX.

- **gguf_path**: путь к .gguf файлу на сервере
- **output_dir**: директория для сохранения результата
- **model_type**: тип модели для оптимизатора (gpt2, bert, bart)
- **opset**: версия ONNX opset (рекомендуется 17)
- **optimize**: запустить оптимизацию после экспорта


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
