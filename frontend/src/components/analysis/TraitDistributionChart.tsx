import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { TraitDistribution } from '../../types';

interface TraitDistributionChartProps {
  distributions: TraitDistribution[];
  mode: 'trait-centric' | 'single-persona';
}

export default function TraitDistributionChart({
  distributions,
  mode,
}: TraitDistributionChartProps) {
  if (mode === 'trait-centric') {
    // Group by traitKey
    const grouped = distributions.reduce<Record<string, TraitDistribution[]>>(
      (acc, d) => {
        if (!acc[d.traitKey]) acc[d.traitKey] = [];
        acc[d.traitKey].push(d);
        return acc;
      },
      {}
    );

    return (
      <div className="space-y-6">
        {Object.entries(grouped).map(([traitKey, items]) => (
          <div key={traitKey}>
            <h4 className="text-sm font-medium text-gray-600 mb-2 capitalize">
              {traitKey.replace(/_/g, ' ')}
            </h4>
            <ResponsiveContainer width="100%" height={40 * items.length}>
              <BarChart
                layout="vertical"
                data={items.map((d) => ({
                  name: d.traitValue,
                  value: Math.round(d.successRate * 100),
                  issues: d.issues.length,
                }))}
                margin={{ left: 80, right: 40, top: 4, bottom: 4 }}
              >
                <XAxis type="number" domain={[0, 100]} hide />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 13 }}
                  width={80}
                />
                <Tooltip
                  formatter={(v) => [`${v}%`, 'Success rate']}
                  cursor={{ fill: '#f3f4f6' }}
                />
                <Bar dataKey="value" radius={4} maxBarSize={24}>
                  {items.map((d, i) => (
                    <Cell
                      key={i}
                      fill={
                        d.successRate >= 0.7
                          ? '#22c55e'
                          : d.successRate >= 0.4
                            ? '#eab308'
                            : '#ef4444'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ))}
      </div>
    );
  }

  // single-persona mode: aggregate by trait combo key, sort by worst success rate
  const personaMap = distributions.reduce<
    Record<string, { traits: string; successRate: number; issueCount: number }>
  >((acc, d) => {
    const key = `${d.traitKey}=${d.traitValue}`;
    if (!acc[key]) {
      acc[key] = {
        traits: `${d.traitKey.replace(/_/g, ' ')}: ${d.traitValue}`,
        successRate: d.successRate,
        issueCount: d.issues.length,
      };
    }
    return acc;
  }, {});

  const data = Object.values(personaMap).sort(
    (a, b) => a.successRate - b.successRate
  );

  return (
    <div>
      <ResponsiveContainer
        width="100%"
        height={Math.max(200, data.length * 36)}
      >
        <BarChart
          layout="vertical"
          data={data.map((p) => ({
            name: p.traits,
            value: Math.round(p.successRate * 100),
          }))}
          margin={{ left: 180, right: 40, top: 4, bottom: 4 }}
        >
          <XAxis type="number" domain={[0, 100]} hide />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 12 }}
            width={180}
          />
          <Tooltip
            formatter={(v) => [`${v}%`, 'Success rate']}
            cursor={{ fill: '#f3f4f6' }}
          />
          <Bar dataKey="value" fill="#6366f1" radius={4} maxBarSize={24} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
