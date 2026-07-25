#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Проверка media_type в БД."""

import sqlite3
from pathlib import Path

DB_PATH = Path('plugins/media_organizer/data/media.db')

conn = sqlite3.connect(DB_PATH)
rows = conn.execute('SELECT media_type, COUNT(*) as cnt FROM media GROUP BY media_type').fetchall()
print('media_type в БД:')
for r in rows:
    print(f'  {r[0] or "NULL"}: {r[1]}')

conn.close()
