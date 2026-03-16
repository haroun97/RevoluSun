import { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Zap, Sun, BarChart3, ArrowUpRight, Users, AlertCircle, Loader2 } from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { HeroSummary } from "@/components/hero/HeroSummary";
import { KpiCard } from "@/components/kpi/KpiCard";
import { FilterBar, type DateRange } from "@/components/filters/FilterBar";
import { BuildingVsPvChart } from "@/components/charts/BuildingVsPvChart";
import { PvUsageChart } from "@/components/charts/PvUsageChart";
import { TenantComparisonChart } from "@/components/charts/TenantComparisonChart";
import { TenantTrendChart } from "@/components/charts/TenantTrendChart";
import { EnergySharingChart } from "@/components/charts/EnergySharingChart";
import { DataQualityView } from "@/components/charts/DataQualityView";
import { TenantInsights } from "@/components/cards/TenantInsights";
import { GoogleDriveImportButton } from "@/components/import/GoogleDriveImportButton";
import {
  fetchDateRange,
  fetchSummary,
  fetchBuildingTimeseries,
  fetchTenants,
  fetchSharing,
  fetchQuality,
} from "@/api/energyApi";
import type { KpiData, Granularity } from "@/types/energy";

function last90DaysFrom(endDate: string): DateRange {
  const end = new Date(endDate + "T12:00:00");
  const start = new Date(end);
  start.setDate(start.getDate() - 89);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

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
  const [dateRange, setDateRange] = useState<DateRange | null>(null);

  const dateRangeQuery = useQuery({
    queryKey: ["dateRange"],
    queryFn: fetchDateRange,
    staleTime: 60_000,
  });

  const defaultDateRange = useMemo<DateRange | null>(() => {
    const max = dateRangeQuery.data?.max_date;
    if (!max) return null;
    return last90DaysFrom(max);
  }, [dateRangeQuery.data?.max_date]);

  const fullDateRange = useMemo<DateRange | null>(() => {
    const min = dateRangeQuery.data?.min_date;
    const max = dateRangeQuery.data?.max_date;
    if (!min || !max) return null;
    return { start: min, end: max };
  }, [dateRangeQuery.data?.min_date, dateRangeQuery.data?.max_date]);

  useEffect(() => {
    if (dateRange !== null) return;
    const next = defaultDateRange ?? fullDateRange;
    if (next) setDateRange(next);
  }, [dateRange, defaultDateRange, fullDateRange]);

  const summaryQuery = useQuery({
    queryKey: ["summary", dateRange?.start ?? "", dateRange?.end ?? ""],
    queryFn: () => fetchSummary(dateRange?.start, dateRange?.end),
    staleTime: 60_000,
  });
  const timeseriesQuery = useQuery({
    queryKey: ["timeseries", "building", granularity, dateRange?.start ?? "", dateRange?.end ?? ""],
    queryFn: () => fetchBuildingTimeseries(granularity, dateRange?.start, dateRange?.end),
    staleTime: 60_000,
  });
  const tenantsQuery = useQuery({
    queryKey: ["tenants", dateRange?.start ?? "", dateRange?.end ?? ""],
    queryFn: () => fetchTenants(dateRange?.start, dateRange?.end),
    staleTime: 60_000,
  });
  const sharingQuery = useQuery({
    queryKey: ["sharing", dateRange?.start ?? "", dateRange?.end ?? ""],
    queryFn: () => fetchSharing(dateRange?.start, dateRange?.end),
    staleTime: 60_000,
  });
  const qualityQuery = useQuery({
    queryKey: ["quality"],
    queryFn: () => fetchQuality(),
    staleTime: 60_000,
  });

  const kpi = summaryQuery.data ?? defaultKpi;
  const timeSeries = timeseriesQuery.data ?? [];
  const tenants = tenantsQuery.data ?? [];
  const allocations = sharingQuery.data ?? [];
  const qualityData = qualityQuery.data;
  const dataQualityEntries = qualityData?.entries ?? [];
  const dataQualityAlerts = qualityData?.alerts ?? [];
  const qualityBreakdown = qualityData?.breakdown ?? null;
  const dataQualityMissingTenants = qualityData?.missingTenants ?? [];

  // --- Derived operational KPIs for secondary row ---

  // Total grid import (kWh) from tenant allocations; convert to MWh for display.
  const totalGridImportKwh = allocations.reduce((sum, a) => sum + (a.gridImport ?? 0), 0);
  const totalGridImportMwh = totalGridImportKwh / 1000;

  // Total grid export (kWh) from surplus PV in building timeseries; convert to MWh.
  const totalGridExportKwh = timeSeries.reduce((sum, p) => sum + (p.surplus ?? 0), 0);
  const totalGridExportMwh = totalGridExportKwh / 1000;

  // Building meter coverage %, taken from coverage table.
  const buildingCoverageEntry = dataQualityEntries.find((e) => e.meterId === "building_total");
  const buildingCoveragePct = buildingCoverageEntry?.coverage ?? null;

  // Count of tenant-building mismatch days.
  const mismatchCount =
    qualityBreakdown?.mismatchCount != null ? qualityBreakdown.mismatchCount : 0;

  const isLoading =
    dateRangeQuery.isLoading ||
    summaryQuery.isLoading ||
    timeseriesQuery.isLoading ||
    tenantsQuery.isLoading ||
    sharingQuery.isLoading ||
    qualityQuery.isLoading;
  const isError =
    dateRangeQuery.isError ||
    summaryQuery.isError ||
    timeseriesQuery.isError ||
    tenantsQuery.isError ||
    sharingQuery.isError ||
    qualityQuery.isError;

  const dataAlertsSubtitle =
    qualityBreakdown &&
    (qualityBreakdown.negativeDeltas > 0 ||
      qualityBreakdown.missingDays > 0 ||
      mismatchCount > 0)
      ? `${qualityBreakdown.negativeDeltas} invalid deltas · ${qualityBreakdown.missingDays} gaps · ${mismatchCount} mismatch`
      : "Quality notices";

  // Secondary KPI row: operational metrics only (no duplication of hero KPIs).
  const kpiCards = [
    {
      title: "Surplus Ratio",
      value: `${kpi.surplusRatio}%`,
      subtitle: "PV exported to grid",
      icon: ArrowUpRight,
      iconColor: "text-solar",
      gradient: "gradient-card-solar",
    },
    {
      title: "Grid Import",
      value: totalGridImportKwh > 0 ? `${totalGridImportMwh.toFixed(1)} MWh` : "–",
      subtitle: "Tenant demand from grid", // TODO: refine if backend exposes building-level import directly
      icon: Zap,
      iconColor: "text-primary",
      gradient: "gradient-card-teal",
    },
    {
      title: "Grid Export",
      value: totalGridExportKwh > 0 ? `${totalGridExportMwh.toFixed(1)} MWh` : "–",
      subtitle: "PV sent to grid",
      icon: Sun,
      iconColor: "text-solar",
      gradient: "gradient-card-solar",
    },
    {
      title: "Data Alerts",
      value: `${kpi.dataQualityAlerts}`,
      subtitle: dataAlertsSubtitle,
      icon: AlertCircle,
      iconColor: "text-solar",
      gradient: "gradient-card-solar",
    },
    {
      title: "Coverage %",
      value:
        buildingCoveragePct != null ? `${buildingCoveragePct.toFixed(1)}%` : "–",
      subtitle: "Building meter data coverage",
      icon: BarChart3,
      iconColor: "text-primary",
      gradient: "gradient-card-teal",
    },
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
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
            {kpiCards.map((card, idx) => (
              <KpiCard key={card.title} {...card} index={idx} />
            ))}
          </div>
        </section>

        <FilterBar
          dateRange={dateRange}
          defaultDateRange={defaultDateRange}
          fullDateRange={fullDateRange}
          onDateRangeChange={setDateRange}
          granularity={granularity}
          onGranularityChange={setGranularity}
          onReset={() => setDateRange(defaultDateRange)}
        />

        <section className="flex flex-wrap items-center gap-4">
          <GoogleDriveImportButton />
        </section>

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
          <EnergySharingChart allocations={allocations} />
        </section>

        <section>
          <SectionHeader id="data-quality" title="Data Quality & Coverage" subtitle="Transparency metrics for metering data completeness and consistency." />
          <DataQualityView
            entries={dataQualityEntries}
            alerts={dataQualityAlerts}
            breakdown={qualityBreakdown}
            missingTenants={dataQualityMissingTenants}
          />
        </section>
      </div>

      <Footer />
    </div>
  );
}
