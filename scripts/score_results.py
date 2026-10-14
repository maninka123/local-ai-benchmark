import _bootstrap, argparse
from benchmark.util import ROOT,read_json,write_json,now
from benchmark.scoring.aggregate_scorer import export
from benchmark.harness.runner import SCORERS
def main():
    for path in (ROOT/'models').glob('*/*/*/result.json'):
        result=read_json(path);run=path.parent
        # Re-score into a dated separate audit file. Original scores/result remain immutable.
        score=SCORERS[result['task']].score(run)
        write_json(run/'score_revisions'/(now().replace(':','')+'.json'),{'timestamp':now(),'original_scores':result['scores'],'recalculated_without_execution':score,
            'note':'Browser/reproducibility checks use retained observations. Re-execution requires a new attempt.'})
    export();print('Independent score audit snapshots generated; original results preserved.')
if __name__=='__main__':main()
