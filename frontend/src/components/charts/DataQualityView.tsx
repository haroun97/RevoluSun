import { motion } from 'framer-motion';
import { AlertTriangle, Info, CheckCircle2, ShieldAlert } from 'lucide-react';
import type { DataQualityEntry, DataQualityAlert } from '@/types/energy';

interface Props {
  entries: DataQualityEntry[];
  alerts: DataQualityAlert[];
}

const statusIcon = {
  good: CheckCircle2,
  warning: AlertTriangle,
  critical: ShieldAlert,
};

const statusColor = {
  good: 'text-primary',
  warning: 'text-solar',
  critical: 'text-destructive',
};

const alertIcon = {
  info: Info,
  warning: AlertTriangle,
  error: ShieldAlert,
};

const alertBg = {
  info: 'bg-primary/5 border-primary/10',
  warning: 'bg-solar/5 border-solar/15',
  error: 'bg-destructive/5 border-destructive/15',
};

const alertIconColor = {
  info: 'text-primary',
  warning: 'text-solar',
  error: 'text-destructive',
};

export function DataQualityView({ entries, alerts }: Props) {
  return (
    <div className="space-y-6">
      {/* Coverage Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="chart-container overflow-hidden"
      >
        <h3 className="font-display text-lg font-semibold text-foreground mb-1">Meter Coverage Overview</h3>
        <p className="text-sm text-muted-foreground mb-4">Data completeness and anomaly summary for each metering point.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2.5 px-3 font-medium text-muted-foreground text-xs">Meter</th>
                <th className="text-left py-2.5 px-3 font-medium text-muted-foreground text-xs">Type</th>
                <th className="text-center py-2.5 px-3 font-medium text-muted-foreground text-xs">Coverage</th>
                <th className="text-center py-2.5 px-3 font-medium text-muted-foreground text-xs">Active</th>
                <th className="text-center py-2.5 px-3 font-medium text-muted-foreground text-xs">Gaps</th>
                <th className="text-center py-2.5 px-3 font-medium text-muted-foreground text-xs">Anomalies</th>
                <th className="text-center py-2.5 px-3 font-medium text-muted-foreground text-xs">Status</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry, idx) => {
                const StatusIcon = statusIcon[entry.status];
                return (
                  <motion.tr
                    key={entry.meterId}
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: idx * 0.03 }}
                    className="border-b border-border/40 hover:bg-muted/30 transition-colors"
                  >
                    <td className="py-2.5 px-3 font-medium text-foreground">{entry.meterName}</td>
                    <td className="py-2.5 px-3">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        entry.type === 'pv' ? 'bg-solar/10 text-solar-warm' : entry.type === 'building' ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
                      }`}>
                        {entry.type.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${entry.coverage >= 95 ? 'bg-primary' : 'bg-solar'}`}
                            style={{ width: `${entry.coverage}%` }}
                          />
                        </div>
                        <span className="text-xs">{entry.coverage}%</span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-center text-xs">{entry.activeDays}/{entry.totalDays}</td>
                    <td className="py-2.5 px-3 text-center text-xs">{entry.gaps}</td>
                    <td className="py-2.5 px-3 text-center text-xs">{entry.anomalies}</td>
                    <td className="py-2.5 px-3 text-center">
                      <StatusIcon className={`w-4 h-4 mx-auto ${statusColor[entry.status]}`} />
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Alerts */}
      <div className="grid gap-3 sm:grid-cols-2">
        {alerts.map((alert, idx) => {
          const AlertIcon = alertIcon[alert.severity];
          return (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.08 }}
              className={`rounded-2xl p-4 border ${alertBg[alert.severity]}`}
            >
              <div className="flex items-start gap-3">
                <AlertIcon className={`w-4 h-4 mt-0.5 shrink-0 ${alertIconColor[alert.severity]}`} />
                <div>
                  <p className="text-sm font-medium text-foreground">{alert.message}</p>
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{alert.detail}</p>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
