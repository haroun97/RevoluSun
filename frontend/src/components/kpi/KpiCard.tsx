import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: LucideIcon;
  iconColor?: string;
  gradient?: string;
  index: number;
}

export function KpiCard({ title, value, subtitle, icon: Icon, iconColor = 'text-primary', gradient = 'gradient-card-teal', index }: KpiCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.5, delay: index * 0.08 }}
      whileHover={{ y: -2 }}
      className={`${gradient} rounded-2xl p-5 border border-border/50 transition-shadow duration-300 hover:shadow-lg cursor-default`}
      style={{ boxShadow: 'var(--shadow-card)' }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-xl bg-card/60 ${iconColor}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="font-display text-2xl font-bold text-foreground mb-0.5">{value}</div>
      <div className="text-sm font-medium text-foreground/80 mb-1">{title}</div>
      <div className="text-xs text-muted-foreground">{subtitle}</div>
    </motion.div>
  );
}
