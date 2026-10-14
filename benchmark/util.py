from pathlib import Path
import hashlib, json, datetime, yaml, uuid, os

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.0.0'

def config():
    return yaml.safe_load((ROOT / 'config.yaml').read_text(encoding='utf-8'))

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    temp.replace(path)

def read_json(path, default=None):
    try: return json.loads(Path(path).read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError): return default

def append_json(path, value):
    with Path(path).open('a', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, default=str)+'\n')

def artifact_files(base):
    """Skip dependency trees and inaccessible Linux reparse points on Windows."""
    base=Path(base)
    for parent,dirs,files in os.walk(base,followlinks=False,onerror=lambda _:None):
        dirs[:]=[name for name in dirs if name!='node_modules']
        for name in files:
            if name=='node_modules':continue
            p=Path(parent)/name
            try:
                if not p.is_symlink() and p.is_file() and p.resolve().is_relative_to(base.resolve()):yield p
            except OSError:continue

def source_hash():
    h=hashlib.sha256()
    for p in sorted((ROOT/'benchmark').rglob('*')):
        if p.is_file() and p.suffix in ('.py','.md'):
            h.update(str(p.relative_to(ROOT)).encode()); h.update(p.read_bytes())
    h.update((ROOT/'config.yaml').read_bytes())
    for name in ['requirements.txt','sandbox/Dockerfile','sandbox/package.json','sandbox/package-lock.json','sandbox/browser_probe.mjs']:
        p=ROOT/name
        if p.exists():h.update(name.encode());h.update(p.read_bytes())
    manifest=ROOT/'results'/'dataset_manifest.json'
    if manifest.exists():h.update(manifest.read_bytes())
    return h.hexdigest()
