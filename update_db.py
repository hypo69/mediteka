import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / 'plugins' / 'media_organizer' / 'media.db'
DB_BACKUP = DB_PATH.with_suffix('.db.backup')

print(f'Working with: {DB_PATH}')
print(f'Backup at: {DB_BACKUP}')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Step 1: Rename current media table to media_old
print('\n[1] Renaming media -> media_old...')
cursor.execute('ALTER TABLE media RENAME TO media_old')

# Step 2: Create new media table with updated schema
print('[2] Creating new media table...')
cursor.execute("""
CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    internal_number INTEGER DEFAULT 0,
    disk_name TEXT NOT NULL,
    path TEXT NOT NULL,
    size INTEGER DEFAULT 0,
    type TEXT NOT NULL CHECK(type IN ('movie', 'series', 'anime')),
    title_ru TEXT NOT NULL,
    title_orig TEXT,
    title TEXT,
    year INTEGER NOT NULL,
    main_category TEXT,
    country TEXT,
    genres TEXT,
    directors TEXT,
    cast TEXT,
    status TEXT,
    seasons_count INTEGER DEFAULT 0,
    episodes_per_season TEXT,
    seasons_summary TEXT,
    can_stop_at TEXT,
    rating TEXT,
    awards TEXT,
    plot TEXT,
    review TEXT,
    final_verdict TEXT,
    atmosphere TEXT,
    mood TEXT,
    why_watch TEXT,
    quote TEXT,
    catchphrases TEXT DEFAULT NULL,
    facts TEXT,
    similar TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(disk_name, title, type)
)
""")
print('   new media table created')

# Step 3: Create new series_episodes table
print('[3] Creating new series_episodes table...')
cursor.execute("""
CREATE TABLE IF NOT EXISTS series_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER NOT NULL,
    season_number INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,
    title TEXT,
    path TEXT NOT NULL,
    size INTEGER NOT NULL DEFAULT 0,
    duration INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE,
    UNIQUE (media_id, season_number, episode_number)
)
""")
print('   new series_episodes table created')

# Step 4: Create duplicates table (if not exists)
print('[4] Creating duplicates table...')
cursor.execute("""
CREATE TABLE IF NOT EXISTS duplicates (
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    disk_name TEXT NOT NULL,
    PRIMARY KEY (title, type, disk_name)
)
""")
print('   duplicates table created')

conn.commit()
print('\n=== SCHEMA UPDATED ===')
conn.close()
