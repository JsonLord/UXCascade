import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import type { Fix, CreateFixInput, EvaluationResult, HtmlPatch } from '../types'

export function useFixes(experimentId: string) {
  return useQuery({
    queryKey: ['fixes', experimentId],
    queryFn: () =>
      apiClient.get(`/experiments/${experimentId}/fixes`).then(r =>
        r.data.map((item: any) => ({
          id: item.id,
          experimentId: item.experiment_id,
          issueId: item.issue_id,
          instruction: item.instruction,
          status: item.status,
          notes: item.notes ?? '',
          createdAt: item.created_at,
          patches: [],
        })) as Fix[]
      ),
    enabled: !!experimentId,
  })
}

export function useCreateFix() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateFixInput) =>
      apiClient
        .post(`/experiments/${input.experimentId}/fixes`, {
          issue_id: input.issueId,
          instruction: input.instruction,
          status: 'ok',
          notes: '',
          patches: [],
        })
        .then(r => {
          const item = r.data
          return {
            id: item.id,
            experimentId: item.experiment_id,
            issueId: item.issue_id,
            instruction: item.instruction,
            status: item.status,
            notes: item.notes ?? '',
            createdAt: item.created_at,
            patches: [],
          } as Fix
        }),
    onSuccess: (fix) => {
      qc.invalidateQueries({ queryKey: ['fixes', fix.experimentId] })
    },
  })
}

export function useFixDetail(experimentId: string, fixId: string) {
  return useQuery({
    queryKey: ['fixes', experimentId, fixId],
    queryFn: () =>
      apiClient
        .get(`/experiments/${experimentId}/fixes/${fixId}`)
        .then(r => {
          const fix = r.data.fix
          const patches = (r.data.patches ?? []).map((p: any) => ({
            selector: p.selector,
            action: p.action,
            value: p.value ?? null,
            name: p.name ?? null,
            rationale: p.rationale,
          })) as HtmlPatch[]

          const evaluations = (r.data.evaluations ?? []).map((e: any) => ({
            fixId: e.fix_id,
            agentRunId: e.agent_run_id,
            step: e.step,
            actionChanged: e.action_changed,
            issueResolved: e.issue_resolved,
            summary: e.summary,
            beforeAction: e.before_action,
            afterAction: e.after_action,
            createdAt: e.created_at,
          })) as EvaluationResult[]

          return {
            fix: {
              id: fix.id,
              experimentId: fix.experiment_id,
              issueId: fix.issue_id,
              instruction: fix.instruction,
              status: fix.status,
              notes: fix.notes ?? '',
              createdAt: fix.created_at,
              patches,
            } as Fix,
            evaluations,
          }
        }),
    enabled: !!experimentId && !!fixId,
  })
}

export function useRunEvaluation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      experimentId,
      fixId,
    }: {
      experimentId: string
      fixId: string
    }) =>
      apiClient
        .post(`/experiments/${experimentId}/fixes/${fixId}/evaluate`)
        .then(r => {
          const item = r.data
          return {
            fixId: item.fix_id,
            agentRunId: item.agent_run_id,
            step: item.step,
            actionChanged: item.action_changed,
            issueResolved: item.issue_resolved,
            summary: item.summary,
            beforeAction: item.before_action,
            afterAction: item.after_action,
            createdAt: item.created_at,
          } as EvaluationResult
        }),
    onSuccess: (_result, { experimentId, fixId }) => {
      qc.invalidateQueries({ queryKey: ['fixes', experimentId, fixId] })
    },
  })
}
