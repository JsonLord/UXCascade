import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import type { AgentRunDetail, JourneyData } from '../types'

export function useJourneys(experimentId: string) {
  return useQuery({
    queryKey: ['journeys', experimentId],
    queryFn: () =>
      apiClient
        .get(`/experiments/${experimentId}/journeys`)
        .then(r => r.data as JourneyData),
    enabled: !!experimentId,
  })
}

export function useAgentRunSteps(experimentId: string) {
  return useQuery({
    queryKey: ['agent-run-steps', experimentId],
    queryFn: () =>
      apiClient
        .get(`/experiments/${experimentId}/agent-run-steps`)
        .then(r =>
          (r.data as Record<string, unknown>[]).map(item => ({
            runId: item['run_id'] as string,
            goal: item['goal'] as string,
            personaTraits: (item['persona_traits'] ?? {}) as Record<string, string>,
            status: item['status'] as string,
            steps: ((item['steps'] as Record<string, unknown>[]) ?? []).map(s => ({
              step: s['step'] as number,
              screenshot: s['screenshot'] as string,
              reasoning: s['reasoning'] as string,
              actionType: s['action_type'] as string,
              actionValue: s['action_value'] as string | null,
              tabUrl: s['tab_url'] as string,
              tabTitle: s['tab_title'] as string,
            })),
          })) as AgentRunDetail[]
        ),
    enabled: !!experimentId,
  })
}
