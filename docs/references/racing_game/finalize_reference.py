"""Persist auditable metadata for the saved, resumed racing-game reference."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))
def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
def fingerprint(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

now = datetime.now(timezone.utc).isoformat()
prompts = []
for saved, original in [('prompt.md', 'racing_game_prompt.md'), ('system_prompt.md', 'common_system_prompt.md')]:
    same = (ROOT / saved).read_bytes() == (REPO / 'benchmark/prompts' / original).read_bytes()
    assert same, f'Original prompt mismatch: {saved}'
    prompts.append({**fingerprint(ROOT / saved), 'original': 'benchmark/prompts/' + original, 'byte_identical': same})

# Preserve original damaged bytes before replacing the optional barrier screenshot.
barrier = ROOT / 'output/screenshots/barrier_collision.png'
archive = ROOT / 'output/screenshots/barrier_collision.interrupted.png'
if not archive.exists():
    shutil.copyfile(barrier, archive)
shutil.copyfile(ROOT / 'output/screenshots/continuation_barrier_collision.png', barrier)
images = []
for path in sorted((ROOT / 'output/screenshots').glob('*.png')):
    row = {**fingerprint(path), 'interruption_evidence': '.interrupted.' in path.name}
    try:
        with Image.open(path) as im:
            im.load()
            row.update(valid_png=im.format == 'PNG', dimensions=list(im.size))
    except Exception as exc:
        row.update(valid_png=False, error=str(exc))
    images.append(row)
required = ['menu.png', 'race_chase.png', 'race_hood.png', 'race_overhead.png']
assert all(next(r for r in images if r['path'].endswith('/' + name))['valid_png'] for name in required)
assert all(r['valid_png'] or r['interruption_evidence'] for r in images)
save('screenshot-validation.json', {'verified_at_utc': now, 'required_screenshots': required,
     'required_screenshots_valid': True, 'method': 'Pillow full PNG decode; required views and completed-results capture visually inspected',
     'interruption_evidence_policy': 'Damaged original captures retained with .interrupted.png suffix; excluded from successful visual evidence.', 'files': images})

simulation = read('simulation-verification.json')
browser = read('browser-verification-continuation.json')
production = read('production-browser-verification.json')
assert all(t['passed'] for t in simulation['tests'])
assert all(t['passed'] for t in browser['checks']) and not browser.get('failure') and not browser['browserErrors']
assert production['passed'] and not production['errors'] and not production['requestFailures']
assert all(c['completedLaps'] == 3 and c['passedCheckpoints'] == 48 for c in browser['finalRace']['cars'])
limitations = [
 'Arcade planar physics with circular collision bodies; tight contacts can temporarily block the player. Space recovery is available.',
 'Deterministic heuristic NPC tactics; no guarantee of optimal overtakes or exhaustive collision recovery.',
 'Headless Chromium checks on one Windows host; not exhaustive browser/GPU/accessibility coverage.',
 'Production route smoke-tested directly under dashboard CSP; dashboard iframe navigation is outside this author verification scope.',
 'Fresh npm dependency installation was not performed in the completion pass; supplied sandbox dependencies were used.',
 'One original task assignment with tool-assisted implementation and resumed verification after interruptions; not a single inference.',
 'Overall authoring elapsed time and token usage unknown; no measured benchmark score assigned.'
]
context = {
 'reference_type': 'self-authored tool-assisted reference', 'task': 'racing_game',
 'requested_model': 'gpt-6-astra', 'configured_model': 'gpt-6-astra',
 'requested_reasoning_effort': 'high', 'configured_reasoning_effort': 'high',
 'configuration_basis': 'Explicit model and reasoning selection in parent agent runtime tool call, confirmed by parent for original and both continuations; provider-side attestation unavailable.',
 'execution_mode': 'Single original task assignment with tool-assisted implementation and verification; interrupted authoring/verification sessions resumed to complete delivery. Not a single model inference.',
 'original_prompts': {'system': 'system_prompt.md', 'task': 'prompt.md', 'byte_identical_to_originals': True, 'files': prompts},
 'subsequent_user_correction_prompts': [],
 'parent_delivery_guidance': 'Resume saved original task/source; complete testing and missing reports; preserve interruption evidence; verify dashboard production route. No new benchmark task prompt or feature request.',
 'source_restriction': 'Saved racing source, prompts and verification artifacts; sibling data_analysis metadata schema only. No candidate answers, evaluation_private, scoring answers, Ollama or local campaigns accessed.',
 'tools_used': ['PowerShell', 'Node.js 24.21.0', 'provided Vite and Three.js dependencies', 'Playwright Chromium keyboard/browser tests', 'Python/Pillow PNG validation', 'local image viewing'],
 'local_gpu_or_ollama_used': False,
 'gpu_scope_note': 'No local LLM/GPU benchmark invoked. Browser WebGL rendering was used; GPU versus software rendering was not measured.',
 'other_models_or_subagents_called': False,
 'local_model_campaign_modified_or_resumed': False,
 'timing': {'kind': 'browser verification intervals measured; overall authoring elapsed unknown',
    'measurement_started_utc': browser['startedAt'], 'measurement_finished_utc': browser['completedAt'],
    'elapsed_wall_seconds': (datetime.fromisoformat(browser['completedAt'].replace('Z','+00:00')) - datetime.fromisoformat(browser['startedAt'].replace('Z','+00:00'))).total_seconds(),
    'scope': 'Completed resumed development-browser verification only, not total authoring or model inference latency.',
    'overall_authoring_elapsed_wall_seconds': None, 'comparable_to_ollama_benchmark': False},
 'tokens': {'input': None, 'output': None, 'total': None, 'status': 'unknown; not measured'},
 'benchmark_score': None, 'not_ground_truth': True
}
save('execution_context.json', context)
verification = {
 'assessment': 'Share with caveats', 'verified_at_utc': now,
 'method': 'Direct simulation assertions, actual headless Chromium keyboard gameplay with read-only diagnostics, production-route browser smoke under response CSP, full PNG decode and visual inspection.',
 'checks_passed': len(simulation['tests']) + len(browser['checks']) + len(production['checks']),
 'checks_failed': 0,
 'check_groups': {'simulation': len(simulation['tests']), 'development_browser': len(browser['checks']), 'production_browser': len(production['checks'])},
 'key_verified_results': {'cars_selectable': 3, 'npc_count': 5, 'cameras': 3, 'player_completed_laps': 3,
    'player_passed_checkpoints': 48, 'player_finish_simulated_seconds': browser['finalRace']['cars'][0]['finishTime'],
    'npc_browser_finishes': 5, 'npc_simulation_finishes_across_three_selections': 15,
    'browser_javascript_errors': 0, 'required_screenshots_valid': True},
 'reproducibility': {'commands': ['cd output/game; npm install', 'npm test', 'npm run build', 'npm run dev -- --host 127.0.0.1 --port 5187'],
    'browser_harnesses': ['browser-verification-continuation.mjs', 'browser-production-verification.mjs'],
    'detailed_checks': ['simulation-verification.json', 'browser-verification-continuation.json', 'production-browser-verification.json', 'screenshot-validation.json'],
    'build': 'Passed using provided Vite CLI and Three.js fallback; no source changes required during final completion pass.'},
 'presentation': {'visual_checks': 'Required menu, chase, hood and overhead 1440x900 screenshots plus 960x600 final standings visually inspected.',
    'production_preview_url': production['url'], 'production_http_status': production['httpStatus'],
    'production_camera_captures': 'Pause overlay visible in production_race_*.png; unobstructed driving views are the four required screenshots.',
    'interrupted_evidence': 'Damaged *.interrupted.png captures preserved and excluded from successful verification.'},
 'limitations': limitations, 'original_inputs_and_prompts_unchanged': True, 'not_ground_truth': True
}
save('verification.json', verification)
files = [fingerprint(p) for p in sorted(ROOT.rglob('*')) if p.is_file()
         and 'node_modules' not in p.parts and p.name != 'status.json']
save('status.json', {'status': 'completed', 'completed': True, 'task': 'racing_game',
    'reference_model': 'gpt-6-astra', 'reasoning_effort': 'high', 'entrypoint': 'output/index.html',
    'output_entrypoint': 'output/index.html', 'game_entrypoint': 'output/game/dist/index.html',
    'completed_at_utc': now, 'verification_summary': {'assessment': verification['assessment'],
    'checks_passed': verification['checks_passed'], 'checks_failed': 0, **verification['key_verified_results']},
    'limitations': limitations, 'is_ground_truth': False, 'measured_benchmark_score': None, 'files': files})
print(json.dumps({'status': 'completed', 'checks': verification['check_groups'], 'required_pngs_valid': True,
                  'prompts_byte_identical': True, 'files_fingerprinted': len(files)}, indent=2))
