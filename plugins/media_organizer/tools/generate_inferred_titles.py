import re
import csv

# Regex for pattern: ##. Russian Title (Year) ...
# Example: 06. Дом Gucci (2021) 2021
pattern = re.compile(r"^\d+\.\s+([А-Яа-яЁё\s!]+?)(?:\s*\(|\s*\[|\s*\d{4}|\s*s\d+e\d+|\s*Season|\s*-\s*Season|$)")

inferred_data = []

with open("empty_title_ru_list.txt", "r", encoding="utf-8") as f:
    for line in f:
        # Each line is in format: (id, 'path', 'title', None)
        # Need to parse this, simplest is just evaluating it as a tuple
        try:
            # Reconstruct the tuple from string representation
            # This is safe here because we created the file
            data = eval(line.strip())
            rec_id, path, title, _ = data
            
            # Try to extract title_ru from title
            match = pattern.match(title)
            if match:
                inferred_title = match.group(1).strip()
            else:
                inferred_title = "COULD_NOT_INFER"
                
            inferred_data.append((rec_id, title, inferred_title))
        except Exception as e:
            print(f"Error processing line: {line.strip()} - {e}")

# Write report
with open("inferred_titles_report.csv", "w", encoding="utf-8", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["ID", "Original Title", "Inferred Title_ru"])
    writer.writerows(inferred_data)

print(f"Generated inferred_titles_report.csv with {len(inferred_data)} entries.")
