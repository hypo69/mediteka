# -*- coding: utf-8 -*-
import os, re

path = 'src/rag/document_ingestor.py'
c = open(path, encoding='utf-8').read()

old = 'source_name = file.filename\r\n        temp_path = f"temp_{source_name}"'
new = (
    'source_name = file.filename or "upload"\n'
    '        # Use only basename as suffix \u2014 avoids path errors when filename\n'
    '        # contains subdirs (e.g. "ru/about.md" from webkitdirectory).\n'
    '        suffix = os.path.splitext(os.path.basename(source_name))[1] or ".tmp"\n'
    '        tmp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)\n'
    '        temp_path = tmp_file.name\n'
    '        tmp_file.close()'
)

if old not in c:
    # try \n only
    old = old.replace('\r\n', '\n')

found = old in c
if found:
    c2 = c.replace(old, new, 1)
    open(path, 'w', encoding='utf-8').write(c2)
    open('tmp_patch_result.txt', 'w').write('OK')
else:
    open('tmp_patch_result.txt', 'w').write('NOT FOUND')
