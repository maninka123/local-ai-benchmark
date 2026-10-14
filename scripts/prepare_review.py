"""Create anonymous artifact packets; mapping stays separate from reviewers."""
import _bootstrap,random,uuid,shutil,hashlib
from benchmark.util import ROOT,read_json,write_json,source_hash,now,artifact_files

def main():
    records=[r for r in read_json(ROOT/'results'/'master_results.json',[]) if r['protocol_hash']==source_hash()]
    random.SystemRandom().shuffle(records);batch=uuid.uuid4().hex[:10];root=ROOT/'evaluation_private'/'review_packets'/batch;mapping=[]
    for i,r in enumerate(records,1):
        label=f'attempt_{i:03}';dest=root/label;dest.mkdir(parents=True);source=ROOT/r['run_path']/'artifacts'
        for p in artifact_files(source):
            out=dest/'artifacts'/p.relative_to(source);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
        write_json(dest/'review_context.json',{'task':r['task'],'case':r.get('case'),'rubric':r['scores']['rubric'],
            'instructions':'Review artifacts using the fixed rubric. Candidate identity, speed, prior points and metadata are deliberately withheld. Do not consult the mapping until all quality judgments are saved.',
            'rubric_sha256':hashlib.sha256((ROOT/'evaluation_private'/'scoring_config'/'human_rubric.md').read_bytes()).hexdigest()})
        name='business.json' if r['task']=='data_analysis' else r.get('case','')+'.json'
        truth=ROOT/'evaluation_private'/'ground_truth'/name
        if truth.exists():shutil.copy2(truth,dest/'ground_truth.json')
        if r['task']=='detective':shutil.copytree(ROOT/'datasets'/'detective'/r['case']/'public',dest/'public_evidence')
        mapping.append({'packet':label,'run_id':r['run_id'],'model':r['model']['name']})
    mapdir=ROOT/'evaluation_private'/'review_mappings';mapdir.mkdir(exist_ok=True)
    write_json(mapdir/(batch+'.json'),{'timestamp':now(),'mapping':mapping,'protocol_hash':source_hash()})
    print(f'Created {len(records)} anonymous review packets: {root}. Candidate identities remain in the separate mapping directory.')
if __name__=='__main__':main()
