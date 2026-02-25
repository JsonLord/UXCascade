import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import type { Experiment, CreateExperimentInput } from '../types'

export function useExperiments() {
  return useQuery({
    queryKey: ['experiments'],
    queryFn: () =>
      apiClient.get('/experiments').then(r =>
        r.data.map((item: any) => ({
          id: item.id,
          name: item.name,
          targetUrl: item.target_url,
          status: item.status,
          traits: item.traits ?? [],
          goals: item.goals ?? [],
          agentCount: item.agent_count ?? 0,
          createdAt: item.created_at,
          updatedAt: item.updated_at,
        })) as Experiment[]
      ),
  })
}

export function useExperiment(id: string) {
  return useQuery({
    queryKey: ['experiments', id],
    queryFn: () =>
      apiClient.get(`/experiments/${id}`).then(r => {
        const item = r.data
        return {
          id: item.id,
          name: item.name,
          targetUrl: item.target_url,
          status: item.status,
          traits: item.traits ?? [],
          goals: item.goals ?? [],
          agentCount: item.agent_count ?? 0,
          createdAt: item.created_at,
          updatedAt: item.updated_at,
        } as Experiment
      }),
    enabled: !!id,
  })
}

export function useCreateExperiment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (form: CreateExperimentInput) =>
      apiClient
        .post('/experiments', {
          name: form.name,
          target_url: form.targetUrl,
          traits: form.traits,
          goals: form.goals,
        })
        .then(r => {
          const item = r.data
          return {
            id: item.id,
            name: item.name,
            targetUrl: item.target_url,
            status: item.status,
            traits: item.traits ?? [],
            goals: item.goals ?? [],
            agentCount: item.agent_count ?? 0,
            createdAt: item.created_at,
            updatedAt: item.updated_at,
          } as Experiment
        }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['experiments'] }),
  })
}

export function useRunExperiment(experimentId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () =>
      apiClient.post(`/experiments/${experimentId}/run`).then(r => r.data),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ['experiments', experimentId] }),
  })
}
