from benchmark.util import read_json
from benchmark.common_tools.browser_tools import browser_probe
from benchmark.scoring.writing_scorer import safe_text,score_result

def score(run,box=None):
    art=run/'artifacts'
    if box and (art/'game').exists():browser_probe(box)
    result=read_json(art/'browser_validation.json',{})
    build=result.get('build',False);loads=result.get('loads',False);errors=result.get('errors',[]);checks=result.get('checks',{})
    report=safe_text(art/'implementation_report.md',art)
    implementation=any(p.suffix in ['.js','.ts','.html'] and p.is_file() and not p.is_symlink() and 'node_modules' not in p.parts and safe_text(p,art).strip() not in ['', '// Infrastructure only. Implement the game here.'] for p in (art/'game'/'src').rglob('*')) if (art/'game'/'src').exists() else False
    observed_game=bool(implementation and build and loads and checks.get('canvas') and not errors)
    categories={'build_execution':15 if observed_game else 8 if implementation and build else 0,
        'driving':None if loads else 0,'npc_intelligence':None if loads else 0,'collisions':None if loads else 0,
        'camera_ui':None if loads else 0,'race_mechanics':None if loads else 0,'visual_quality':None if loads else 0,
        'code_robustness':None if implementation and build else 0}
    # A playable shell is not a completed racing challenge. A human must verify the missing mechanics.
    complete=False
    return score_result('racing_game',categories,{'browser':result,'implementation_report_present':bool(report),
        'build_success':build and implementation,'browser_started':loads,'implementation_present':implementation,'runtime_error_count':len(errors),'candidate_hook_checks_unverified':checks},complete,
        ['Playwright validates build, page loads, error collection and screenshot capture. Candidate-supplied hooks are diagnostic only; driving/collision/checkpoint/NPC claims require independent manual review. Completion stays unverified until reviewed.'])
