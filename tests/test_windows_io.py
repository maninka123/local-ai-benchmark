import json
from pathlib import Path
import pytest
from extensions.windows_io import atomic_replacements
from benchmark.util import write_json


def test_sharing_lock_retries_and_keeps_previous_json_until_success(tmp_path,monkeypatch):
    target=tmp_path/'progress.json'
    target.write_text('{"old":true}')
    original=Path.replace
    calls=[]
    def flaky(source,destination):
        calls.append(destination)
        if len(calls)<3:
            assert json.loads(target.read_text())=={'old':True}
            error=PermissionError('Temporary sharing lock');error.winerror=32;raise error
        return original(source,destination)
    monkeypatch.setattr(Path,'replace',flaky)
    monkeypatch.setattr('extensions.windows_io.time.sleep',lambda _:None)
    with atomic_replacements(tmp_path):write_json(target,{'new':True})
    assert len(calls)==3 and json.loads(target.read_text())=={'new':True}
    assert not list(tmp_path.glob('*.tmp'))


def test_unrelated_permission_failure_is_not_retried(tmp_path,monkeypatch):
    calls=[]
    def denied(source,destination):
        calls.append(destination);raise PermissionError('Permanent ACL error')
    monkeypatch.setattr(Path,'replace',denied)
    with atomic_replacements(tmp_path),pytest.raises(PermissionError):write_json(tmp_path/'progress.json',{})
    assert len(calls)==1


@pytest.mark.skipif(__import__('os').name!='nt',reason='Windows MAX_PATH regression')
def test_evaluation_copy_handles_a_filename_beyond_max_path(tmp_path):
    import shutil
    from extensions.windows_io import extended_path,long_file_copies
    source=tmp_path/'source.txt';source.write_text('preserved snapshot')
    parent=tmp_path
    while len(str(parent))<235:parent=parent/('snapshot_'+('x'*20))
    Path(extended_path(parent)).mkdir(parents=True)
    destination=parent/('artifact_'+('y'*50)+'.txt')
    assert len(str(destination))>260
    with long_file_copies():shutil.copy2(source,destination)
    assert Path(extended_path(destination)).read_text()=='preserved snapshot'
