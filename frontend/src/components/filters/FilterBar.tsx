import { motion } from 'framer-motion';
import { Calendar, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { Granularity } from '@/types/energy';

export interface DateRange {
  start: string;
  end: string;
}

interface FilterBarProps {
  dateRange: DateRange | null;
  /** Default range (e.g. last 90 days) used for Reset and "Last 90 days" preset. */
  defaultDateRange: DateRange | null;
  /** Full data range (min–max) for "Full period" preset. */
  fullDateRange: DateRange | null;
  onDateRangeChange: (range: DateRange) => void;
  granularity: Granularity;
  onGranularityChange: (g: Granularity) => void;
  onReset: () => void;
}

const granularities: { value: Granularity; label: string }[] = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
];

function formatRange(range: DateRange): string {
  const start = new Date(range.start + 'T12:00:00');
  const end = new Date(range.end + 'T12:00:00');
  return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} – ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
}

export function FilterBar({
  dateRange,
  defaultDateRange,
  fullDateRange,
  onDateRangeChange,
  granularity,
  onGranularityChange,
  onReset,
}: FilterBarProps) {
  const rangeLabel = dateRange ? formatRange(dateRange) : 'Loading…';

  const presets: { label: string; getRange: () => DateRange }[] = [];
  if (defaultDateRange) {
    const endDate = new Date(defaultDateRange.end + 'T12:00:00');
    presets.push({
      label: 'Last 30 days',
      getRange: () => {
        const e = new Date(endDate);
        const s = new Date(e);
        s.setDate(s.getDate() - 29);
        return { start: s.toISOString().slice(0, 10), end: e.toISOString().slice(0, 10) };
      },
    });
    presets.push({
      label: 'Last 90 days',
      getRange: () => defaultDateRange,
    });
  }
  if (fullDateRange) {
    presets.push({
      label: 'Full period',
      getRange: () => fullDateRange,
    });
  }

  const isPresetActive = (getRange: () => DateRange) => {
    if (!dateRange) return false;
    const r = getRange();
    return dateRange.start === r.start && dateRange.end === r.end;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="flex flex-wrap items-center gap-3 bg-card rounded-2xl p-4 border border-border/60"
      style={{ boxShadow: 'var(--shadow-card)' }}
    >
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Calendar className="w-4 h-4 shrink-0" />
        <span className="font-medium">{rangeLabel}</span>
      </div>

      {presets.length > 0 && (
        <>
          <div className="h-5 w-px bg-border hidden sm:block" />
          <div className="flex flex-wrap gap-1.5">
            {presets.map((p) => {
              const active = isPresetActive(p.getRange);
              return (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => onDateRangeChange(p.getRange())}
                  className={`px-2.5 py-1 text-xs font-medium rounded-full border transition-all ${
                    active
                      ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                      : 'border-border/60 text-muted-foreground hover:text-foreground hover:border-border'
                  }`}
                >
                  {p.label}
                </button>
              );
            })}
          </div>
        </>
      )}

      <div className="h-5 w-px bg-border hidden sm:block" />

      <div className="flex items-center bg-muted rounded-full p-0.5">
        {granularities.map((g) => (
          <button
            key={g.value}
            type="button"
            onClick={() => onGranularityChange(g.value)}
            className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
              granularity === g.value
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {g.label}
          </button>
        ))}
      </div>

      <div className="ml-auto">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="text-xs text-muted-foreground"
          onClick={onReset}
          disabled={!defaultDateRange}
        >
          <RotateCcw className="w-3.5 h-3.5 mr-1" />
          Reset
        </Button>
      </div>
    </motion.div>
  );
}
