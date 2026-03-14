/**
 * Energy dashboard API: summary, timeseries, tenants, sharing, quality.
 * Maps backend responses to frontend types where needed.
 */

import { apiGet } from "./client";
import type {
  KpiData,
  TimeSeriesPoint,
  TenantData,
  TenantAllocation,
  DataQualityEntry,
  DataQualityAlert,
} from "@/types/energy";

const TENANT_COLORS = ["#3E8F87", "#F2B544", "#7ED3C1", "#E07A5F", "#5B8C5A", "#8B7EC8", "#C9A227", "#6B9080", "#E8B4B8", "#A8DADC", "#457B9D", "#1D3557", "#F4A261"];

// --- Backend response types (minimal) ---
interface SummaryDto {
  total_building_consumption: number;
  total_pv_generation: number;
  self_consumption_ratio: number;
  surplus_pv_ratio: number;
  active_tenants: number;
  data_quality_alerts: number;
}

interface BuildingPointDto {
  date: string;
  building_consumption: number;
  pv_generation: number;
  self_consumed_pv: number;
  surplus_pv: number;
}

interface TenantComparisonDto {
  tenant_id: string;
  total_consumption: number;
  average_daily_consumption: number;
  active_days: number;
}

interface TenantTimeseriesPointDto {
  date: string;
  consumption: number;
}

interface SharingTenantDto {
  tenant_id: string;
  demand: number;
  allocated_pv: number;
  grid_import: number;
  self_sufficiency_ratio: number;
}

interface QualityIssueDto {
  id: number;
  issue_type: string;
  meter_id: string | null;
  tenant_id: string | null;
  date: string | null;
  severity: string;
  message: string;
}

interface CoverageRangeDto {
  meter_id: string;
  meter_name: string;
  meter_type: string;
  active_days: number;
  total_days: number;
  coverage: number;
  gaps: number;
  anomalies: number;
  status: "good" | "warning" | "critical";
}

interface QualityDto {
  negative_deltas: number;
  missing_days: number;
  coverage_ranges: CoverageRangeDto[];
  consistency_checks: { name: string; count: number }[];
  issues: QualityIssueDto[];
}

// --- API functions ---

export async function fetchSummary(): Promise<KpiData> {
  const d = await apiGet<SummaryDto>("/api/summary");
  return {
    totalConsumption: d.total_building_consumption,
    totalPvGeneration: d.total_pv_generation,
    selfConsumptionRatio: d.self_consumption_ratio,
    surplusRatio: d.surplus_pv_ratio,
    activeTenants: d.active_tenants,
    dataQualityAlerts: d.data_quality_alerts,
  };
}

export async function fetchBuildingTimeseries(_granularity?: string): Promise<TimeSeriesPoint[]> {
  const list = await apiGet<BuildingPointDto[]>("/api/timeseries/building?granularity=daily");
  return list.map((p) => ({
    date: p.date,
    buildingConsumption: p.building_consumption,
    pvGeneration: p.pv_generation,
    selfConsumed: p.self_consumed_pv,
    surplus: p.surplus_pv,
  }));
}

export async function fetchTenantsComparison(): Promise<TenantComparisonDto[]> {
  return apiGet<TenantComparisonDto[]>("/api/tenants/comparison");
}

export async function fetchTenantTimeseries(tenantId: string): Promise<{ date: string; consumption: number }[]> {
  return apiGet<TenantTimeseriesPointDto[]>(`/api/tenants/timeseries/${encodeURIComponent(tenantId)}`);
}

/** Build full TenantData[]: comparison + timeseries for each tenant, colors assigned. */
export async function fetchTenants(): Promise<TenantData[]> {
  const comparison = await fetchTenantsComparison();
  const timeseriesByTenant = await Promise.all(
    comparison.map((t) => fetchTenantTimeseries(t.tenant_id))
  );
  return comparison.map((t, idx) => ({
    id: t.tenant_id,
    name: t.tenant_id,
    unit: t.tenant_id,
    totalConsumption: t.total_consumption,
    avgDailyConsumption: t.average_daily_consumption,
    activeDays: t.active_days,
    color: TENANT_COLORS[idx % TENANT_COLORS.length],
    timeSeries: timeseriesByTenant[idx].map((p) => ({ date: p.date, consumption: p.consumption })),
  }));
}

export async function fetchSharing(): Promise<TenantAllocation[]> {
  const list = await apiGet<SharingTenantDto[]>("/api/sharing");
  return list.map((a) => ({
    tenantId: a.tenant_id,
    tenantName: a.tenant_id,
    unit: a.tenant_id,
    totalDemand: a.demand,
    pvAllocated: a.allocated_pv,
    gridImport: a.grid_import,
    selfSufficiency: a.self_sufficiency_ratio,
  }));
}

function mapSeverity(s: string): "info" | "warning" | "error" {
  if (s === "warning" || s === "error" || s === "info") return s;
  return s === "error" ? "error" : s === "warning" ? "warning" : "info";
}

export async function fetchQuality(): Promise<{
  entries: DataQualityEntry[];
  alerts: DataQualityAlert[];
}> {
  const d = await apiGet<QualityDto>("/api/quality");
  const entries: DataQualityEntry[] = d.coverage_ranges.map((r) => ({
    meterId: r.meter_id,
    meterName: r.meter_name,
    type: (r.meter_type === "pv" ? "pv" : r.meter_type === "building_total" ? "building" : "tenant") as "building" | "pv" | "tenant",
    activeDays: r.active_days,
    totalDays: r.total_days,
    coverage: r.coverage,
    gaps: r.gaps,
    anomalies: r.anomalies,
    status: r.status,
  }));
  const alerts: DataQualityAlert[] = d.issues.map((i, idx) => ({
    id: `q-${i.id}-${idx}`,
    severity: mapSeverity(i.severity),
    message: i.message,
    detail: i.message,
  }));
  return { entries, alerts };
}
