import json,re
from benchmark.util import ROOT,read_json
from benchmark.scoring.writing_scorer import safe_text,writing_evidence,score_result

def score(run,box=None):
    art=run/'artifacts';identity=read_json(run/'identity.json');truth=read_json(ROOT/'evaluation_private'/'ground_truth'/(identity['case']+'.json'))
    contents={name:safe_text(art/name,art) for name in ['investigation_report.md','timeline.json','evidence_analysis.json','conclusions.json']}
    parsed={}
    for name in ['timeline.json','evidence_analysis.json','conclusions.json']:
        try:parsed[name]=json.loads(contents[name])
        except ValueError:parsed[name]=None
    text='\n'.join(contents.values());low=text.lower();con=parsed.get('conclusions.json') or {}
    person=con.get('responsible_person',con.get('responsible',con.get('suspect'))) if isinstance(con,dict) else None
    abstention=person is None and any(w in json.dumps(con).lower() for w in ['insufficient','uncertain','cannot','inconclusive'])
    correct=person==truth['responsible_person'] if truth['identifiable'] else abstention
    timeline_text=contents['timeline.json'];events=[]
    for event in truth['timeline']:
        ok=event['time'] in timeline_text and any(e in timeline_text for e in event['exhibits'])
        events.append({'expected':event,'timestamp_and_reference_present':ok})
    ids=set(re.findall(r'\b[VD]\d\d\b',text));valid={f'V{i:02}' for i in range(1,11)}|{'D01','D02','D03'};bad=sorted(ids-valid)
    inventory=parsed.get('evidence_analysis.json')
    inventory_text=contents['evidence_analysis.json'];coverage=sum(f'V{i:02}' in inventory_text for i in range(1,11))/10
    report=contents['investigation_report.md'];write=writing_evidence(report,['executive','inventory','timeline','suspect','deduction','contradiction','conclusion','confidence|limitation','next|recommend'])
    from benchmark.harness.metrics_collector import rows
    received=set()
    for call in rows(run/'inference_calls.jsonl'):
        if not call.get('success'):continue
        for message in call.get('request_messages',[]):
            if message.get('images'):
                received.update(re.findall(r'Native visual exhibit[:\s]+(?:/input/images/)?(V\d{2})\.png',message.get('content','')))
    final_refs=set(re.findall(r'\b[VD]\d\d\b',contents['conclusions.json']))
    categories={'event_reconstruction':None if timeline_text else 0,'visual_evidence':None if inventory_text else 0,
        'logic':20 if correct and len(final_refs)>=2 and not bad else 0,'evidence_accuracy':None if text else 0,
        'uncertainty':10 if (not truth['identifiable'] and abstention) else None if truth['identifiable'] and text else 0,
        'report_quality':None if report else 0}
    complete=all(contents.values()) and all(parsed.values()) and coverage==1 and write['words']>=400 and all(write['sections'].values()) and correct and not bad and len(received)==10
    return score_result('detective',categories,{'conclusion_correct':correct,'declared_person':person,'expected_person':truth['responsible_person'],
        'abstention':abstention,'timeline_checks':events,'visual_exhibit_coverage':coverage,'native_exhibits_actually_received':sorted(received),'invalid_exhibit_ids':bad,'writing':write},complete,
        ['Correct identity/abstention is scored deterministically; correctness of reasoning and observations is pending ground-truth review. Timestamp/reference presence is diagnostic, not proof that an event is reconstructed correctly.'])
