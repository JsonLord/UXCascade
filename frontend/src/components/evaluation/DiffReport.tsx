import type { EvaluationResult, Fix } from '../../types';

interface DiffReportProps {
  evaluation: EvaluationResult;
  fix: Fix;
}

export default function DiffReport({ evaluation, fix }: DiffReportProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-5">
      <h3 className="text-sm font-semibold text-gray-700">Difference Report</h3>

      {/* Before / After actions */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs font-medium text-gray-500 mb-2">
            Original action
          </p>
          <code className="text-xs text-gray-700">
            {evaluation.beforeAction.type}
            {evaluation.beforeAction.selector
              ? ` ${evaluation.beforeAction.selector}`
              : ''}
          </code>
        </div>
        <div className="bg-blue-50 rounded-lg p-3">
          <p className="text-xs font-medium text-blue-600 mb-2">
            Updated action
          </p>
          <code className="text-xs text-gray-700">
            {evaluation.afterAction.type}
            {evaluation.afterAction.selector
              ? ` ${evaluation.afterAction.selector}`
              : ''}
          </code>
        </div>
      </div>

      {/* Outcome indicators */}
      <div className="space-y-2">
        <ResultRow
          ok={evaluation.actionChanged}
          label="Action changed"
          description={
            evaluation.actionChanged
              ? 'The agent took a different action after the fix.'
              : 'The agent took the same action as before.'
          }
        />
        <ResultRow
          ok={evaluation.issueResolved}
          label="Issue resolved (estimated)"
          description={
            evaluation.issueResolved === null
              ? 'Could not determine whether the issue was resolved.'
              : evaluation.issueResolved
                ? 'The issue appears to have been resolved.'
                : 'The issue may still be present.'
          }
        />
      </div>

      {/* Summary */}
      <div className="bg-gray-50 rounded-lg p-4">
        <p className="text-xs font-medium text-gray-500 mb-1">Summary</p>
        <p className="text-sm text-gray-700">{evaluation.summary}</p>
      </div>

      {/* Applied patches */}
      {fix.patches.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">
            Applied patches ({fix.patches.length})
          </p>
          <div className="space-y-1">
            {fix.patches.map((p, i) => (
              <div
                key={i}
                className="flex items-start gap-2 text-xs text-gray-600"
              >
                <code className="bg-gray-100 px-1.5 py-0.5 rounded text-gray-700 shrink-0">
                  {p.action}
                </code>
                <code className="text-gray-500">{p.selector}</code>
                <span className="text-gray-400 ml-auto shrink-0">
                  {p.rationale}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ResultRow({
  ok,
  label,
  description,
}: {
  ok: boolean | null;
  label: string;
  description: string;
}) {
  const icon = ok === true ? '✅' : ok === false ? '❌' : '❓';
  return (
    <div className="flex items-start gap-2">
      <span className="text-base leading-none mt-0.5">{icon}</span>
      <div>
        <p className="text-sm font-medium text-gray-700">{label}</p>
        <p className="text-xs text-gray-500 mt-0.5">{description}</p>
      </div>
    </div>
  );
}
