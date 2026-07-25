import pandas as pd
import os
import ast

# Load the candidate report
df = pd.read_csv('duplicates_report_candidates.csv')

# Filter for Poirot
poirot_rows = df[df['title'].str.contains('Пуаро', na=False)]

files_to_delete = []

for _, row in poirot_rows.iterrows():
    # Paths are stored as a comma-separated string in the 'paths' column
    paths = row['paths'].split(',')
    
    # Check if there is an HD version
    has_hd = any('(HD)' in p for p in paths)
    
    if has_hd:
        for path in paths:
            if '(HD)' not in path:
                # This is a candidate for deletion
                if os.path.exists(path):
                    files_to_delete.append(path)
                else:
                    print(f"Candidate not found: {path}")

print("\n--- CONFIRMATION REQUIRED ---")
print(f"Found {len(files_to_delete)} non-HD Poirot files to delete:")
for f in files_to_delete:
    print(f"  {f}")
print("------------------------------")
print("Run the deletion script with '--execute' to perform the deletion.")
