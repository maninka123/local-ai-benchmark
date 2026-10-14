"""Read-only frontier references, separate from scored local benchmark attempts."""
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from benchmark.util import ROOT

router = APIRouter(prefix='/api/references', tags=['Frontier references'])
BASE = ROOT / 'results' / 'references' / 'gpt-6-astra-high'
TASKS = {
    'racing_game': ('Racing game', 'Build a playable 3D circuit racer: three selectable cars, four opponents, collisions, three camera views and a three-lap race. Test the game in a browser.', 'Play racing game'),
    'data_analysis': ('Data analysis', 'Examine every company dataset, explain data quality and cleaning, verify at least five findings, create six meaningful charts, and deliver a reproducible analysis with a professional report.', 'Open analysis report'),
    'detective': ('Detective investigation', 'Inspect the supplied images, documents and access records. Reconstruct the timeline, assess every suspect, cite exhibits, and explain both the conclusion and what remains uncertain.', 'Open investigation report'),
}


def read(path):
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return {}


def folder(task):
    if task not in TASKS:
        raise HTTPException(404, 'Unknown reference task.')
    path = BASE / task
    if path.is_symlink() or not path.resolve().is_relative_to(BASE.resolve()):
        raise HTTPException(404, 'Reference folder unavailable.')
    return path


def safe_file(task, name):
    base = folder(task)
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts or any(p.startswith('.') or p in ('node_modules', '__pycache__') for p in relative.parts):
        raise HTTPException(404, 'Reference file unavailable.')
    candidate = base / relative
    if not candidate.resolve().is_relative_to(base.resolve()) or not candidate.is_file():
        raise HTTPException(404, 'Reference file unavailable.')
    if candidate.is_symlink() or any(p.is_symlink() for p in candidate.parents if p != base.parent and p.is_relative_to(base)):
        raise HTTPException(404, 'Reference file unavailable.')
    return candidate


@router.get('')
def overview():
    tasks = []
    for task, (title, summary, action) in TASKS.items():
        base = folder(task)
        status = read(base / 'status.json')
        context = read(base / 'execution_context.json')
        entry = status.get('entrypoint', '')
        available = False
        if isinstance(entry, str) and entry.startswith('output/'):
            try:
                available = safe_file(task, entry).suffix.lower() == '.html'
            except HTTPException:
                pass
        prompt_path = base / 'prompt.md'
        prompt = prompt_path.read_text(encoding='utf-8-sig') if prompt_path.is_file() else ''
        system_path = base / 'system_prompt.md'
        system = system_path.read_text(encoding='utf-8-sig') if system_path.is_file() else ''
        original = ROOT / 'benchmark' / 'prompts' / (task + '_prompt.md')
        matches = bool(prompt and original.is_file() and prompt_path.read_bytes() == original.read_bytes())
        tasks.append({'id': task, 'title': title, 'summary': summary, 'action': action,
                      'available': available, 'status': status, 'context': context,
                      'prompt': prompt, 'system_prompt': system, 'original_prompt_matches': matches,
                      'prompt_sha256': hashlib.sha256(prompt_path.read_bytes()).hexdigest() if prompt else None,
                      'output_url': f'/api/references/{task}/open' if available else None,
                      'folder': str(base.resolve()), 'verification': read(base / 'verification.json')})
    return {'model': 'GPT-6 Astra', 'model_id': 'gpt-6-astra', 'reasoning': 'High',
            'mode': 'One original task prompt per reference; tool-assisted creation and verification. Interrupted verification may resume from saved work.',
            'comparison_note': 'Frontier reference outputs. These use the original task prompts and public inputs, but a different execution environment from the local benchmark. No comparable token, speed or quality score is claimed.',
            'tasks': tasks}


@router.get('/{task}/open')
def open_output(task: str):
    entry = read(folder(task) / 'status.json').get('entrypoint', '')
    if not isinstance(entry, str) or not entry.startswith('output/') or safe_file(task, entry).suffix.lower() != '.html':
        raise HTTPException(409, 'This reference output is not ready to open.')
    return RedirectResponse(f'/api/references/{task}/files/{quote(entry, safe="/")}', status_code=307)


@router.get('/{task}/files')
def files(task: str):
    base = folder(task)
    found = []
    if base.exists():
        for root, dirs, names in os.walk(base, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in ('node_modules', '__pycache__', '.git') and not d.startswith('.') and not (Path(root) / d).is_symlink())
            for name in sorted(names):
                candidate = Path(root) / name
                relative = candidate.relative_to(base).as_posix()
                try:
                    path = safe_file(task, relative)
                except HTTPException:
                    continue
                found.append({'path': relative, 'bytes': path.stat().st_size,
                              'url': f'/api/references/{task}/files/{quote(relative, safe="/")}'})
    return found


@router.get('/{task}/files/{name:path}')
def file(task: str, name: str):
    path = safe_file(task, name)
    headers = {'Cache-Control': 'no-cache', 'Access-Control-Allow-Origin': '*'}
    # Generated documents cannot access dashboard cookies, storage or APIs. Local
    # module/assets may be fetched by the opaque-origin game via explicit CORS.
    if path.suffix.lower() in ('.html', '.svg'):
        headers['Content-Security-Policy'] = "sandbox allow-scripts allow-pointer-lock; default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'none'; media-src 'self' blob:; object-src 'none'; base-uri 'none'; form-action 'none'"
    return FileResponse(path, headers=headers)


@router.post('/{task}/open-folder')
def open_folder(task: str, request: Request):
    origin = request.headers.get('origin')
    allowed = {str(request.base_url).rstrip('/'), str(request.base_url).rstrip('/').replace('127.0.0.1', 'localhost')}
    if request.headers.get('sec-fetch-site') == 'cross-site' or (origin and origin not in allowed):
        raise HTTPException(403, 'Open folders from this local dashboard.')
    path = folder(task)
    if not path.is_dir():
        raise HTTPException(404, 'Reference folder is not ready.')
    try:
        os.startfile(str(path.resolve()))
    except (OSError, AttributeError) as error:
        raise HTTPException(503, 'Could not open the folder. Copy the displayed path into File Explorer.') from error
    return {'opened': True, 'path': str(path.resolve())}
