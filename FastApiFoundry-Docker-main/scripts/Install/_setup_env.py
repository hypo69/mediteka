# -*- coding: utf-8 -*-
# Helper: create .env from .env.example if missing
import shutil
from pathlib import Path

root = Path(__file__).parent.parent
env = root / ".env"
example = root / ".env.example"

if env.exists():
    print(".env already exists — skipping")
elif example.exists():
    shutil.copy(example, env)
    print(f".env created from .env.example")
else:
    env.write_text("# FastAPI Foundry\nFOUNDRY_BASE_URL=http://localhost:63995/v1\n", encoding="utf-8")
    print(".env created with defaults")
