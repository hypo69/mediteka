# Project Principles: Torrent & Media Management

This document outlines the operational principles and workflows established for managing torrents and media files within the `gemini-simplechat` project.

## Core Architecture
The system relies on three main components:
1.  **Media Database (`media.db`):** A SQLite database tracking media file paths, titles, and `torrent_id` (hashes).
2.  **qBittorrent:** The torrent client managing downloads, locations, and state.
3.  **Python Utilities:** Scripts acting as the glue between the DB and qBittorrent API.

## Established Workflows

### 1. Automated Torrent Matching (`assign_torrents_ids.py`)
*   **Purpose:** Map local media files to torrents based on AI analysis.
*   **Workflow:**
    1.  Fetch media list from SQLite `media` table.
    2.  Build JSON representation of media and available torrents.
    3.  Query Gemini AI to find `media_path` <-> `torrent_hash` matches.
    4.  Update `media.db` with `torrent_id` (hash).
    5.  Trigger `qbt_client.set_location(hash, new_path)` to ensure the torrent moves to the directory where the media file is located.

### 2. Path Synchronization (`update_torrents_path.py`)
*   **Purpose:** Ensure qBittorrent download locations are in sync with the database.
*   **Workflow:**
    1.  Read all records from `media.db` containing `torrent_id` and `path`.
    2.  Iterate through all torrents in qBittorrent.
    3.  For matched `torrent_id`, compare `save_path` (qBittorrent) with `Path(db_path).parent` (DB).
    4.  If they differ, issue `qbt_client.set_location`.

### 3. Torrent State Management (`update_torrent_state.py`)
*   **Purpose:** Verify file integrity.
*   **Workflow:**
    1.  Get all unique `torrent_id`s from the `media.db`.
    2.  Call `qbt_client.recheck(hash)` for every mapped torrent to trigger a "Force Recheck" in qBittorrent.

### 6. Media Size Calculation (`update_media_sizes.py`)
*   **Purpose:** Sync media file/directory sizes to `media.db` and update storage statistics.
*   **Workflow:**
    1.  Read all `path` entries from `media.db`.
    2.  If path is a file, use `file.stat().st_size`.
    3.  If path is a directory, recursively calculate size (`rglob('*')`).
    4.  Update `media_size` in `media` table.
    5.  Update `storage` table with disk usage statistics.

### 7. Media Organizer Logic (`run_media_organizer.py`)
*   **Purpose:** Orchestrate media scanning, AI-driven classification, and auditing.
*   **Workflow:**
    1.  **CLI Interface:** Uses `argparse` to handle modes: scan, audit, rebuild, classify single title.
    2.  **Scan Mode:**
        - Identifies target disks/paths.
        - Uses `MediaOrganizerPlugin` (with AI model) to crawl directories, classify media content via Gemini (using `INSTRUCTION`), and save results to JSON reports and the SQLite `media.db`.
        - Supports output formats: `md`, `csv`, `txt`.
    3.  **Audit Mode (`--audit`):**
        - Uses `MediaAuditor` to compare local file structure on disk with `media.db` records.
        - Detects missing seasons, discrepancies in episode counts, and incomplete files.
        - Optionally interfaces with `QBittorrentClient` to cross-check status in torrents.
    4.  **Classification Mode (`--title`):**
        - Uses `PersistentGenreClassifier` to classify a single title and generate a Markdown report.
    5.  **Force Mode (`--force`):**
        - Performs clean reset: deletes corresponding JSON reports and wipes records from `media.db` for the specified disk before re-scanning.
