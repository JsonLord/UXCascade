import { useState } from 'react'
import { useCreateFix } from '../../hooks/useFixes'
import type { Fix } from '../../types'

interface RefinementChatProps {
  experimentId: string
  issueId: string
  snapshotStep: number
  onFixCreated: (fix: Fix) => void
  initialFix?: Fix
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function RefinementChat({
  experimentId,
  issueId,
  snapshotStep,
  onFixCreated,
  initialFix,
}: RefinementChatProps) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (!initialFix?.instruction) return []
    const summary =
      initialFix.status === 'ok'
        ? initialFix.notes
        : initialFix.status === 'ambiguous'
          ? `Ambiguous: ${initialFix.notes}`
          : `Could not apply: ${initialFix.notes}`
    return [
      { role: 'user', content: initialFix.instruction },
      { role: 'assistant', content: summary },
    ]
  })
  const createFix = useCreateFix()

  async function handleSend() {
    const instruction = input.trim()
    if (!instruction) return

    setMessages(prev => [...prev, { role: 'user', content: instruction }])
    setInput('')

    try {
      const fix = await createFix.mutateAsync({
        experimentId,
        issueId,
        instruction,
        snapshotStep,
      })

      const summary =
        fix.status === 'ok'
          ? `Applied ${fix.patches.length} patch(es). ${fix.notes}`
          : fix.status === 'ambiguous'
            ? `Ambiguous: ${fix.notes}`
            : `Could not apply: ${fix.notes}`

      setMessages(prev => [...prev, { role: 'assistant', content: summary }])
      onFixCreated(fix)
    } catch (err: any) {
      const detail: string =
        err?.response?.data?.detail ?? 'Failed to generate patch. Please try again.'
      setMessages(prev => [...prev, { role: 'assistant', content: detail }])
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Message history */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-3 min-h-[160px]">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400 text-center pt-6">
            Describe the change you want to make…
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] px-3 py-2 rounded-xl text-sm ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {createFix.isPending && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-400 text-sm px-3 py-2 rounded-xl">
              Generating patch…
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder='e.g. "Move the cart button to a more prominent position"'
          rows={2}
          className="flex-1 text-sm border border-gray-200 rounded-lg px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={createFix.isPending}
        />
        <button
          onClick={handleSend}
          disabled={createFix.isPending || !input.trim()}
          className="self-end bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  )
}
