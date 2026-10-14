# Run the benchmark on your own PC

[← Main README](../../README.md) · [Public dashboard](https://maninka123.github.io/local-ai-benchmark/) · [Methodology](METHODOLOGY.md)

The published dashboard and saved outputs need no model download. These steps are for **fresh local inference and task execution**. Model packages are downloaded separately through Ollama and are not included in this repository.

## Requirements

- Python 3.10 or newer, Node 20.19+ or 22.12+, Git and a running Ollama server.
- Docker with Linux containers; on Windows, Docker Desktop with a working WSL2 backend.
- Enough disk, RAM and GPU memory for the models you choose. The published results used an RTX 4080 16 GB, i9-13900K and 64 GB RAM; your speeds and offload behavior will differ.

Start Docker and Ollama before setup. Choose exact installed Ollama IDs rather than shortened dashboard display labels. You can use [local-llm-fit](https://github.com/maninka123/local-llm-fit) to explore candidate models for your hardware first.

## Windows PowerShell setup

```powershell
git clone https://github.com/maninka123/local-ai-benchmark.git
cd local-ai-benchmark
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm.cmd run dashboard:install
npm.cmd run dashboard:build
docker build -t local-llm-benchmark:1.0 sandbox
```

Pull a model you can accommodate, for example:

```powershell
ollama pull qwen3.5:9b-q4_K_M
```

Model availability and tags are controlled by their publishers/Ollama. Substitute a current installed ID if necessary. On Linux/macOS, use `.venv/bin/python` and `npm` in place of the Windows commands.

## Generate fresh inputs and validate isolation

```powershell
.\.venv\Scripts\python.exe scripts/setup.py
.\.venv\Scripts\python.exe scripts/run_all.py --list-models
```

Setup records your hardware/software, generates the synthetic data and case inputs, and verifies the Docker boundary, read-only inputs, blocked network, path restrictions and browser. **It does not start the long benchmark.** Private answer/reference files are created locally for independent evaluation and are never mounted in the candidate container.

Use a fresh working clone for reruns. If the repository includes published example outputs, keep those preserved; a new model task creates a new attempt directory. `config.yaml` controls task budgets, selected models and exclusions. Set `selected_models` to exact installed IDs if you do not want every discovered model tested. DeepSeek-OCR is excluded from this capability benchmark.

## Run one task first

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --model 'qwen3.5:9b-q4_K_M' --task data_analysis --pilot
.\.venv\Scripts\python.exe scripts/score_results.py
.\.venv\Scripts\python.exe scripts/generate_report.py
.\.venv\Scripts\python.exe scripts/dashboard.py
```

Open **http://127.0.0.1:8765**. Initial files, measurements and automatic scoring appear after the attempt. Subjective task-quality judgments require a separate evidence-based review; the publication's AI judgments are saved examples, not automatic ground truth for your new outputs.

For a vision model's Detective case:

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --model 'qwen3.5:9b-q4_K_M' --task detective --case case_01 --pilot
```

The general runner skips native image Detective for text-only models. Written-evidence tests use the separate `extensions/text_detective.py` protocol and original campaign scripts; they must not be silently substituted into the visual ranking.

## Larger runs and further work

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --model 'qwen3.5:9b-q4_K_M' --pilot
```

Models run sequentially through a shared GPU lock. Saved matching attempts are skipped on resume; `--force` creates a new attempt, while `--retry-failed` retries failed harness runs. Inspect the pilot before starting repetitions: `scripts/review_pilot.py --acknowledge --notes 'Reviewed pilot inputs, execution and scoring.'`, then `scripts/run_all.py --repetitions 3` for the selected models. Budget changes and repetitions create distinct comparison cohorts.

In the local dashboard, Further work continues in a separate workspace. Original outputs stay preserved; each prompt and re-evaluation adds an audit record. Initial time, update time and total time remain separate. Public Pages has no server-side model execution, so prompting is available only locally.

## Rebuild the publication figures

```powershell
.\.venv\Scripts\python.exe docs/publication/build_figures.py
```

The script regenerates the ten SVG charts from the saved projected [`chart-data.json`](chart-data.json). It does not download models or execute candidate code. To publish results from a new run, prepare a fresh sanitized measurement projection and review records first; do not mix new hardware/budgets into the existing figure cohort without labelling the change.

## Verify the software

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd run dashboard:build
```

Frontend browser checks live in `dashboard/frontend/tests`; Docker isolation checks run during setup. Candidate output can be incorrect even when infrastructure checks pass. Keep execution checks, output-quality judgments and completion separate.
