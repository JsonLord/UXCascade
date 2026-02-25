import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import type { Issue, IssueWithSnapshot } from '../types'

export function useIssues(experimentId: string, goal?: string) {
  return useQuery({
    queryKey: ['issues', experimentId, goal],
    queryFn: () =>
      apiClient
        .get(`/experiments/${experimentId}/issues`, {
          params: goal ? { goal } : undefined,
        })
        .then(r =>
          r.data.map((item: any) => ({
            id: item.id,
            agentRunId: item.agent_run_id,
            step: item.step,
            type: item.type,
            element: item.element,
            reason: item.reason,
            fix: item.fix,
            uptCodes: item.upt_codes ?? [],
            uptExplanation: item.upt_explanation ?? '',
            severity: item.severity,
          })) as Issue[]
        ),
    enabled: !!experimentId,
  })
}

export function useIssue(experimentId: string, issueId: string) {
  return useQuery({
    queryKey: ['issues', experimentId, issueId],
    queryFn: () =>
      apiClient
        .get(`/experiments/${experimentId}/issues/${issueId}`)
        .then(r => {
          const item = r.data.issue ?? r.data
          const snap = r.data.snapshot ?? null
          return {
            id: item.id,
            agentRunId: item.agent_run_id,
            step: item.step,
            type: item.type,
            element: item.element,
            reason: item.reason,
            fix: item.fix,
            uptCodes: item.upt_codes ?? [],
            uptExplanation: item.upt_explanation ?? '',
            severity: item.severity,
            snapshot: snap
              ? {
                  step: snap.step,
                  screenshot: snap.screenshot ?? '',
                  reasoning: snap.reasoning ?? '',
                  rawHtml: snap.raw_html ?? '',
                }
              : null,
          } as IssueWithSnapshot
        }),
    enabled: !!experimentId && !!issueId,
  })
}
