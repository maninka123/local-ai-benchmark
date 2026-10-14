import _bootstrap,argparse
from benchmark.util import ROOT,source_hash,write_json,read_json,now
p=argparse.ArgumentParser();p.add_argument('--acknowledge',action='store_true',required=True);p.add_argument('--notes',required=True)
args=p.parse_args();runs=read_json(ROOT/'results'/'master_results.json',[])
if not runs:raise SystemExit('No pilot results to review')
write_json(ROOT/'results'/'pilot_review.json',{'timestamp':now(),'protocol_hash':source_hash(),'reviewed_run_ids':[r['run_id'] for r in runs if r['pilot']],'notes':args.notes})
print('Pilot review acknowledgement saved. Three-repetition runs can now be requested.')
