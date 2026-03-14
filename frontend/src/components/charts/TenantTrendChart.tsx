import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { ChartWrapper } from './ChartWrapper';
import type { TenantData } from '@/types/energy';

interface Props {
  tenants: TenantData[];
}

export function TenantTrendChart({ tenants }: Props) {
  // Merge all tenant time series into unified data
  const dateMap = new Map<string, Record<string, number>>();
  tenants.forEach(t => {
    t.timeSeries.forEach(p => {
      const existing = dateMap.get(p.date) || {};
      existing[t.id] = p.consumption;
      dateMap.set(p.date, existing);
    });
  });

  const data = Array.from(dateMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .filter((_, i) => i % 3 === 0) // sample every 3 days for readability
    .map(([date, values]) => ({
      dateLabel: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      ...values,
    }));

  return (
    <ChartWrapper
      title="Tenant Consumption Trends"
      description="Individual tenant demand patterns over the analysis period (sampled every 3 days)."
    >
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(160 10% 90%)" />
          <XAxis dataKey="dateLabel" tick={{ fontSize: 11 }} stroke="hsl(220 10% 70%)" interval="preserveStartEnd" tickLine={false} />
          <YAxis tick={{ fontSize: 11 }} stroke="hsl(220 10% 70%)" tickLine={false} axisLine={false} unit=" kWh" width={60} />
          <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid hsl(160 10% 90%)', fontSize: '13px' }} formatter={(v: number) => [`${v} kWh`]} />
          <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} formatter={(v) => tenants.find(t => t.id === v)?.name || v} />
          {tenants.map(t => (
            <Line key={t.id} type="monotone" dataKey={t.id} stroke={t.color} strokeWidth={1.5} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
}
