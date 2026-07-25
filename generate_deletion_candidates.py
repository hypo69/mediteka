import sqlite3
import pandas as pd
import os

DB_PATH = r'C:\mediateka\plugins\media_organizer\data\media.db'
TARGET_DRIVES = ['O:', 'P:', 'Q:', 'W:']

def get_deletion_candidates():
    conn = sqlite3.connect(DB_PATH)
    # Get all media records
    df = pd.read_sql_query("SELECT id, path, title_orig FROM media", conn)
    conn.close()

    # Identify if a path belongs to target drives
    df['is_target_drive'] = df['path'].apply(lambda x: any(str(x).startswith(drive) for drive in TARGET_DRIVES) if x else False)

    # Find duplicates based on title_orig
    # We only care about title_orig that appears more than once
    duplicates = df[df.duplicated(subset=['title_orig'], keep=False)].copy()

    # Create a list of candidates
    candidates = []

    for title, group in duplicates.groupby('title_orig'):
        # Check if this group has files both on target and non-target drives
        has_target = group['is_target_drive'].any()
        has_other = (~group['is_target_drive']).any()

        if has_target and has_other:
            # Candidates are rows in target drives, if there is at least one copy outside
            target_files = group[group['is_target_drive']]
            for _, row in target_files.iterrows():
                candidates.append({
                    'id': row['id'],
                    'title_orig': row['title_orig'],
                    'path': row['path'],
                    'reason': f'Exists on other drives: {list(group[~group["is_target_drive"]]["path"].values)}'
                })

    return pd.DataFrame(candidates)

if __name__ == '__main__':
    candidates_df = get_deletion_candidates()
    if not candidates_df.empty:
        candidates_df.to_csv('deletion_candidates.csv', index=False, encoding='utf-8')
        print(f"Found {len(candidates_df)} candidates for deletion on drives {', '.join(TARGET_DRIVES)}.")
        print("Report saved to 'deletion_candidates.csv'.")
        print(candidates_df.head(10))
    else:
        print("No candidates found for deletion.")
