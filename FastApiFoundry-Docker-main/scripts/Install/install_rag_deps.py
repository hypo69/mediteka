# -*- coding: utf-8 -*-
# =============================================================================
# Process name: RAG Dependency Installation
# =============================================================================
# Description:
#   Intelligent installer for heavy RAG dependencies.
#   Automatically detects CUDA and picks between faiss-cpu/faiss-gpu.
#   Reads versions directly from requirements.txt to ensure consistency.
#
# File: scripts/Install/install_rag_deps.py
# Version: 0.5.0
# =============================================================================

import subprocess
import sys
import logging
import shutil
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_cuda() -> bool:
    """Простая проверка наличия NVIDIA GPU через nvidia-smi."""
    return shutil.which("nvidia-smi") is not None

def check_disk_space(required_gb: int = 5) -> bool:
    """Проверка свободного места (по умолчанию нужно 5 ГБ)."""
    _, _, free = shutil.disk_usage(".")
    free_gb = free // (2**30)
    if free_gb < required_gb:
        logger.error(f"Недостаточно места на диске: {free_gb}GB. Нужно минимум {required_gb}GB.")
        return False
    return True

def get_rag_packages_from_file(req_path: Path) -> dict:
    """Читает требования из requirements.txt и адаптирует под GPU/CPU."""
    packages = {}
    if not req_path.exists():
        logger.error(f"Файл {req_path} не найден!")
        return {}

    content = req_path.read_text(encoding='utf-8')
    
    # Ищем torch и sentence-transformers
    for name in ["torch", "sentence-transformers"]:
        match = re.search(rf"^{name}==([\d\.]+)", content, re.MULTILINE)
        if match:
            packages[name] = f"{name}=={match.group(1)}"

    # Логика FAISS: берем версию из faiss-cpu, но меняем имя если есть GPU
    faiss_match = re.search(r"^faiss-cpu==([\d\.]+)", content, re.MULTILINE)
    if faiss_match:
        version = faiss_match.group(1)
        if check_cuda():
            logger.info("Обнаружена CUDA. Будет установлена GPU-версия FAISS.")
            packages["faiss-gpu"] = f"faiss-gpu=={version}"
        else:
            logger.info("CUDA не найдена. Используется CPU-версия FAISS.")
            packages["faiss-cpu"] = f"faiss-cpu=={version}"
    
    return packages

def get_import_name(pkg_name: str) -> str:
    """Сопоставление имени пакета pip с именем для import."""
    name_only = pkg_name.split('==')[0]
    mapping = {
        "sentence-transformers": "sentence_transformers",
        "faiss-cpu": "faiss",
        "faiss-gpu": "faiss",
        "torch": "torch"
    }
    return mapping.get(name_only, name_only)

def is_installed(import_name: str) -> bool:
    """Проверка наличия пакета через импорт."""
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

def install_package(package: str) -> bool:
    """Установка пакета через pip со стримингом вывода."""
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "pip", "install", package],
            stdout=sys.stdout, stderr=sys.stderr
        )
        process.wait()
        return process.returncode == 0
    except Exception as e:
        logger.error(f"Исключение при установке {package}: {e}")
        return False

def main() -> None:
    """Основной цикл проверки и установки RAG-зависимостей."""
    if not check_disk_space():
        sys.exit(1)

    # Путь к requirements.txt на два уровня выше (так как мы в scripts/Install)
    root_dir = Path(__file__).parent.parent.parent
    rag_packages_map = get_rag_packages_from_file(root_dir / "requirements.txt")
    
    if not rag_packages_map:
        logger.error("Не удалось определить список пакетов из requirements.txt")
        sys.exit(1)

    to_install = []
    already = []

    for pkg_name, full_spec in rag_packages_map.items():
        if is_installed(get_import_name(pkg_name)):
            already.append(pkg_name)
        else:
            to_install.append(full_spec)

    if already:
        logger.info(f"Уже установлено: {', '.join(already)}")

    if not to_install:
        logger.info("Все RAG-зависимости уже установлены.")
        return

    logger.info(f"Установка ({len(to_install)} пакетов, ~2 GB): {', '.join(to_install)}")

    failed = []
    for spec in to_install:
        logger.info(f"  Установка {spec}...")
        if install_package(spec):
            logger.info(f"  OK: {spec}")
        else:
            failed.append(spec)

    if failed:
        logger.error(f"Не удалось установить: {', '.join(failed)}")
        sys.exit(1)

    logger.info("Установка RAG-зависимостей успешно завершена.")

if __name__ == "__main__":
    main()