import type { AgentResponse } from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "";

export async function runAgent(
  message: string,
  threadId?: string
): Promise<AgentResponse> {
  const res = await fetch(`${BASE}/agent/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, thread_id: threadId }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Agent error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function approveAction(
  threadId: string,
  approved: boolean
): Promise<AgentResponse> {
  const res = await fetch(`${BASE}/agent/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, approved }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Approval error ${res.status}: ${text}`);
  }
  return res.json();
}
