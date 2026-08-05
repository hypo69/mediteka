with open('plugins/web_search/playwright_searcher.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_text = '''                import urllib.request
                import urllib.parse
                
                url = 'https://lite.duckduckgo.com/lite/'''

new_text = '''                import urllib.request as urllib_req
                
                url = 'https://lite.duckduckgo.com/lite/'''

content = content.replace(old_text, new_text)

old_text2 = '''                        with urllib.request.urlopen(req, timeout=10) as response:'''
new_text2 = '''                        with urllib_req.urlopen(req, timeout=10) as response:'''

content = content.replace(old_text2, new_text2)

with open('plugins/web_search/playwright_searcher.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('FIXED IMPORTS')
