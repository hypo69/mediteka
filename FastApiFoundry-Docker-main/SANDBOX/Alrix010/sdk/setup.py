# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI Foundry SDK Setup
# =============================================================================
# Описание:
#   Установочный скрипт для пакета fastapi-foundry-sdk.
#   Определяет метаданные пакета, зависимости и параметры сборки
#   для публикации в PyPI или локальной установки через pip.
#
#   Логика работы:
#   1. Читает README.md как long_description для страницы пакета на PyPI
#   2. Регистрирует пакет с именем 'fastapi-foundry-sdk' версии 0.2.1
#   3. Автоматически находит все подпакеты через find_packages()
#   4. Объявляет обязательную зависимость: requests>=2.25.0
#   5. Объявляет dev-зависимости: pytest, black, flake8 (через extras_require)
#
# Примеры:
#   # Локальная установка в режиме разработки:
#   pip install -e .
#
#   # Установка с dev-зависимостями:
#   pip install -e .[dev]
#
#   # Сборка дистрибутива:
#   python setup.py sdist bdist_wheel
#
# File: setup.py
# Project: Ai Assistant (Docker)
# Version: 0.2.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: 9 декабря 2025
# =============================================================================

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fastapi-foundry-sdk",
    version="0.2.1",
    author="hypo69",
    author_email="hypo69@example.com",
    description="Python SDK для работы с FastAPI Foundry API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hypo69/FastApiFoundry-Docker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio",
            "black",
            "flake8",
        ],
    },
)