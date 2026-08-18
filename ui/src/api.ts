import type { ChangeReport, Health, IngestSummary, RepositoryStatus } from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const payload = (await response.json()) as T & { detail?: string };
  if (!response.ok) {
    throw new Error(payload.detail ?? `Request failed with status ${response.status}`);
  }
  return payload;
}

export const api = {
  health: () => request<Health>("/api/health"),
  status: (repoId: string) =>
    request<RepositoryStatus>(`/api/repositories/${encodeURIComponent(repoId)}`),
  index: (repoPath: string, repoId: string) =>
    request<IngestSummary>("/api/index", {
      method: "POST",
      body: JSON.stringify({ repo_path: repoPath, repo_id: repoId || null }),
    }),
  analyze: (repoId: string, target: string, maxHops: number) =>
    request<ChangeReport>("/api/analyze", {
      method: "POST",
      body: JSON.stringify({ repo_id: repoId, targets: [target], max_hops: maxHops }),
    }),
  analyzeDiff: (repoId: string, diff: string, maxHops: number) =>
    request<ChangeReport>("/api/analyze-diff", {
      method: "POST",
      body: JSON.stringify({ repo_id: repoId, diff, max_hops: maxHops }),
    }),
  recordIncident: (
    repoId: string,
    trigger: string,
    impacted: string,
    description: string,
    severity: string,
  ) =>
    request<{ incident_id: string }>("/api/incidents", {
      method: "POST",
      body: JSON.stringify({
        repo_id: repoId,
        trigger,
        impacted: [impacted],
        description,
        severity,
        source: "dashboard",
      }),
    }),
};
