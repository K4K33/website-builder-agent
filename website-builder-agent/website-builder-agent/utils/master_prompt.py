"""Single versioned operating contract shared by all build and review paths."""
from hashlib import sha256
from pathlib import Path

MASTER_PROMPT_PATH = Path(__file__).resolve().parents[1] / 'docs/KAURIVO_MESTARI_PROMPT.md'
MASTER_PROMPT = MASTER_PROMPT_PATH.read_text(encoding='utf-8')
if not MASTER_PROMPT.strip():
    raise RuntimeError('Kaurivo master prompt is empty; refusing an uncontracted build')
MASTER_PROMPT_SHA256 = sha256(MASTER_PROMPT.encode('utf-8')).hexdigest()
