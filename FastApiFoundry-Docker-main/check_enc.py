with open('static/index.html', 'rb') as f:
    raw = f.read()

# Check BOM
print('BOM:', raw[:4].hex())

# Find first non-ASCII sequence
for i, b in enumerate(raw):
    if b > 127:
        print(f'First non-ASCII at byte {i}: {raw[i:i+4].hex()} context: {raw[max(0,i-20):i+20]}')
        break

# Try decoding
for enc in ['utf-8', 'utf-8-sig', 'cp1251', 'cp1252', 'latin-1']:
    try:
        text = raw.decode(enc)
        # check if cyrillic present
        has_cyr = any('\u0400' <= c <= '\u04ff' for c in text)
        print(f'{enc}: OK, has_cyrillic={has_cyr}')
    except Exception as e:
        print(f'{enc}: FAIL {e}')
