import sqlite3
from pathlib import Path
import json

def generate_reports(db_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get list of disks
    disks = [row['disk_name'] for row in cursor.execute('SELECT DISTINCT disk_name FROM media').fetchall()]

    for disk in disks:
        report_file = output_dir / f"report_{disk.replace(' ', '_')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Отчет по медиатеке: {disk}\n\n")

            for media_type in ['movie', 'series']:
                f.write(f"## Категория: {media_type.upper()}\n\n")
                
                # Fetch items
                items = cursor.execute(
                    'SELECT * FROM media WHERE disk_name = ? AND media_type = ? ORDER BY title',
                    (disk, media_type)
                ).fetchall()

                # Identify duplicates
                titles = {}
                for item in items:
                    titles.setdefault(item['title'], []).append(item)
                
                # Report duplicates and missing
                for title, records in titles.items():
                    if len(records) > 1:
                        f.write(f"### ⚠️ Дубликаты: {title}\n")
                        # Sort by size descending to suggest keeping the largest
                        sorted_recs = sorted(records, key=lambda x: x['media_size'] or 0, reverse=True)
                        f.write(f"- ✅ **Оставить:** {sorted_recs[0]['path']} (Size: {sorted_recs[0]['media_size']})\n")
                        for rec in sorted_recs[1:]:
                            f.write(f"- 🗑️ **Удалить:** {rec['path']} (Size: {rec['media_size']})\n")
                        f.write("\n")
                
                if not any(len(recs) > 1 for recs in titles.values()):
                    f.write("Нет дубликатов в этой категории.\n\n")

    conn.close()
    print(f"Reports generated in {output_dir}")

if __name__ == "__main__":
    db_path = Path('plugins/media_organizer/data/media.db')
    output_dir = Path('media_reports')
    generate_reports(db_path, output_dir)
