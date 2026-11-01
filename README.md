# Security fuzzing of LLM-based multi-agent workflows

Code and recorded experimental results for baseline-aware, effect-based security assessment of reader–planner–executor workflows.

## Repository layout

- `src/`: workflow harness, policy oracles, selection strategies, analysis code, and third-party tool notices.
- `experiments/expanded/`: development qualification, 7B evaluation traces, configurations, audit scripts, and recorded run provenance.
- `experiments/primary/`: original study results and raw traces.
- `experiments/supplementary/`: independent replay, executor diagnostics, and increased-budget pilot records.
- `experiments/summary/`: reconstructed summary tables and JSON results.
- `experiments/figures/`: PDF, SVG, PNG, plotting script, and figure data.
- `reproduce.py`: offline verification and reconstruction.
- `run_inference.py`: portable entry point for fresh development and expanded runs.
- `download_models.py`: hash-verified model download.

## Verify recorded results

Python 3.12 is recommended. Verification uses only the standard library; no model download or API key is needed.

```bash
python reproduce.py --check
python reproduce.py --write
```

`--write` saves reconstructed summaries under `verification_output/`. Verification checks recorded traces, inference references, development qualification, policy outcomes, mutation/selection replay, supplementary results, and figure counts. It performs no model inference. `MANIFEST.sha256` checks packaged file integrity.

## Install optional dependencies

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
```

For plotting only, use `requirements-figures.txt`. For fresh inference only, use `requirements-inference.txt`; llama-cpp-python may require platform build tools.

## Rebuild figures

```bash
python experiments/figures/plot_results.py
```

Outputs are written beside the plotting script in `experiments/figures/`.

## Run fresh expanded experiments

Model weights are not bundled. Download the recorded, SHA256-pinned weights, then run development qualification before evaluation:

```bash
python download_models.py --models 7B
python run_inference.py --model 7B --stage baseline --threads 4 --prefix-reuse
python run_inference.py --model 7B --stage evaluation --threads 4 --prefix-reuse
```

New outputs go to `reruns/7B/`, without overwriting accepted records. Evaluation requires the newly computed development gate to pass. Fresh generations may differ by backend, hardware, and numerical settings. Original scripts retained with experiment records document past execution; use the root entry point for portable expanded runs.

## Recorded findings

The expansion contains 36 development workflows and 510 7B evaluation workflows across 15 task variants and four selectors. All selectors yield zero executor policy violations: 0/15 raw and 0/13 strictly baseline-qualified tasks. Unsafe planner proposals occur in 2/120, 3/120, 3/120, and 3/120 queries for random, rarity, tool-name, and policy selection. They concern private-record export and are not successful executor attacks.

Supplementary records cover eight independent clean/attack replays, four executor diagnostics, and a 250-workflow budget pilot. Results do not demonstrate superiority of feedback-guided selection. Menus are shuffled by case ID and fixed within each task; their static position distribution is not a menu-order robustness experiment.

## Provenance and scope

Repackaged from the completed experiment archive (SHA256 `f9aaa51d698bd4169e8f3ad42b2ae628e28dba19c0d82e1775e5d74434df54f7`). Recorded experiment data are unchanged. Paths in portable verification scripts were adapted to this layout. No model inference was performed during repackaging. Manuscript/LaTeX files and publishing instructions are excluded.

The workflow uses synthetic tasks and finite action menus. Third-party tool code is a limited integration, not a full benchmark evaluation. See `LICENSE_NOTICE.md` and vendor notices for licensing scope. No new project-wide license is assigned by this package.
