/**
 * Area chart: building consumption vs PV generation over time (daily from API).
 */
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { ChartWrapper } from './ChartWrapper';
import type { TimeSeriesPoint } from '@/types/energy';

interface Props {
  data: TimeSeriesPoint[];
}

export function BuildingVsPvChart({ data }: Props) {
  const formatted = data.map(d => ({
    ...d,
    dateLabel: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  }));

  return (
    <ChartWrapper
      title="Building Consumption vs PV Generation"
      description="Daily comparison of total building electricity demand against photovoltaic output."
    >
      <ResponsiveContainer width="100%" height={320}>
        <AreaChart data={formatted} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="gradConsumption" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3E8F87" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#3E8F87" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradPv" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#F2B544" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#F2B544" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(160 10% 90%)" />
          <XAxis dataKey="dateLabel" tick={{ fontSize: 11 }} stroke="hsl(220 10% 70%)" interval="preserveStartEnd" tickLine={false} />
          <YAxis tick={{ fontSize: 11 }} stroke="hsl(220 10% 70%)" tickLine={false} axisLine={false} unit=" kWh" width={65} />
          <Tooltip
            contentStyle={{ borderRadius: '12px', border: '1px solid hsl(160 10% 90%)', fontSize: '13px' }}
            formatter={(value: number, name: string) => [`${value} kWh`, name === 'buildingConsumption' ? 'Building' : 'PV']}
            labelFormatter={(l) => l}
          />
          <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} formatter={(v) => v === 'buildingConsumption' ? 'Building Consumption' : 'PV Generation'} />
          <Area type="monotone" dataKey="buildingConsumption" stroke="#3E8F87" fill="url(#gradConsumption)" strokeWidth={2} dot={false} />
          <Area type="monotone" dataKey="pvGeneration" stroke="#F2B544" fill="url(#gradPv)" strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
}
