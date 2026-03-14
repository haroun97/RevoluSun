"""REST API routes."""
from fastapi import APIRouter, Depends, HTTPException
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
    get_latest_batch_id,
    summary_from_db,
    building_timeseries,
    tenants_comparison,
    tenant_timeseries,
    sharing_aggregates,
    quality_from_db,
)

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


@router.get("/summary", response_model=SummaryResponse)
def summary(db: Session = Depends(get_db)):
    """KPI summary from persisted tables."""
    data = summary_from_db(db)
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
    db: Session = Depends(get_db),
):
    """Building and PV time series (daily)."""
    points = building_timeseries(db, get_latest_batch_id(db), granularity)
    return [BuildingTimeseriesPoint(**p) for p in points]


@router.get("/tenants/comparison", response_model=list[TenantComparisonItem])
def tenants_comparison_route(db: Session = Depends(get_db)):
    """Per-tenant comparison metrics."""
    items = tenants_comparison(db, get_latest_batch_id(db))
    return [TenantComparisonItem(**x) for x in items]


@router.get("/tenants/timeseries/{tenant_id}", response_model=list[TenantTimeseriesPoint])
def tenant_timeseries_route(tenant_id: str, db: Session = Depends(get_db)):
    """Time series for one tenant."""
    points = tenant_timeseries(db, tenant_id, get_latest_batch_id(db))
    return [TenantTimeseriesPoint(**p) for p in points]


@router.get("/sharing", response_model=list[SharingTenantItem])
def sharing(db: Session = Depends(get_db)):
    """Energy sharing aggregates per tenant."""
    items = sharing_aggregates(db, get_latest_batch_id(db))
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
            issues=[],
        )
    issues = [QualityIssueItem(**i) for i in data["issues"]]
    return QualityResponse(
        negative_deltas=data["negative_deltas"],
        missing_days=data["missing_days"],
        coverage_ranges=data["coverage_ranges"],
        consistency_checks=data["consistency_checks"],
        issues=issues,
    )
