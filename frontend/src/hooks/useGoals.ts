import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import type { GoalSummary, TraitDistribution } from '../types'

export function useGoalSummaries(experimentId: string) {
  return useQuery({
    queryKey: ['goals', experimentId],
    queryFn: () =>
      apiClient
        .get(`/experiments/${experimentId}/goals`)
        .then(r =>
          r.data.map((item: any) => ({
            experimentId,
            goal: item.goal,
            agentCount: item.agent_count,
            successCount: item.success_count,
            successRate: item.success_rate,
            issueCount: item.issue_count,
            traitDistributions: [],
          })) as GoalSummary[]
        ),
    enabled: !!experimentId,
  })
}

export function useTraitDistributions(experimentId: string, goal: string) {
  return useQuery({
    queryKey: ['goals', experimentId, goal, 'traits'],
    queryFn: () =>
      apiClient
        .get(
          `/experiments/${experimentId}/goals/${encodeURIComponent(goal)}/traits`
        )
        .then(r =>
          r.data.map((item: any) => ({
            traitKey: item.trait_key,
            traitValue: item.trait_value,
            agentCount: item.agent_count,
            successRate: item.success_rate,
            issues: (item.issues ?? []).map((issue: any) => ({
              id: issue.id,
              agentRunId: issue.agent_run_id,
              step: issue.step,
              type: issue.type,
              element: issue.element,
              reason: issue.reason,
              fix: issue.fix,
              uptCodes: issue.upt_codes ?? [],
              uptExplanation: issue.upt_explanation ?? '',
              severity: issue.severity,
            })),
          })) as TraitDistribution[]
        ),
    enabled: !!goal,
  })
}
