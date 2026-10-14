import re
from pathlib import Path

def safe_text(path, root):
    path=Path(path);root=Path(root).resolve()
    if path.is_symlink() or not path.resolve().is_relative_to(root):return ''
    try:return path.read_text(encoding='utf-8')[:500000]
    except (OSError,UnicodeError):return ''

def writing_evidence(text,sections):
    low=text.lower();words=len(re.findall(r'\b\w+\b',text))
    found={s:any(w in low for w in s.split('|')) for s in sections}
    return {'words':words,'sections':found,'section_coverage':sum(found.values())/len(found),'nonempty':words>100,
        'subjective_quality':'pending blinded human review; word count and headings do not establish quality'}

RUBRICS={
 'data_analysis':{'data_understanding':15,'numerical_accuracy':20,'hidden_patterns':20,'visualization':15,'report_quality':15,'recommendations':15},
 'racing_game':{'build_execution':15,'driving':15,'npc_intelligence':20,'collisions':15,'camera_ui':10,'race_mechanics':10,'visual_quality':10,'code_robustness':5},
 'detective':{'event_reconstruction':25,'visual_evidence':20,'logic':20,'evidence_accuracy':15,'uncertainty':10,'report_quality':10}}

def score_result(task,categories,evidence,complete,limitations=None):
    available={k:v for k,v in categories.items() if v is not None}
    return {'rubric':RUBRICS[task],'categories':categories,'verified_points':round(sum(available.values()),3),
        'pending_points':sum(RUBRICS[task][k] for k,v in categories.items() if v is None),
        'quality_score':None if any(v is None for v in categories.values()) else sum(available.values()),
        'complete':bool(complete),'evidence':evidence,'limitations':limitations or [],'review_status':'pending' if any(v is None for v in categories.values()) else 'automatic',
        'scoring_version':'1.0.0','judge':'deterministic independent artifact/ground-truth checks; no model judge'}
