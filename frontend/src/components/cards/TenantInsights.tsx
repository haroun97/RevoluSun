/**
 * Four insight cards: highest demand, lowest avg daily, lowest avg weekly, most stable tenant.
 * If there are no tenants, we show a single "No tenant data available" card.
 */
import { motion } from 'framer-motion';
import { Trophy, TrendingDown, Activity } from 'lucide-react';
import type { TenantData } from '@/types/energy';

interface Props {
  tenants: TenantData[];
}

export function TenantInsights({ tenants }: Props) {
  if (!tenants.length) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-card rounded-2xl p-4 border border-border/60 flex items-start gap-3">
          <div className="p-2 rounded-xl bg-muted text-muted-foreground">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Tenant insights</div>
            <div className="font-display font-semibold text-foreground text-sm">
              No tenant data available
            </div>
            <div className="text-xs text-muted-foreground">
              Once tenant consumption data is loaded, highlights will appear here.
            </div>
          </div>
        </div>
      </div>
    );
  }

  const sorted = [...tenants].sort((a, b) => b.totalConsumption - a.totalConsumption);
  const topConsumer = sorted[0];
  const lowestAvgDaily = [...tenants].sort((a, b) => a.avgDailyConsumption - b.avgDailyConsumption)[0];
  const lowestAvgWeekly = [...tenants].sort((a, b) => a.avgWeeklyConsumption - b.avgWeeklyConsumption)[0];
  // Most stable = lowest coefficient of variation of daily consumption
  const mostStable = [...tenants].sort((a, b) => {
    const cvA = getCV(a);
    const cvB = getCV(b);
    return cvA - cvB;
  })[0];

  const insights = [
    { label: 'Highest Demand', tenant: topConsumer, detail: `${topConsumer.totalConsumption} kWh total`, icon: Trophy, color: 'text-solar' },
    { label: 'Lowest Avg Daily', tenant: lowestAvgDaily, detail: `${lowestAvgDaily.avgDailyConsumption} kWh/day`, icon: TrendingDown, color: 'text-primary' },
    { label: 'Lowest Avg Weekly', tenant: lowestAvgWeekly, detail: `${lowestAvgWeekly.avgWeeklyConsumption} kWh/week`, icon: TrendingDown, color: 'text-primary' },
    { label: 'Most Stable', tenant: mostStable, detail: 'Lowest variability', icon: Activity, color: 'text-teal-light' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {insights.map((ins, idx) => (
        <motion.div
          key={ins.label}
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: idx * 0.1 }}
          className="bg-card rounded-2xl p-4 border border-border/60 flex items-start gap-3"
          style={{ boxShadow: 'var(--shadow-card)' }}
        >
          <div className={`p-2 rounded-xl bg-muted ${ins.color}`}>
            <ins.icon className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs text-muted-foreground">{ins.label}</div>
            <div className="font-display font-semibold text-foreground text-sm">{ins.tenant.name}</div>
            <div className="text-xs text-muted-foreground">{ins.detail}</div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

/** Coefficient of variation (std/mean). Returns Infinity when there are no positive values so the tenant sorts last for "most stable". Exported for tests. */
export function getCV(t: TenantData): number {
  const vals = t.timeSeries.map(p => p.consumption).filter(v => v > 0);
  if (vals.length === 0) return Infinity;
  const mean = vals.reduce((s, v) => s + v, 0) / vals.length;
  const variance = vals.reduce((s, v) => s + (v - mean) ** 2, 0) / vals.length;
  return Math.sqrt(variance) / mean;
}
