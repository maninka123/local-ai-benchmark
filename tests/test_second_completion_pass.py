import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/'scripts'))
import run_second_completion_pass as second
import run_completion_pass as runner
from benchmark.util import write_json,read_json


def test_second_prompt_uses_separate_metadata_and_does_not_repeat_saved_request(tmp_path,monkeypatch):
    folder=tmp_path/'work/artifacts';folder.mkdir(parents=True)
    (folder.parent/'completion_pass_prompt.txt').write_text('First prompt preserved')
    workspace={'further_folder':str(folder),'revision':{'revision_id':'revision','status':'finished','prompts':[]}};sent=[]
    def request(client,method,path,payload=None):
        if method=='POST':
            sent.append(payload);workspace['revision']['prompts'].append({'update_id':'second','name':payload['name'],'prompt':payload['prompt'],'created':'2026-10-13T01:00:00+00:00'})
        return workspace
    monkeypatch.setattr(runner,'request',request);monkeypatch.setattr(runner,'PASS_NUMBER',2);monkeypatch.setattr(runner,'METADATA_PREFIX','completion_pass_2')
    campaign={'campaign_id':'second','created':'2026-10-13T00:00:00+00:00'}
    entry={'run_id':'run','model':'model','task':'racing_game','review':{'prompt':'The menu exists; the race still crashes. Complete the playable race.'}}
    runner.submit(None,campaign,entry);runner.submit(None,campaign,dict(entry))
    assert len(sent)==1 and sent[0]['name']=='Completion pass 2 - racing game'
    assert (folder.parent/'completion_pass_prompt.txt').read_text()=='First prompt preserved'
    assert (folder.parent/'completion_pass_2_prompt.txt').read_text()==entry['review']['prompt']


def test_audit_detects_changed_prior_prompt_and_extra_second_prompt(tmp_path,monkeypatch):
    base=tmp_path/'pass_2';base.mkdir();work=tmp_path/'work';work.mkdir();(work/'artifacts').mkdir()
    frozen=tmp_path/'saved.txt';frozen.write_text('Initial output')
    write_json(base/'preserved_fingerprints.json',{'saved.txt':second.digest(frozen)})
    old={'update_id':'old','name':'First','prompt':'Prior prompt','created':'2026-10-12'}
    new={'update_id':'new','name':'Completion pass 2 - task','prompt':'New prompt','created':'2026-10-13'}
    write_json(work/'revision.json',{'prompts':[old,new]})
    monkeypatch.setattr(second,'ROOT',tmp_path);monkeypatch.setattr(second,'BASE',base);monkeypatch.setattr(second,'source_hash',lambda:'fixed')
    campaign={'created':'2026-10-13','protocol_hash':'fixed','entries':[{'run_id':'run','further_folder':str(work/'artifacts'),'previous_requests':[dict(old)]}]}
    assert second.audit(campaign)
    old['prompt']='Overwritten';write_json(work/'revision.json',{'prompts':[old,new,new]})
    assert not second.audit(campaign)
    audit=read_json(base/'execution_validation.json')
    assert audit['changed_previous_prompts']==['run'] and not audit['one_prompt_per_incomplete_result']
    frozen.write_text('Changed initial output')
    assert not second.audit(campaign) and read_json(base/'execution_validation.json')['changed_paths']==['saved.txt']
