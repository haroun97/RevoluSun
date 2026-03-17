/**
 * Data quality section: breakdown counts, coverage table per meter, and expandable alert list.
 * Shows negative deltas, missing days, tenant/building mismatch, and missing tenants.
 */
import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Info, CheckCircle2, ShieldAlert, ChevronDown, ChevronRight } from 'lucide-react';
import type { DataQualityEntry, DataQualityAlert, DataQualityIssueType, QualityAlertBreakdown } from '@/types/energy';

const TABLE_PAGE_SIZE = 50;

interface Props {
  entries: DataQualityEntry[];
  alerts: DataQualityAlert[];
  breakdown?: QualityAlertBreakdown | null;
  missingTenants?: string[];
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

const issueTypeLabel: Record<DataQualityIssueType, string> = {
  negative_delta: 'Invalid deltas',
  missing_days: 'Missing days',
  tenant_building_mismatch: 'Mismatch',
};

export type AlertGroup = {
  groupKey: string;
  meterLabel: string;
  typeLabel: string;
  issueType: DataQualityIssueType;
  alerts: DataQualityAlert[];
};

/** Group alerts by meter and issue type for the expandable list. */
function buildAlertGroups(alerts: DataQualityAlert[]): AlertGroup[] {
  const map = new Map<string, DataQualityAlert[]>();
  for (const a of alerts) {
    const meter = a.meterId ?? '—';
    const key = `${a.issueType}|${meter}`;
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(a);
  }
  const groups: AlertGroup[] = [];
  map.forEach((groupAlerts, key) => {
    const [issueType, meterId] = key.split('|');
    const meterLabel = meterId === '—' ? '—' : meterId;
    groups.push({
      groupKey: key,
      meterLabel,
      typeLabel: issueTypeLabel[issueType as DataQualityIssueType],
      issueType: issueType as DataQualityIssueType,
      alerts: groupAlerts.sort((x, y) => (x.date ?? '').localeCompare(y.date ?? '')),
    });
  });
  return groups.sort((a, b) => b.alerts.length - a.alerts.length);
}

export function DataQualityView({ entries, alerts, breakdown, missingTenants = [] }: Props) {
  const [expandedGroupKey, setExpandedGroupKey] = useState<string | null>(null);
  const [tablePage, setTablePage] = useState(1);

  const alertGroups = useMemo(() => buildAlertGroups(alerts), [alerts]);

  const showBreakdown =
    breakdown &&
    (breakdown.negativeDeltas > 0 || breakdown.missingDays > 0 || breakdown.mismatchCount > 0);
  const showMismatchNote = false;

  return (
    <div className="space-y-6">
      {/* Alert breakdown strip */}
      {showBreakdown && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="flex flex-wrap items-center gap-2"
        >
          <span className="text-xs text-muted-foreground font-medium">Alert breakdown:</span>
          <span className="inline-flex flex-wrap gap-1.5">
            <span className="inline-block px-2.5 py-1 rounded-full text-xs font-medium bg-destructive/10 text-destructive border border-destructive/20">
              Invalid deltas: {breakdown!.negativeDeltas}
            </span>
            <span className="inline-block px-2.5 py-1 rounded-full text-xs font-medium bg-solar/10 text-solar-warm border border-solar/20">
              Missing days: {breakdown!.missingDays}
            </span>
            <span className="inline-block px-2.5 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary border border-primary/20">
              Mismatch: {breakdown!.mismatchCount}
            </span>
          </span>
        </motion.div>
      )}

      {showMismatchNote && null}

      {/* Missing tenants (e.g. Kunde7) + documentation note */}
      {missingTenants.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="rounded-2xl p-4 border bg-primary/5 border-primary/10"
        >
          <p className="text-sm text-foreground">
            Tenants not present in the dataset are excluded from all tenant metrics and comparisons; zero consumption is not assumed.
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            <span className="font-medium text-foreground">Tenants not in dataset:</span>{' '}
            {missingTenants.join(', ')}
          </p>
        </motion.div>
      )}

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

      {/* Data Alerts: summary-first, expand by group */}
      <div>
        <h3 className="font-display text-lg font-semibold text-foreground mb-2">Data Alerts</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Invalid deltas = days with negative/invalid consumption change (excluded from totals). Missing days = gaps in time series. Mismatch = tenant total ≠ building total.
        </p>

        {alertGroups.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">No alerts.</p>
        ) : (
          <div className="space-y-1 border border-border/60 rounded-xl overflow-hidden bg-card">
            {alertGroups.map((group) => {
              const isExpanded = expandedGroupKey === group.groupKey;
              return (
                <div key={group.groupKey} className="border-b border-border/40 last:border-b-0">
                  <button
                    type="button"
                    onClick={() => {
                      setExpandedGroupKey((k) => (k === group.groupKey ? null : group.groupKey));
                      setTablePage(1);
                    }}
                    className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left hover:bg-muted/40 transition-colors"
                  >
                    <span className="flex items-center gap-2">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
                      )}
                      <span className="font-medium text-foreground">
                        {group.meterLabel} · {group.typeLabel}
                      </span>
                    </span>
                    <span className="text-sm text-muted-foreground tabular-nums">{group.alerts.length} alerts</span>
                  </button>
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="px-4 pb-4 pt-0">
                          <div className="overflow-x-auto rounded-lg border border-border/60 bg-muted/20">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="border-b border-border bg-muted/40">
                                  <th className="text-left py-2 px-3 font-medium text-muted-foreground text-xs">Date</th>
                                  <th className="text-left py-2 px-3 font-medium text-muted-foreground text-xs">Meter</th>
                                  <th className="text-left py-2 px-3 font-medium text-muted-foreground text-xs">Message</th>
                                </tr>
                              </thead>
                              <tbody>
                                {group.alerts
                                  .slice(0, TABLE_PAGE_SIZE * tablePage)
                                  .map((alert) => (
                                    <tr key={alert.id} className="border-b border-border/40 last:border-b-0 hover:bg-muted/30">
                                      <td className="py-2 px-3 text-muted-foreground tabular-nums">{alert.date ?? '—'}</td>
                                      <td className="py-2 px-3 text-foreground">{alert.meterId ?? '—'}</td>
                                      <td className="py-2 px-3 text-foreground">{alert.message}</td>
                                    </tr>
                                  ))}
                              </tbody>
                            </table>
                          </div>
                          {group.alerts.length > TABLE_PAGE_SIZE * tablePage && (
                            <button
                              type="button"
                              onClick={() => setTablePage((p) => p + 1)}
                              className="mt-2 text-xs font-medium text-primary hover:underline"
                            >
                              Show next {TABLE_PAGE_SIZE} ({group.alerts.length - TABLE_PAGE_SIZE * tablePage} remaining)
                            </button>
                          )}
                          {tablePage > 1 && group.alerts.length <= TABLE_PAGE_SIZE * tablePage && (
                            <p className="mt-2 text-xs text-muted-foreground">Showing all {group.alerts.length} alerts.</p>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
