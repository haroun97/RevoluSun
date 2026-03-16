"""REST API routes."""
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.responses import (
    BuildingTimeseriesPoint,
    HealthResponse,
    QualityIssueItem,
    QualityResponse,
    SharingTenantItem,
    SummaryResponse,
    TenantComparisonItem,
    TenantTimeseriesPoint,
)
from app.services.analytics import (
    get_date_range,
    get_latest_batch_id,
    summary_from_db,
    building_timeseries,
    tenants_comparison,
    tenant_timeseries,
    sharing_aggregates,
    quality_from_db,
)


def _parse_date(s: str | None) -> date | None:
    if not s or not s.strip():
        return None
    try:
        return date.fromisoformat(s.strip())
    except ValueError:
        return None

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    """Health check and DB connectivity."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return HealthResponse(status="ok", database=db_status)


@router.get("/date-range")
def date_range(db: Session = Depends(get_db)):
    """Min and max date for the latest batch (for default range in UI)."""
    batch_id = get_latest_batch_id(db)
    if batch_id is None:
        return {"min_date": None, "max_date": None}
    min_d, max_d = get_date_range(db, batch_id)
    return {"min_date": min_d.isoformat() if min_d else None, "max_date": max_d.isoformat() if max_d else None}


@router.get("/summary", response_model=SummaryResponse)
def summary(
    start_date: Annotated[str | None, Query(description="ISO date")] = None,
    end_date: Annotated[str | None, Query(description="ISO date")] = None,
    db: Session = Depends(get_db),
):
    """KPI summary from persisted tables (optionally filtered by date range)."""
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    data = summary_from_db(db, start_date=start, end_date=end)
    if data is None:
        return SummaryResponse(
            total_building_consumption=0,
            total_pv_generation=0,
            self_consumption_ratio=0,
            surplus_pv_ratio=0,
            active_tenants=0,
            data_quality_alerts=0,
        )
    return SummaryResponse(**data)


@router.get("/timeseries/building", response_model=list[BuildingTimeseriesPoint])
def timeseries_building(
    granularity: str = "daily",
    start_date: Annotated[str | None, Query(description="ISO date")] = None,
    end_date: Annotated[str | None, Query(description="ISO date")] = None,
    db: Session = Depends(get_db),
):
    """Building and PV time series (daily, weekly, or monthly)."""
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    points = building_timeseries(db, get_latest_batch_id(db), granularity, start_date=start, end_date=end)
    return [BuildingTimeseriesPoint(**p) for p in points]


@router.get("/tenants/comparison", response_model=list[TenantComparisonItem])
def tenants_comparison_route(
    start_date: Annotated[str | None, Query(description="ISO date")] = None,
    end_date: Annotated[str | None, Query(description="ISO date")] = None,
    db: Session = Depends(get_db),
):
    """Per-tenant comparison metrics (optionally filtered by date range)."""
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    items = tenants_comparison(db, get_latest_batch_id(db), start_date=start, end_date=end)
    return [TenantComparisonItem(**x) for x in items]


@router.get("/tenants/timeseries/{tenant_id}", response_model=list[TenantTimeseriesPoint])
def tenant_timeseries_route(
    tenant_id: str,
    start_date: Annotated[str | None, Query(description="ISO date")] = None,
    end_date: Annotated[str | None, Query(description="ISO date")] = None,
    db: Session = Depends(get_db),
):
    """Time series for one tenant (optionally filtered by date range)."""
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    points = tenant_timeseries(db, tenant_id, get_latest_batch_id(db), start_date=start, end_date=end)
    return [TenantTimeseriesPoint(**p) for p in points]


@router.get("/sharing", response_model=list[SharingTenantItem])
def sharing(
    start_date: Annotated[str | None, Query(description="ISO date")] = None,
    end_date: Annotated[str | None, Query(description="ISO date")] = None,
    db: Session = Depends(get_db),
):
    """Energy sharing aggregates per tenant (optionally filtered by date range)."""
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    items = sharing_aggregates(db, get_latest_batch_id(db), start_date=start, end_date=end)
    return [SharingTenantItem(**x) for x in items]


@router.get("/quality", response_model=QualityResponse)
def quality(db: Session = Depends(get_db)):
    """Data quality issues and summary."""
    data = quality_from_db(db, get_latest_batch_id(db))
    if data is None:
        return QualityResponse(
            negative_deltas=0,
            missing_days=0,
            coverage_ranges=[],
            consistency_checks=[],
            missing_tenants=[],
            issues=[],
        )
    issues = [QualityIssueItem(**i) for i in data["issues"]]
    return QualityResponse(
        negative_deltas=data["negative_deltas"],
        missing_days=data["missing_days"],
        coverage_ranges=data["coverage_ranges"],
        consistency_checks=data["consistency_checks"],
        missing_tenants=data["missing_tenants"],
        issues=issues,
    )
