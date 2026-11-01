# GDPval morph: 2025 → 2026

The animated treemap lives at `change/index.html`; the original remains at `../index.html`. Drag timeline or play/replay. Size, positions, colours, and labels morph smoothly; the 9 sector names and 44 occupations remain fixed. Click a tile for original GDPval task prompts plus newly observed 2026 O*NET work tasks.

**What is measured?** 2025 colours = original best-of-seven model wins-or-ties by occupation (GDPval September 2025); 2025 sizes = BLS May 2024 occupational employment × annual mean wage. 2026 sizes = BLS May 2025 (latest available in October 2026). 2026 work tasks = Anthropic Economic Index May 2026, exact O*NET task IDs mapped to O*NET 30.1 occupations and the 44 GDPval SOC codes, with shared tasks apportioned. February 2026 task-success judgements from Anthropic are linked by normalized exact task text. These outcomes are model-classified, not blind human expert evaluations.

**What is not measured?** 2026 occupational GDPval win rates. The 2026 colours are an *illustrative projection*, not evaluation results. The script uses log-odds uplift of the original occupational scores with a small capped, sample-size-shrunk correction from February task success, and calibrates the equal-occupation mean to GPT-5.5's published **84.9% overall GDPval** result (April 2026). This combines a best-of-seven baseline with one-model aggregate and is *not* strictly like-for-like, nor a statistical estimate. Do not use individual projected scores as facts or claim any wage bill is automatable. Intermediate slider values are animation only.

**Economic weight caveat:** All occupational wage estimates are nationwide *across industries*. The nine GDPval sector labels are groupings, not industry-specific payroll. Salary is not GDP; neither wage movements nor observed Claude usage establishes AI-driven employment effects.

## Sources & rebuild

- Original: https://openai.com/index/gdpval/
- 2026 aggregate: https://openai.com/index/introducing-gpt-5-5/
- Official O*NET 30.1 tasks (public mirror): https://raw.githubusercontent.com/theodorewright11/ai-workforce-exposure-dataset-construction-public/main/data/task_statements_v30.1.csv
- BLS OEWS national May 2025 (public mirror): https://raw.githubusercontent.com/theodorewright11/ai-workforce-exposure-dataset-construction-public/main/data/oews_national_2025.csv
- May 2026 usage: https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv
- Feb 2026 success: https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2026_03_24/data/aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv
- Original SOC mapping derived from: https://apps.lawrencewu.net/job-tasks/

`build_morph.py` downloads/reuses sources in Windows %TEMP%, joins and validates 44 occupation keys, and generates `morph-data.json`. That JSON includes full source URLs and SHA256 digests. The large raw source CSV files are not stored in Git.

```powershell
cd C:\code\datastories\gdpval\change
uv run --no-project python build_morph.py
uv run --no-project python -m unittest -v test_morph.py
uv run --no-project python -m http.server 8766 --bind 127.0.0.1
```

**Best next step for scientific validity:** independently run new models on the *original 220 GDPval tasks* with consistent expert-quality grading; publish occupation-level 2026 scores and replace the modelled endpoint. This current version is a preview; no commit or push.
