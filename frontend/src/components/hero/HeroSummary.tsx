/**
 * Hero section: title, subtitle, and four main KPIs (PV generation, building demand, self-consumption %, active tenants).
 * Uses the summary KPIs from the API to show the big numbers at the top of the dashboard.
 */
import { motion } from 'framer-motion';
import { Sun, Zap, BarChart3, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { KpiData } from '@/types/energy';

interface HeroSummaryProps {
  kpi: KpiData;
}

/** Which KPI to show and how to format it (MWh, %, or count). */
const summaryItems = [
  { key: 'pvGen', label: 'PV Generation', icon: Sun, format: (v: number) => `${(v / 1000).toFixed(1)} MWh`, color: 'text-solar' },
  { key: 'demand', label: 'Building Demand', icon: Zap, format: (v: number) => `${(v / 1000).toFixed(1)} MWh`, color: 'text-primary' },
  { key: 'selfCons', label: 'Self-Consumption', icon: BarChart3, format: (v: number) => `${v}%`, color: 'text-teal-light' },
  { key: 'tenants', label: 'Active Tenants', icon: Users, format: (v: number) => `${v}`, color: 'text-foreground' },
] as const;

function getVal(key: string, kpi: KpiData): number {
  switch (key) {
    case 'pvGen': return kpi.totalPvGeneration;
    case 'demand': return kpi.totalConsumption;
    case 'selfCons': return kpi.selfConsumptionRatio;
    case 'tenants': return kpi.activeTenants;
    default: return 0;
  }
}

export function HeroSummary({ kpi }: HeroSummaryProps) {
  return (
    <section className="relative gradient-hero overflow-hidden pt-24 pb-12">
      {/* Floating decorative elements */}
      <div className="absolute top-20 right-[15%] w-32 h-32 rounded-full bg-solar/10 animate-float blur-2xl" />
      <div className="absolute bottom-10 left-[10%] w-48 h-48 rounded-full bg-primary/8 animate-float blur-3xl" style={{ animationDelay: '2s' }} />
      <div className="absolute top-1/2 right-[30%] w-20 h-20 rounded-full bg-mint/20 animate-glow blur-xl" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
          className="text-center mb-10"
        >
          <Badge variant="secondary" className="mb-4 px-3 py-1 text-xs font-semibold bg-primary/10 text-primary border-0">
            RevoluSUN MVP
          </Badge>
          <h1 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground tracking-tight mb-3">
            Energy Sharing Dashboard
          </h1>
          <p className="text-muted-foreground text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
            Interactive analysis of building load, PV generation, tenant demand, and fair solar allocation.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 max-w-3xl mx-auto"
        >
          {summaryItems.map((item, idx) => {
            const Icon = item.icon;
            const value = getVal(item.key, kpi);
            return (
              <motion.div
                key={item.key}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 + idx * 0.1 }}
                className="bg-card/80 backdrop-blur-sm rounded-2xl p-4 border border-border/40 text-center"
              >
                <Icon className={`w-5 h-5 mx-auto mb-1.5 ${item.color}`} />
                <div className="font-display text-xl sm:text-2xl font-bold text-foreground">
                  {item.format(value)}
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">{item.label}</div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
