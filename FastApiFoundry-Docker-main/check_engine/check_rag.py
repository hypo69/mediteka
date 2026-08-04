# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: RAG System Test
# =============================================================================
# Описание:
#   Простой тест для проверки работы RAG системы
#   Создает минимальный индекс и тестирует поиск
#
# File: test_rag.py
# Project: Ai Assistant (Docker)
# Version: 0.3.3
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: 9 декабря 2025
# =============================================================================

import asyncio
import json
from pathlib import Path

async def test_rag_system():
    """Тест RAG системы"""
    print("🧪 Testing RAG System")
    print("=" * 30)
    
    try:
        from src.rag.rag_system import rag_system
        
        # Проверяем статус
        print("📊 Checking RAG status...")
        status = await rag_system.get_status()
        print(f"   Available: {status['available']}")
        print(f"   Enabled: {status['enabled']}")
        print(f"   Loaded: {status['loaded']}")
        
        if not status['available']:
            print("❌ RAG dependencies not available")
            print("   Install: pip install sentence-transformers faiss-cpu")
            return False
        
        if not status['enabled']:
            print("⚠️  RAG disabled in config.json")
            print("   Set rag_system.enabled = true")
            return False
        
        # Попытка инициализации
        print("\n🚀 Initializing RAG system...")
        success = await rag_system.initialize()
        
        if not success:
            print("⚠️  RAG not initialized (no index found)")
            print("   Run: python create_rag_index.py")
            return False
        
        print("✅ RAG system initialized")
        
        # Тестовый поиск
        print("\n🔍 Testing search...")
        test_queries = [
            "FastAPI configuration",
            "Docker setup",
            "Foundry models",
            "API endpoints"
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            results = await rag_system.search(query, top_k=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"     [{i}] {result['source']} (score: {result['score']:.3f})")
                    print(f"         {result['text'][:80]}...")
            else:
                print("     No results found")
        
        print("\n✅ RAG system test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Install RAG dependencies: python install_rag_deps.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def create_minimal_index():
    """Создать минимальный тестовый индекс"""
    print("\n🔧 Creating minimal test index...")
    
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np
        from config_manager import config
        
        # Тестовые документы
        test_docs = [
            {
                'text': 'FastAPI Foundry is a REST API server for local AI models through Foundry',
                'source': 'README.md',
                'section': 'intro',
                'file_name': 'README.md'
            },
            {
                'text': 'Configuration is stored in config.json file with sections for fastapi_server, foundry_ai, and rag_system',
                'source': 'config.json',
                'section': 'config',
                'file_name': 'config.json'
            },
            {
                'text': 'Docker support allows easy deployment with docker-compose up --build command',
                'source': 'docker-compose.yml',
                'section': 'docker',
                'file_name': 'docker-compose.yml'
            },
            {
                'text': 'RAG system uses FAISS for vector search and sentence-transformers for embeddings',
                'source': 'src/rag/rag_system.py',
                'section': 'rag',
                'file_name': 'rag_system.py'
            }
        ]
        
        # Создать модель
        model = SentenceTransformer(config.rag_model)
        
        # Создать эмбеддинги
        texts = [doc['text'] for doc in test_docs]
        embeddings = model.encode(texts)
        embeddings = np.array(embeddings).astype('float32')
        faiss.normalize_L2(embeddings)
        
        # Создать индекс
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        
        # Сохранить
        index_dir = Path(config.rag_index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(index, str(index_dir / "faiss.index"))
        
        with open(index_dir / "chunks.json", 'w', encoding='utf-8') as f:
            json.dump(test_docs, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Minimal test index created: {index_dir}")
        print(f"   Documents: {len(test_docs)}")
        print(f"   Vectors: {index.ntotal}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test index: {e}")
        return False

async def main():
    """Главная функция"""
    print("🚀 FastAPI Foundry RAG Test")
    print("=" * 40)
    
    # Сначала тестируем RAG
    success = await test_rag_system()
    
    if not success:
        print("\n🔧 Attempting to create minimal test index...")
        index_created = await create_minimal_index()
        
        if index_created:
            print("\n🔄 Retesting RAG system...")
            success = await test_rag_system()
    
    if success:
        print("\n🎉 RAG system is working correctly!")
        print("\n📝 Next steps:")
        print("   1. Start server: python run.py")
        print("   2. Test API: http://localhost:8000/api/v1/rag/status")
        print("   3. Search API: http://localhost:8000/api/v1/rag/search")
    else:
        print("\n❌ RAG system test failed")
        print("\n🔧 Troubleshooting:")
        print("   1. Install dependencies: python install_rag_deps.py")
        print("   2. Create index: python create_rag_index.py")
        print("   3. Check config: rag_system.enabled = true")

if __name__ == "__main__":
    asyncio.run(main())