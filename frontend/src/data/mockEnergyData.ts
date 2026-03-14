import type { TimeSeriesPoint, TenantData, TenantAllocation, DataQualityEntry, DataQualityAlert, KpiData } from '@/types/energy';

const TENANT_COLORS = ['#3E8F87', '#F2B544', '#7ED3C1', '#E07A5F', '#5B8C5A', '#8B7EC8'];

function generateTimeSeries(): TimeSeriesPoint[] {
  const points: TimeSeriesPoint[] = [];
  const startDate = new Date('2024-06-01');
  
  for (let i = 0; i < 90; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];
    
    const month = date.getMonth();
    const isSummer = month >= 5 && month <= 7;
    const dayOfWeek = date.getDay();
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    
    // Building consumption: 80-160 kWh/day, higher on weekdays
    const baseConsumption = isSummer ? 95 : 120;
    const weekdayFactor = isWeekend ? 0.75 : 1.1;
    const buildingConsumption = Math.round((baseConsumption + (Math.random() - 0.5) * 40) * weekdayFactor * 10) / 10;
    
    // PV generation: 20-80 kWh/day, peaks in summer, with some cloudy days
    const basePv = isSummer ? 55 : 35;
    const cloudFactor = Math.random() > 0.2 ? 1 : 0.3;
    const pvGeneration = Math.round(Math.max(0, (basePv + (Math.random() - 0.3) * 30) * cloudFactor) * 10) / 10;
    
    const selfConsumed = Math.round(Math.min(pvGeneration, buildingConsumption * (0.6 + Math.random() * 0.25)) * 10) / 10;
    const surplus = Math.round(Math.max(0, pvGeneration - selfConsumed) * 10) / 10;
    
    points.push({ date: dateStr, buildingConsumption, pvGeneration, selfConsumed, surplus });
  }
  
  return points;
}

function generateTenants(): TenantData[] {
  const names = [
    { name: 'Schmidt, A.', unit: '1A' },
    { name: 'Müller, K.', unit: '1B' },
    { name: 'Weber, M.', unit: '2A' },
    { name: 'Fischer, L.', unit: '2B' },
    { name: 'Wagner, T.', unit: '3A' },
    { name: 'Becker, S.', unit: '3B' },
  ];
  
  const startDate = new Date('2024-06-01');
  
  return names.map((t, idx) => {
    const baseDaily = 8 + Math.random() * 18;
    const activeDays = 82 + Math.floor(Math.random() * 8);
    const timeSeries: { date: string; consumption: number }[] = [];
    let totalConsumption = 0;
    
    for (let i = 0; i < 90; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      const dateStr = date.toISOString().split('T')[0];
      const isActive = i < activeDays;
      const consumption = isActive ? Math.round((baseDaily + (Math.random() - 0.5) * baseDaily * 0.5) * 10) / 10 : 0;
      totalConsumption += consumption;
      timeSeries.push({ date: dateStr, consumption });
    }
    
    return {
      id: `tenant-${idx + 1}`,
      name: t.name,
      unit: t.unit,
      totalConsumption: Math.round(totalConsumption),
      avgDailyConsumption: Math.round((totalConsumption / activeDays) * 10) / 10,
      activeDays,
      color: TENANT_COLORS[idx],
      timeSeries,
    };
  });
}

function generateAllocations(tenants: TenantData[], totalPv: number): TenantAllocation[] {
  const totalDemand = tenants.reduce((s, t) => s + t.totalConsumption, 0);
  
  return tenants.map(t => {
    const share = t.totalConsumption / totalDemand;
    const pvAllocated = Math.round(Math.min(t.totalConsumption, totalPv * share));
    const gridImport = t.totalConsumption - pvAllocated;
    const selfSufficiency = Math.round((pvAllocated / t.totalConsumption) * 1000) / 10;
    
    return {
      tenantId: t.id,
      tenantName: t.name,
      unit: t.unit,
      totalDemand: t.totalConsumption,
      pvAllocated,
      gridImport,
      selfSufficiency,
    };
  });
}

function generateDataQuality(): { entries: DataQualityEntry[]; alerts: DataQualityAlert[] } {
  const entries: DataQualityEntry[] = [
    { meterId: 'BLD-001', meterName: 'Building Main', type: 'building', activeDays: 89, totalDays: 90, coverage: 98.9, gaps: 1, anomalies: 0, status: 'good' },
    { meterId: 'PV-001', meterName: 'PV Inverter', type: 'pv', activeDays: 87, totalDays: 90, coverage: 96.7, gaps: 2, anomalies: 1, status: 'good' },
    { meterId: 'T-001', meterName: 'Unit 1A', type: 'tenant', activeDays: 88, totalDays: 90, coverage: 97.8, gaps: 1, anomalies: 0, status: 'good' },
    { meterId: 'T-002', meterName: 'Unit 1B', type: 'tenant', activeDays: 85, totalDays: 90, coverage: 94.4, gaps: 3, anomalies: 1, status: 'warning' },
    { meterId: 'T-003', meterName: 'Unit 2A', type: 'tenant', activeDays: 90, totalDays: 90, coverage: 100, gaps: 0, anomalies: 0, status: 'good' },
    { meterId: 'T-004', meterName: 'Unit 2B', type: 'tenant', activeDays: 86, totalDays: 90, coverage: 95.6, gaps: 2, anomalies: 0, status: 'good' },
    { meterId: 'T-005', meterName: 'Unit 3A', type: 'tenant', activeDays: 82, totalDays: 90, coverage: 91.1, gaps: 5, anomalies: 2, status: 'warning' },
    { meterId: 'T-006', meterName: 'Unit 3B', type: 'tenant', activeDays: 89, totalDays: 90, coverage: 98.9, gaps: 1, anomalies: 0, status: 'good' },
  ];
  
  const alerts: DataQualityAlert[] = [
    { id: 'a1', severity: 'warning', message: '3 negative delta readings detected', detail: 'Unit 1B meter showed negative consumption deltas on Jun 15, Jul 2, Jul 18. Likely meter reset or communication error.' },
    { id: 'a2', severity: 'info', message: '2 missing days on PV inverter', detail: 'No data received from PV inverter on Jun 22 and Jul 10. Possibly maintenance downtime.' },
    { id: 'a3', severity: 'warning', message: 'Tenant sum deviates from building total', detail: 'On 4 days, the sum of tenant meters deviated >5% from building main meter. Common area consumption may not be metered.' },
    { id: 'a4', severity: 'info', message: 'Unit 3A has lowest coverage (91.1%)', detail: '5 gap days detected. Meter communication issues suspected. Data interpolation applied for allocation model.' },
  ];
  
  return { entries, alerts };
}

// Generate and cache data
const timeSeries = generateTimeSeries();
const tenants = generateTenants();
const totalPv = Math.round(timeSeries.reduce((s, p) => s + p.pvGeneration, 0));
const totalConsumption = Math.round(timeSeries.reduce((s, p) => s + p.buildingConsumption, 0));
const totalSelfConsumed = Math.round(timeSeries.reduce((s, p) => s + p.selfConsumed, 0));
const totalSurplus = Math.round(timeSeries.reduce((s, p) => s + p.surplus, 0));
const allocations = generateAllocations(tenants, totalPv);
const { entries: dataQualityEntries, alerts: dataQualityAlerts } = generateDataQuality();

export const mockTimeSeries = timeSeries;
export const mockTenants = tenants;
export const mockAllocations = allocations;
export const mockDataQualityEntries = dataQualityEntries;
export const mockDataQualityAlerts = dataQualityAlerts;

export const mockKpi: KpiData = {
  totalConsumption,
  totalPvGeneration: totalPv,
  selfConsumptionRatio: Math.round((totalSelfConsumed / totalPv) * 1000) / 10,
  surplusRatio: Math.round((totalSurplus / totalPv) * 1000) / 10,
  activeTenants: tenants.length,
  dataQualityAlerts: dataQualityAlerts.length,
};
