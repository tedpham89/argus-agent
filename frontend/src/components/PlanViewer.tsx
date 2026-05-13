import type { PlanStep } from "../types";

interface Props {
  steps: PlanStep[];
}

const STATUS_CONFIG = {
  pending: { icon: "○", color: "text-gray-500", bg: "bg-gray-500/10" },
  running: { icon: "◌", color: "text-amber-400", bg: "bg-amber-400/10" },
  completed: { icon: "●", color: "text-emerald-400", bg: "bg-emerald-400/10" },
  failed: { icon: "✕", color: "text-red-400", bg: "bg-red-400/10" },
};

export default function PlanViewer({ steps }: Props) {
  if (steps.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-600 text-sm">
        <p>No active plan</p>
        <p className="text-xs text-gray-700 mt-1">Steps will appear here when the agent executes</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-1">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
        Execution Plan
      </h3>
      <div className="space-y-2">
        {steps.map((step) => {
          const cfg = STATUS_CONFIG[step.status];
          return (
            <div key={step.step_number} className={`rounded-lg p-3 ${cfg.bg} border border-gray-800`}>
              <div className="flex items-start gap-2">
                <span className={`${cfg.color} text-sm mt-0.5 ${step.status === "running" ? "animate-spin" : ""}`}>
                  {cfg.icon}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-200 truncate">
                      {step.description}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 font-mono">
                      {step.tool_name}
                    </span>
                    <span className={`text-xs ${cfg.color} capitalize`}>
                      {step.status}
                    </span>
                  </div>
                  {step.result && (
                    <pre className="mt-2 text-xs text-gray-400 bg-gray-900/50 rounded p-2 overflow-x-auto max-h-32 whitespace-pre-wrap">
                      {step.result}
                    </pre>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
