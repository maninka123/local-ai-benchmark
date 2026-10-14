import type {Run} from './types';
export default function ScoreSummary({scores,compact=false}:{scores:Run['scores'];compact?:boolean}){
 const missing=Math.max(0,100-(scores.quality_score??scores.verified_points)-scores.pending_points);
 return <div className={compact?'score-status':'score-summary'}><b>Verified so far: {scores.verified_points.toFixed(1)} points</b><small>Awaiting manual review: {scores.pending_points.toFixed(1)} points</small><small>Points not earned: {missing.toFixed(1)}</small><small className="final-score">Final score: {scores.quality_score===null?'Not available yet':`${scores.quality_score.toFixed(1)} / 100`}</small>{!compact?<p>Verified points are already supported by automatic checks. Pending points need a person to inspect the output files and apply the rubric. They are not failed points.</p>:null}</div>;
}
