# Investigation: Negative Deltas and “Deleted” Data After Pipeline Rerun

**Date:** 2026-03-15  
**Question:** After rerunning the pipeline (Option A), did we delete or wrongly exclude real data?  
**Conclusion:** **No.** The pipeline does not delete real data. Negative deltas in the **source Excel** correspond to cumulative values that **decrease** (meter reset or export error). Excluding them from aggregation is correct. Tenant data is unaffected.

---

## 1. Source data (Excel)

- **File:** `document/Messdaten_Nürnberg_2024-2026.xlsx`
- **Sheets:** Summenzähler (building), PV-Zähler (PV), Kunde1–Kunde13 (no Kunde7).
- **Columns used:** `timestamp`, `value`. Building sheet has `measuring_point__conversion_factor` = 50; we apply the same in code (50 for building, 1 for PV/tenant).

## 2. Findings from scripts

### 2.1 Negative deltas come from the raw data

- **PV-Zähler:** 380 negative deltas. Example: `prev=2487.63 kWh`, `curr=111.58 kWh` → delta = -2376. So the **cumulative value in the Excel really goes down** (e.g. 2487 → 111). That is either a meter reset or an export/aggregation error; it is not caused by our code.
- **Summenzähler (building_total):** 305 negative deltas. Same pattern: e.g. `prev=5342.50`, `curr=1300.00` → large drop. Again, the **raw cumulative decreases** in the source.
- **Tenants (Kunde1–Kunde13):** **0 negative deltas** in all tenant sheets. No tenant consumption is excluded by the pipeline.

So we are not inventing negative deltas; we are **detecting** them where the source series decreases.

### 2.2 What the pipeline does

- Sorts by meter and timestamp (no wrong order).
- Computes `delta = current_reading - previous_reading`.
- If `delta < 0`: we **do not add** it to the daily total and we **flag** the day (anomaly). We still write a row for that day with `delta_kwh = sum(positive deltas only)` and `is_valid = False`.
- We do **not** drop rows or “delete” readings. We only **exclude negative deltas from the consumption sum**.

So:

- **Tenant data:** Unchanged; no negatives, so nothing is excluded.
- **Building / PV:** On days where the cumulative drops, we refuse to add that drop to consumption (correct) and we undercount that day (or count only the positive part before the drop). That is the intended behavior when the meter “resets” or the export has an error.

### 2.3 Totals: valid-only vs “if we included negative”

| Meter           | Total kWh (valid deltas only) | Total kWh (if we summed all deltas including negative) |
|----------------|-------------------------------|--------------------------------------------------------|
| Summenzähler   | 2,321,341                     | 7,875                                                  |
| PV-Zähler      | 5,509,265                     | 3,769                                                  |

If we **included** negative deltas, building total would be only 7,875 kWh (the huge negative steps would cancel the positive ones). So the “valid only” total is the one that makes sense. We are **not** throwing away real consumption; we are **avoiding** adding impossible (negative) steps that are present in the source.

### 2.4 Why the chart “drops to zero” around Feb 2025

- **Summenzähler:** Negative-delta days start 2024-12-31; from **Feb 2025 onward** there are about **20–27 such days per month**. So from that period on, **most days** have at least one negative delta and get a zero or very small valid daily total.
- So the **dashboard** shows building consumption falling to near zero not because we “deleted” data, but because the **source file has cumulative decreases on most days** (resets or errors). We correctly exclude those steps, so the chart reflects “valid consumption only” and is sparse from Feb 2025 onward.

Same idea for PV: many negative-delta days from Nov 2024 onward, so some days contribute zero or little to the PV series.

### 2.5 Readings per day

- Building and PV: **max 2 readings per day**, median 2. So two timestamps per day; when the second cumulative is lower than the first we get one negative delta for that day and we exclude it from that day’s consumption.
- Tenants: 1 reading per day (median 1). No negatives, so no exclusion.

---

## 3. Tests run

- `scripts/investigate_negative_deltas.py`: Loads Excel, applies same logic as pipeline (ingestion + normalization + resampling), reports negative counts and totals per sheet.
- `scripts/investigate_excel_columns.py`: Confirms columns `timestamp`, `value` and conversion factors (50 / 1).
- `scripts/investigate_negative_dates_distribution.py`: Counts negative-delta days by month for building and PV; shows concentration from late 2024 / Feb 2025 onward.

---

## 4. Conclusion

- **No real data was deleted** by the pipeline. We do not remove rows; we only exclude **negative** deltas from the consumption sum.
- **Negative deltas exist in the source Excel**: cumulative `value` (after conversion) sometimes decreases. Excluding them is correct.
- **Tenant data:** No negative deltas; no exclusion; totals and charts use all tenant readings.
- **Building / PV:** Many days in the source have a decreasing cumulative (resets or errors). On those days we undercount by design. The “abrupt drop” in the chart is a **data quality issue in the source**, not a bug in the pipeline.
- **Recommendation:** Treat the current pipeline behavior as correct. If building/PV totals or charts look wrong, the next step is to fix or clarify the **source data** (meter resets, export logic, or aggregation) rather than change how we handle negative deltas.
