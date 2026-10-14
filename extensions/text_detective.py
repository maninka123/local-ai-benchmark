"""Written-evidence investigation, kept distinct from native multimodal evaluation."""
import hashlib,json,re
from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageSystem,ChatMessageUser
from benchmark.util import ROOT,config,source_hash,read_json,write_json
from benchmark.scoring import detective_scorer
from benchmark.scoring.writing_scorer import safe_text

TRACK='text_only_detective'
RUBRIC={'event_reconstruction':25,'logic':25,'evidence_accuracy':20,'uncertainty':15,'report_quality':15}

def protocol():return hashlib.sha256((source_hash()+TRACK).encode()+__import__('pathlib').Path(__file__).read_bytes()).hexdigest()

def prompt():
    original=(ROOT/'benchmark/prompts/detective_prompt.md').read_text(encoding='utf-8')
    return original+'\n\nTEXT-ONLY VERSION: Only the written case brief and documents D01–D03 are supplied. Images V01–V10 are unavailable and are not part of this version. Do not claim to inspect images or invent their contents. Use only written evidence, explicitly note missing visual evidence, and abstain when it prevents a defensible identification. The review rubric covers reconstruction (25), logic (25), written-evidence accuracy (20), uncertainty (15), and report quality (15).'

def workspace(original,model,kind,case):
    run=original(model,kind,case)
    if kind!='detective':return run
    images=run/'input/images'
    # Only remove image files from this newly-created private copy, never the dataset.
    for p in images.glob('*.png'):
        if not p.is_symlink() and p.resolve().is_relative_to((run/'input').resolve()):p.unlink()
    brief=run/'input/case_brief.md'
    brief.write_text(brief.read_text(encoding='utf-8')+'\nText-only track: visual exhibits are not supplied. Use written exhibits D01–D03.\n',encoding='utf-8')
    identity=read_json(run/'identity.json');identity.update(sensory_track=TRACK,variant_protocol=protocol());write_json(run/'identity.json',identity)
    return run

def make_task(kind,run,box,model,deadline):
    from benchmark.harness.runner import PROTOCOL,local_agent,artifact_score
    cfg=config()['benchmark'];system=(ROOT/'benchmark/prompts/common_system_prompt.md').read_text(encoding='utf-8')
    text=prompt()+'\n'+(run/'input/case_brief.md').read_text(encoding='utf-8')
    for doc in sorted((run/'input/documents').glob('*')):text+='\nPUBLIC WRITTEN EXHIBIT '+doc.name+'\n'+doc.read_text(encoding='utf-8')
    text+=f"\nBudget: {cfg['max_calls']} model calls, {cfg['max_output_tokens_per_call']} output tokens per call, {cfg['task_timeout_seconds']} seconds."
    return Task(name='local_detective_text_only',version=1,dataset=[Sample(id='attempt',input=[ChatMessageSystem(content=system+'\n'+PROTOCOL),ChatMessageUser(content=text)])],
        solver=local_agent(box,model,deadline,run,cfg['max_calls']),scorer=artifact_score(run,box,kind),metadata={'sensory_track':TRACK,'protocol_hash':protocol(),'run_path':str(run)},time_limit=cfg['task_timeout_seconds']+300)

def score(run,box=None):
    original=detective_scorer.score(run,box);art=run/'artifacts'
    conclusion=safe_text(art/'conclusions.json',art);refs=set(re.findall(r'\b[VD]\d\d\b',conclusion));unsupported=sorted(refs-{'D01','D02','D03'})
    categories={'event_reconstruction':original['categories']['event_reconstruction'],
        'logic':25 if original['evidence']['conclusion_correct'] and len(refs)>=2 and not unsupported else 0,
        'evidence_accuracy':original['categories']['evidence_accuracy'],'uncertainty':15 if original['categories']['uncertainty']==10 else original['categories']['uncertainty'],
        'report_quality':original['categories']['report_quality']}
    return {**original,'rubric':RUBRIC,'categories':categories,'verified_points':sum(v for v in categories.values() if v is not None),
        'pending_points':sum(RUBRIC[k] for k,v in categories.items() if v is None),'quality_score':None if any(v is None for v in categories.values()) else sum(categories.values()),'complete':False,
        'evidence':{**original['evidence'],'sensory_track':TRACK,'available_exhibits':['D01','D02','D03'],'unsupported_conclusion_references':unsupported},
        'limitations':original['limitations']+['Written-evidence version with a separate 100-point rubric. Images were not supplied; exclude from native multimodal rankings. Full completion needs independent review.'],
        'scoring_version':'text-detective-1.0','review_status':'pending' if any(v is None for v in categories.values()) else 'automatic'}

REVIEW_GUIDE='''Written-evidence Detective (images not supplied)
Reconstruction (25): Build a consistent chronology from D01-D03. Distinguish observations from hypotheses and identify gaps.
Logic (25): Support deductions and abstention with written exhibits. Do not infer image contents.
Evidence accuracy (20): Check each quotation, claim and citation against D01-D03. Image references can identify unavailable evidence, but cannot substantiate an observation.
Uncertainty (15): Explain what cannot be established without visual evidence; calibrate confidence and avoid unsupported identification.
Report quality (15): Present a readable report, timeline, evidence inventory and defensible conclusion, with limitations and next steps.
Full completion requires independent review of all four output files. This rubric is separate from the visual Detective benchmark.'''
