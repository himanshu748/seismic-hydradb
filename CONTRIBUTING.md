# Contributing to Seismic

Seismic maps Python repositories and Git diffs to graph-backed change gates. Start
with a small, reproducible change and check existing
[issues](https://github.com/himanshu748/seismic-hydradb/issues) and
[pull requests](https://github.com/himanshu748/seismic-hydradb/pulls) for overlap.
For changes to graph contracts, gate policy, dependencies, or platform support,
describe the intended behavior and tradeoffs in an issue before a large implementation.

## Start without HydraDB

Use Linux or macOS, Git, Python 3.12, and [uv](https://docs.astral.sh/uv/).
Python 3.12 matches CI; the package metadata currently allows Python 3.11 and newer.
Windows is currently blocked by the POSIX `fcntl` import in `src/seismic/ingest.py`.

Fork this repository on GitHub, then substitute your GitHub username below:

```bash
git clone https://github.com/YOUR-USERNAME/seismic-hydradb.git
cd seismic-hydradb
git switch -c your-change
uv venv --python 3.12
uv pip install -e '.[dev]'
.venv/bin/pytest -q -m 'not integration'
```

This fast suite needs no running HydraDB, token, `.env` file, or Node.js setup.
It covers parser fixtures, identities, diff parsing, gate policy, risk scoring,
MCP registration, and web API contracts with a fake service. The parser tests
create temporary Git repositories. A useful first focused run is:

```bash
.venv/bin/pytest -q tests/test_diffing.py
```

The running Seismic service still requires HydraDB. Passing the fast suite does
not verify Bolt queries, native graph paths, or live MCP transports.

## Find the relevant code

| Area | Code | Existing checks |
| --- | --- | --- |
| Repository parsing and ownership | `src/seismic/parser.py`, `src/seismic/gitmeta.py` | `tests/test_parser.py` |
| Patch paths and changed ranges | `src/seismic/diffing.py` | `tests/test_diffing.py` |
| Change decisions and risk | `src/seismic/gate.py`, `src/seismic/risk.py` | `tests/test_gate.py`, `tests/test_risk.py` |
| Immutable snapshots and graph operations | `src/seismic/ingest.py`, `src/seismic/tools.py`, `src/seismic/db.py` | `tests/test_hydradb.py` (live) |
| MCP contract and transports | `src/seismic/server.py` | `tests/test_server.py` (fast), `tests/test_mcp_stdio.py`, `tests/test_mcp_http.py` (live) |
| Dashboard and web API | `ui/src/`, `src/seismic/web.py` | UI build, `tests/test_web.py` |

The [README](README.md) explains the graph direction invariant, conservative
abstention, configuration, benchmarks, and current product boundaries.

## Verify your change

Run the Python fast gate from the repository root:

```bash
.venv/bin/ruff format --check src tests benchmarks
.venv/bin/ruff check src tests benchmarks
.venv/bin/mypy src
.venv/bin/pytest -q -m 'not integration'
```

To format changed Python files, use `.venv/bin/ruff format path/to/file.py`.
Add a focused regression test for changed behavior, then run the relevant suite.
Use the existing fixtures and fake services when live graph behavior is not needed.
Keep parser evidence, immutable snapshot semantics, and conservative gate results
explicit in tests; do not infer runtime certainty from static graph evidence.

### Dashboard changes

Use Node.js 22 to match CI. From the repository root:

```bash
cd ui
npm ci
npm run build
cd ..
git diff -- ui/dist
```

`ui/dist` is tracked and included in the Python wheel. Commit the rebuilt bundle
when UI sources change. CI rebuilds it and runs `git diff --exit-code -- ui/dist`
to detect stale generated files. For unchanged UI, that command should exit cleanly.
`npm run dev` in `ui/` starts Vite; actual repository analysis also needs the
configured Seismic backend and HydraDB described in the README.

### Live graph and transport changes

The integration marker requires a running HydraDB Bolt endpoint. Use only a
disposable local graph: the live suite leaves snapshots, receipts, and incidents
behind. After testing, stop the test node and manually discard its disposable
graph data. Do not use a graph containing data you need to keep. Follow the
[README setup](README.md#quick-start) for the connection variables and allowed
repository roots, then run:

```bash
.venv/bin/pytest -q -m integration
```

[The live workflow](.github/workflows/live-hydradb.yml) contains the pinned HydraDB
revision, Linux source-build dependencies, node startup configuration, and readiness
check used in CI. It runs on pushes to `main` and manual dispatch; the
[fast workflow](.github/workflows/ci.yml) runs on pushes and pull requests.
Record which live checks you actually ran and any unavailable prerequisites in
your PR. Do not substitute an unrelated graph database for HydraDB validation.

## Report a bug or propose a feature

Use the issue templates. Include the commit, OS, Python version, exact command,
expected and actual behavior, and a minimal fixture or patch. For graph-dependent
reports, include the HydraDB revision and relevant configuration names with secret
values removed. Distinguish observed behavior from an untested hypothesis.

For features, describe the user problem, a bounded scope, acceptance criteria,
and how the behavior could be verified. Search for an existing discussion first.
Keep tokens, `.env` contents, private repository code, and sensitive local paths
out of issues, logs, fixtures, and screenshots.

## Submit a pull request

Target `main` in `himanshu748/seismic-hydradb`. Keep unrelated changes separate.
Explain the problem, resulting behavior, related issue (if any), and exact checks
run with their results. For visible UI changes, include a screenshot when useful.
Update documentation for behavior or configuration changes. Inspect your diff for
generated files and accidental secrets before pushing.

Contributions use the repository's existing [MIT license](LICENSE).
