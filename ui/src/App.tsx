import {
  AlertTriangle,
  ArrowRight,
  Check,
  ChevronRight,
  CircleDot,
  Database,
  FileCode2,
  GitCommitHorizontal,
  History,
  LoaderCircle,
  Network,
  RefreshCw,
  SearchCode,
  Server,
  TriangleAlert,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import { GraphCanvas } from "./GraphCanvas";
import { Logo } from "./Logo";
import type {
  ChangeReport,
  Health,
  ImpactResult,
  IngestSummary,
  RepositoryStatus,
} from "./types";

const DEFAULT_REPO_ID = "seismic";
const DEFAULT_TARGET = "src/sample_app/pricing.py::calculate";

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [repoId, setRepoId] = useState(DEFAULT_REPO_ID);
  const [repoPath, setRepoPath] = useState("");
  const [target, setTarget] = useState(DEFAULT_TARGET);
  const [maxHops, setMaxHops] = useState(4);
  const [status, setStatus] = useState<RepositoryStatus | null>(null);
  const [ingest, setIngest] = useState<IngestSummary | null>(null);
  const [report, setReport] = useState<ChangeReport | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [busy, setBusy] = useState<"health" | "index" | "analyze" | "incident" | null>("health");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [incidentOpen, setIncidentOpen] = useState(false);
  const [incidentDescription, setIncidentDescription] = useState("");
  const [incidentSeverity, setIncidentSeverity] = useState("high");

  const selected = useMemo(
    () => report?.results.find((result) => result.artifact_key === selectedKey) ?? null,
    [report, selectedKey],
  );

  useEffect(() => {
    let current = true;
    Promise.allSettled([api.health(), api.status(DEFAULT_REPO_ID)]).then(([healthResult, statusResult]) => {
      if (!current) return;
      if (healthResult.status === "fulfilled") setHealth(healthResult.value);
      else setError(healthResult.reason instanceof Error ? healthResult.reason.message : "HydraDB health check failed.");
      if (statusResult.status === "fulfilled") setStatus(statusResult.value);
      setBusy(null);
    });
    return () => {
      current = false;
    };
  }, []);

  async function checkRepository() {
    setError(null);
    try {
      setStatus(await api.status(repoId));
    } catch (caught) {
      setStatus(null);
      setError(messageOf(caught));
    }
  }

  async function handleIndex(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setBusy("index");
    try {
      const result = await api.index(repoPath, repoId);
      setIngest(result);
      setRepoId(result.repo_id);
      setStatus(await api.status(result.repo_id));
      setNotice(`Activated ${result.artifacts} artifacts and ${result.relationships} code relationships.`);
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy(null);
    }
  }

  async function handleAnalyze(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setBusy("analyze");
    try {
      const result = await api.analyze(repoId, target, maxHops);
      setReport(result);
      setSelectedKey(result.results[0]?.artifact_key ?? null);
      if (result.results.length === 0) {
        const unresolved = result.unresolved_targets.length
          ? ` Target not found: ${result.unresolved_targets.join(", ")}.`
          : " No supported path exists within this hop bound.";
        setNotice(`Analysis returned no affected artifacts.${unresolved}`);
      } else {
        setNotice(`Found ${result.results.length} affected artifacts through ${result.engine}.`);
      }
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy(null);
    }
  }

  async function handleIncident(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    setBusy("incident");
    setError(null);
    try {
      await api.recordIncident(repoId, target, selected.logical_key, incidentDescription, incidentSeverity);
      setIncidentOpen(false);
      setIncidentDescription("");
      setNotice("Incident stored in HydraDB. Re-analyze to include it in risk ordering.");
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <Logo />
        <div className="track-label">Hack Hydra · Track 02B</div>
        <div className="header-snapshot">
          <GitCommitHorizontal size={15} />
          <span>{status ? shortSha(status.commit_sha) : "No active snapshot"}</span>
        </div>
        <div className={`connection ${health?.ok ? "connected" : ""}`}>
          <span />
          {busy === "health" ? "Connecting" : health?.ok ? "HydraDB · Bolt" : "Backend unavailable"}
        </div>
        <a className="header-docs" href="/" aria-label="Open Seismic overview">Overview</a>
      </header>

      <aside className="repository-rail">
        <div className="rail-heading">
          <span>Repository</span>
          <button type="button" onClick={checkRepository} aria-label="Refresh repository status">
            <RefreshCw size={15} />
          </button>
        </div>
        <label className="field-label" htmlFor="repo-id">Repository ID</label>
        <div className="compact-input">
          <Database size={15} />
          <input id="repo-id" value={repoId} onChange={(event) => setRepoId(event.target.value)} />
        </div>

        <div className="snapshot-block">
          <div className="snapshot-icon"><GitCommitHorizontal size={18} /></div>
          <div>
            <span>Active snapshot</span>
            <strong>{status ? shortSha(status.commit_sha) : "Not indexed"}</strong>
          </div>
        </div>
        <dl className="snapshot-facts">
          <div><dt>Artifacts</dt><dd>{status?.artifact_count.toLocaleString() ?? "0"}</dd></div>
          <div><dt>Relations</dt><dd>{status?.relationship_count.toLocaleString() ?? "0"}</dd></div>
          <div><dt>Status</dt><dd className={status?.status === "ready" ? "ready" : ""}>{status?.status ?? "empty"}</dd></div>
        </dl>

        <form className="index-form" onSubmit={handleIndex}>
          <div className="form-title"><Server size={16} /><span>Index a checkout</span></div>
          <label className="field-label" htmlFor="repo-path">Allowed Git path</label>
          <input
            id="repo-path"
            placeholder="/path/to/repository"
            value={repoPath}
            onChange={(event) => setRepoPath(event.target.value)}
            required
          />
          <button className="secondary-button" type="submit" disabled={busy !== null || !repoPath.trim()}>
            {busy === "index" ? <LoaderCircle className="spin" size={16} /> : <Network size={16} />}
            {busy === "index" ? "Building snapshot" : "Index repository"}
          </button>
        </form>

        <div className="rail-proof">
          <span>Graph invariant</span>
          <code>consumer → dependency</code>
          <small>Blast radius traverses incoming edges.</small>
        </div>
      </aside>

      <main className="analysis-workspace">
        <div className="canvas-header">
          <div>
            <span>Dependency fault map</span>
            <strong>{report ? report.targets.join(", ") : "Awaiting a change target"}</strong>
          </div>
          <div className="canvas-engine"><CircleDot size={14} />{report?.engine ?? "HydraDB native paths"}</div>
        </div>
        <GraphCanvas
          report={report}
          selectedKey={selectedKey}
          onSelect={setSelectedKey}
          loading={busy === "analyze"}
        />

        <section className="evidence-drawer" aria-label="Selected impact evidence">
          {selected ? (
            <>
              <div className="evidence-title">
                <span>Exact evidence path</span>
                <strong>{selected.reason}</strong>
              </div>
              <div className="path-strip">
                {selected.nodes.map((node, index) => (
                  <div className="path-step" key={node.key}>
                    <span className={index === 0 ? "change" : ""}>{node.kind}</span>
                    <strong>{node.qualified_name || node.logical_key}</strong>
                    {selected.hops[index] && (
                      <small><ArrowRight size={13} /> {selected.hops[index].type}</small>
                    )}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="drawer-empty"><SearchCode size={18} /> Select an affected artifact to inspect its path.</div>
          )}
        </section>

        <form className="analysis-bar" onSubmit={handleAnalyze}>
          <div className="target-field">
            <label htmlFor="target">Planned change</label>
            <div><FileCode2 size={18} /><input id="target" value={target} onChange={(event) => setTarget(event.target.value)} required /></div>
          </div>
          <label className="hop-field" htmlFor="max-hops">
            Max hops
            <select id="max-hops" value={maxHops} onChange={(event) => setMaxHops(Number(event.target.value))}>
              {[2, 3, 4, 5, 6].map((value) => <option key={value}>{value}</option>)}
            </select>
          </label>
          <button className="primary-button" type="submit" disabled={busy !== null || !target.trim() || !repoId.trim()}>
            {busy === "analyze" ? <LoaderCircle className="spin" size={18} /> : <TriangleAlert size={18} />}
            {busy === "analyze" ? (
              "Tracing paths"
            ) : (
              <><span className="analyze-label-wide">Analyze change</span><span className="analyze-label-short">Analyze</span></>
            )}
          </button>
        </form>
      </main>

      <aside className="impact-rail">
        <div className="impact-heading">
          <div><span>Affected artifacts</span><strong>{report?.results.length ?? 0}</strong></div>
          <small>{report ? `within ${maxHops} hops` : "run an analysis"}</small>
        </div>
        <div className="impact-list">
          {report?.results.length ? report.results.map((result, index) => (
            <ImpactRow
              key={result.artifact_key}
              result={result}
              index={index}
              selected={selectedKey === result.artifact_key}
              onSelect={() => setSelectedKey(result.artifact_key)}
            />
          )) : (
            <div className="impact-empty">
              <Network size={24} />
              <strong>No evidence yet</strong>
              <span>Run a change analysis to rank callers, tests and entrypoints.</span>
            </div>
          )}
        </div>
        {selected && (
          <div className="impact-detail">
            <div><span>Risk score</span><strong>{selected.risk_score.toFixed(2)}</strong></div>
            <dl>
              <div><dt>Distance</dt><dd>{selected.hop_distance} {selected.hop_distance === 1 ? "hop" : "hops"}</dd></div>
              <div><dt>Confidence</dt><dd>{Math.round(selected.resolution_confidence * 100)}%</dd></div>
              <div><dt>Incidents</dt><dd>{selected.incident_count}</dd></div>
              <div><dt>Last author</dt><dd>{selected.last_author || "Unknown"}</dd></div>
            </dl>
            <button className="incident-button" type="button" onClick={() => setIncidentOpen(true)}>
              <History size={15} /> Record an incident
            </button>
          </div>
        )}
      </aside>

      {(error || notice) && (
        <div className={`toast ${error ? "error" : "success"}`} role="status" aria-live="polite">
          {error ? <AlertTriangle size={18} /> : <Check size={18} />}
          <span>{error ?? notice}</span>
          <button type="button" onClick={() => { setError(null); setNotice(null); }} aria-label="Dismiss message">×</button>
        </div>
      )}

      {incidentOpen && selected && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setIncidentOpen(false)}>
          <form className="incident-modal" onSubmit={handleIncident} onMouseDown={(event) => event.stopPropagation()}>
            <div className="modal-icon"><History size={20} /></div>
            <h2>Record breakage evidence</h2>
            <p>Link a real incident to this change path so future ranking can use it.</p>
            <div className="incident-route"><code>{target}</code><ArrowRight size={14} /><code>{selected.logical_key}</code></div>
            <label htmlFor="incident-description">What broke</label>
            <textarea id="incident-description" value={incidentDescription} onChange={(event) => setIncidentDescription(event.target.value)} required autoFocus />
            <label htmlFor="incident-severity">Severity</label>
            <select id="incident-severity" value={incidentSeverity} onChange={(event) => setIncidentSeverity(event.target.value)}>
              <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
            </select>
            <div className="modal-actions">
              <button type="button" onClick={() => setIncidentOpen(false)}>Cancel</button>
              <button className="primary-button" type="submit" disabled={busy === "incident" || !incidentDescription.trim()}>
                {busy === "incident" ? <LoaderCircle className="spin" size={16} /> : <History size={16} />}
                Store in HydraDB
              </button>
            </div>
          </form>
        </div>
      )}
      <span className="sr-only" aria-live="polite">
        {report ? `${report.results.length} affected artifacts found.` : ""}
      </span>
    </div>
  );
}

function ImpactRow({ result, index, selected, onSelect }: { result: ImpactResult; index: number; selected: boolean; onSelect: () => void }) {
  return (
    <button className={`impact-row ${selected ? "selected" : ""}`} type="button" onClick={onSelect}>
      <span className="rank">{String(index + 1).padStart(2, "0")}</span>
      <span className="row-copy"><strong>{result.qualified_name || result.logical_key}</strong><small>{result.kind} · {result.hop_distance} {result.hop_distance === 1 ? "hop" : "hops"}</small></span>
      <span className={`risk-chip ${result.risk_score >= 70 ? "high" : result.risk_score >= 45 ? "medium" : "low"}`}>{result.risk_score.toFixed(2)}</span>
      <ChevronRight size={16} />
    </button>
  );
}

function shortSha(value: string) {
  if (!value) return "worktree";
  return value.startsWith("worktree-") ? value.slice(0, 18) : value.slice(0, 10);
}

function messageOf(caught: unknown) {
  return caught instanceof Error ? caught.message : "The operation failed. Check the server and try again.";
}
