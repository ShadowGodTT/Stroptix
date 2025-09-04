# StrOptix Lite

Minimal, production-grade CLI that reads structured inputs and a plate-size library, applies simple rules, ranks combinations by lowest steel weight, and exports an Excel matching a target layout.

## Quickstart

```bash
# Create venv (Windows PowerShell)
python -m venv .venv
. .venv/Scripts/Activate.ps1

# Or using uv
# uv venv && . .venv/Scripts/Activate.ps1

pip install -e .

# Run
stroptix run --input data/sample_input.xlsx --library data/plate_library.xlsx --config data/config.yaml --out results/output.xlsx
```

If `data/sample_input.xlsx` or `data/plate_library.xlsx` are missing, the CLI will bootstrap minimal demo files.

## Features
- Input → Output only (no analysis integration)
- Simple configuration-driven rules and frame-type to depth mapping
- Pydantic models, pandas processing, Excel export via openpyxl/xlsxwriter
- Deterministic and local-only

## Repository Layout
```
pyproject.toml
README.md
stroptix/
  __init__.py
  cli.py
  models.py
  config.py
  library.py
  rules.py
  generator.py
  io_excel.py
  mapping.py
  version.py
data/
  sample_input.xlsx
  plate_library.xlsx
  config.yaml
tests/
  test_end_to_end.py
  test_rules.py
  test_generator.py
```

## Testing
```bash
pytest -q
```

## Notes
- Density assumed 7850 kg/m^3
- Code-check status is a placeholder: "Not evaluated"
- Rules are minimal and toggleable via feature flags in `config.yaml`



