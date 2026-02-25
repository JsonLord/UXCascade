import type { GoalSummary } from '../../types'

interface GoalSummaryListProps {
  goals: GoalSummary[]
  selectedGoal?: string
  onSelectGoal: (goal: string) => void
}

export default function GoalSummaryList({
  goals,
  selectedGoal,
  onSelectGoal,
}: GoalSummaryListProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-200">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="text-left px-4 py-3 font-medium text-gray-600">Goal</th>
            <th className="text-right px-4 py-3 font-medium text-gray-600">Agents</th>
            <th className="text-right px-4 py-3 font-medium text-gray-600">Issues</th>
            <th className="text-right px-4 py-3 font-medium text-gray-600">Success</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {goals.map((g) => {
            const pct = Math.round(g.successRate * 100)
            const isSelected = g.goal === selectedGoal
            return (
              <tr
                key={g.goal}
                onClick={() => onSelectGoal(g.goal)}
                className={`cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-blue-50'
                    : 'hover:bg-gray-50'
                }`}
              >
                <td className="px-4 py-3 text-gray-800 max-w-xs">
                  <p className="truncate">{g.goal}</p>
                </td>
                <td className="px-4 py-3 text-right text-gray-500">{g.agentCount}</td>
                <td className="px-4 py-3 text-right">
                  <span className={g.issueCount > 0 ? 'text-red-600 font-medium' : 'text-gray-500'}>
                    {g.issueCount}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span
                    className={`font-medium ${
                      pct >= 70
                        ? 'text-green-600'
                        : pct >= 40
                          ? 'text-yellow-600'
                          : 'text-red-600'
                    }`}
                  >
                    {pct}%
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
