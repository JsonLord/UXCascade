import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useIssue } from '../hooks/useIssues'
import { useFixes } from '../hooks/useFixes'
import RefinementChat from '../components/fix/RefinementChat'
import type { Fix, IssueWithSnapshot } from '../types'

const SEVERITY_LABEL = ['Cosmetic', 'Minor', 'Major', 'Serious', 'Catastrophic']

export default function FixPage() {
  const { id = '', issueId = '' } = useParams()
  const navigate = useNavigate()
  const { data: issue, isLoading } = useIssue(id, issueId)
  const { data: fixes } = useFixes(id)
  const [activeFix, setActiveFix] = useState<Fix | null>(null)

  const existingFix = fixes?.filter(f => f.issueId === issueId).at(-1) ?? null
  const displayFix = activeFix ?? existingFix

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-400">
        Loading…
      </div>
    )
  }

  if (!issue) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-400">
        Issue not found.
      </div>
    )
  }

  const snap = (issue as IssueWithSnapshot).snapshot

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <Link
              to={`/experiments/${id}`}
              className="text-sm text-gray-400 hover:text-gray-600"
            >
              ← Analysis
            </Link>
          </div>
          <h1 className="text-lg font-bold text-gray-900 mt-2">Fix Issue</h1>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Issue summary + chat */}
        <div className="space-y-5">
          {/* Issue summary */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-gray-800 capitalize">
                {issue.type.replace(/_/g, ' ')}
              </span>
              <span className="text-xs text-gray-400 font-mono">
                {issue.uptCodes.join(', ')}
              </span>
            </div>
            <div className="space-y-2 text-sm">
              <p className="text-gray-500">
                <span className="font-medium text-gray-600">Severity:</span>{' '}
                {issue.severity} — {SEVERITY_LABEL[issue.severity]}
              </p>
              <p className="text-gray-500">
                <span className="font-medium text-gray-600">Element:</span>{' '}
                <code className="text-xs bg-gray-50 px-1.5 py-0.5 rounded">{issue.element}</code>
              </p>
              <p className="text-gray-700">{issue.reason}</p>
              <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
                <p className="text-xs font-medium text-blue-600 mb-1">Suggested fix</p>
                <p className="text-sm text-blue-800">{issue.fix}</p>
              </div>
            </div>
          </div>

          {/* Chat */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Refinement Chat</h3>
            <RefinementChat
              key={existingFix?.id ?? 'new'}
              experimentId={id}
              issueId={issueId}
              snapshotStep={issue.step}
              onFixCreated={(fix) => setActiveFix(fix)}
              initialFix={existingFix ?? undefined}
            />
          </div>

          {/* Proceed button */}
          {displayFix && (
            <button
              onClick={() =>
                navigate(`/experiments/${id}/issues/${issueId}/evaluate`)
              }
              className="w-full bg-green-600 text-white text-sm font-medium py-2.5 rounded-lg hover:bg-green-700 transition-colors"
            >
              Proceed to Evaluation →
            </button>
          )}
        </div>

        {/* Right: Annotated screenshot */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Agent Screenshot — Step {issue.step}
          </h3>

          {snap?.screenshot ? (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <img
                src={snap.screenshot}
                alt={`Step ${snap.step} screenshot`}
                className="w-full block"
              />
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-center h-48">
              <p className="text-sm text-gray-400">No screenshot available.</p>
            </div>
          )}

          {snap?.reasoning && (
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Agent Reasoning
              </p>
              <p className="text-sm text-gray-600 leading-relaxed">{snap.reasoning}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
