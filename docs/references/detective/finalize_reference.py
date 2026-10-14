from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
import jsonschema

root=Path(__file__).resolve().parent
def read(p): return json.loads((root/p).read_text(encoding='utf-8'))
def save(p,obj): (root/p).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
schemas=read('output_schemas.json')
for cid in ['case_01','case_02','case_03']:
    for kind,schema in schemas.items(): jsonschema.Draft202012Validator(schema).validate(read(f'output/{cid}/{kind}.json'))
render=read('render_validation.json')
assert render['sandbox_lightbox_opens'] and render['sandbox_lightbox_closes'] and not render['page_errors']
verification=read('verification.json')
verification['status']='passed_with_explicit_evidentiary_limitations'
verification['render_validation']={'status':'passed','details_file':'render_validation.json','visual_inspection':['preview_desktop.png','preview_evidence.png','preview_mobile.png','preview_lightbox.png'],'observations':'Desktop and mobile layouts visibly readable with 18px body text, no horizontal overflow; 30 embedded images; section links, expandable evidence notes, and in-document full-image dialog work. Dialog tested with sandbox allow-scripts and no external network access.'}
verification['checks'] += ['All 9 final JSON outputs revalidated after final wording adjustment','Browser: 18px body text at desktop/mobile; zero horizontal overflow; 30 source images; zero page errors','In-document image enlargement opens, loads full-resolution image, and closes under opaque-origin CSP sandbox allow-scripts','All four rendered preview screenshots visually inspected by author']
verification['verification_limitations']=['Source review and validation were performed by the same author, not an independent reviewer.','Public evidence cannot determine definitive identity, exact removal act, or authorisation.','The benchmark prompt supplies no formal JSON schema; the included schema is reference-authored.','Default Playwright Chromium executable was unavailable; validation used installed Google Chrome in headless mode.']
save('verification.json',verification)
ctx=read('execution_context.json')
finished=datetime.now(timezone.utc)
ctx['authoring_finished_utc']=finished.isoformat()
ctx['wall_time_seconds']=round((finished-datetime.fromisoformat(ctx['authoring_started_utc'])).total_seconds(),3)
ctx['wall_time_measurement_scope']='Elapsed from first recorded UTC clock reading after initial prompt/path inspection through final verification. Not a benchmark response-time measurement.'
ctx['tools_used'] += ['Python jsonschema for local output-schema validation','Python Playwright with installed headless Google Chrome for desktop/mobile and sandbox rendering checks']
save('execution_context.json',ctx)
required=['output/index.html']+[f'output/{cid}/{f}' for cid in ['case_01','case_02','case_03'] for f in ['investigation_report.md','timeline.json','evidence_analysis.json','conclusions.json']]
for p in required: assert (root/p).is_file()
save('status.json',{'status':'complete','completed':True,'task':'detective','model':'gpt-6-astra','reasoning_effort':'high','entrypoint':'output/index.html','output_entrypoint':'output/index.html','completion':'Three independently assessed public-evidence cases, each with a nine-part investigation report and three structured JSON outputs, combined in one self-contained light-theme HTML report.','reference_only':True,'comparable_local_benchmark_run':False,'ground_truth':False,'cases':{'case_01':'Nora is the probable lead; no definitive personal attribution.','case_02':'Eli is the probable lead after subtracting five minutes from the service-camera time; ENTRY-direction ambiguity remains.','case_03':'Responsible individual unresolved; Eli and Maya are opportunity leads without a possession link.'},'required_files':required,'verification':'verification.json','verification_status':verification['status'],'limitations':['Identity relies on coats and credentials rather than biometric evidence.','No removal act or authorisation record is supplied.','Case 03 remains unattributable.','Token usage is unknown; wall time is reference-authoring elapsed time.','Validation is self-review against public evidence and a reference-authored schema, not benchmark scoring.'],'finished_utc':finished.isoformat(),'wall_time_seconds':ctx['wall_time_seconds'],'token_usage':None})
save('artifact_manifest.json',[{'path':p,'bytes':(root/p).stat().st_size,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in required])
print(json.dumps({'status':'complete','required_files':len(required),'wall_time_seconds':ctx['wall_time_seconds'],'entrypoint':'output/index.html'},indent=2))
