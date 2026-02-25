import { useState } from 'react';
import type { AgentRunDetail, AgentRunStep } from '../../types';

interface AgentRunTimelineProps {
  runs: AgentRunDetail[];
}

const STATUS_COLOR: Record<string, string> = {
  completed: 'bg-green-100 text-green-700',
  running: 'bg-blue-100 text-blue-700',
  failed: 'bg-red-100 text-red-700',
};

const ACTION_COLOR: Record<string, string> = {
  click: 'bg-blue-100 text-blue-700',
  type: 'bg-purple-100 text-purple-700',
  navigate: 'bg-teal-100 text-teal-700',
  scroll: 'bg-gray-100 text-gray-600',
  done: 'bg-green-100 text-green-700',
};

function actionLabel(step: AgentRunStep): string {
  const t = step.actionType || 'unknown';
  if (step.actionValue) return `${t}: ${step.actionValue.slice(0, 40)}`;
  return t;
}

export default function AgentRunTimeline({ runs }: AgentRunTimelineProps) {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(
    runs.length > 0 ? runs[0].runId : null
  );
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  const activeRun = runs.find((r) => r.runId === selectedRunId) ?? null;

  if (runs.length === 0) {
    return (
      <div className="text-center py-10 text-gray-400 text-sm">
        No agent run data available.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      {/* Run selector (left) */}
      <div className="lg:col-span-1 space-y-2">
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Agent Runs
        </h4>
        {runs.map((run, idx) => (
          <button
            key={run.runId}
            onClick={() => {
              setSelectedRunId(run.runId);
              setExpandedStep(null);
            }}
            className={`w-full text-left rounded-lg border p-3 transition-all ${
              selectedRunId === run.runId
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono text-gray-400">
                #{idx + 1}
              </span>
              <span
                className={`text-xs px-1.5 py-0.5 rounded font-medium ${STATUS_COLOR[run.status] ?? 'bg-gray-100 text-gray-600'}`}
              >
                {run.status}
              </span>
            </div>
            <p className="text-xs text-gray-700 line-clamp-2 leading-snug">
              {run.goal}
            </p>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {Object.entries(run.personaTraits)
                .slice(0, 3)
                .map(([k, v]) => (
                  <span
                    key={k}
                    className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded"
                  >
                    {k}: {v}
                  </span>
                ))}
            </div>
            <p className="text-xs text-gray-400 mt-1">
              {run.steps.length} steps
            </p>
          </button>
        ))}
      </div>

      {/* Step timeline (right) */}
      <div className="lg:col-span-3">
        {activeRun ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3 mb-2">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Step-by-step Trace
              </h4>
              <span className="text-xs text-gray-400">{activeRun.goal}</span>
            </div>

            {activeRun.steps.map((step) => (
              <div
                key={step.step}
                className="border border-gray-200 rounded-xl bg-white overflow-hidden"
              >
                {/* Step header */}
                <button
                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors text-left"
                  onClick={() =>
                    setExpandedStep(
                      expandedStep === step.step ? null : step.step
                    )
                  }
                >
                  <span className="shrink-0 w-7 h-7 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center">
                    {step.step}
                  </span>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-medium ${ACTION_COLOR[step.actionType] ?? 'bg-gray-100 text-gray-600'}`}
                      >
                        {actionLabel(step)}
                      </span>
                      {step.tabTitle && (
                        <span className="text-xs text-gray-400 truncate max-w-[200px]">
                          {step.tabTitle}
                        </span>
                      )}
                    </div>
                    {step.reasoning && (
                      <p className="text-xs text-gray-500 mt-0.5 truncate">
                        {step.reasoning}
                      </p>
                    )}
                  </div>

                  <span className="text-gray-300 text-xs shrink-0">
                    {expandedStep === step.step ? '▲' : '▼'}
                  </span>
                </button>

                {/* Expanded content */}
                {expandedStep === step.step && (
                  <div className="border-t border-gray-100 grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
                    {/* Screenshot */}
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                        Screenshot
                      </p>
                      {step.screenshot ? (
                        <img
                          src={step.screenshot}
                          alt={`Step ${step.step}`}
                          className="w-full rounded-lg border border-gray-200"
                        />
                      ) : (
                        <div className="h-32 bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-center text-xs text-gray-400">
                          No screenshot
                        </div>
                      )}
                      {step.tabUrl && (
                        <p className="text-xs text-gray-400 mt-1 font-mono truncate">
                          {step.tabUrl}
                        </p>
                      )}
                    </div>

                    {/* Reasoning */}
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                        Agent Reasoning
                      </p>
                      <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                        {step.reasoning || 'No reasoning recorded.'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-40 text-sm text-gray-400">
            Select a run to view the timeline.
          </div>
        )}
      </div>
    </div>
  );
}
