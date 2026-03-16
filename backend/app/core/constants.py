"""Domain constants and helpers for tenant/meter metadata."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


def _tenant_config_path() -> Path:
    """Location of tenant configuration (per-dataset, outside of code).

    The file is expected to be a JSON object with:

      { "expected_tenants": ["Kunde1", "Kunde2", ...] }

    If the file is missing or invalid, we fall back to an empty list
    (meaning no missing-tenant detection).
    """
    # backend/app/core/constants.py -> backend/app/core -> backend/app -> backend
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root.parent / "document" / "tenant_config.json"


@lru_cache(maxsize=1)
def expected_tenant_ids() -> list[str]:
    """Return the configured expected tenant IDs for this dataset.

    This is loaded from `document/tenant_config.json` so that the list
    is configurable per project/dataset and not hard-coded in code.
    """
    path = _tenant_config_path()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []
    tenants = data.get("expected_tenants", [])
    return [t for t in tenants if isinstance(t, str) and t.strip()]


# Backwards-compatible alias used in tests and existing code
EXPECTED_TENANT_IDS = expected_tenant_ids()


def get_missing_tenant_ids(present_tenant_ids: list[str]) -> list[str]:
    """Return expected tenant IDs that have no data.

    Expected tenants come from configuration (`tenant_config.json`),
    so this works for arbitrary tenant naming schemes and datasets.
    """
    expected = set(expected_tenant_ids())
    if not expected:
        return []
    present_set = {t for t in present_tenant_ids if t}
    return sorted(expected - present_set)


def tenant_id_sort_key(tenant_id: str | None) -> tuple[int, int]:
    """Sort key for natural Kunde order: Kunde1, Kunde2, ..., Kunde9, Kunde10, ...
    Returns (0, n) for KundeN, (1, 0) for other/empty so Kunde* comes first in natural order."""
    if not tenant_id or not isinstance(tenant_id, str):
        return (1, 0)
    s = tenant_id.strip()
    if s.startswith("Kunde"):
        try:
            n = int(s[5:])
            return (0, n)
        except ValueError:
            pass
    return (1, 0)


def canonical_tenant_id(tenant_id: str | None) -> str:
    """Normalize tenant_id so Kunde01 and Kunde1 both become Kunde1 (for deduplication)."""
    if not tenant_id or not isinstance(tenant_id, str):
        return tenant_id or ""
    s = tenant_id.strip()
    if s.startswith("Kunde"):
        try:
            n = int(s[5:])
            return f"Kunde{n}"
        except ValueError:
            pass
    return s


def coverage_entry_sort_key(entry: dict) -> tuple[int, int, str]:
    """Sort key for meter coverage: building_total first, then pv, then tenants Kunde1..Kunde13.
    Returns (type_order, kunde_num, meter_id). type_order: 0=building, 1=pv, 2=tenant."""
    meter_id = (entry.get("meter_id") or "").strip()
    meter_type = (entry.get("meter_type") or "").strip()
    if meter_id == "building_total" or meter_type == "building_total":
        return (0, 0, meter_id)
    if meter_id == "pv" or meter_type == "pv":
        return (1, 0, meter_id)
    # tenant (KundeN)
    if meter_id.startswith("Kunde"):
        try:
            n = int(meter_id[5:])
            return (2, n, meter_id)
        except ValueError:
            pass
    return (2, 999, meter_id)
