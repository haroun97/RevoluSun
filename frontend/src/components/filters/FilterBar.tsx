import { motion } from 'framer-motion';
import { Calendar, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { Granularity } from '@/types/energy';

interface FilterBarProps {
  granularity: Granularity;
  onGranularityChange: (g: Granularity) => void;
}

const granularities: { value: Granularity; label: string }[] = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
];

export function FilterBar({ granularity, onGranularityChange }: FilterBarProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="flex flex-wrap items-center gap-3 bg-card rounded-2xl p-4 border border-border/60"
      style={{ boxShadow: 'var(--shadow-card)' }}
    >
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Calendar className="w-4 h-4" />
        <span className="font-medium">Jun 1 – Aug 29, 2024</span>
      </div>

      <div className="h-5 w-px bg-border hidden sm:block" />

      <div className="flex items-center bg-muted rounded-full p-0.5">
        {granularities.map((g) => (
          <button
            key={g.value}
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
        <Button variant="ghost" size="sm" className="text-xs text-muted-foreground">
          <RotateCcw className="w-3.5 h-3.5 mr-1" />
          Reset
        </Button>
      </div>
    </motion.div>
  );
}
