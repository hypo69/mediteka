# System Stats

**Файл:** `src/api/endpoints/system_stats.py`  
**Тип:** `.py`

---

### `_gpu_stats` — Функция

```python
def _gpu_stats() -> list
```

Collect per-GPU stats via pynvml.

Returns:
    list: Each item has name, ram_used_mb, ram_total_mb, ram_pct, gpu_pct.

### `system_stats` — Функция

```python
@router.get('/stats')
```

RAM, CPU, disk and GPU usage.

Returns:
    dict: success, ram_used_mb, ram_available_mb, ram_total_mb, ram_pct,
          cpu_pct, disk_used_gb, disk_total_gb, disk_pct,
          proc_ram_mb, proc_cpu_pct, proc_threads,
          gpus (list).


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
