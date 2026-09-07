# Contributing

- Keep the scope discipline: `data_policy` only, fail closed, no host files modified.
- `uv run --extra dev pytest -q` and `uv run --extra dev ruff check .` must stay green.
- If Hermes refactors the wrapped seam, update `tests/test_seam_shape.py` and `CHANGELOG.md` together.
