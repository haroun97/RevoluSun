"""Domain constants: expected tenant set for missing-tenant detection and sort order."""

# Case study: tenant meters are Kunde1–Kunde13; Kunde7 may be absent from the workbook.
# Used to compute which expected tenants have no data (e.g. Kunde7).
EXPECTED_TENANT_IDS = [
    "Kunde1",
    "Kunde2",
    "Kunde3",
    "Kunde4",
    "Kunde5",
    "Kunde6",
    "Kunde7",
    "Kunde8",
    "Kunde9",
    "Kunde10",
    "Kunde11",
    "Kunde12",
    "Kunde13",
]


def get_missing_tenant_ids(present_tenant_ids: list[str]) -> list[str]:
    """Return expected tenant IDs that have no data (e.g. Kunde7 when sheet is absent)."""
    present_set = {t for t in present_tenant_ids if t}
    return sorted(set(EXPECTED_TENANT_IDS) - present_set)


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
