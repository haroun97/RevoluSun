/**
 * Types used by the dashboard for KPIs, charts, and data quality.
 * API responses are mapped to these shapes in api/energyApi.ts.
 */

export interface TimeSeriesPoint {
  date: string;
  buildingConsumption: number;
  pvGeneration: number;
  selfConsumed: number;
  surplus: number;
}

export interface TenantData {
  id: string;
  name: string;
  unit: string;
  totalConsumption: number;
  avgDailyConsumption: number;
  avgWeeklyConsumption: number;
  activeDays: number;
  color: string;
  timeSeries: { date: string; consumption: number }[];
}

export interface TenantAllocation {
  tenantId: string;
  tenantName: string;
  unit: string;
  totalDemand: number;
  pvAllocated: number;
  gridImport: number;
  selfSufficiency: number;
}

export interface DataQualityEntry {
  meterId: string;
  meterName: string;
  type: 'building' | 'pv' | 'tenant';
  activeDays: number;
  totalDays: number;
  coverage: number;
  gaps: number;
  anomalies: number;
  status: 'good' | 'warning' | 'critical';
}

export type DataQualityIssueType = 'negative_delta' | 'missing_days' | 'tenant_building_mismatch';

export interface DataQualityAlert {
  id: string;
  issueType: DataQualityIssueType;
  meterId: string | null;
  date: string | null;
  severity: 'info' | 'warning' | 'error';
  message: string;
  detail: string;
}

export interface QualityAlertBreakdown {
  negativeDeltas: number;
  missingDays: number;
  mismatchCount: number;
}

export interface KpiData {
  totalConsumption: number;
  totalPvGeneration: number;
  selfConsumptionRatio: number;
  surplusRatio: number;
  activeTenants: number;
  dataQualityAlerts: number;
}

export type Granularity = 'daily' | 'weekly' | 'monthly';
export type TenantComparisonView = 'total' | 'average' | 'weekly' | 'activeDays';
