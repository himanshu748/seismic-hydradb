# Seismic judge guide

## The 20-second pitch

Seismic gives coding agents a proof-carrying change gate before they edit code. It turns a real git diff into a safe, review or block decision, backed by exact HydraDB paths, required tests and affected entrypoints.

## What to inspect first

1. Open the dashboard at `http://127.0.0.1:8791/app`.
2. Select **Paste diff** and run the prefilled pricing patch in the seeded `seismic` repository.
3. Show the `review` decision, required test and affected CLI entrypoint.
4. Select an affected result to see the exact graph path.
5. Compare the risk score components and incident evidence.
6. Open `src/seismic/gate.py` and `src/seismic/tools.py` to inspect the policy and native path calls.

## Why HydraDB is essential

- `algo.SSpaths` answers one changed target.
- `algo.MSpaths` evaluates multiple changed targets in one native graph operation.
- `algo.SPpaths` proves one claimed source-to-target impact path.
- Immutable snapshot nodes preserve commit context.
- Stable artifact identity nodes carry incidents across snapshots.
- The Python process stores no durable memory. Fresh MCP processes recover the same active graph from HydraDB.

Replacing HydraDB with a vector store would remove the dependency direction, bounded path proof, multi-hop reachability and stable cross-snapshot incident graph.

## Three-minute demo

### 0:00 to 0:25, problem

Show the landing page. Explain that an agent can find similar code yet still miss a test, CLI entrypoint or indirect caller that will break.

### 0:25 to 1:15, exact blast radius

Open the analyzer, select **Paste diff** and submit the prefilled unified diff. Show how Seismic resolves the changed line to `pricing.calculate`, then returns `review`, `test_total` and the `sample` entrypoint. Select the service handler and trace `calculate` to `total` to `handler` on the graph.

### 1:15 to 1:45, decision through evidence

Point to the gate reasons, relationship labels, hop count and score breakdown. Explain that every action is derived from HydraDB path evidence. An unresolved symbol returns review, never safe.

### 1:45 to 2:15, product depth

Show repository status, immutable commit metadata and the incident modal. Explain that incident edges attach to stable identities and influence later rankings after a new snapshot is indexed.

### 2:15 to 2:40, real MCP

Run the fresh-process stdio test or call `analyze_change` from an attached agent. Then mention that Streamable HTTP is explicitly sessionless and has a separate fresh-client test.

### 2:40 to 3:00, evidence

Show the raw evaluation and stress JSON. State the scope precisely: a self-authored 12-task Track 02 smoke and a deterministic 5,000-artifact, 20,000-relationship local stress proof.

## Reproduce the proof

```bash
.venv/bin/ruff format --check src tests benchmarks
.venv/bin/ruff check src tests benchmarks
.venv/bin/mypy src
.venv/bin/pytest -q -m 'not integration'
.venv/bin/pytest -q -m integration
cd ui && npm run build
```

Current test split: 16 fast tests and 3 live integration tests.

```bash
PYTHONPATH=src .venv/bin/python -m benchmarks.track02_eval
PYTHONPATH=src .venv/bin/python -m benchmarks.stress --queries 25
```

## Honest boundaries

- Python is the production language adapter today.
- The parser is conservative static analysis and cannot prove runtime behavior.
- The 12-task result is a self-authored smoke, not an official track score.
- The HTTP transport is intended for trusted local use until authentication is added.
