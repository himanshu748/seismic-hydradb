## Problem and resulting behavior

<!-- Explain the concrete problem and what changes. Link a related issue if any. -->

## Validation

<!-- List exact commands and results; explain checks you could not run.
Python fast gate from the repository root:
  .venv/bin/ruff format --check src tests benchmarks
  .venv/bin/ruff check src tests benchmarks
  .venv/bin/mypy src
  .venv/bin/pytest -q -m 'not integration'
UI changes: (cd ui && npm ci && npm run build); commit the updated ui/dist bundle.
Live graph/transport changes: .venv/bin/pytest -q -m integration with HydraDB.
See CONTRIBUTING.md for prerequisites and the distinction between these checks.
-->

## Review notes

<!-- Relevant tradeoffs or remaining limitations, documentation changes, and
screenshots for visible UI changes. Remove tokens, private code, and sensitive paths.
-->
