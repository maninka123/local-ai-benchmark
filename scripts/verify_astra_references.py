"""Verify saved reference delivery and preservation without invoking any model."""
import _bootstrap
import hashlib
import json
from pathlib import Path
from benchmark.util import ROOT, now, source_hash
from extensions.windows_io import extended_path


def digest(path):
    return hashlib.sha256(Path(extended_path(path)).read_bytes()).hexdigest()


def main():
    base = ROOT / 'results/references/gpt-6-astra-high'
    tasks = {}
    hashes = {}
    for task in ('data_analysis', 'racing_game', 'detective'):
        path = base / task
        status_path = path / 'status.json'
        status = json.loads(status_path.read_text(encoding='utf-8-sig')) if status_path.exists() else {}
        entry = path / status.get('entrypoint', 'missing')
        prompt = path / 'prompt.md'
        system = path / 'system_prompt.md'
        tasks[task] = {
            'marked_complete': status.get('completed') is True,
            'entrypoint_exists': entry.is_file() and entry.resolve().is_relative_to((path / 'output').resolve()),
            'original_task_prompt_unchanged': prompt.is_file() and digest(prompt) == digest(ROOT / f'benchmark/prompts/{task}_prompt.md'),
            'original_system_prompt_unchanged': system.is_file() and digest(system) == digest(ROOT / 'benchmark/prompts/common_system_prompt.md'),
            'verification_record_exists': (path / 'verification.json').is_file(),
            'execution_context_exists': (path / 'execution_context.json').is_file(),
        }
        import os
        for current, dirs, names in os.walk(path, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in ('node_modules', '__pycache__', '.git') and not (Path(current) / d).is_symlink())
            for name in sorted(names):
                file = Path(current) / name
                if not file.is_symlink():
                    hashes[file.relative_to(base).as_posix()] = digest(file)
    preserved_path = ROOT / 'results/improvement_campaign/pass_2/preserved_fingerprints.json'
    preserved = json.loads(preserved_path.read_text())
    changed = [name for name, value in preserved.items() if digest(ROOT / name) != value]
    campaign = json.loads((ROOT / 'results/improvement_campaign/pass_2/campaign.json').read_text())
    baseline_path = base / 'reference_file_fingerprints.json'
    baseline_changed = []
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text())
        baseline_changed = sorted(name for name in set(baseline) | set(hashes) if hashes.get(name) != baseline.get(name))
    ready = all(all(checks.values()) for checks in tasks.values())
    expected_protocol = '4ca3101df485abbc202f43244551a7c93b2ec8055ac09845b480c58c1fe0f4e0'
    protocol_unchanged = source_hash() == expected_protocol
    paused = campaign.get('status') == 'paused' and (ROOT / 'results/improvement_campaign/stop_requested').is_file()
    valid = ready and not changed and not baseline_changed and protocol_unchanged and paused
    record = {'timestamp': now(), 'delivery_checks_passed': valid, 'tasks': tasks,
              'preserved_local_files_checked': len(preserved), 'changed_local_files': changed,
              'core_protocol_unchanged': protocol_unchanged, 'changed_reference_files': baseline_changed,
              'local_campaign_status': campaign.get('status'),
              'local_campaign_stop_flag': (ROOT / 'results/improvement_campaign/stop_requested').is_file(),
              'scope': 'File delivery, prompt identity and preservation checks only. Behavioral/analytical checks are in each task verification.json. This does not assign a benchmark quality score.'}
    if valid and not baseline_path.exists():
        baseline_path.write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    (base / 'reference_validation.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))
    raise SystemExit(0 if valid else 1)


if __name__ == '__main__':
    main()
