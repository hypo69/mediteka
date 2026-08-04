# RAG System API

## Индексация директорий

Запуск переиндексации файлов в указанных папках. Если папки не указаны, используются `source_dirs` из `config.json`.

**Endpoint:** `POST /v1/rag/index`

**Примеры вызова через curl:**

### 1. Индексация по умолчанию (из конфига)
```bash
curl -X POST http://localhost:9696/v1/rag/index \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_API_KEY"
```

### 2. Индексация конкретных путей
```bash
curl -X POST http://localhost:9696/v1/rag/index \
     -H "Content-Type: application/json" \
     -d '{
       "source_dirs": ["C:/Users/Admin/Documents/AI_Project", "/mnt/data/docs"]
     }'
```