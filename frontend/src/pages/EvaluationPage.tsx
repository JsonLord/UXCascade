import { useParams, Link } from 'react-router-dom';
import DiffReport from '../components/evaluation/DiffReport';
import { useFixDetail, useFixes, useRunEvaluation } from '../hooks/useFixes';
import { useIssue } from '../hooks/useIssues';

export default function EvaluationPage() {
  const { id = '', issueId = '' } = useParams();
  const { data: issue, isLoading: issueLoading } = useIssue(id, issueId);
  const { data: fixes } = useFixes(id);
  const runEvaluation = useRunEvaluation();

  // Latest fix for this issue
  const latestFix = fixes?.filter((f) => f.issueId === issueId).at(-1);
  const latestFixId = latestFix?.id ?? '';
  const { data: fixDetail } = useFixDetail(id, latestFixId);
  const evaluation = fixDetail?.evaluations?.at(-1);
  const fixForReport = fixDetail?.fix ?? latestFix;

  if (issueLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-400">
        Loading…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <Link
              to={`/experiments/${id}/issues/${issueId}/fix`}
              className="text-sm text-gray-400 hover:text-gray-600"
            >
              ← Fix
            </Link>
            <span className="text-gray-300">/</span>
            <Link
              to={`/experiments/${id}`}
              className="text-sm text-gray-400 hover:text-gray-600"
            >
              Analysis
            </Link>
          </div>
          <h1 className="text-lg font-bold text-gray-900 mt-2">Evaluate Fix</h1>
          {issue && (
            <p className="text-sm text-gray-400 mt-0.5 capitalize">
              {issue.type.replace(/_/g, ' ')} · {issue.element}
            </p>
          )}
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6 space-y-6">
        {latestFix && !evaluation && (
          <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-1">
                No evaluation yet
              </h3>
              <p className="text-sm text-gray-500">
                Run the Preview Agent to re-simulate the patched step and
                compare before/after behavior.
              </p>
            </div>
            {runEvaluation.isError && (
              <p className="text-sm text-red-600">
                {(runEvaluation.error as any)?.response?.data?.detail ??
                  'Evaluation failed.'}
              </p>
            )}
            <button
              onClick={() =>
                runEvaluation.mutate({ experimentId: id, fixId: latestFix.id })
              }
              disabled={runEvaluation.isPending}
              className="w-full bg-green-600 text-white text-sm font-medium py-2.5 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {runEvaluation.isPending
                ? 'Running evaluation…'
                : 'Run Evaluation'}
            </button>
          </div>
        )}

        {!latestFix && (
          <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
            <p className="text-gray-400 text-sm">
              No fix found for this issue.{' '}
              <Link
                to={`/experiments/${id}/issues/${issueId}/fix`}
                className="text-blue-600 hover:underline"
              >
                Go back to Fix
              </Link>
            </p>
          </div>
        )}

        {/* Diff report */}
        {evaluation && fixForReport && (
          <DiffReport evaluation={evaluation} fix={fixForReport} />
        )}

        {/* Navigation */}
        <div className="flex justify-between">
          <Link
            to={`/experiments/${id}/issues/${issueId}/fix`}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            ← Back to Fix
          </Link>
          <Link
            to={`/experiments/${id}`}
            className="text-sm text-blue-600 hover:underline"
          >
            Back to Analysis →
          </Link>
        </div>
      </div>
    </div>
  );
}
