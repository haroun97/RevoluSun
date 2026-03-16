import { Sun } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t border-border/60 bg-card mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <Sun className="w-4 h-4 text-solar" />
            <span className="font-display font-semibold text-foreground">RevoluSUN</span>
            <span>· Energy Sharing MVP</span>
          </div>
          <p className="text-xs text-muted-foreground max-w-xl">
            Case study dashboard · Nürnberg measurement data (2024–2026). Tenants not in the dataset (e.g. Kunde7) are excluded from metrics; zero consumption is not assumed.
          </p>
        </div>
      </div>
    </footer>
  );
}
