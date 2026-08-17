import sqlite3
import pandas as pd

# Path to the database
db_path = r'C:\mediateka\plugins\media_organizer\data\media.db'

# Connect to the DB
conn = sqlite3.connect(db_path)

# Query to find duplicates based on title and potentially partial paths
# Since we need to identify duplicates across different locations, 
# we'll group by title.
query = """
SELECT 
    title, 
    GROUP_CONCAT(disk_name) as disks, 
    GROUP_CONCAT(path) as paths
FROM media
GROUP BY title
HAVING COUNT(*) > 1
"""

# Fetch the duplicates
df = pd.read_sql_query(query, conn)
conn.close()

# Filter candidates for deletion (disks R:, S:, T:, X:)
candidate_disks = ['R:', 'S:', 'T:', 'X:']

def identify_candidates(row):
    paths = row['paths'].split(',')
    disks = row['disks'].split(',')
    
    candidates = []
    has_other_location = False
    
    # Check if there's any location NOT in the candidate list
    for disk in disks:
        # Check if disk name or path start with R:, S:, T:, or X:
        if not any(disk.startswith(d) for d in candidate_disks):
            has_other_location = True
            break
            
    if has_other_location:
        for i, path in enumerate(paths):
            if any(path.startswith(d) for d in candidate_disks):
                candidates.append(path)
                
    return candidates

df['candidates_for_deletion'] = df.apply(identify_candidates, axis=1)

# Keep only rows that have candidates
df = df[df['candidates_for_deletion'].map(lambda x: len(x) > 0)]

# Print results to a file for review
df.to_csv('duplicates_report_candidates.csv', index=False)
print(f"Found {len(df)} duplicate groups with candidates for deletion.")
print("Report saved to duplicates_report_candidates.csv")
