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

export interface DataQualityAlert {
  id: string;
  severity: 'info' | 'warning' | 'error';
  message: string;
  detail: string;
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
export type TenantComparisonView = 'total' | 'average' | 'activeDays';
