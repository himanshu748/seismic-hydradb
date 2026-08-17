import { useMemo } from "react";
import type { ChangeReport, EvidenceNode } from "./types";

type GraphCanvasProps = {
  report: ChangeReport | null;
  selectedKey: string | null;
  onSelect: (key: string) => void;
  loading: boolean;
};

type PositionedNode = EvidenceNode & { x: number; y: number; depth: number };

export function GraphCanvas({ report, selectedKey, onSelect, loading }: GraphCanvasProps) {
  const graph = useMemo(() => layoutGraph(report), [report]);
  const activeKeys = new Set(
    report?.results.find((result) => result.artifact_key === selectedKey)?.nodes.map((node) => node.key) ??
      [],
  );

  if (!report || report.results.length === 0) {
    return (
      <div className={`graph-empty ${loading ? "is-loading" : ""}`}>
        <svg viewBox="0 0 680 360" aria-hidden="true">
          <g className="survey-lines">
            {[80, 160, 240, 320].map((y) => (
              <path key={y} d={`M20 ${y} C180 ${y - 28}, 420 ${y + 28}, 660 ${y}`} />
            ))}
          </g>
          <path className="empty-fault" d="M40 190h170l35-62 48 130 44-95 38 55h255" />
          <circle className="empty-origin" cx="245" cy="128" r="8" />
        </svg>
        <div className="empty-message">
          <strong>{loading ? "Tracing dependency paths" : "No blast radius loaded"}</strong>
          <span>
            {loading
              ? "HydraDB is walking incoming code relationships."
              : "Index a Git repository, enter a file or symbol and analyze the change."}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`graph-stage ${loading ? "is-loading" : ""}`}>
      <svg viewBox="0 0 960 540" role="img" aria-label="Code change blast radius graph">
        <defs>
          <marker id="edge-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
            <path d="M0 0l7 3.5L0 7z" />
          </marker>
          <marker
            id="edge-arrow-active"
            markerWidth="7"
            markerHeight="7"
            refX="6"
            refY="3.5"
            orient="auto"
          >
            <path d="M0 0l7 3.5L0 7z" />
          </marker>
        </defs>
        <g className="graph-grid">
          {Array.from({ length: 11 }, (_, index) => (
            <line key={`v${index}`} x1={index * 96} y1="0" x2={index * 96} y2="540" />
          ))}
          {Array.from({ length: 7 }, (_, index) => (
            <line key={`h${index}`} x1="0" y1={index * 90} x2="960" y2={index * 90} />
          ))}
        </g>
        <g className="graph-edges">
          {graph.edges.map((edge) => {
            const source = graph.nodes.get(edge.source);
            const target = graph.nodes.get(edge.target);
            if (!source || !target) return null;
            const active = activeKeys.has(edge.source) && activeKeys.has(edge.target);
            const d = `M${source.x + 66} ${source.y} C${source.x + 110} ${source.y}, ${target.x - 110} ${target.y}, ${target.x - 66} ${target.y}`;
            return (
              <g key={`${edge.source}:${edge.target}:${edge.type}`} className={active ? "active" : ""}>
                <path className="edge-shadow" d={d} />
                <path className="edge-line" d={d} markerEnd={`url(#edge-arrow${active ? "-active" : ""})`} />
                {active && <path className="edge-pulse" d={d} />}
                <text x={(source.x + target.x) / 2} y={(source.y + target.y) / 2 - 9}>
                  {edge.type}
                </text>
              </g>
            );
          })}
        </g>
        <g className="graph-nodes">
          {[...graph.nodes.values()].map((node) => {
            const isOrigin = node.depth === 0;
            const result = report.results.find((item) => item.artifact_key === node.key);
            const selected = selectedKey === node.key;
            const active = activeKeys.has(node.key);
            const label = node.qualified_name || shortPath(node.logical_key);
            return (
              <g
                key={node.key}
                className={`graph-node ${isOrigin ? "origin" : ""} ${active ? "active" : ""} ${selected ? "selected" : ""}`}
                transform={`translate(${node.x - 66} ${node.y - 34})`}
                role={result ? "button" : undefined}
                tabIndex={result ? 0 : undefined}
                onClick={() => result && onSelect(result.artifact_key)}
                onKeyDown={(event) => {
                  if (result && (event.key === "Enter" || event.key === " ")) {
                    event.preventDefault();
                    onSelect(result.artifact_key);
                  }
                }}
              >
                <rect width="132" height="68" rx="8" />
                <text className="node-kind" x="13" y="19">
                  {isOrigin ? "CHANGE" : node.kind.toUpperCase()}
                </text>
                <text className="node-label" x="13" y="42">
                  {truncate(label, 18)}
                </text>
                <text className="node-risk" x="13" y="58">
                  {result ? `risk ${result.risk_score.toFixed(2)}` : shortPath(node.path)}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
      <div className="graph-legend" aria-hidden="true">
        <span><i className="origin-dot" /> Changed target</span>
        <span><i className="impact-dot" /> Affected artifact</span>
        <span><i className="path-line" /> Selected evidence path</span>
      </div>
    </div>
  );
}

function layoutGraph(report: ChangeReport | null) {
  const nodes = new Map<string, PositionedNode>();
  const edges: { source: string; target: string; type: string }[] = [];
  if (!report) return { nodes, edges };

  const depthBuckets = new Map<number, EvidenceNode[]>();
  for (const result of report.results) {
    result.nodes.forEach((node, depth) => {
      if (!nodes.has(node.key)) {
        const bucket = depthBuckets.get(depth) ?? [];
        bucket.push(node);
        depthBuckets.set(depth, bucket);
        nodes.set(node.key, { ...node, x: 0, y: 0, depth });
      }
    });
    result.hops.forEach((hop, index) => {
      const source = result.nodes[index];
      const target = result.nodes[index + 1];
      if (source && target && !edges.some((edge) => edge.source === source.key && edge.target === target.key)) {
        edges.push({ source: source.key, target: target.key, type: hop.type });
      }
    });
  }

  const maxDepth = Math.max(...depthBuckets.keys(), 1);
  depthBuckets.forEach((bucket, depth) => {
    bucket.forEach((node, index) => {
      const current = nodes.get(node.key);
      if (!current) return;
      current.x = 96 + (depth / maxDepth) * 768;
      current.y = 88 + ((index + 1) / (bucket.length + 1)) * 360;
    });
  });
  return { nodes, edges };
}

function shortPath(value: string) {
  return value.split("/").at(-1)?.split("::").at(-1) ?? value;
}

function truncate(value: string, length: number) {
  return value.length > length ? `${value.slice(0, length - 1)}…` : value;
}
