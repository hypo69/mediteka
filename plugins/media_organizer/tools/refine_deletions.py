import pandas as pd
import ast

# Load the report
df = pd.read_csv('duplicates_report_candidates.csv')

# Define active disks
active_disks = ['R:', 'S:', 'T:', 'X:']

def check_for_deletion(row):
    # Parse the candidates list
    try:
        candidates = ast.literal_eval(row['candidates_for_deletion'])
    except:
        return []
    
    # Parse original paths and disks
    paths = row['paths'].split(',')
    disks = row['disks'].split(',')
    
    # Files to keep (not on active disks)
    keep_paths = [path for i, path in enumerate(paths) if not any(path.startswith(d) for d in active_disks)]
    
    # If we have no paths to keep, we can't safely delete everything
    if not keep_paths:
        return []
        
    # Candidates to delete (must be on active disks AND have a 'keep' counterpart)
    return candidates

df['to_delete'] = df.apply(check_for_deletion, axis=1)

# Keep only rows with deletions
df_deletions = df[df['to_delete'].map(lambda x: len(x) > 0)][['title', 'to_delete']]

# Save actionable report
df_deletions.to_csv('actionable_deletions.csv', index=False)
print("Actionable report saved to actionable_deletions.csv")
