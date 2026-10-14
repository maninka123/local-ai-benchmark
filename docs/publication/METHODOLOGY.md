# Methodology and measurement guide

[← Main README](../../README.md) · [Dashboard](https://maninka123.github.io/local-ai-benchmark/) · [Results](RESULTS.md) · [Run on your PC](RUN_ON_YOUR_PC.md)

## Scope and fair comparisons

The publication covers **13 local models, three task families and 53 saved task results**, with an initial output and two benchmark continuation prompts reviewed separately: **159 output judgments**. The original model files, automatic scores and measurements remain preserved. Older setup prompts are audit history, not additional benchmark completion attempts.

This is a capability study on one desktop, not a standardized universal model ranking. Installed quantization differs; historical baseline budgets differ; Detective inputs differ by track; one run cannot support a confidence interval or broad reliability claim. The dashboard retains those distinctions instead of hiding them.

## Task-specific rubric

Every review uses the public task requirements and saved model output. Points reflect demonstrated behavior and evidence rather than the model's assertions. Missing artifacts, incorrect claims, incomplete gameplay and unsupported deductions receive reduced credit. Scores are not spread artificially to create differences between models.

| Task | Output rubric, total 100 points |
| :-- | :-- |
| Data analysis | Data understanding 15; numerical accuracy 20; substantive unexpected-pattern investigation 20; visualization 15; report quality 15; recommendations 15. |
| Racing game | Runnable application/game flow 10; circuit/scenery 12; differentiated vehicles 10; driving/handling 12; interacting opponents 14; collisions 10; cameras 8; valid laps/positions/finish 14; interface 5; truthful deliverables/verification 5. |
| Visual Detective | Evidence examination/fidelity 25; timeline reconstruction 20; defensible conclusion/alternatives/follow-up 20; suspect analysis 15; required deliverables/structure 10; clarity/consistency 10. |
| Written Detective | The AI output review uses the same six weighted categories as Visual Detective: 25/20/20/15/10/10. Evidence is judged against the written inputs actually supplied. |

This table describes the **published AI output-review rubric**. Preserved automatic benchmark rubrics are separate; their visual and written Detective categories differ. Sharing AI review weights does not make the tracks equivalent: their available evidence and case coverage differ.

Reviewers used saved source/output and independent public-input checks. This was **not a blinded evaluation**: existing campaign metadata was available during earlier completion review. Private answer matching was not used as the AI output-quality rubric. The review distinguishes observed, source-supported and unverified behavior; a screenshot or candidate diagnostic hook alone is insufficient proof of a complete game.

## One final score per task result

The final completion policy awards one score for the task result. Earlier failed attempts retain status, feedback and review receipts; they have no awarded score. The final rubric quality, Q, is used only for partial credit when the task remains incomplete after the third prompt:

| Final task state | Awarded score | Rule |
| :-- | :-- | :-- |
| Complete on initial prompt | 100 | Fixed completion credit |
| Complete on second prompt | 60 | Fixed completion credit |
| Complete on third prompt | 30 | Fixed completion credit |
| Incomplete after third prompt | 0–30 partial credit | 0.3 × final raw rubric quality |

For example, work still incomplete after three prompts with final rubric quality 75.0 receives **22.5/100**, clearly labelled incomplete. A task fully completed on its third prompt receives **30.0/100**. Review records preserve what happened at each stage without awarding earlier failures their own scores.

**Excluded from quality scoring:** elapsed time, token speed, model size, hardware efficiency, frontier reference outputs and separately assisted repairs. AI review judgments are not human ratings and can be challenged by examining the rubric evidence. Original automatic verified points are a separate, often incomplete, check of the output.

## Detective tracks and averages

Seven vision-capable models have three native multimodal cases each, for **21 visual case results**. Six text-only entries have one written-evidence case each, for **six written results**. Written inputs do not provide the same sensory evidence as the images; the tracks are explicitly labelled **[V]** and **[W]**.

Figures average recorded observations within a case, then give contributing cases equal weight. Missing values are omitted, not treated as zero. A three-case visual average and a single written case should not be interpreted as an identical test. The dashboard exposes individual case reviews and coverage.

## Measurement definitions

| Measurement | Meaning and limits |
| :-- | :-- |
| Generation tokens/s | Within a run, sum of recorded output tokens divided by sum of generation durations. README speed plot uses initial run measurements; task/case averages are then formed for display. Not an average of individual call ratios. |
| Prompt tokens/s | Analogous recorded input-token processing speed. Context length, cold loading and cache behavior can affect it. |
| Initial task time | Recorded elapsed task execution, shown in minutes. Budget and timeout states are retained. |
| Total time | Initial work + saved update work + re-evaluations; queue waiting excluded. README Detective values are per-case averages. Includes other saved model updates in the workspace, so it is not a strictly equal-three-prompt cost comparison. |
| Installed model size | Downloaded package bytes ÷ 1,000,000,000: decimal GB. Different quantization and auxiliary weights affect size. Not measured peak VRAM/RAM. |
| Total parameters | Installed GGUF language-model tensor count, where available; kept distinct from rounded publisher counts. |
| Calculated active parameters | Total tensors minus inactive routed expert weights; shared experts, attention, embeddings and other language-model weights remain. Dense models count all language-model weights as active by convention. Auxiliary encoders are separated. |
| Estimated active weight GB | Installed bytes × active language-model parameters ÷ all counted parameters. A proportional storage estimate affected by mixed quantization and file overhead; not a measured memory footprint. |
| RAM/VRAM peaks | Whole-machine/device samples; other applications can contribute. Process memory is separately recorded where available. |

Ollama did not record expert activation traces. **Token speed and VRAM cannot determine the actual active parameter count.** All model weights still need to be available, even when an MoE routes only a few experts per token. An apparent active-storage estimate does not establish that a model fits entirely on the GPU.

## Sandbox and reproducibility

Candidate code executes in a task-specific Docker container, with read-only inputs and a separate writable output directory, no network, no host-shell fallback, no private answer mounts and bounded resources. Model calls run sequentially. Public game previews use compiled, read-only saved builds; preview availability is distinct from full-task correctness.

Data and fictional case inputs are generated by the repository's setup scripts. New benchmark runs must generate their own private reference calculations locally; published outputs are examples, not hidden answers to be supplied to models.

## Figure provenance

The ten README figures are produced by [`build_figures.py`](build_figures.py) using the projected scalar records in [`chart-data.json`](chart-data.json). This projection contains measurements, installed identities, track/case identifiers and review scores, without model weights, local account paths, process lists or private expected-answer data. [`figure-validation.json`](figure-validation.json) records figure count, source coverage and completion totals.

Figures use one decimal place for displayed values, a stable task palette and explicit axes. A line joining initial and latest quality represents progress on the same task result, not an inferred causal relationship or confidence estimate.
