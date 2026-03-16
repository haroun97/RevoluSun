# Investigation: PV “Negative Delta” Alerts vs Spreadsheet (No Negative Deltas Visible)

**Date:** 2026-03-15  
**Question:** The dashboard shows 383 “pv - Invalid deltas” (negative or invalid delta) alerts, but when checking the PV-Zähler spreadsheet the user sees chronologically sorted data and **no** negative deltas (readings are non-decreasing). Could the data be **unsorted by timestamp** before calculating the delta, causing false negatives?  
**Scope:** Deep investigation only; no code changes.

---

## 1. Short answer

- **Sorting:** The pipeline **does** sort by timestamp before computing deltas (per meter). So we are **not** computing deltas on unsorted rows.
- **Likely cause of the mismatch:** The pipeline treats the **entire PV-Zähler sheet** as a **single** time series (one `meter_id` = `"pv"`). If the spreadsheet actually contains **multiple physical meters** (e.g. multiple inverters, identifiable by a column such as `measuring_point__serial` or meter ID in column B), their readings are **merged** into one series. When we then sort by timestamp only, we **interleave** different meters’ cumulative values, which can produce **apparent** negative deltas even though **each** meter’s own series is non-decreasing in the sheet. So the alerts can be **real** from the pipeline’s point of view (cumulative really goes down from one row to the next after our sort), but **not** “real” decreases of a single meter—they are **artifacts of mixing several meters** under one `meter_id`.

---

## 2. Where deltas are computed and how order is enforced

### 2.1 Resampling (delta calculation)

**File:** `backend/app/services/resampling.py`

- Reads from **NormalizedMeterReading** with an explicit **ORDER BY**:
  - `order_by(NormalizedMeterReading.meter_id, NormalizedMeterReading.timestamp)` (line 26).
- Builds a DataFrame, then for **each** group `(meter_id, meter_type, tenant_id)`:
  - `group = group.sort_values("timestamp")` (line 45).
- Then iterates in that order and computes `delta = cum - prev_cumulative` (lines 54–55).

So **both** the DB read and the per-group pandas processing use **timestamp order**. Deltas are **not** computed on unsorted data.

### 2.2 Normalization and ingestion

- **Normalization** copies from RawMeterReading to NormalizedMeterReading with **no** ORDER BY; order there does not matter for correctness because **resampling** re-orders by `(meter_id, timestamp)` when reading from NormalizedMeterReading.
- **Ingestion** inserts rows in **Excel row order** (sheet order). So the order in the DB is sheet order; the **only** place we rely on order for deltas is in resampling, and there we **do** sort by timestamp per meter.

So the hypothesis *“data is not sorted by timestamp before calculating the delta”* is **not** true in the code: sorting by timestamp is applied before delta calculation.

---

## 3. Why you can still see “negative deltas” when the spreadsheet looks fine

### 3.1 One `meter_id` for the whole PV sheet

In **ingestion** (`backend/app/services/ingestion.py`):

- For the PV sheet we set: `meter_id = tenant_id or meter_type` → so **every** row from the PV-Zähler sheet gets `meter_id = "pv"` (and `meter_type = "pv"`).
- We **do not** use any **per-row** identifier from the Excel (e.g. `measuring_point__serial`, or the meter ID in column B such as `1ESY1162172XXX`) to split the series. So **all** PV rows are treated as **one** cumulative series.

So from the pipeline’s perspective there is **one** PV meter. Its “cumulative” is the sequence of all (timestamp, value) rows from the sheet, sorted by timestamp. If that sequence ever goes **down** from one row to the next, we report a negative delta.

### 3.2 Multiple physical meters in one sheet → false “decreases”

If the PV-Zähler sheet actually contains **several physical meters** (e.g. several inverters), each with its **own** cumulative series, then:

- In the **spreadsheet** you might look at **one** device (e.g. filter or scroll to one meter ID/serial) and see only **non-decreasing** values—so “no negative delta” in that view.
- In the **pipeline** we **merge** all rows from the sheet into one series and sort by **timestamp only**. So we get an ordering like:
  - … (2024-11-18 23:00, **3933.6**), (2024-11-19 04:00, **3933.6**), …  ← Meter A
  - … (2024-11-19 05:00, **111.58**), …  ← Meter B (different device, lower cumulative)
  - … (2024-11-19 06:00, **2487.63**), …  ← Meter A again

  Then:
  - `prev = 2487.63`, `curr = 111.58` → **delta = -2376** → we flag a “negative delta” and create an alert.
- So the **alert is correct** for the **single merged series** we build (value really goes down from one row to the next), but the “decrease” is **not** a single meter’s cumulative going down—it’s **switching from one meter to another** (different cumulatives). That matches the example in `INVESTIGATION_NEGATIVE_DELTAS.md`: `prev=2487.63 kWh`, `curr=111.58 kWh` → large negative delta.

So:

- **You:** “In the spreadsheet I see no negative delta” → likely true for **one** meter’s series (or the portion you checked).
- **Pipeline:** “We see negative deltas” → true for the **merged** series (one `meter_id` = `"pv"`), because we mix several devices’ cumulatives when we sort only by time.

### 3.3 What to check in the spreadsheet

To confirm this hypothesis **without changing code**:

1. **Multiple meter IDs / serials in PV-Zähler**
   - Check whether the PV-Zähler sheet has a column that identifies the device (e.g. meter ID like `1ESY1162172XXX` in column B, or `measuring_point__serial`).
   - If yes, count **distinct** values in that column. If there are **2 or more**, then the sheet holds **multiple** cumulative series. The pipeline currently merges them into one, so interleaving by timestamp can produce the 383 “negative delta” alerts even though **no single meter** has a negative delta in the sheet.
2. **Same timestamp, different values**
   - If two rows share the same (or very close) timestamp but have different values, they are likely two different meters. After sort by timestamp, going from a high value to a low value at the same time (or next row) would yield a negative delta.
3. **Portion you checked**
   - Your screenshot shows rows 478–511 with a **single** meter ID (e.g. `1ESY1162172XXX`) and non-decreasing values. The 383 alerts might come from **other** parts of the sheet (other dates or the other meter(s)), or from the **combined** series when both meters’ rows are interleaved by timestamp.

---

## 4. Column detection (value column)

- The pipeline detects the value column via `_detect_value_column()` (e.g. `value`, `Value`, `Wert`, or first numeric column). If the sheet has **several** numeric columns and the “real” cumulative is not the one we pick, we could in theory read the wrong series. That could also cause odd deltas.
- From existing investigations, the **magnitudes** of the values (e.g. 2487, 111) match realistic kWh, so we are likely using **a** valid numeric column. If you want to be sure, run `backend/scripts/investigate_excel_columns.py` and confirm which column is used for PV-Zähler and that it matches the column you’re inspecting (e.g. column D in your view).

---

## 5. Summary table

| Question | Finding |
|----------|--------|
| Is data sorted by timestamp before delta? | **Yes.** Resampling uses `order_by(meter_id, timestamp)` and `group.sort_values("timestamp")`. So no unsorted-delta bug. |
| Why do I see 383 negative-delta alerts for PV? | The pipeline builds **one** series for the whole PV sheet (`meter_id = "pv"`). If the sheet has **multiple** physical meters (e.g. different serials), sorting by timestamp **merges** their cumulatives and can produce **apparent** decreases when the next row is a different meter with a lower cumulative. |
| So is the “negative delta” real? | It is **real** for the **merged** series (value does go down from one row to the next after our sort). It is **not** necessarily a single meter’s cumulative decreasing in the source; it can be an **artifact of mixing several meters** under one `meter_id`. |
| What should I check in the spreadsheet? | (1) Whether PV-Zähler has more than one distinct meter ID/serial; (2) whether multiple devices’ rows are interleaved by timestamp; (3) that the column we use for “value” is the one you’re checking. |

---

## 6. Conclusion

- **Sorting:** Data **is** sorted by timestamp before computing deltas (per meter). The negative-delta alerts are **not** caused by unsorted data.
- **Likely cause:** The PV sheet is treated as a **single** time series (`meter_id = "pv"`), while the Excel may contain **multiple** physical meters (e.g. identifiable by a serial/meter ID column). Merging their rows and sorting only by timestamp produces **interleaved** cumulatives and thus **apparent** negative deltas, even though each meter’s own series in the spreadsheet is non-decreasing. To confirm, check in the PV-Zähler sheet for multiple distinct meter IDs/serials and whether readings from different devices appear in the same timestamp column.

No code changes were made; this is investigation only.
