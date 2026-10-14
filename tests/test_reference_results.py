import json
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from dashboard.backend import references


@pytest.fixture
def reference_client(tmp_path, monkeypatch):
    monkeypatch.setattr(references, 'BASE', tmp_path / 'references')
    monkeypatch.setattr(references, 'ROOT', tmp_path)
    root = references.BASE / 'racing_game'
    (root / 'output').mkdir(parents=True)
    (root / 'output/index.html').write_text('<html><h1>Game</h1></html>')
    (root / 'status.json').write_text(json.dumps({'entrypoint': 'output/index.html'}))
    prompts = tmp_path / 'benchmark/prompts'
    prompts.mkdir(parents=True)
    (prompts / 'racing_game_prompt.md').write_text('Original task')
    (root / 'prompt.md').write_text('Original task')
    app = FastAPI()
    app.include_router(references.router)
    return TestClient(app), root


def test_reference_availability_prompt_identity_and_isolated_html(reference_client):
    client, _ = reference_client
    tasks = client.get('/api/references').json()['tasks']
    assert len(tasks) == 3
    assert tasks[0]['available'] and tasks[0]['original_prompt_matches']
    assert not tasks[1]['available']
    response = client.get('/api/references/racing_game/open')
    assert response.status_code == 200
    assert 'sandbox allow-scripts' in response.headers['content-security-policy']
    assert 'allow-same-origin' not in response.headers['content-security-policy']
    assert response.headers['access-control-allow-origin'] == '*'


def test_reference_routes_cannot_escape_or_serve_dependency_tree(reference_client):
    client, root = reference_client
    (root / 'node_modules').mkdir()
    (root / 'node_modules/private.txt').write_text('dependency')
    for path in ('../status.json', '/absolute', 'node_modules/private.txt', '.secret'):
        with pytest.raises(Exception) as exc:
            references.safe_file('racing_game', path)
        assert exc.value.status_code == 404
    assert client.get('/api/references/unknown/open').status_code == 404
    listing = client.get('/api/references/racing_game/files').json()
    assert all('node_modules' not in item['path'] for item in listing)
    (root / 'status.json').write_text(json.dumps({'entrypoint': '../private.html'}))
    assert client.get('/api/references/racing_game/open').status_code == 409
    assert not client.get('/api/references').json()['tasks'][0]['available']


def test_open_folder_rejects_foreign_origins(reference_client, monkeypatch):
    client, root = reference_client
    opened = []
    monkeypatch.setattr(references.os, 'startfile', lambda path: opened.append(path), raising=False)
    assert client.post('/api/references/racing_game/open-folder', headers={'Origin': 'https://evil.example'}).status_code == 403
    assert client.post('/api/references/racing_game/open-folder', headers={'Sec-Fetch-Site': 'cross-site'}).status_code == 403
    assert not opened
    assert client.post('/api/references/racing_game/open-folder').status_code == 200
    assert opened == [str(root.resolve())]
