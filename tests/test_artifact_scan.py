from benchmark.util import artifact_files,ROOT,read_json
def test_artifact_scan_excludes_real_linux_dependency_link():
    value=read_json(ROOT/'results'/'game_environment_validation.json')
    if not value:return
    files=list(artifact_files(ROOT/value['path']/'artifacts'))
    assert any(p.name=='main.js' for p in files)
    assert all('node_modules' not in p.parts for p in files)
