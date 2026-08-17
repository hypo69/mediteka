import os
import csv
import ast
import pandas as pd

# Load actionable deletions
if not os.path.exists('actionable_deletions.csv'):
    print("Error: actionable_deletions.csv not found.")
    exit(1)

df = pd.read_csv('actionable_deletions.csv')

# Filter for Poirot
poirot_rows = df[df['title'].str.contains('Пуаро', na=False)]

deleted_count = 0
for _, row in poirot_rows.iterrows():
    candidates = ast.literal_eval(row['to_delete'])
    
    # We want to keep (HD) and delete non-HD
    has_hd = any('(HD)' in c for c in candidates)
    
    if has_hd:
        for candidate in candidates:
            if '(HD)' not in candidate and os.path.exists(candidate):
                print(f"Deleting: {candidate}")
                # os.remove(candidate) # Uncomment to execute
                deleted_count += 1
            elif '(HD)' not in candidate:
                print(f"File not found or already deleted: {candidate}")

print(f"Total non-HD files identified for deletion: {deleted_count}")
