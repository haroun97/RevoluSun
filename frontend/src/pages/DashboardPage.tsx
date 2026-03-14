import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Zap, Sun, BarChart3, ArrowUpRight, Users, AlertCircle, Sparkles, Shield, Loader2 } from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { HeroSummary } from "@/components/hero/HeroSummary";
import { KpiCard } from "@/components/kpi/KpiCard";
import { FilterBar } from "@/components/filters/FilterBar";
import { BuildingVsPvChart } from "@/components/charts/BuildingVsPvChart";
import { PvUsageChart } from "@/components/charts/PvUsageChart";
import { TenantComparisonChart } from "@/components/charts/TenantComparisonChart";
import { TenantTrendChart } from "@/components/charts/TenantTrendChart";
import { EnergySharingChart } from "@/components/charts/EnergySharingChart";
import { DataQualityView } from "@/components/charts/DataQualityView";
import { TenantInsights } from "@/components/cards/TenantInsights";
import {
  fetchSummary,
  fetchBuildingTimeseries,
  fetchTenants,
  fetchSharing,
  fetchQuality,
} from "@/api/energyApi";
import type { KpiData, Granularity } from "@/types/energy";

function SectionHeader({ id, title, subtitle }: { id: string; title: string; subtitle: string }) {
  return (
    <motion.div
      id={id}
      initial={{ opacity: 0, y: 15 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="scroll-mt-20 mb-6"
    >
      <h2 className="section-title">{title}</h2>
      <p className="section-subtitle mt-1">{subtitle}</p>
    </motion.div>
  );
}

const defaultKpi: KpiData = {
  totalConsumption: 0,
  totalPvGeneration: 0,
  selfConsumptionRatio: 0,
  surplusRatio: 0,
  activeTenants: 0,
  dataQualityAlerts: 0,
};

export default function DashboardPage() {
  const [granularity, setGranularity] = useState<Granularity>("daily");

  const summaryQuery = useQuery({
    queryKey: ["summary"],
    queryFn: fetchSummary,
    staleTime: 60_000,
  });
  const timeseriesQuery = useQuery({
    queryKey: ["timeseries", "building", granularity],
    queryFn: () => fetchBuildingTimeseries(granularity),
    staleTime: 60_000,
  });
  const tenantsQuery = useQuery({
    queryKey: ["tenants"],
    queryFn: fetchTenants,
    staleTime: 60_000,
  });
  const sharingQuery = useQuery({
    queryKey: ["sharing"],
    queryFn: fetchSharing,
    staleTime: 60_000,
  });
  const qualityQuery = useQuery({
    queryKey: ["quality"],
    queryFn: fetchQuality,
    staleTime: 60_000,
  });

  const kpi = summaryQuery.data ?? defaultKpi;
  const timeSeries = timeseriesQuery.data ?? [];
  const tenants = tenantsQuery.data ?? [];
  const allocations = sharingQuery.data ?? [];
  const { entries: dataQualityEntries = [], alerts: dataQualityAlerts = [] } = qualityQuery.data ?? {};

  const isLoading =
    summaryQuery.isLoading ||
    timeseriesQuery.isLoading ||
    tenantsQuery.isLoading ||
    sharingQuery.isLoading ||
    qualityQuery.isLoading;
  const isError =
    summaryQuery.isError ||
    timeseriesQuery.isError ||
    tenantsQuery.isError ||
    sharingQuery.isError ||
    qualityQuery.isError;

  const kpiCards = [
    { title: "Building Consumption", value: `${(kpi.totalConsumption / 1000).toFixed(1)} MWh`, subtitle: "90-day total demand", icon: Zap, iconColor: "text-primary", gradient: "gradient-card-teal" },
    { title: "PV Generation", value: `${(kpi.totalPvGeneration / 1000).toFixed(1)} MWh`, subtitle: "90-day solar output", icon: Sun, iconColor: "text-solar", gradient: "gradient-card-solar" },
    { title: "Self-Consumption", value: `${kpi.selfConsumptionRatio}%`, subtitle: "PV used on-site", icon: BarChart3, iconColor: "text-primary", gradient: "gradient-card-teal" },
    { title: "Surplus Ratio", value: `${kpi.surplusRatio}%`, subtitle: "PV exported to grid", icon: ArrowUpRight, iconColor: "text-solar", gradient: "gradient-card-solar" },
    { title: "Active Tenants", value: `${kpi.activeTenants}`, subtitle: "Metered residential units", icon: Users, iconColor: "text-primary", gradient: "gradient-card-teal" },
    { title: "Data Alerts", value: `${kpi.dataQualityAlerts}`, subtitle: "Quality notices", icon: AlertCircle, iconColor: "text-solar", gradient: "gradient-card-solar" },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4">
        <Navbar />
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
        <p className="text-muted-foreground">Loading dashboard…</p>
        <Footer />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4 p-4">
        <Navbar />
        <p className="text-destructive font-medium">Failed to load dashboard data. Is the backend running?</p>
        <p className="text-muted-foreground text-sm">Ensure the API is available at the configured VITE_API_URL (default: http://localhost:8000).</p>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <HeroSummary kpi={kpi} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
        <section id="overview" className="scroll-mt-20">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
            {kpiCards.map((card, idx) => (
              <KpiCard key={card.title} {...card} index={idx} />
            ))}
          </div>
        </section>

        <FilterBar granularity={granularity} onGranularityChange={setGranularity} />

        <section>
          <SectionHeader id="core-charts" title="Energy Overview" subtitle="Building electricity demand and photovoltaic generation over the analysis period." />
          <div className="grid lg:grid-cols-2 gap-6">
            <BuildingVsPvChart data={timeSeries} />
            <PvUsageChart data={timeSeries} />
          </div>
        </section>

        <section>
          <SectionHeader id="tenants" title="Tenant Analysis" subtitle="Individual tenant consumption patterns, comparisons, and key insights." />
          <TenantInsights tenants={tenants} />
          <div className="grid lg:grid-cols-2 gap-6 mt-6">
            <TenantComparisonChart tenants={tenants} />
            <TenantTrendChart tenants={tenants} />
          </div>
        </section>

        <section>
          <SectionHeader id="energy-sharing" title="Fair Energy Sharing Simulation" subtitle="PV generation is allocated proportionally to tenant demand for each period." />
          <div className="flex items-center gap-2 mb-6">
            <Sparkles className="w-4 h-4 text-solar" />
            <span className="text-sm text-muted-foreground">Allocation model applied across {tenants.length} tenants</span>
          </div>
          <EnergySharingChart allocations={allocations} />
        </section>

        <section>
          <SectionHeader id="data-quality" title="Data Quality & Coverage" subtitle="Transparency metrics for metering data completeness and consistency." />
          <div className="flex items-center gap-2 mb-6">
            <Shield className="w-4 h-4 text-primary" />
            <span className="text-sm text-muted-foreground">Automated checks across all metering points</span>
          </div>
          <DataQualityView entries={dataQualityEntries} alerts={dataQualityAlerts} />
        </section>
      </div>

      <Footer />
    </div>
  );
}
