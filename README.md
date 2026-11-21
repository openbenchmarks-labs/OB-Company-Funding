# OB-Company-Funding

Open, independent benchmark of company funding data APIs. Every provider receives the same company domain and returns the company's latest funding round: stage, amount and announced date, checked against funding events verified from official sources. Two boards: freshness for rounds announced in the last 30 days, enrichment for older rounds. Providers measured include Crunchbase, Harmonic, Apollo, People Data Labs, ZoomInfo, Crustdata, Explorium, Fundable, PredictLeads, Ocean.io, Exa, Parallel, Firecrawl and Seltz.

**Live leaderboard:** [openbenchmarks.com/company-funding](https://openbenchmarks.com/company-funding) · **Public dataset:** [`openbenchmarks/OB-Company-Funding`](https://huggingface.co/datasets/openbenchmarks/OB-Company-Funding)

Published and maintained by **[OpenBenchmarks Labs](https://openbenchmarks.com)**.

## Methodology

The benchmark evaluates providers across two separate boards based on round age:

- **Enrichment**: Rounds announced more than 30 days ago (durable historical accuracy).
- **Freshness**: Rounds announced in the trailing 30 days (recent announcement coverage).

Every provider response is graded on three core fields (`judge/config.yaml`):

- `latest_stage`: Funding stage, normalized with stage equivalence rules (`judge/stage_aliases.json`).
- `amount`: Round size in USD (exact match within ±5% tolerance).
- `announced_on`: Announced date in `YYYY-MM-DD` (exact match within ±7 days tolerance).

The live board ranks providers on latest funding stage. Providers are scored against the company observations they were actually measured on, with 95% confidence intervals computed in `judge/grader.py`.

## Tools evaluated

16 tools configured in [`tools/`](tools/README.md):

`apollo`, `company-enrich`, `crustdata`, `exa`, `explorium`, `fiber`, `firecrawl`, `fundable`, `fundingwire`, `nimble`, `ocean`, `parallel`, `people-data-labs`, `predictleads`, `seltz`, `zoominfo`

## Dataset

- **Public split:** 10 companies published on Hugging Face at [`openbenchmarks/OB-Company-Funding`](https://huggingface.co/datasets/openbenchmarks/OB-Company-Funding).
- **Public sample:** 4 example companies are committed in [`data/sample.jsonl`](data/sample.jsonl) for offline verification (`selftest`) and schema reference.
- **Held-out split:** The evaluation cohorts used for the published Enrichment and Freshness boards stay private so providers cannot train on them.

See [`data/README.md`](data/README.md) for the file schema.

## Repository structure

- [`data/`](data/README.md): Input schema documentation and 4-row public sample (`sample.jsonl`) for offline checks.
- [`harness/`](harness/README.md): CLI runner (`run`, `grade`, `selftest`, `list-tools`) and one adapter per tool.
- [`tools/`](tools/README.md): One `<tool>.yaml` config per funding-data provider (16 tools).
- [`judge/`](judge/README.md): Deterministic field grader, stage alias table (`stage_aliases.json`), and confidence intervals.
- [`benchmark.yaml`](benchmark.yaml): Benchmark contract, scope, and refresh cadence.
- [`AGENTS.md`](AGENTS.md): Entry guide for coding agents.

## Quick start

Run the offline check (no API keys required):

```sh
uv venv && uv pip install -r requirements.txt
.venv/bin/python -B -m harness.run selftest --tasks data/sample.jsonl
```

Ask tools about your companies. Without `--execute` this prints the plan and calls nothing; with it, the tools are called and billed:

```sh
cp .env.example .env   # then add the keys for the tools you run
.venv/bin/python -B -m harness.run run --tasks data/sample.jsonl --setups exa,apollo
.venv/bin/python -B -m harness.run run --tasks data/sample.jsonl --setups exa,apollo --out runs/sample --execute
```

Grade one setup's answers against ground truth:

```sh
.venv/bin/python -B -m harness.run grade --tasks data/sample.jsonl --predictions runs/sample/exa.jsonl
```

List configured tools:

```sh
.venv/bin/python -B -m harness.run list-tools
```

## Adding or updating a tool

1. Add or edit `tools/<tool>.yaml` (and `.env.example` if adding a new API key).
2. For a new tool, add `harness/adapters/<tool>.py`.
3. Run the offline `selftest` command above.
4. Open a pull request.

## Links

- [Live leaderboard](https://openbenchmarks.com/company-funding) and [methodology](https://openbenchmarks.com/company-funding#methodology)
- [JSON API](https://openbenchmarks.com/api/benchmarks/company-funding)
- [Hugging Face dataset](https://huggingface.co/datasets/openbenchmarks/OB-Company-Funding)
- [`llms.txt`](https://openbenchmarks.com/llms.txt)

## Related benchmarks

- [OB-Company-Enrichment](https://github.com/openbenchmarks-labs/OB-Company-Enrichment): Core firmographic enrichment ([leaderboard](https://openbenchmarks.com/company-enrichment))
- [OB-Company-News](https://github.com/openbenchmarks-labs/OB-Company-News): Company news search and news-index APIs ([leaderboard](https://openbenchmarks.com/company-news))
- [OB-Company-Search-Lookalikes](https://github.com/openbenchmarks-labs/OB-Company-Search-Lookalikes): Company lookalike discovery ([leaderboard](https://openbenchmarks.com/lookalikes))
- [All OpenBenchmarks leaderboards](https://openbenchmarks.com)

## License

MIT. See [LICENSE](LICENSE).
