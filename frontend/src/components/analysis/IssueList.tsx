import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { Issue } from '../../types';

interface IssueListProps {
  issues: Issue[];
  experimentId: string;
  selectedIssueId?: string;
  onSelectIssue: (issue: Issue) => void;
}

const SEVERITY_COLOR = [
  'bg-gray-100 text-gray-500', // S0 Cosmetic
  'bg-blue-100 text-blue-600', // S1 Minor
  'bg-yellow-100 text-yellow-700', // S2 Major
  'bg-orange-100 text-orange-700', // S3 Serious
  'bg-red-100 text-red-700', // S4 Catastrophic
];
const PAGE_SIZE = 5;

export default function IssueList({
  issues,
  experimentId,
  selectedIssueId,
  onSelectIssue,
}: IssueListProps) {
  const [activeSeverities, setActiveSeverities] = useState<Set<number>>(
    new Set([0, 1, 2, 3, 4])
  );
  const [page, setPage] = useState(0);

  function toggleSeverity(s: number) {
    setActiveSeverities((prev) => {
      const next = new Set(prev);
      if (next.has(s)) {
        if (next.size > 1) next.delete(s); // keep at least one selected
      } else {
        next.add(s);
      }
      return next;
    });
    setPage(0);
  }

  const sorted = [...issues].sort((a, b) => b.severity - a.severity);
  const filtered = sorted.filter((i) => activeSeverities.has(i.severity));
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paged = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="space-y-3">
      {/* Severity filter */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="text-xs text-gray-400 mr-1">Filter:</span>
        {[0, 1, 2, 3, 4].map((s) => (
          <button
            key={s}
            onClick={() => toggleSeverity(s)}
            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold transition-opacity ${
              SEVERITY_COLOR[s]
            } ${activeSeverities.has(s) ? 'opacity-100' : 'opacity-30'}`}
          >
            S{s}
          </button>
        ))}
        <span className="ml-auto text-xs text-gray-400">
          {filtered.length} issues
        </span>
      </div>

      {/* Issue rows */}
      {paged.length === 0 ? (
        <div className="text-center py-8 text-gray-400 text-sm">
          No issues found.
        </div>
      ) : (
        <div className="space-y-2">
          {paged.map((issue) => (
            <div
              key={issue.id}
              onClick={() => onSelectIssue(issue)}
              className={`border rounded-xl p-4 cursor-pointer transition-all ${
                selectedIssueId === issue.id
                  ? 'border-blue-300 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="flex items-start gap-3">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold shrink-0 ${SEVERITY_COLOR[issue.severity] ?? SEVERITY_COLOR[0]}`}
                >
                  S{issue.severity}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 font-mono">
                      {issue.uptCodes.join(', ')}
                    </span>
                    <span className="text-sm font-medium text-gray-800 truncate">
                      {issue.type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-0.5 line-clamp-2">
                    {issue.reason}
                  </p>
                  <p className="text-xs text-gray-400 mt-1 font-mono">
                    {issue.element}
                  </p>
                </div>
                <Link
                  to={`/experiments/${experimentId}/issues/${issue.id}/fix`}
                  onClick={(e) => e.stopPropagation()}
                  className="shrink-0 text-xs text-blue-600 hover:underline"
                >
                  Fix →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-1 pt-1">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-2 py-1 text-xs rounded border border-gray-200 text-gray-500 disabled:opacity-30 hover:bg-gray-50"
          >
            ←
          </button>
          {Array.from({ length: totalPages }, (_, i) => (
            <button
              key={i}
              onClick={() => setPage(i)}
              className={`w-7 h-7 text-xs rounded border transition-colors ${
                i === page
                  ? 'border-blue-400 bg-blue-50 text-blue-600 font-medium'
                  : 'border-gray-200 text-gray-500 hover:bg-gray-50'
              }`}
            >
              {i + 1}
            </button>
          ))}
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page === totalPages - 1}
            className="px-2 py-1 text-xs rounded border border-gray-200 text-gray-500 disabled:opacity-30 hover:bg-gray-50"
          >
            →
          </button>
        </div>
      )}
    </div>
  );
}
