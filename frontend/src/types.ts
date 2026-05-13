export interface PlanStep {
  step_number: number;
  description: string;
  tool_name: string;
  tool_args: Record<string, unknown>;
  status: "pending" | "running" | "completed" | "failed";
  result: string | null;
}

export interface AgentResponse {
  thread_id: string;
  plan: PlanStep[];
  final_response: string | null;
  status: "completed" | "needs_approval" | "error";
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  plan?: PlanStep[];
}
