from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
BASE=Path(__file__).resolve().parent
OUT=BASE/'output'
now=datetime.now(timezone.utc)
start=datetime(2026,10,13,6,26,13,tzinfo=timezone.utc)
verification=json.loads((BASE/'verification.json').read_text(encoding='utf-8'))
verification['presentation']={
 'static_checks':'Passed: eight embedded PNGs, required report sections, valid section targets, no external network assets, no replacement characters or placeholders.',
 'visual_checks':'All eight final chart images inspected in a contact sheet; chart title overlaps corrected. Chrome desktop preview at 1920x911 and narrow preview at 390x844 inspected. All eight browser images loaded. No body horizontal overflow at either width. Main-findings and executive-summary links checked. Expanded chart opened/closed on mobile; desktop selected customer-chart DOM content verified. Browser console returned no errors or warnings.',
 'chart_review_artifact':'output/figures_review.png',
 'preview_url':'http://127.0.0.1:8767/',
 'browser_surface':'Chrome; in-app browser unavailable',
 'interaction_scope':'Static report with section links and chart expansion. No analytical filters, no server data dependencies.',
 'limitations':'No PDF export verification; no claim of exhaustive assistive-technology testing. Dashboard embedding is delivered for parent integration; standalone page was browser-tested.'
}
verification['verified_at_utc']=now.isoformat()
(BASE/'verification.json').write_text(json.dumps(verification,indent=2,ensure_ascii=False),encoding='utf-8')
context={
 'reference_type':'self-authored tool-assisted reference',
 'task':'data_analysis',
 'requested_model':'gpt-6-astra',
 'configured_model':'gpt-6-astra',
 'requested_reasoning_effort':'high',
 'configured_reasoning_effort':'high',
 'configuration_basis':'Explicit model/reasoning assignment supplied by the parent task; this file is not a provider-side usage attestation.',
 'execution_mode':'Single assigned task with tool-assisted implementation and verification; multiple tool iterations within the original assignment.',
 'original_prompts':{'system':'system_prompt.md','task':'prompt.md','byte_identical_to_originals':True},
 'subsequent_user_correction_prompts':[],
 'parent_delivery_guidance':'One delivery-integration message about dashboard endpoint and CSP; not an analytical correction prompt.',
 'source_restriction':'Only datasets/data_analysis for analytical evidence; evaluation_private, candidate results, scoring answers and prior analyses were not read.',
 'tools_used':['PowerShell and provided Python environment','pandas/numpy/matplotlib/Pillow','standard-library csv/Decimal independent verification','Chrome via cua_repl for rendered inspection'],
 'local_gpu_or_ollama_used':False,
 'other_models_or_subagents_called':False,
 'local_model_campaign_modified_or_resumed':False,
 'python_executable':'D:/LocalLLM/benchmark-env/Scripts/python.exe',
 'timing':{'kind':'measured wall-clock interval only','measurement_started_utc':start.isoformat(),'measurement_finished_utc':now.isoformat(),'elapsed_wall_seconds':round((now-start).total_seconds(),3),'scope':'Clock interval from after initial prompt/skill inspection through final artifact persistence; excludes earlier setup and is not a single model-response latency.','comparable_to_ollama_benchmark':False},
 'tokens':{'input':None,'output':None,'total':None,'status':'unknown; not measured'},
 'benchmark_score':None,
 'not_ground_truth':True
}
(BASE/'execution_context.json').write_text(json.dumps(context,indent=2),encoding='utf-8')
files=[{'path':str(p.relative_to(BASE)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='status.json']
status={
 'status':'completed',
 'completed':True,
 'task':'data_analysis',
 'reference_model':'gpt-6-astra',
 'reasoning_effort':'high',
 'entrypoint':'output/index.html',
 'output_entrypoint':'output/index.html',
 'completed_at_utc':now.isoformat(),
 'report_word_count_approx':2342,
 'figure_count':8,
 'structured_finding_count':8,
 'verification_summary':{'assessment':'Share with caveats','independent_checks_passed':verification['checks_passed'],'checks_failed':0,'revenue_aud':17355447.83,'gross_profit_aud':5047935.83,'gross_margin':0.29085598248143846,'retained_sales':24963,'all_input_and_prompt_hashes_verified':True,'desktop_and_narrow_browser_checks':'passed within recorded scope'},
 'limitations':verification['limitations']+['Timing covers the recorded authoring interval, not total setup or a benchmark-equivalent model inference.','Dashboard iframe integration not independently tested by this reference author.'],
 'is_ground_truth':False,
 'measured_benchmark_score':None,
 'files':files
}
(BASE/'status.json').write_text(json.dumps(status,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'status':status['status'],'entrypoint':status['entrypoint'],'files':len(files),'elapsed_wall_seconds':context['timing']['elapsed_wall_seconds'],'verification_checks':verification['checks_passed']}))
