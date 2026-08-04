# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Главное окно приложения
# =============================================================================
# Описание:
#   Инициализация окна pywebview и подключение Python Bridge (api.py).
#   Настройка параметров отображения и путей фронтенда.
#
# Примеры:
#   >>> python app.py
#
# File: app.py
# Project: Ai Assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sys
import os
import webview
from api import Api

def main() -> None:
    """Инициализация и запуск окна приложения.

    ПОЧЕМУ ПРЯМОЙ ПУТЬ К HTML:
      Использование абсолютного пути исключает ошибки поиска файлов 
      при запуске из разных директорий.
    """
    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    html_path: str = os.path.abspath(os.path.join(current_dir, 'index.html'))

    if not os.path.exists(html_path):
        print(f"❌ Critical Error: File not found at {html_path}")
        sys.exit(1)

    # Создание окна приложения
    try:
        webview.create_window(
            title='Ai Assistant Desktop',
            url=html_path,
            js_api=Api(),
            width=1200,
            height=800,
            min_size=(800, 600),
            background_color='#ffffff'
        )
        # debug=True позволяет открывать консоль по ПКМ
        webview.start(debug=True)
    except Exception as ex:
        print(f"❌ WebView Error: {ex}")
        sys.exit(1)

if __name__ == '__main__':
    main()