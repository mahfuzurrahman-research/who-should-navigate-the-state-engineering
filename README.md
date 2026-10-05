# Who Should Navigate the State? — Research Engineering Demonstration

Public engineering companion to **Who Should Navigate the State? Administrative Burden, Navigation Responsibility, and the Organizational Allocation of State Complexity**.

This repository demonstrates the engineering patterns used around the private scientific project without redistributing restricted survey records, unpublished manuscript material, accepted empirical coefficients, or private scientific artifacts.

## What this public repository demonstrates

- Python analytical orchestration
- R/Python cross-language numerical validation on synthetic data
- DuckDB relational modeling
- typed staging, core relations, and analytical marts
- relational and domain QA gates
- synthetic survey-style data generation
- automated reporting
- static dashboard generation
- unit, integration, and failure-mode testing
- GitHub Actions continuous integration
- Docker-based reproducibility

## Architecture

```text
Synthetic encounter generator
          │
          ▼
Schema / domain validation
          │
          ▼
Python weighted analytics
          │
          ├──────────────┐
          ▼              ▼
   Python summary     R summary
          │              │
          └──────┬───────┘
                 ▼
        Cross-language parity
                 │
                 ▼
       DuckDB staging layer
                 │
                 ▼
         Core relational model
                 │
                 ▼
          Analytical marts
                 │
                 ▼
            QA gates
                 │
                 ▼
      JSON / Markdown / HTML
```

## Synthetic data only

All tracked records in `data/synthetic/` are generated specifically for this public repository. They are not samples, subsets, perturbations, or transformations of the private research data.

The synthetic schema uses generic fields: `region`, `stratum_id`, `psu_id`, `service_type`, `redirect_flag`, `attained_flag`, and `weight`. These names are intentionally generic and are not a release of the private scientific variable dictionary.

## Quick start

```bash
python -m pip install -r requirements.txt
./run_public_demo.sh
```

The demo regenerates deterministic synthetic data, validates input contracts, computes Python summaries, builds the DuckDB warehouse, executes relational QA, runs R/Python parity when `Rscript` is available, and generates JSON, Markdown, and HTML outputs.

Run tests with:

```bash
python -m unittest discover -s tests -v
```

## Public / private boundary

### Public here

- synthetic inputs
- generic validation logic
- generic weighted analytics
- SQL/DuckDB engineering
- R/Python parity demonstration
- testing, CI, Docker, reporting, documentation

### Kept private

- restricted source microdata
- private constructed analytical records
- original survey variable mappings
- exact accepted empirical specifications
- accepted coefficients and covariance matrices
- manuscript and supplement
- private provenance and execution artifacts
- journal-review material

## Scientific boundary

This repository is an **engineering demonstration**. Synthetic results are illustrative only and must not be interpreted as findings from the paper. It does not establish causal effects, population estimates, administrative outcomes, lawful closure, or any result from the private scientific analysis.

## Authorship

Copyright © Mahfuzur Rahman. See `COPYRIGHT.md`.

No open-source license is granted by this repository unless a separate license file is added later.
