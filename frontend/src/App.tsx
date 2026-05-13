import { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import PlanViewer from "./components/PlanViewer";
import ConfirmModal from "./components/ConfirmModal";
import { runAgent, approveAction } from "./api";
import type { ChatMessage, PlanStep } from "./types";

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [planSteps, setPlanSteps] = useState<PlanStep[]>([]);
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | undefined>();

  // Approval state
  const [pendingApproval, setPendingApproval] = useState<string | null>(null);
  const [approvalLoading, setApprovalLoading] = useState(false);

  const handleSend = async (message: string) => {
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setPlanSteps([]);
    setLoading(true);

    try {
      const res = await runAgent(message, threadId);
      setThreadId(res.thread_id);
      setPlanSteps(res.plan);

      if (res.status === "needs_approval") {
        setPendingApproval(res.final_response ?? "This action requires approval.");
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: res.final_response ?? "Done.",
            plan: res.plan,
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Something went wrong"}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (approved: boolean) => {
    if (!threadId) return;
    setApprovalLoading(true);
    try {
      const res = await approveAction(threadId, approved);
      setPendingApproval(null);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: approved
            ? res.final_response ?? "Action approved and executed."
            : "Action rejected.",
        },
      ]);
      if (res.plan) setPlanSteps(res.plan);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Approval error: ${err instanceof Error ? err.message : "Unknown error"}`,
        },
      ]);
      setPendingApproval(null);
    } finally {
      setApprovalLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.64 0 8.577 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.64 0-8.577-3.007-9.963-7.178z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-gray-100 tracking-tight">Argus Agent</h1>
            <p className="text-xs text-gray-500">Financial Operations Intelligence</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 text-xs text-gray-500">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Online
          </span>
        </div>
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat panel */}
        <div className="flex-1 flex flex-col min-w-0">
          <ChatPanel messages={messages} onSend={handleSend} loading={loading} />
        </div>

        {/* Plan sidebar */}
        <div className="w-80 border-l border-gray-800 overflow-y-auto hidden lg:block">
          <PlanViewer steps={planSteps} />
        </div>
      </div>

      {/* Confirm modal */}
      {pendingApproval && threadId && (
        <ConfirmModal
          threadId={threadId}
          action={pendingApproval}
          onApprove={() => handleApproval(true)}
          onReject={() => handleApproval(false)}
          loading={approvalLoading}
        />
      )}
    </div>
  );
}
