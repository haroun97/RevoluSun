# Investigation: Remaining Dashboard Issues (No Implementation)

**Date:** 2026-03-15  
**Scope:** Remaining issues identified earlier (average weekly, tenant trend sampling, data quality UX, empty states, self-consumption vs self-sufficiency, Data Alerts breakdown). Investigation only; no code changes.

---

## 1. Average weekly consumption (normalized tenant metric)

**Status:** Not implemented.

**Current state:**
- **Backend:** `tenants_comparison()` returns `total_consumption`, `average_daily_consumption`, `active_days`. No `average_weekly_consumption`.
- **Frontend:** Tenant comparison chart and TenantInsights use `avgDailyConsumption`; no weekly metric.
- **Documentation:** `data_solution.md` lists "average daily consumption" and "average weekly consumption" as normalized metrics for fair comparison.

**Findings:**
- Average weekly could be derived as `average_daily_consumption * 7` (or a dedicated weekly aggregate). It would live in the same tenant-comparison API and table.
- No bug; it is a documented but unimplemented feature. Impact: users cannot compare tenants in "kWh per week" without mental math.

---

## 2. Tenant trend chart: "every 3 days" sampling

**Status:** Implemented as client-side sampling only.

**Current state:**
- **Backend:** Returns **daily** tenant timeseries (one point per day per tenant). No weekly/monthly aggregation for tenants.
- **Frontend:** `TenantTrendChart.tsx` builds a merged series from all tenants' `timeSeries`, then **filters** with `.filter((_, i) => i % 3 === 0)` (every 3rd point). Subtitle says "sampled every 3 days."

**Findings:**
- Sampling is by **array index**, not by calendar (e.g. "every 3rd day" in the sorted list). So if there are gaps in dates, "every 3 days" is not strictly every 3 calendar days.
- For long ranges (e.g. full period), the chart can still have many points and feel dense; for short ranges it may show very few points.
- Optional improvement (not implemented): when range is long, aggregate tenant consumption by week on the backend and show one point per week. Would require a new API or parameter.

---

## 3. Data Quality: Coverage vs Anomalies

**Status:** Definitions are in code but not explained in the UI.

**Current state:**
- **Backend** (`quality_from_db`):
  - **Coverage:** `active_days / total_days * 100`, where `total_days = (max_date - min_date) + 1` and `active_days` = count of rows in `daily_meter_consumption` for that meter. So "coverage" = share of days in the meter’s date range that have **at least one row** (any value, including invalid).
  - **Anomalies:** Count of `DataQualityIssue` rows with `issue_type == "negative_delta"` and that `meter_id`. So a day with a negative delta is still an "active day" but also an "anomaly."
- **Frontend:** Table shows Meter, Type, Coverage (%), Active (e.g. 478/564), Gaps, Anomalies, Status. No tooltip or text explaining that "Coverage = data present" and "Anomalies = invalid (e.g. negative) deltas."

**Findings:**
- A meter can have high coverage (e.g. 84.8%) and many anomalies (e.g. 383). That is correct: data is *present* but often *invalid*. Users might assume "coverage" means "good data."
- **Gap:** No in-UI explanation. A short subtitle or tooltip would reduce misinterpretation.

---

## 4. Building–tenant mismatch and missing tenants

**Status:** Missing-tenant note exists; no explicit link to mismatch.

**Current state:**
- **Backend:** Quality check compares building_total daily sum vs sum of tenant daily sums (valid deltas only). If difference > 5%, creates `tenant_building_mismatch` issue. `missing_tenants` is returned separately in the quality response.
- **Frontend:** When `missingTenants.length > 0`, Data Quality shows: "Tenants not in dataset: Kunde7" and the exclusion note. Mismatch alerts are shown in the same alerts list as "Negative or invalid delta…" with no distinction that some alerts are "tenant sum vs building" and that the gap can be due to missing tenants (e.g. Kunde7).

**Findings:**
- Logic is correct. UX gap: when there are both `missing_tenants` and `tenant_building_mismatch` alerts, the UI does not state that "Difference may be due to missing tenants (see list above)."

---

## 5. Empty and edge states

**Current state:**
- **Loading / Error:** Dashboard shows a full-page loading spinner and a clear error message if the API fails. Good.
- **Empty data:** Charts receive `data={timeSeries}` or `tenants={tenants}` etc. If the selected date range has no data, the API returns empty arrays. Charts (BuildingVsPvChart, PvUsageChart, TenantTrendChart, EnergySharingChart) render with `data=[]` or empty series. Recharts renders an empty axes/area; there is **no** "No data for this period" or "Adjust date range" message.
- **Zero PV:** When `pv_total` is 0, backend sets `self_consumption_ratio` and `surplus_ratio` to 0. Frontend shows "0%"; no extra note that this means "no PV generation in period."

**Findings:**
- Empty charts are technically correct but not self-explanatory. A short empty state (e.g. "No data for the selected period" or "Try a different date range") would improve UX.
- Zero-PV case is handled; optional improvement is a one-line note when ratio is 0.

---

## 6. Self-consumption (0.34%) vs tenant self-sufficiency (100%)

**Status:** Logic is consistent; the apparent contradiction is due to date overlap.

**Definitions in code:**
- **Building self-consumption ratio:** `self_consumed / pv_total * 100`, where `self_consumed` = sum of `DailyEnergySharing.allocated_pv_kwh` over the **selected date range**, and `pv_total` = sum of valid PV `delta_kwh` over the **same range**.
- **Tenant self-sufficiency:** Per tenant, `allocated_pv / demand * 100` over the selected range. So each tenant’s share of demand met by allocated PV.

**When is allocation created?**
- In `run_sharing()`, we iterate over **dates in `pv_daily.index`** (dates with valid PV). For each such date we need **tenant_daily.loc[d]** (at least one tenant with valid data on that date). If there is no tenant data for that date, we `continue` and **do not create any sharing row for that day**.
- So **allocation exists only on dates where both (1) PV has valid data and (2) at least one tenant has valid data.** That is the **intersection** of PV dates and tenant dates.

**Why 0.34% vs 100%?**
- **pv_total** (and building_total) are summed over **all** days in the selected range that have valid PV (or building) data.
- **self_consumed** = sum(allocated_pv) is summed only over days that have **both** PV and tenant data.
- If in the selected range there are many days with PV but **few days with any tenant data** (e.g. tenants started later, or different coverage), then:
  - `pv_total` = large (e.g. 149 MWh over 90 days of PV).
  - `self_consumed` = sum of allocation on the few overlapping days (e.g. 0.5 MWh).
  - So **self_consumption_ratio** = 0.5 / 149 ≈ 0.34%.
- On those **few overlapping days**, allocation is proportional: if that day’s PV ≥ that day’s total demand, we allocate 100% of demand to PV, so **grid_import = 0** and **self_sufficiency = 100%** for each tenant on that day. Aggregated over the range, if most of each tenant’s demand falls on such days, we get **~100% self-sufficiency** per tenant.

**Conclusion:** We are not double-counting or mis-defining. The building ratio is "allocated PV as % of total PV in range"; the tenant ratio is "allocated PV as % of that tenant’s demand in range." Low overlap (few days with both PV and tenant data) makes the first small and can keep the second high. Optional improvement: show in the UI how many days in the range had allocation (e.g. "Allocation on N days") so the 0.34% is less surprising.

**Empirical run (script: `backend/scripts/investigate_self_consumption_vs_sufficiency.py`, 30-day range 2026-02-05 to 2026-03-06):**
- **PV (valid only):** 7 distinct dates in range; sum `delta_kwh` (pv_total) = **149,146.70 kWh** (very large daily PV values on those 7 days).
- **Tenants (valid only):** 30 distinct dates with at least one tenant; total tenant demand in range = **2,128.77 kWh**.
- **Overlap:** 7 dates have both PV and tenant data → sharing rows exist only for these 7 days.
- **DailyEnergySharing (in range):** 7 days; sum `allocated_pv_kwh` (self_consumed) = **506.93 kWh**; sum `tenant_demand_kwh` = 506.93 kWh; `grid_import_kwh` = 0.
- **Building self-consumption:** 506.93 / 149,146.70 × 100 = **0.34%** (matches dashboard).
- **Per-tenant:** On the 7 allocation days, demand equals allocated PV for each tenant → **self_sufficiency = 100%** for all tenants in range.

So the denominator (pv_total) is dominated by the 7 days’ very high PV sums, while the numerator (self_consumed) is only what was allocated to tenants on those same 7 days; on those days allocation covered 100% of demand, hence 100% tenant self-sufficiency.

---

## 7. Data Alerts (844): no breakdown

**Current state:**
- **Backend:** `summary_from_db()` returns `data_quality_alerts` = total count of `DataQualityIssue` rows for the batch (no date filter). The `/api/quality` endpoint returns `issues` (list with `issue_type`, `message`, etc.) and summary counts (`negative_deltas`, `missing_days`, `consistency_checks`).
- **Frontend:** KPI card shows "Data Alerts: 844" and "Quality notices." The Data Quality section shows the alerts list (many cards) and the coverage table, but the **KPI does not break down** the 844 (e.g. "Negative deltas: 688, Missing days: X, Mismatch: Y").

**Findings:**
- The information exists in the API (`/api/quality` has `negative_deltas`, `missing_days`, `consistency_checks`). The dashboard does not surface this breakdown in the KPI or in a short summary. Users see a single number and must scroll to the full list to understand what the 844 are.

**Gap in frontend API layer:** `fetchQuality()` returns only `{ entries, alerts, missingTenants }`. It does **not** pass through `negative_deltas`, `missing_days`, or `consistency_checks` from the API response, so the breakdown is never available in the UI even though the backend sends it.

---

### Deep investigation: best UX for Data Alerts (data analyst + data engineer + full-stack + frontend)

**User problem:** A single number (e.g. 844) with no context forces users to scroll through hundreds of alert cards to understand what’s wrong. Heavy dominance of one type (e.g. negative deltas) makes the list repetitive and hard to act on.

**Data model (backend):**
- Alert types: `negative_delta` (invalid daily consumption change), `missing_days` (gaps in coverage), `tenant_building_mismatch` (tenant sum ≠ building).
- `/api/quality` already returns: `negative_deltas`, `missing_days`, `consistency_checks` (e.g. `[{ name: "tenant_building_mismatch", count: N }]`), plus `issues[]`, `coverage_ranges[]`, `missing_tenants[]`.
- Total alerts = sum of these counts (backend uses total count for summary KPI).

**Recommended UX (no implementation):**

1. **Expose breakdown in the frontend**
   - Have `fetchQuality()` return the breakdown: `negative_deltas`, `missing_days`, and either a single `mismatchCount` or the first element of `consistency_checks` (tenant_building_mismatch). Add a small type (e.g. `QualitySummary` or extend the existing return type) so the Data Quality section and optionally the KPI can consume it.

2. **KPI card: at-a-glance breakdown**
   - **Preferred:** Keep the KPI value (e.g. "844") and change the subtitle from "Quality notices" to a **one-line breakdown**, e.g.  
     `688 invalid deltas · 12 gaps · 5 mismatch`  
     so the card is self-explanatory without a click. If space is tight, use a tooltip on the card that shows the same breakdown (e.g. "Negative deltas: 688, Missing days: 12, Tenant–building mismatch: 5").
   - **Alternative:** Add a small expandable section under the number (e.g. "See breakdown") that reveals the three counts. Slightly more discoverable but adds interaction.

3. **Data Quality section: summary strip above the table**
   - Add a **short breakdown strip** directly under the section header (or under the optional "Coverage = … ; Anomalies = …" line): e.g. chips or badges:  
     `[Invalid deltas: 688] [Missing days: 12] [Mismatch: 5]`  
     with consistent wording (e.g. "Invalid deltas" = negative_delta, "Missing days" = gaps, "Mismatch" = tenant_building_mismatch). This gives users an immediate summary before they see the Meter Coverage Overview table and the long alerts list.

4. **Terminology and clarity**
   - Use one consistent set of terms and optionally a single short definition (e.g. in the section subtitle or a tooltip):  
     - **Invalid deltas** = days where consumption delta was negative or invalid (excluded from totals).  
     - **Missing days** = gaps in the time series (no data).  
     - **Mismatch** = tenant total vs building total inconsistency (e.g. due to missing tenants).  
   - This reduces confusion between "Anomalies" in the table (per meter) and "Invalid deltas" in the alert breakdown (same concept, building-wide count).

5. **Optional: filter alerts list by type**
   - Allow filtering the alert cards by type (e.g. tabs or dropdown: "All" | "Invalid deltas" | "Missing days" | "Mismatch") so users can focus on one category when one type dominates (e.g. 688 negative deltas). Reduces scroll and cognitive load; implementation can use existing `issue_type` on each alert.

6. **Mobile and accessibility**
   - Breakdown in the KPI: on small screens use a single line of text or stacked chips; avoid horizontal scroll. Ensure the breakdown is available to screen readers (e.g. as part of the card label or aria-describedby).
   - Summary strip: same — one line or wrap; keep touch targets adequate for chips if used.

7. **Link to missing tenants**
   - When both `missing_tenants` and mismatch count are non-zero, add one sentence in the Data Quality section (e.g. near the breakdown or the missing-tenant note): "Difference in tenant vs building totals may be due to missing tenants (e.g. Kunde7)." This ties the "Mismatch" number to an actionable cause.

**Summary of changes (conceptual):**
- **API consumer:** Return `negative_deltas`, `missing_days`, `mismatchCount` (or `consistency_checks`) from `fetchQuality()`.
- **KPI:** Subtitle or tooltip with the three counts; keep total number.
- **Data Quality section:** Breakdown strip (chips or one line) under the header; consistent terminology; optional filter on alerts list; optional sentence linking mismatch to missing tenants.

---

## 8. Summary table

| Issue | Current state | Root cause / finding |
|-------|----------------|----------------------|
| Average weekly consumption | Not in API or UI | Documented feature not implemented; can be derived from average daily × 7. |
| Tenant trend sampling | Client-side every 3rd index | Works; "every 3 days" is by index not strict calendar; long ranges can be dense. |
| Coverage vs anomalies | No in-UI definition | Coverage = days with data; anomalies = negative-delta days. High coverage + high anomalies is possible. |
| Mismatch + missing tenants | No link in UI | Missing-tenant note exists; no sentence linking mismatch to "e.g. Kunde7." |
| Empty charts | Empty axes, no message | No "No data for this period" or "Try another range." |
| Zero PV | 0% shown | Correct; optional note "No PV in period" could help. |
| Self-consumption 0.34% vs 100% tenant | Logic correct | Few overlapping days (PV + tenant) → low building ratio; on those days allocation can be 100% → high tenant self-sufficiency. |
| Data Alerts 844 | Single number only | Breakdown (negative_deltas, missing_days, mismatch) exists in API but not shown in KPI/summary. |

---

## 9. Conclusion

- No bugs found in the logic; remaining items are **missing features**, **UX clarity** (definitions, empty state, alert breakdown), and **optional copy** (mismatch ↔ missing tenants, allocation days).
- Implementing the above would improve clarity and completeness but is not required for correctness.
