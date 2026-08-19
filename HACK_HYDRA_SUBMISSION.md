# Hack Hydra submission draft: Seismic

Use this document to fill the official form. Keep the claims and numbers unchanged unless the checked-in evidence is regenerated.

## Project name

Seismic

## Short description

Seismic gives coding agents an evidence-backed safe, review or block decision before they edit code by traversing an immutable code graph in HydraDB.

## Track

Select `Track 2 | Repos, Dependencies + Code as Graphs` in the form. Seismic follows direction B from the participant guide: code graphs for IDE assistants.

Seismic is meaningfully distinct from the HydraMind Track 03 entry. Seismic
analyzes source-code dependency paths before edits; HydraMind manages changing
cross-session facts and trust provenance. The products use different schemas,
benchmarks and workflows.

## The problem

Coding agents can retrieve code that looks relevant while missing the exact caller, test or entrypoint that a change can break. Text similarity is useful for discovery, but it cannot prove dependency direction or transitive blast radius. That leaves agents confident without the evidence needed to act safely.

## What I built

Seismic parses a real Python Git repository into an immutable HydraDB snapshot. Files, functions, classes, tests, entrypoints and package versions become artifacts connected by typed relationships such as `CALLS`, `IMPORTS`, `TESTS` and `STARTS_AT`.

A coding agent sends either a symbol or a bounded unified diff. Seismic resolves the changed lines to symbols, asks HydraDB for reverse dependency paths and returns:

- a deterministic `safe`, `review` or `block` decision
- required tests with ready-to-run pytest commands
- affected entrypoints and CODEOWNERS
- ranked impacts with exact HydraDB path evidence
- a conservative abstention when the graph cannot support a claim

The same workflow is available through eight stateless MCP tools and a local dashboard. Incident evidence attaches to stable artifact identities across snapshots, so later analyses can use previous breakage without rewriting old commits. Every gate also writes a `DecisionReceipt` to HydraDB. Missing targets or incomplete parser coverage force review and preserve the fallback reason for future agents.

## How the project uses HydraDB

HydraDB is Seismic's system of record and path engine, not a replaceable log sink. Seismic connects with the official Neo4j Python driver over Bolt and stores immutable repository snapshots, artifact identities, typed code relationships and incident evidence in HydraDB.

At query time, Seismic calls HydraDB's native `algo.SSpaths`, `algo.MSpaths` and `algo.SPpaths` procedures for bounded reverse dependency traversal, multi-target analysis and exact source-to-impact proof. Every supported impact is backed by a returned graph path. Unresolved inputs produce a review decision without inventing an impact path. Fresh MCP processes recover the active snapshot from HydraDB because the Python service keeps no durable project state.

Without HydraDB, Seismic would lose dependency direction, bounded multi-hop reachability, inspectable path proof and durable incident links across snapshots. A vector store can retrieve similar text, but it cannot answer the core blast-radius question by itself.

## Quality and evaluation evidence

All figures below are reproducible local evidence, not official hackathon scores.

- 22 tests pass: 19 database-independent tests and 3 live tests against local HydraDB plus real MCP transports
- 12 source-reviewed Track 02 smoke tasks: 10 supported cases with valid exact paths and 2 correct abstentions
- HydraDB graph retrieval: 1.0000 precision@k, 1.0000 recall@k and 1.0000 MRR
- TF-IDF baseline on the same tasks: 0.1321 precision@k, 0.1321 recall@k and 0.2250 MRR
- deterministic portability smoke across HydraMind, OmniDev and BlastRadius: 49 supported impacts with every returned path structurally valid
- deterministic stress proof: 5,000 artifacts, 20,000 relationships and 25/25 exact target recoveries
- stress query latency: 17.045 ms p50 and 21.100 ms p95 on the recorded isolated-store run

Raw results are checked into `benchmarks/results/track02-evaluation.json`, `benchmarks/results/real-repositories.json` and `benchmarks/results/stress.json`.

## Tech stack

- Python 3.12
- HydraDB and OpenCypher over Bolt
- official Neo4j Python driver
- MCP Python SDK with stateless stdio and Streamable HTTP transports
- FastAPI, Uvicorn and Pydantic
- React, TypeScript and Vite
- Remotion with Murf narration for the demo video
- Pytest, Ruff and MyPy for verification

## Team members and contributions

Primary contact: Himanshu Kumar

Team size: 1

Team member: Himanshu Kumar, using the same email entered in the form's Primary Contact Email field.

Contribution: solo builder responsible for the product concept, system architecture, HydraDB graph model, parser, ingestion, MCP tools, dashboard, evaluation, testing and demo video.

LinkedIn: https://linkedin.com/in/himanshu748

X / Twitter: @jhahimanshu653

## Public GitHub repository

https://github.com/himanshu748/seismic-hydradb

The repository is public and licensed under MIT. Its participant-authored history begins on August 17, 2026.

## Deployed project link

https://seismic-hydradb.vercel.app/

This is the public product landing page. The real analyzer and MCP run locally because Seismic requires a running HydraDB node and access to a local Git checkout. The landing page does not pretend to expose that trusted local workflow as a public backend.

## Demo video

Final local file:

`videos/seismic-remotion-demo/renders/seismic-hack-hydra.mp4`

Verified duration: 2:59.00. The final file is 1920x1080 H.264 with 48 kHz stereo AAC audio. Both streams passed full decode checks and the inspected proof frames show eight MCP tools, the 22-test split, conservative abstention and a durable HydraDB receipt. SHA-256: `e29e733d29d87ea4d306ef2f9954067777668aea777168f2eda5a8d86e6a918d`.

Public unlisted demo: https://youtu.be/8cI9_XvLKGQ

The upload completed in both SD and HD. Signed-out access was verified through YouTube's public oEmbed endpoint, which returned the correct Seismic title and playable embed.

The video covers the four required sections in order: the problem, what Seismic is, the working change-analysis flow and why HydraDB is essential.

## Three-minute demo flow

1. Problem: similarity can miss an exact caller, test or entrypoint.
2. Product: index a real repository into an immutable HydraDB snapshot.
3. Working demo: analyze a changed symbol and light up the exact two-hop dependency path.
4. Agent gate: send a unified diff and return review, required tests, an affected entrypoint and path evidence.
5. Auditable fallback: an unresolved symbol returns review, no invented impact path and a durable HydraDB receipt.
6. HydraDB: show the native path procedures and stable cross-snapshot incident graph.
7. Receipts: show the test split, graph-versus-TF-IDF evaluation and deterministic stress result.

## Setup and testing instructions for judges

Follow the README quick start with a source-built HydraDB `graph-node`. Docker is not required. Set `SEISMIC_TOKEN` to the same token used by `graph-node` and set `SEISMIC_ALLOWED_ROOTS` to the parent directory of a Git repository.

Run the dashboard with:

```bash
.venv/bin/seismic-web
```

Run the fast checks with:

```bash
.venv/bin/ruff format --check src tests benchmarks
.venv/bin/ruff check src tests benchmarks
.venv/bin/mypy src
.venv/bin/pytest -q -m 'not integration'
cd ui && npm run build
```

With HydraDB running, run the live transport and database checks with:

```bash
.venv/bin/pytest -q -m integration
```

## Known limitations

- The production parser currently supports Python.
- Dynamic dispatch, reflection and generated code can remain unresolved.
- A `safe` decision means no supported impact exists within the indexed graph and requested bound. It is not a claim of runtime certainty.
- Streamable HTTP is intended for trusted local use until a real network authentication boundary is added.
- The evaluation is a transparent self-authored smoke suite, not SWE-bench or an official Hack Hydra score.
- Local writers use per-repository cross-process locks, validate both artifact and
  relationship counts, and reject stale activations. Cross-host indexing would
  require distributed coordination.

## Required form confirmations

- Originality Confirmation: supported by the public Git history. The first participant-authored commit is dated August 17, 2026.
- Submission Eligibility: Seismic was built for Hack Hydra and is not a substantially pre-built or previously completed project.
- HydraDB Requirement: HydraDB stores the code graph and runs the native path queries that power Seismic's core workflow.
- Link Accessibility: the final YouTube URL and public GitHub repository both open while signed out.
- One Submission Rule: multiple meaningfully distinct submissions are confirmed as
  allowed. HydraMind and Seismic are separate products in different tracks.
- Final Confirmation: confirm only after every answer and link has been checked for accuracy.

## Final pre-submit checklist

- [x] Final MP4 is under 3 minutes and has passed full video and audio decode checks
- [x] Video is uploaded to a public or unlisted YouTube URL
- [x] Video URL opens while signed out
- [x] GitHub repository opens while signed out
- [x] Latest commit and green CI are visible on `main`
- [x] Repository contains the MIT license, README, setup instructions and HydraDB explanation
- [x] Official form uses `Track 2 | Repos, Dependencies + Code as Graphs`
- [x] Team lists Himanshu Kumar as the solo builder with team size 1
- [x] Required originality, eligibility, HydraDB and final confirmations are checked truthfully
- [x] Multiple meaningfully distinct submissions are confirmed as allowed
- [x] Form was submitted on August 19, 2026 and the confirmation page reported that the Hack Hydra submission was received
