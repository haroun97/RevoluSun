"""Pydantic response models for API."""
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


# --- Health ---
class HealthResponse(BaseModel):
    status: str
    database: str


# --- Summary ---
class SummaryResponse(BaseModel):
    total_building_consumption: float
    total_pv_generation: float
    self_consumption_ratio: float
    surplus_pv_ratio: float
    active_tenants: int
    data_quality_alerts: int


# --- Timeseries building ---
class BuildingTimeseriesPoint(BaseModel):
    date: str
    building_consumption: float
    pv_generation: float
    self_consumed_pv: float
    surplus_pv: float


# --- Tenants comparison ---
class TenantComparisonItem(BaseModel):
    tenant_id: str
    total_consumption: float
    average_daily_consumption: float
    average_weekly_consumption: float
    active_days: int


# --- Tenant timeseries ---
class TenantTimeseriesPoint(BaseModel):
    date: str
    consumption: float


# --- Sharing ---
class SharingTenantItem(BaseModel):
    tenant_id: str
    demand: float
    allocated_pv: float
    grid_import: float
    self_sufficiency_ratio: float


# --- Quality ---
class QualityIssueItem(BaseModel):
    id: int
    issue_type: str
    meter_id: str | None
    tenant_id: str | None
    date: str | None
    severity: str
    message: str


class QualityResponse(BaseModel):
    negative_deltas: int
    missing_days: int
    coverage_ranges: list[dict[str, Any]]
    consistency_checks: list[dict[str, Any]]
    missing_tenants: list[str]
    issues: list[QualityIssueItem]
