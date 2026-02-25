import { Link } from 'react-router-dom';
import type { Issue } from '../../types';

interface IssueDetailProps {
  issue: Issue;
  experimentId: string;
}

const SEVERITY_LABEL = [
  'Cosmetic',
  'Minor',
  'Major',
  'Serious',
  'Catastrophic',
];

export default function IssueDetail({ issue, experimentId }: IssueDetailProps) {
  return (
    <div className="space-y-3">
      <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono text-gray-400">
              {issue.uptCodes.join(', ')}
            </span>
            <span className="text-sm font-semibold text-gray-800 capitalize">
              {issue.type.replace(/_/g, ' ')}
            </span>
          </div>
          <p className="text-xs text-gray-500">
            Severity {issue.severity} — {SEVERITY_LABEL[issue.severity] ?? ''}
          </p>
        </div>

        <div className="space-y-3 text-sm">
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
              Element
            </p>
            <code className="text-xs bg-gray-50 px-2 py-1 rounded text-gray-700">
              {issue.element}
            </code>
          </div>

          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
              Reason
            </p>
            <p className="text-gray-700">{issue.reason}</p>
          </div>

          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
              Suggested Fix
            </p>
            <p className="text-gray-700">{issue.fix}</p>
          </div>

          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
              UPT Explanation
            </p>
            <p className="text-gray-600 text-xs">{issue.uptExplanation}</p>
          </div>
        </div>
      </div>

      <Link
        to={`/experiments/${experimentId}/issues/${issue.id}/fix`}
        className="flex items-center justify-center gap-2 w-full py-2.5 border border-gray-300 hover:border-gray-400 text-gray-600 hover:text-gray-800 text-sm font-medium rounded-lg transition-colors bg-white"
      >
        Fix This Issue →
      </Link>
    </div>
  );
}
