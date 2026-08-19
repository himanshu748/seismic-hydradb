export type Health = {
  ok: boolean;
  product: string;
  version: string;
  backend: string;
  transport: string;
};

export type IngestSummary = {
  repo_id: string;
  snapshot_id: string;
  commit_sha: string;
  files: number;
  artifacts: number;
  packages: number;
  relationships: number;
  unresolved_imports: number;
  unresolved_calls: number;
  skipped_files: number;
  duration_ms: number;
  activated: boolean;
  warnings: string[];
};

export type RepositoryStatus = {
  repo_id: string;
  snapshot_id: string;
  commit_sha: string;
  status: string;
  artifact_count: number;
  relationship_count: number;
  unresolved_imports: number;
  unresolved_calls: number;
  skipped_files: number;
  evidence_complete: boolean;
  created_at: string;
};

export type EvidenceNode = {
  key: string;
  logical_key: string;
  kind: string;
  path: string;
  qualified_name: string;
};

export type EvidenceHop = {
  type: string;
  source: string;
  target: string;
  evidence_line: number;
  confidence: number;
};

export type ImpactResult = {
  target: string;
  artifact_key: string;
  logical_key: string;
  kind: string;
  path: string;
  qualified_name: string;
  hop_distance: number;
  risk_score: number;
  score_components: Record<string, number>;
  resolution_confidence: number;
  owner: string;
  owner_source: string;
  last_author: string;
  last_modified: string;
  incident_count: number;
  incident_pair_count: number;
  reason: string;
  nodes: EvidenceNode[];
  hops: EvidenceHop[];
};

export type ChangeGate = {
  policy: string;
  decision: "safe" | "review" | "block";
  headline: string;
  summary: string;
  max_risk_score: number;
  impacted_artifacts: number;
  required_tests: string[];
  verification_commands: string[];
  affected_entrypoints: string[];
  affected_owners: string[];
  reasons: string[];
};

export type ChangeReport = {
  repo_id: string;
  snapshot_id: string;
  targets: string[];
  diff_files?: string[];
  engine: string;
  gate: ChangeGate;
  results: ImpactResult[];
  unresolved_targets: string[];
  warnings: string[];
  evidence: {
    status: "supported" | "bounded-empty" | "incomplete";
    complete: boolean;
    fallback: boolean;
    reason: string;
    unresolved_imports: number;
    unresolved_calls: number;
    skipped_files: number;
  };
  receipt_id: string;
};
