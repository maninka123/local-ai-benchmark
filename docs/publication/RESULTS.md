# Saved results and playable outputs

[← Main README](../../README.md) · [Open dashboard](https://maninka123.github.io/local-ai-benchmark/) · [Methodology](METHODOLOGY.md) · [Run on your PC](RUN_ON_YOUR_PC.md)

## Start in the dashboard

1. **Overview:** choose a task and metric. Compare final task scores, generation speed, file size, active parameters or total time. Scatter plots let you select both axes; existing task plots remain available.
2. **Model outputs:** select a model and task. Read initial outputs or further work, inspect saved files and open available reports, images and game previews.
3. **Reviews:** inspect each task's single final score, category reasons and completion state. Earlier failed prompts retain status and review notes, without an awarded score.
4. **Reference outputs:** explore the separately labelled frontier examples. They are illustrations, not comparable local-speed measurements and not replacements for local model outputs.

The public Pages dashboard is a **read-only publication**: saved outputs and playable static game builds are available; it cannot invoke models, open your local folders or run the benchmark. Follow the local setup guide to enable those operations on your own PC.

## Attempt labels

| Label | Meaning |
| :-- | :-- |
| Initial / attempt 1 | The original saved benchmark output. |
| Update 1 / attempt 2 | One detailed continuation prompt based on the original work. |
| Update 2 / attempt 3 | One further continuation prompt based on the previous result. |
| Failed to complete | Some required output or behavior remains missing; partial credit may still be earned. |
| Completed successfully | Independent review found all required task behavior complete. |
| Preview opens / script runs | An execution check passed; this alone does not establish task completion. |

Only **Qwen 3.5 27B, Detective case 3** is fully complete, on attempt 3, earning **30.0/100**. The other **52 results remain incomplete** against the full challenge and receive partial credit based on their final output only. Some outputs are still informative or runnable. All 159 review receipts are retained so that progress and regressions remain visible.

## Original model work and assisted repairs

Original outputs and their measured scores are preserved. Six separately labelled repair copies contain small source fixes, each with **fewer than 50 changed source lines**, disclosed counts, patches and validation evidence. Their source changes are not counted as model completion and their outputs do not enter quality scoring.

| Separate repair copy | Changed source lines | What was checked | Remaining limit |
| :-- | --: | :-- | :-- |
| Qwen 3.5 9B · racing | 20 | Static track preview opens. | Not a complete driving game. |
| Nemotron 3 Omni 33B · racing | 27 | Basic WASD movement and steering. | Demo, not a complete race. |
| Qwen 3 VL 30B · racing | 23 | Basic WASD movement and steering. | Full race requirements incomplete. |
| GPT-OSS 20B · data | 8 | Analysis runs and outputs regenerate. | Financial/investigation/report issues remain. |
| GLM 4.7 Flash · data | 12 | Analysis runs and outputs regenerate. | Full deliverables incomplete. |
| Nemotron 3 Nano 30B · data | 2 | Profiling JSON can be generated. | Profiling only, not the full analysis. |

Check the repair card's validation notes before treating an output as usable. A game build can launch and still contain runtime errors, a missing canvas, static geometry or incomplete controls. Builds that did not compile are unavailable for play and remain listed with their failure state.

## Source-backed plots and downloads

The README gallery contains ten compact plots, all sourced from [`chart-data.json`](chart-data.json). The dashboard provides filterable figures and exact values. Review reasons and per-stage records document why two superficially similar outputs can receive different scores.

If you want to compare hardware suitability rather than task outputs, [local-llm-fit](https://github.com/maninka123/local-llm-fit) is a separate model-fit tool. Small active parameter counts should not be confused with the memory required to store every model weight.
