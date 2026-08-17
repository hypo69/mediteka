import sqlite3
import pandas as pd

DB_PATH = r'C:\mediateka\plugins\media_organizer\data\media.db'

def get_media_data():
    conn = sqlite3.connect(DB_PATH)
    # Load into pandas for easier analysis
    df = pd.read_sql_query("SELECT id, path, title_orig, media_type FROM media", conn)
    conn.close()
    return df

def analyze_duplicates(df):
    # Find records with same title_orig
    duplicates = df[df.duplicated(subset=['title_orig'], keep=False)].copy()
    
    # Simple report on duplicates
    print("Potential duplicates (based on title_orig):")
    print(duplicates.groupby('title_orig').size().sort_values(ascending=False).head(20))
    
    # Store to CSV for review
    duplicates.sort_values(by='title_orig').to_csv('duplicates_report.csv', index=False)
    print("\nFull duplicate report saved to 'duplicates_report.csv'")

def analyze_series_fragmentation(df):
    series_df = df[df['media_type'] == 'series'].copy()
    # This is a very rough heuristic, needs refinement based on path structure
    # and actual file contents (torrent metadata if available)
    print("\nSeries entries found:", len(series_df))
    
    # Basic check for path-based fragmentation
    series_df.to_csv('series_analysis.csv', index=False)
    print("Series data saved to 'series_analysis.csv' for further manual/AI review.")

if __name__ == '__main__':
    df = get_media_data()
    analyze_duplicates(df)
    analyze_series_fragmentation(df)
