/**
 * Energy dashboard API: summary, timeseries, tenants, sharing, quality.
 * Maps backend responses to frontend types where needed.
 */

import { apiGet, apiPost } from "./client";
import type {
  KpiData,
  TimeSeriesPoint,
  TenantData,
  TenantAllocation,
  DataQualityEntry,
  DataQualityAlert,
  DataQualityIssueType,
  QualityAlertBreakdown,
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
  average_weekly_consumption: number;
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
  missing_tenants: string[];
  issues: QualityIssueDto[];
}

export interface DateRangeDto {
  min_date: string | null;
  max_date: string | null;
}

/** Get min/max date for the latest batch (for default range in UI). */
export async function fetchDateRange(): Promise<DateRangeDto> {
  return apiGet<DateRangeDto>("/api/date-range");
}

/** Response from POST /api/admin/import-google-drive */
export interface GoogleDriveImportResponse {
  batch_id: number;
  message: string;
}

/** Trigger backend to download a Drive file (by id) using the user's token and run the ingestion pipeline. */
export async function importGoogleDriveFile(accessToken: string, fileId: string): Promise<GoogleDriveImportResponse> {
  return apiPost<GoogleDriveImportResponse>("/api/admin/import-google-drive", {
    access_token: accessToken,
    file_id: fileId,
  });
}

// --- API functions (with optional date range) ---

export async function fetchSummary(start?: string, end?: string): Promise<KpiData> {
  const params = start && end ? `?start_date=${encodeURIComponent(start)}&end_date=${encodeURIComponent(end)}` : "";
  const d = await apiGet<SummaryDto>(`/api/summary${params}`);
  return {
    totalConsumption: d.total_building_consumption,
    totalPvGeneration: d.total_pv_generation,
    selfConsumptionRatio: d.self_consumption_ratio,
    surplusRatio: d.surplus_pv_ratio,
    activeTenants: d.active_tenants,
    dataQualityAlerts: d.data_quality_alerts,
  };
}

export async function fetchBuildingTimeseries(
  granularity: string,
  start?: string,
  end?: string
): Promise<TimeSeriesPoint[]> {
  const params = new URLSearchParams({ granularity });
  if (start) params.set("start_date", start);
  if (end) params.set("end_date", end);
  const list = await apiGet<BuildingPointDto[]>(`/api/timeseries/building?${params.toString()}`);
  return list.map((p) => ({
    date: p.date,
    buildingConsumption: p.building_consumption,
    pvGeneration: p.pv_generation,
    selfConsumed: p.self_consumed_pv,
    surplus: p.surplus_pv,
  }));
}

export async function fetchTenantsComparison(start?: string, end?: string): Promise<TenantComparisonDto[]> {
  const params = start && end ? `?start_date=${encodeURIComponent(start)}&end_date=${encodeURIComponent(end)}` : "";
  return apiGet<TenantComparisonDto[]>(`/api/tenants/comparison${params}`);
}

export async function fetchTenantTimeseries(
  tenantId: string,
  start?: string,
  end?: string
): Promise<{ date: string; consumption: number }[]> {
  const params = start && end ? `?start_date=${encodeURIComponent(start)}&end_date=${encodeURIComponent(end)}` : "";
  return apiGet<TenantTimeseriesPointDto[]>(
    `/api/tenants/timeseries/${encodeURIComponent(tenantId)}${params}`
  );
}

/** Build full TenantData[]: comparison + timeseries for each tenant, colors assigned. */
export async function fetchTenants(start?: string, end?: string): Promise<TenantData[]> {
  const comparison = await fetchTenantsComparison(start, end);
  const timeseriesByTenant = await Promise.all(
    comparison.map((t) => fetchTenantTimeseries(t.tenant_id, start, end))
  );
  return comparison.map((t, idx) => ({
    id: t.tenant_id,
    name: t.tenant_id,
    unit: t.tenant_id,
    totalConsumption: t.total_consumption,
    avgDailyConsumption: t.average_daily_consumption,
    avgWeeklyConsumption: t.average_weekly_consumption,
    activeDays: t.active_days,
    color: TENANT_COLORS[idx % TENANT_COLORS.length],
    timeSeries: timeseriesByTenant[idx].map((p) => ({ date: p.date, consumption: p.consumption })),
  }));
}

export async function fetchSharing(start?: string, end?: string): Promise<TenantAllocation[]> {
  const params = start && end ? `?start_date=${encodeURIComponent(start)}&end_date=${encodeURIComponent(end)}` : "";
  const list = await apiGet<SharingTenantDto[]>(`/api/sharing${params}`);
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

function mapIssueType(t: string): DataQualityIssueType {
  if (t === "negative_delta" || t === "missing_days" || t === "tenant_building_mismatch") return t;
  return "negative_delta";
}

export async function fetchQuality(): Promise<{
  entries: DataQualityEntry[];
  alerts: DataQualityAlert[];
  missingTenants: string[];
  breakdown: QualityAlertBreakdown;
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
  const mismatchCount =
    d.consistency_checks.find((c) => c.name === "tenant_building_mismatch")?.count ?? 0;
  const breakdown: QualityAlertBreakdown = {
    negativeDeltas: d.negative_deltas,
    missingDays: d.missing_days,
    mismatchCount,
  };
  const alerts: DataQualityAlert[] = d.issues.map((i, idx) => ({
    id: `q-${i.id}-${idx}`,
    issueType: mapIssueType(i.issue_type),
    meterId: i.meter_id ?? null,
    date: i.date ?? null,
    severity: mapSeverity(i.severity),
    message: i.message,
    detail: i.message,
  }));
  return { entries, alerts, missingTenants: d.missing_tenants ?? [], breakdown };
}
