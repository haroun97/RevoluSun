"""
Pydantic models for API responses.

These define the JSON shape returned by each endpoint so the frontend
and API docs get a clear contract. All fields are serialized to JSON.
"""
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


# --- Health ---
class HealthResponse(BaseModel):
    """GET /health: app status and whether the database is reachable."""
    status: str
    database: str


# --- Summary ---
class SummaryResponse(BaseModel):
    """GET /summary: main KPIs (consumption, PV, ratios, tenant count, quality alert count)."""
    total_building_consumption: float
    total_pv_generation: float
    self_consumption_ratio: float
    surplus_pv_ratio: float
    active_tenants: int
    data_quality_alerts: int


# --- Timeseries building ---
class BuildingTimeseriesPoint(BaseModel):
    """One point in the building/PV time series (one day or one week/month)."""
    date: str
    building_consumption: float
    pv_generation: float
    self_consumed_pv: float
    surplus_pv: float


# --- Tenants comparison ---
class TenantComparisonItem(BaseModel):
    """One row in the tenant comparison: totals and averages for one tenant."""
    tenant_id: str
    total_consumption: float
    average_daily_consumption: float
    average_weekly_consumption: float
    active_days: int


# --- Tenant timeseries ---
class TenantTimeseriesPoint(BaseModel):
    """One day's consumption for one tenant (for the trend chart)."""
    date: str
    consumption: float


# --- Sharing ---
class SharingTenantItem(BaseModel):
    """One tenant's energy-sharing result: demand, PV allocated, grid import, self-sufficiency %."""
    tenant_id: str
    demand: float
    allocated_pv: float
    grid_import: float
    self_sufficiency_ratio: float


# --- Quality ---
class QualityIssueItem(BaseModel):
    """One data quality finding (e.g. negative delta, missing day)."""
    id: int
    issue_type: str
    meter_id: str | None
    tenant_id: str | None
    date: str | None
    severity: str
    message: str


class QualityResponse(BaseModel):
    """GET /quality: counts, coverage per meter, missing tenants, and list of issues."""
    negative_deltas: int
    missing_days: int
    coverage_ranges: list[dict[str, Any]]
    consistency_checks: list[dict[str, Any]]
    missing_tenants: list[str]
    issues: list[QualityIssueItem]


# --- Admin: Google Drive import ---
class GoogleDriveImportRequest(BaseModel):
    """POST body: OAuth access token and the Google Drive file id of the spreadsheet."""
    access_token: str
    file_id: str


class GoogleDriveImportResponse(BaseModel):
    """Response after a successful Google Drive import: new batch id and message."""
    batch_id: int
    message: str
