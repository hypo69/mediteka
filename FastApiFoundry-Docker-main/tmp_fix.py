# -*- coding: utf-8 -*-
path = 'src/rag/document_ingestor.py'
c = open(path, encoding='utf-8').read()

# Fix the bad backslash in the class docstring
old = r'(например C:\\Users\\user\\AppData\\Local\\Temp\\).'
new = '(например %TEMP% или /tmp).'
c = c.replace(old, new)

open(path, 'w', encoding='utf-8').write(c)
print('OK')
