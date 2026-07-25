"""Simple MCP server automation script.

This server watches the repository for file changes and auto-commits them
with a placeholder message, simulating an "MCP server" that automates
commits before model-driven edits. It's intentionally minimal; for a real
deployment you'd run this under a process manager and secure it.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(cmd: str):
    return subprocess.run(["git"] + cmd.split(), cwd=ROOT, check=False)


def commit_if_dirty(message: str):
    git("add -A")
    r = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True)
    if r.stdout.strip():
        git(f"commit -m \"{message}\"")
        print("Committed: ", message)
        return True
    return False


def main():
    print("Starting MCP server (watch & auto-commit)...")
    last_mtime = {}
    while True:
        changed = False
        for p in ROOT.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                try:
                    m = p.stat().st_mtime
                except OSError:
                    continue
                if p not in last_mtime:
                    last_mtime[p] = m
                    continue
                if m != last_mtime[p]:
                    print("Detected change:", p)
                    last_mtime[p] = m
                    changed = True
        if changed:
            commit_if_dirty("chore(mcp): auto-commit changes detected by MCP server")
        time.sleep(5)


if __name__ == '__main__':
    main()
