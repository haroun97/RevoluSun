/**
 * Wrapper for all dashboard charts: title, optional description, and consistent animation.
 */
import { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface ChartWrapperProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function ChartWrapper({ title, description, children }: ChartWrapperProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.5 }}
      className="chart-container"
    >
      <div className="mb-5">
        <h3 className="font-display text-lg font-semibold text-foreground">{title}</h3>
        {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
      </div>
      {children}
    </motion.div>
  );
}
