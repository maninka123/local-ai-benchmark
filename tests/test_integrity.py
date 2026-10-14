import json,pytest
from benchmark.harness.runner import parse_actions
from benchmark.scoring.data_scorer import numeric_match
from benchmark.scoring.writing_scorer import safe_text,score_result
from benchmark.harness.metrics_collector import collect
from benchmark.util import append_json,ROOT,read_json

def test_tool_protocol_rejects_unknown_and_oversized_batch():
    with pytest.raises(ValueError):parse_actions('{"tool":"host_shell"}')
    with pytest.raises(ValueError):parse_actions(json.dumps({'actions':[{'tool':'list'}]*5}))
    assert parse_actions('```json\n{"tool":"list","path":"/input"}\n```')[0]['tool']=='list'
    assert parse_actions('{"tool":"python","code":"print(1)"')[0]['code']=='print(1)'
    with pytest.raises(ValueError):parse_actions('{"tool":"python","code":"print(')

def test_actual_weighted_throughput(tmp_path):
    for tokens,sec in [(100,1),(100,10)]:
        append_json(tmp_path/'inference_calls.jsonl',{'call':sec,'success':True,'wall_seconds':sec,'output_tokens':tokens,'input_tokens':20,'eval_duration_ns':sec*1e9,'prompt_eval_duration_ns':1e9,'load_duration_ns':0})
    result=collect(tmp_path)
    assert result['generation_tps']==pytest.approx(200/11)
    assert result['output_tokens']==200 and result['warm_calls']==[1,10]

def test_reader_blocks_parent_escape(tmp_path):
    inside=tmp_path/'art';inside.mkdir();outside=tmp_path/'secret';outside.write_text('hidden answer')
    assert safe_text(outside,inside)==''

def test_numeric_counts_exact_percent_tolerant():
    assert numeric_match('20 duplicates',20)
    assert not numeric_match('19 duplicates',20)
    assert numeric_match('margin 12.1%',.12)

def test_pending_scores_are_not_full_quality_scores():
    s=score_result('detective',{'event_reconstruction':None,'visual_evidence':None,'logic':20,'evidence_accuracy':None,'uncertainty':None,'report_quality':None},{},False)
    assert s['quality_score'] is None and s['verified_points']==20 and s['pending_points']==80

def test_dataset_ground_truth_consistency():
    from benchmark.generators.business_data_generator import reference
    m,clean,raw=reference(ROOT/'datasets'/'data_analysis')
    truth=read_json(ROOT/'evaluation_private'/'ground_truth'/'business.json')
    assert m==truth['metrics'] and len(raw)==25000 and len(truth['patterns'])==12
    assert m['supplier_A_overall']<m['supplier_B_overall']
    assert m['supplier_A_express']>m['supplier_B_express']
    assert m['supplier_A_standard']>m['supplier_B_standard']
