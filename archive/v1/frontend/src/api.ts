export interface JobRequest {
  cities: string[];
  dimensions: string[];
  depth: "standard" | "deep";
}

export interface JobStatus {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  message: string;
}

export interface DimensionScore {
  score: number;
  rationale: string;
}

export interface Issue {
  name: string;
  why_it_matters: string;
}

export interface CityResult {
  city_name: string;
  overall_health: number;
  category_scores: Record<string, DimensionScore>;
  top_issues: Issue[];
  citations: string[];
  reddit_posts: string[];
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatResponse {
  message: ChatMessage;
  job_request?: JobRequest;
}

export async function startJob(req: JobRequest): Promise<string> {
  const res = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error("Failed to start job");
  const data = await res.json();
  return data.job_id;
}

export async function getJobResults(jobId: string): Promise<{ cities: CityResult[] }> {
  const res = await fetch(`/api/jobs/${jobId}/results`);
  if (!res.ok) throw new Error("Failed to get results");
  return res.json();
}

export async function sendChat(messages: ChatMessage[], jobId?: string): Promise<ChatResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, job_id: jobId }),
  });
  if (!res.ok) throw new Error("Failed to send message");
  return res.json();
}
