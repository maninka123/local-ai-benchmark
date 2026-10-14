"""Record only demonstrated failures of required outputs; never claim completion."""
import _bootstrap,json
from pathlib import Path
from benchmark.util import ROOT,read_json,write_json,now
from extensions.windows_io import atomic_replacements

BASE=ROOT/'results/improvement_campaign'

def main():
    existing=read_json(BASE/'objective_after_reviews.json',[])
    known={(r['run_id'],r['update_id']) for r in existing}
    for entry in read_json(BASE/'campaign.json',{}).get('entries',[]):
        if entry['status']!='needs_final_review' or (entry['run_id'],entry['update_id']) in known:continue
        evaluation=entry.get('evaluation',{});scores=evaluation.get('scores',{});evidence=scores.get('evidence',{})
        run=(ROOT/evaluation['snapshot_path']).resolve()
        if not run.is_relative_to(ROOT.resolve()):raise ValueError('Invalid evaluation path')
        art=run/'artifacts';issues=[];files=[];required=[]
        if entry['task']=='data_analysis':
            required=['report.md','analysis.py','findings.json']
            reproduction=evidence.get('reproducibility',{})
            if reproduction.get('executed') and reproduction.get('exit_code')!=0:issues.append('The saved analysis script failed isolated reproduction. The submitted analytical package is not reproducible.')
            if len(evidence.get('figures',[]))<6:issues.append('Fewer than six readable required chart files were saved.')
            if (evidence.get('writing',{}).get('words') or 0)<1400:issues.append('The analytical report is absent or materially shorter than the requested detailed report.')
        elif entry['task']=='racing_game':
            required=['implementation_report.md']
            if not evidence.get('implementation_present'):issues.append('The saved game source still does not contain a substantive implementation of the racing task.')
            if not evidence.get('browser',{}).get('build'):issues.append('The game failed the isolated build. A working browser application has not been delivered.')
            if evidence.get('runtime_error_count',0):issues.append('The saved browser run still reports runtime errors.')
            if evidence.get('implementation_present') and evidence.get('browser',{}).get('build') and not evidence.get('browser',{}).get('checks',{}).get('canvas'):issues.append('The independent browser capture did not find a rendered game canvas. This is not evidence of a playable 3D race.')
        else:
            required=['investigation_report.md','timeline.json','evidence_analysis.json','conclusions.json']
        for name in required:
            path=art/name
            if not path.is_file() or not path.read_text(encoding='utf-8',errors='replace').strip():issues.append('Required deliverable is missing or empty: '+name)
            else:
                files.append(str(path.relative_to(ROOT)))
                if name.endswith('.json'):
                    try:json.loads(path.read_text(encoding='utf-8'))
                    except (ValueError,UnicodeError):issues.append('Required structured deliverable is not valid JSON: '+name)
        if not issues:continue
        existing.append({'run_id':entry['run_id'],'update_id':entry['update_id'],'completed':False,'completion_basis':'Incomplete after 1 completion pass: '+issues[0],
                         'remaining_issues':issues,'evidence_files':files+[str((run/'evaluation.json').relative_to(ROOT))],
                         'review_method':'Objective required-output gates and saved isolated evaluation; no subjective rating invented.',
                         'review_limitations':['This review proves incompleteness, not every remaining quality defect. No additional improvement prompt was sent.'], 'created':now()})
    write_json(BASE/'objective_after_reviews.json',existing)
    print('Objective incomplete reviews saved:',len(existing))

if __name__=='__main__':
    with atomic_replacements(ROOT):main()
