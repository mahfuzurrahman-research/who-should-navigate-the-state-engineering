# Reproducibility

## Local

```bash
python -m pip install -r requirements.txt
./run_public_demo.sh
python -m unittest discover -s tests -v
```

## Docker

```bash
docker build -t state-navigation-engineering .
docker run --rm state-navigation-engineering
```

Generated files are written under `outputs/` and are intentionally ignored by Git except for `.gitkeep`.

A successful run proves only that the public synthetic engineering demonstration executes reproducibly within its stated boundary.
