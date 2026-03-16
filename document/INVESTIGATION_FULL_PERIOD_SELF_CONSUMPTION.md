# Investigation: 0.47% Self-Consumption Over Full Period (2 Years)

**Date:** 2026-03-15  
**Scope:** Deep investigation of why the dashboard shows **0.47%** Self-Consumption when "Full period" is selected (2 years of data). Investigation only; no code changes.

---

## 1. How “Full period” is defined

- **Frontend:** The filter preset "Full period" uses `fullDateRange`, which comes from the API `/api/date-range` (or equivalent). That returns the **min and max date** across all rows in `DailyMeterConsumption` for the latest batch.
- **Backend:** `get_date_range(session, batch_id)` returns `(min_date, max_date)` from `DailyMeterConsumption` for that batch. So "Full period" = the entire calendar span of the imported data (e.g. 2024-01-xx to 2026-03-xx for the Nürnberg file).
- **Summary API:** When the user selects Full period, the frontend sends `start_date=min_date`, `end_date=max_date` to `/api/summary`. So `summary_from_db(session, batch_id, start_date=min_date, end_date=max_date)` runs over the **full 2 years**.

There is no artificial restriction to 7 days or any other window. The 0.47% is the ratio computed over this full range.

---

## 2. Formula (unchanged)

From `backend/app/services/analytics.py`:

- **pv_total** = sum of `DailyMeterConsumption.delta_kwh` where `meter_type == "pv"`, `is_valid == True`, and `date` in `[start_date, end_date]` (full period).
- **self_consumed** = sum of `DailyEnergySharing.allocated_pv_kwh` where `date` in `[start_date, end_date]`.
- **self_consumption_ratio** = `self_consumed / pv_total * 100` (and surplus_ratio = 100 - self_consumption_ratio).

So **0.47%** means: over the full period, **0.47% of all valid PV generation** was allocated to tenants (counted as “PV used on-site”); the rest is treated as surplus/export.

---

## 3. Why the ratio is low: same mechanism as 0.34% (30-day window)

The **logic** is the same as for the 30-day window (see `document/INVESTIGATION_REMAINING_ISSUES.md` §6). The only difference is the date range.

### 3.1 Denominator: pv_total over full period

- **pv_total** is the sum of **valid** PV `delta_kwh` for **every day** in the full period that has at least one valid PV row.
- From `INVESTIGATION_NEGATIVE_DELTAS.md`, over the full dataset **PV-Zähler** has **5,509,265 kWh** total when using valid deltas only. So for Full period, **pv_total ≈ 5.5 million kWh** (or the exact value in your DB for the batch).
- Many days from **Nov 2024 onward** have negative deltas, so those days are **excluded** from this sum. So the “valid PV” total is dominated by the **earlier part** of the 2 years (2024 and early 2025) when PV had fewer invalid days, plus whatever valid days remain in the later period. The exact number of “valid PV days” in the full range depends on the batch; it is **not** “all days in 2 years” because of the invalid-delta exclusions.

### 3.2 Numerator: self_consumed over full period

- **self_consumed** = sum of `allocated_pv_kwh` from `DailyEnergySharing` over the same full period.
- Sharing rows are created **only on dates where both**:
  1. There is valid PV for that date (`pv_daily.index` in `run_sharing()`),
  2. There is at least one tenant with valid consumption that date (`tenant_daily.loc[d]` exists; otherwise the code `continue`s and no row is written for that day).

So **allocation exists only on the intersection of “dates with valid PV” and “dates with at least one tenant”**. For the full period, that is every date in the **valid-PV** set that also has tenant data. Tenant data has **no** negative deltas (0 in the source), so tenant coverage spans almost the full 2 years. So the **overlap** is essentially “all valid PV days that fall within the tenant coverage span,” which is still the set of **valid PV days** (since tenant coverage is wider). So:

- **self_consumed** = sum over **all allocation days** in the full period.
- On each allocation day, `allocated_pv` ≤ min(tenant_demand_that_day, pv_that_day). So the **cap** for self_consumed on that day is **tenant demand** on that day. So in total, **self_consumed** is at most the **sum of tenant demand on the overlap days**.

If on most valid-PV days the building/tenant demand is **much smaller** than PV generation that day (e.g. PV = 20,000 kWh, demand = 100 kWh), then even if we allocate 100% of demand from PV, we only “use” 100 kWh on-site that day. So over 2 years:

- **pv_total** ≈ 5.5 million kWh (all valid PV in the range),
- **self_consumed** ≈ sum of tenant demand on overlap days (capped by allocation logic), which is in the order of **tens of thousands** of kWh if there are hundreds of overlap days with modest daily demand.

Then:

- **self_consumption_ratio** = self_consumed / pv_total × 100 ≈ (e.g. 26,000 / 5,509,265) × 100 ≈ **0.47%**.

So **0.47%** is the same phenomenon as 0.34%: the **denominator** is “all PV in the period,” and the **numerator** is “only the part of that PV that was allocated to tenants,” which is limited by (1) allocation only on overlap days and (2) on each day, allocation ≤ tenant demand. Over 2 years, total PV is huge and total allocated is relatively small → low ratio.

---

## 4. Back-of-the-envelope check

- From negative-deltas investigation: **pv_total (valid only)** over full dataset ≈ **5,509,265 kWh**.
- If **self_consumption_ratio = 0.47%**, then **self_consumed** = 0.0047 × 5,509,265 ≈ **25,893 kWh**.
- So over the full period, about **26 MWh** of PV is allocated to tenants; the rest (~5.48 million kWh) is surplus. That is consistent with many valid-PV days where daily PV is large and daily tenant demand is small, so the “used on-site” amount is demand-capped and small relative to total PV.

---

## 5. Root causes (summary)

| Factor | Effect on full-period 0.47% |
|--------|------------------------------|
| **Definition** | Self-consumption = allocated PV / **total** PV in range. So denominator is all valid PV over 2 years. |
| **Allocation only on overlap** | Numerator is sum of allocated PV only on days with both valid PV and tenant data. No allocation on valid-PV days with no tenant data. |
| **Demand cap per day** | On each day, allocated ≤ tenant demand. So total self_consumed ≤ total tenant demand on overlap days. |
| **PV >> demand on many days** | From source data, PV total (5.5 M kWh) is much larger than building consumption (2.3 M kWh) and tenant demand. So even with 100% of demand met by PV on overlap days, the **share** of total PV that is “used on-site” stays small. |
| **Invalid PV days excluded** | Many days (especially Nov 2024 onward) have no valid PV; they don’t reduce pv_total (they’re already excluded). So pv_total is the sum over only “valid PV days,” which still dominates the ratio. |

So **0.47% over the full period** is the result of the same correct logic applied to the full 2-year range: a large total valid PV and a much smaller total allocated PV (bounded by tenant demand on overlap days).

---

## 6. How to reproduce the exact numbers (optional)

To get the **exact** full-period counts and sums for your current batch (e.g. number of valid PV days, overlap days, pv_total, self_consumed), you can run the existing investigation script with the **full** date range instead of the last 30 days:

- In `backend/scripts/investigate_self_consumption_vs_sufficiency.py`, replace the 30-day window (lines 29–37) with the full range:  
  `start_date, end_date = get_date_range(db, batch_id)` (and handle `None`).
- Run from `backend/`: `python scripts/investigate_self_consumption_vs_sufficiency.py` (with the script modified to use full range as above).

That will print, for the full period:

- Distinct dates with valid PV, pv_total (kWh),
- Distinct dates with tenant data,
- Overlap (allocation) days,
- Sum of `allocated_pv_kwh` (self_consumed),
- self_consumption_ratio = self_consumed / pv_total × 100.

You should see **≈ 0.47%** and the exact numerator/denominator that produce it.

---

## 7. Conclusion

- **Why 0.47% for Full period?** Because over the full 2 years, **pv_total** (all valid PV in range) is on the order of **5.5 million kWh**, while **self_consumed** (allocated PV only on days with both valid PV and tenant data, and capped by demand each day) is on the order of **~26 thousand kWh**, giving a ratio of about **0.47%**.
- **No bug:** The implementation uses the same formula as for 30 days; the result is driven by the **definition** (share of total PV that is used on-site) and **data** (large total PV, smaller total allocation over the same period).
- **Difference from 30-day 0.34%:** Over 30 days, only 7 days had valid PV and the ratio was 0.34%. Over the full period, more days contribute to both pv_total and self_consumed, but the **proportion** (allocated / total PV) remains small for the same structural reasons, yielding **0.47%**.
