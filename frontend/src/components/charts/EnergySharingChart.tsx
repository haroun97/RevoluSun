import { motion } from 'framer-motion';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { ChartWrapper } from './ChartWrapper';
import { Info } from 'lucide-react';
import type { TenantAllocation } from '@/types/energy';

interface Props {
  allocations: TenantAllocation[];
}

export function EnergySharingChart({ allocations }: Props) {
  const chartData = allocations.map(a => ({
    name: `${a.unit}`,
    pvAllocated: a.pvAllocated,
    gridImport: a.gridImport,
  }));

  return (
    <div className="space-y-6">
      <ChartWrapper
        title="Allocated PV vs Grid Import by Tenant"
        description="Each tenant's demand split between locally allocated solar energy and remaining grid import."
      >
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(160 10% 90%)" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="hsl(220 10% 70%)" tickLine={false} />
            <YAxis tick={{ fontSize: 11 }} stroke="hsl(220 10% 70%)" tickLine={false} axisLine={false} unit=" kWh" width={65} />
            <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid hsl(160 10% 90%)', fontSize: '13px' }} formatter={(v: number, n: string) => [`${v} kWh`, n === 'pvAllocated' ? 'PV Allocated' : 'Grid Import']} />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} formatter={(v) => v === 'pvAllocated' ? 'PV Allocated' : 'Grid Import'} />
            <Bar dataKey="pvAllocated" stackId="a" fill="#3E8F87" radius={[0, 0, 0, 0]} />
            <Bar dataKey="gridImport" stackId="a" fill="#E5E7EB" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartWrapper>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {allocations.map((a, idx) => (
          <motion.div
            key={a.tenantId}
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: idx * 0.05 }}
            className="bg-card rounded-2xl p-4 border border-border/60 text-center"
            style={{ boxShadow: 'var(--shadow-card)' }}
          >
            <div className="text-xs text-muted-foreground mb-1">Unit {a.unit}</div>
            <div className="font-display text-xl font-bold text-primary">{a.selfSufficiency}%</div>
            <div className="text-[10px] text-muted-foreground mt-0.5">self-sufficiency</div>
            {/* Mini bar */}
            <div className="w-full h-1.5 bg-muted rounded-full mt-2 overflow-hidden">
              <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${a.selfSufficiency}%` }} />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
