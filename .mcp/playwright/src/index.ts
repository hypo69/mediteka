import express from 'express';
import bodyParser from 'body-parser';
import { writeFileSync } from 'fs';
import path from 'path';
import { execSync } from 'child_process';

const REPO_ROOT = path.resolve(__dirname, '..', '..', '..');

function git(cmd: string) {
  return execSync(`git ${cmd}`, { cwd: REPO_ROOT }).toString();
}

const app = express();
app.use(bodyParser.json({ limit: '20mb' }));

app.post('/precommit', (req, res) => {
  const { message } = req.body;
  if (!message) return res.status(400).json({ error: 'missing message' });
  try {
    git('add -A');
    const status = git('status --porcelain');
    if (status.trim()) {
      git(`commit -m "${message.replace(/"/g, '\\"')}"`);
      return res.json({ ok: true, committed: true });
    }
    return res.json({ ok: true, committed: false });
  } catch (e: any) {
    return res.status(500).json({ error: e.message });
  }
});

app.post('/apply', (req, res) => {
  const { filePath, content } = req.body;
  if (!filePath || typeof content !== 'string') return res.status(400).json({ error: 'invalid payload' });
  try {
    const full = path.join(REPO_ROOT, filePath);
    writeFileSync(full, content, 'utf8');
    return res.json({ ok: true });
  } catch (e: any) {
    return res.status(500).json({ error: e.message });
  }
});

const PORT = process.env.PORT ? Number(process.env.PORT) : 3041;
app.listen(PORT, () => console.log(`Playwright MCP-like server listening on ${PORT}`));
