import { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { ChartWrapper } from './ChartWrapper';
import type { TenantData, TenantComparisonView } from '@/types/energy';

interface Props {
  tenants: TenantData[];
}

const views: { value: TenantComparisonView; label: string }[] = [
  { value: 'total', label: 'Total (kWh)' },
  { value: 'average', label: 'Avg Daily' },
  { value: 'activeDays', label: 'Active Days' },
];

export function TenantComparisonChart({ tenants }: Props) {
  const [view, setView] = useState<TenantComparisonView>('total');

  const data = tenants.map(t => ({
    name: `${t.unit} · ${t.name}`,
    value: view === 'total' ? t.totalConsumption : view === 'average' ? t.avgDailyConsumption : t.activeDays,
    fill: t.color,
  }));

  const unit = view === 'total' ? ' kWh' : view === 'average' ? ' kWh/d' : ' days';

  return (
    <ChartWrapper
      title="Tenant Consumption Comparison"
      description="Compare tenants across different consumption metrics."
    >
      <div className="flex gap-1 mb-4 bg-muted rounded-full p-0.5 w-fit">
        {views.map(v => (
          <button
            key={v.value}
            onClick={() => setView(v.value)}
            className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
              view === v.value ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {v.label}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(160 10% 90%)" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} stroke="hsl(220 10% 70%)" tickLine={false} unit={unit} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} stroke="hsl(220 10% 70%)" tickLine={false} axisLine={false} width={110} />
          <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid hsl(160 10% 90%)', fontSize: '13px' }} formatter={(v: number) => [`${v}${unit}`, 'Value']} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={20}>
            {data.map((entry, idx) => (
              <rect key={idx} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
}
