from benchmark.util import append_json
from extensions import revision_resume as resume


def test_resume_keeps_remaining_budget_and_does_not_charge_paused_time():
    cfg={'task_timeout_seconds':3600,'max_calls':24}
    info={'current_update_id':'current','resume_checkpoint':{'update_id':'current','used_seconds':423,'started_calls':3}}
    assert resume.budget(info,cfg)[:2]==(3177,21)
    info['current_update_id']='new-request'
    assert resume.budget(info,cfg)==(3600,24,None)


def test_resume_restores_completed_messages_and_tool_errors_without_partial_output(tmp_path):
    append_json(tmp_path/'inference_calls.jsonl',{'start':'2026-10-13T02:50:00','end':'2026-10-13T02:52:00','content':'','request_messages':[{'role':'system','content':'Original rules'},{'role':'user','content':'The same saved improvement prompt'},{'role':'user','content':'Controller budget: stale reminder'}]})
    append_json(tmp_path/'tool_calls.jsonl',{'start':'2026-10-13T02:52:01','category':'invalid_arguments','stderr':'substring not found'})
    append_json(tmp_path/'live_events.jsonl',{'kind':'output','text':'Interrupted unsaved response'})
    messages=resume.saved_messages(tmp_path,{'request_created':'2026-10-13T01:00:00'})
    assert messages[1]['content']=='The same saved improvement prompt'
    assert any('substring not found' in m['content'] for m in messages)
    assert all('stale reminder' not in m['content'] and 'Interrupted unsaved' not in m['content'] for m in messages)


def test_resume_preserves_peak_measurements_and_adds_segment_energy():
    result=resume.prior_hardware({'performance':{'peak_vram_bytes':10,'samples':3,'estimated_gpu_energy_joules':2}}, {'hardware_summary':{'peak_vram_bytes':12,'samples':4,'estimated_gpu_energy_joules':5}})
    assert result['peak_vram_bytes']==12 and result['samples']==7 and result['estimated_gpu_energy_joules']==7
