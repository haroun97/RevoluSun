import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { ChartWrapper } from './ChartWrapper';
import type { TimeSeriesPoint } from '@/types/energy';

interface Props {
  data: TimeSeriesPoint[];
}

export function PvUsageChart({ data }: Props) {
  const formatted = data.map(d => ({
    dateLabel: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    selfConsumed: d.selfConsumed,
    surplus: d.surplus,
  }));

  return (
    <ChartWrapper
      title="PV Self-Consumption vs Surplus"
      description="How much solar energy is consumed on-site versus exported to the grid."
    >
      <ResponsiveContainer width="100%" height={320}>
        <AreaChart data={formatted} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="gradSelf" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#7ED3C1" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#7ED3C1" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradSurplus" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#F2B544" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#F2B544" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(160 10% 90%)" />
          <XAxis dataKey="dateLabel" tick={{ fontSize: 11 }} stroke="hsl(220 10% 70%)" interval="preserveStartEnd" tickLine={false} />
          <YAxis tick={{ fontSize: 11 }} stroke="hsl(220 10% 70%)" tickLine={false} axisLine={false} unit=" kWh" width={65} />
          <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid hsl(160 10% 90%)', fontSize: '13px' }} formatter={(v: number, n: string) => [`${v} kWh`, n === 'selfConsumed' ? 'Self-Consumed' : 'Surplus']} />
          <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} formatter={(v) => v === 'selfConsumed' ? 'Self-Consumed' : 'Surplus to Grid'} />
          <Area type="monotone" dataKey="selfConsumed" stackId="1" stroke="#7ED3C1" fill="url(#gradSelf)" strokeWidth={2} dot={false} />
          <Area type="monotone" dataKey="surplus" stackId="1" stroke="#F2B544" fill="url(#gradSurplus)" strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
}
