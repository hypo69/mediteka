import re

with open('plugins/rag/__init__.py', 'rb') as f:
    content = f.read()

# We need to find the bad segment in bytes.
# We know it contains "answer = await self.ai.chat("
# Let's decode with replace, find the indices, and slice the bytes.
text = content.decode('utf-8', errors='replace')

pattern = re.compile(r'пиш\s+answer = await self\.ai\.chat\([\s\S]*?returnеть \(15-25 слов, только кириллица, числа словами\)\.\.\.\\",\\n\"')
match = pattern.search(text)

if match:
    # Convert string indices back to byte indices (approximate, since errors='replace' might change length, but let's hope it's ascii where the replace happens)
    # Actually, let's just find the byte offsets of unique ascii strings.
    start_str = b"                answer = await self.ai.chat("
    end_str = b"            return"
    
    # But wait, there are multiple "answer = await self.ai.chat(" in the file.
    # The bad one is right after "atmosphere" and "why_watch" things.
    # Let's find "120 \xd0\xb4\xd0\xbe 150 \xd1\x81\xd0\xbb\xd0\xbe\xd0\xb2" which is "120 до 150 слов".
    
    # Let's just do a manual byte replacement.
    text_utf8 = content.decode('utf-8', errors='ignore')
    new_text, count = pattern.subn(r'''пиши «Лента выступает эталоном...».\n"
                    f"### ПРИМЕР СТРУКТУРЫ ОТВЕТА (JSON)\n"
                    f"{{\n"
                    f"  \"title\": \"...\",\n"
                    f"  \"title_ru\": \"...\",\n"
                    f"  \"year\": \"...\",\n"
                    f"  \"type\": \"...\",\n"
                    f"  \"main_category\": \"...\",\n"
                    f"  \"country\": \"...\",\n"
                    f"  \"plot\": \"...\",\n"
                    f"  \"atmosphere\": \"...\",\n"
                    f"  \"why_watch\": \"Смотреть (15-25 слов, только кириллица, числа словами)...\",\n"''', text_utf8)
    
    if count > 0:
        with open('plugins/rag/__init__.py', 'wb') as f:
            f.write(new_text.encode('utf-8'))
        print(f'Replaced {count} times successfully!')
    else:
        print('Pattern not found')
else:
    print('Pattern not found in string search')
