import { useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import type { Experiment, SimulationEvent } from '../types'

export function useRunSimulation(experimentId: string) {
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: () =>
      apiClient.post(`/experiments/${experimentId}/run`).then(r => r.data),
  })

  useEffect(() => {
    if (!experimentId) return

    const wsUrl = `${import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000'}/ws/experiments/${experimentId}`
    const ws = new WebSocket(wsUrl)

    ws.onmessage = (e) => {
      const event: SimulationEvent = JSON.parse(e.data)
      qc.setQueryData(['experiments', experimentId], (old: Experiment | undefined) =>
        old ? { ...old, status: event.status } : old
      )
      if (event.status === 'completed') {
        qc.invalidateQueries({ queryKey: ['goals', experimentId] })
      }
    }

    return () => ws.close()
  }, [experimentId, qc])

  return mutation
}
