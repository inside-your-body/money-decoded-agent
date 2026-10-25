import json, os, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / 'config/channel.json').read_text())
WORK = pathlib.Path(os.environ.get('WORK_DIR', ROOT / 'work'))
WORK.mkdir(parents=True, exist_ok=True)

def sh(cmd, **kw):
    print('$', cmd if isinstance(cmd, str) else ' '.join(map(str, cmd)), flush=True)
    return subprocess.run(cmd, shell=isinstance(cmd, str), check=True, **kw)

def load(p, default=None):
    p = pathlib.Path(p)
    return json.loads(p.read_text()) if p.exists() else default

def save(p, obj):
    pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(p).write_text(json.dumps(obj, indent=1, ensure_ascii=False))
