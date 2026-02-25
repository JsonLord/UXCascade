import type { JourneyData } from '../../types'

interface SankeyDiagramProps {
  data: JourneyData | undefined
  onNodeClick: (nodeId: string) => void
}

// Lightweight placeholder — full D3 Sankey implementation is a follow-up task
export default function SankeyDiagram({ data, onNodeClick }: SankeyDiagramProps) {
  if (!data || data.links.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-sm text-gray-400">
        No navigation data available.
      </div>
    )
  }

  const nodeLabel = Object.fromEntries(data.nodes.map(n => [n.id, n.label]))

  return (
    <div className="space-y-2">
      <div className="overflow-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="text-left text-xs text-gray-500 border-b border-gray-200">
              <th className="py-2 pr-4 font-medium">From</th>
              <th className="py-2 pr-4 font-medium">To</th>
              <th className="py-2 font-medium text-right">Transitions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.links
              .slice()
              .sort((a, b) => b.value - a.value)
              .map((link) => {
                const key = `${link.source}→${link.target}`
                return (
                  <tr
                    key={key}
                    onClick={() => onNodeClick(key)}
                    className="hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="py-2 pr-4 text-gray-700 max-w-xs truncate">
                      {nodeLabel[link.source] ?? link.source}
                    </td>
                    <td className="py-2 pr-4 text-gray-700 max-w-xs truncate">
                      {nodeLabel[link.target] ?? link.target}
                    </td>
                    <td className="py-2 text-right">
                      <span className="inline-flex items-center justify-center w-8 h-5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                        {link.value}
                      </span>
                    </td>
                  </tr>
                )
              })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-gray-400 pt-2">
        Full Sankey diagram visualization coming soon.
      </p>
    </div>
  )
}
