# Investigation: Duplicate Kunde Labels on Y-Axis (Tenant Consumption Comparison)

**Date:** 2025-03-15  
**Issue:** Each tenant (Kunde) appears twice on the Y-axis of the "Tenant Consumption Comparison" horizontal bar chart (e.g. Kunde1, Kunde1, Kunde2, Kunde2, …).

---

## 1. How the chart gets its data

- **TenantComparisonChart** (`frontend/src/components/charts/TenantComparisonChart.tsx`) receives `tenants: TenantData[]` and builds:
  ```ts
  const data = tenants.map(t => ({
    name: `${t.unit} · ${t.name}`,
    value: ...,
    fill: t.color,
  }));
  ```
- This `data` is passed to Recharts as `<BarChart data={data}>`. So **one tenant → one entry in `data` → one bar and one Y-axis label**.
- If each Kunde appears twice on the Y-axis, the chart is therefore receiving **two data points per tenant** (i.e. **24 entries for 12 tenants**).

---

## 2. Where the data comes from (upstream)

- `tenants` is `tenantsQuery.data ?? []` in **DashboardPage** (from `useQuery` with `queryFn: () => fetchTenants(dateRange?.start, dateRange?.end)`).
- **fetchTenants** (`frontend/src/api/energyApi.ts`):
  - Calls `fetchTenantsComparison(start, end)` → one object per tenant from `/api/tenants/comparison`.
  - Then `comparison.map((t, idx) => ({ id: t.tenant_id, name: t.tenant_id, ... }))` → **one TenantData per comparison item**.
- So the length of `tenants` is exactly the length of the **comparison** array returned by the API. If the comparison array has 24 elements (each tenant twice), then `tenants` has 24 elements and the chart shows 24 labels.

---

## 3. Recharts behaviour (why “two per tenant” = 24 data points)

- In **generateCategoricalChart.js**, **displayedData** (used for the category axis and for composing bar data) is built by **getDisplayedData**:
  - It **concatenates** `child.props.data` for every **graphical item** (every `Bar` component).
  - So: one `Bar` → one `props.data` → that many categories. Two `Bar`s → two `props.data` concatenated → doubled categories.
- The Bar’s `data` is produced by **Bar.getComposedData**, which maps over **displayedData** (which for a single Bar comes from the chart’s `props.data` when the Bar doesn’t have `data` yet).
- So the number of Y-axis labels = number of entries in the **chart’s `data`** (or the concatenation of all Bar `data` if there were multiple Bars). With a **single Bar** and no other series, that is exactly **data.length**.
- Conclusion: **Duplicate labels ⇒ the `data` array passed to `BarChart` has 24 elements** (two per tenant). So **`tenants` has 24 elements** at the point it’s passed to TenantComparisonChart.

---

## 4. Custom Bar children (rects) – do they cause duplication?

- In TenantComparisonChart, the Bar is used as:
  ```tsx
  <Bar dataKey="value" ...>
    {data.map((entry, idx) => (
      <rect key={idx} fill={entry.fill} />
    ))}
  </Bar>
  ```
- In Recharts **Bar.js**:
  - **graphicalItems** are found with `findAllByType(children, GraphicalChild)`; **BarChart** uses `GraphicalChild: Bar`. So only **direct** children of type `Bar` count. The Bar’s children are `<rect>` elements (SVG), not `Bar`, so they are **not** counted as graphical items. So we still have **one** graphical item (one Bar).
  - Bar uses **Cell** children for per-bar styling; here we pass **rect**, not **Cell**, so those rects are not used as Cell. The Bar’s **render** path uses **BarRectangle** (one per data point), not the custom rects, to draw the bars.
- So the custom **rect** children do **not** change how many bars or categories Recharts computes. They do **not** explain the duplication. The duplication comes from **data length**, not from the Bar’s children.

---

## 5. Backend – can it return the same tenant twice?

- **tenants_comparison** (`backend/app/services/analytics.py`) uses:
  ```python
  select(..., tenant_id, ...).where(*cond).group_by(DailyMeterConsumption.tenant_id)
  ```
  So the query returns **at most one row per distinct tenant_id**. Then we build `items` from `rows` and sort; we do **not** append the list twice.
- So under normal conditions the backend returns **12 rows** (one per tenant). It would return **24** only if:
  - The same logical tenant appeared under **two different `tenant_id` values** in the DB (e.g. `"Kunde1"` and `"Kunde1 "`, or different casing), or
  - There is another code path or middleware that duplicates the response.

---

## 6. Exact location of the issue

- **Behaviour:** The Y-axis shows each Kunde twice because the chart receives **24 data points** (two per tenant).
- **Source of length:** That length is exactly **tenants.length** (and thus **comparison.length** from the API), because the chart does `tenants.map(...)` and does not duplicate the array.
- **So the issue is in one of:**

| Location | What to check |
|----------|----------------|
| **Backend** `/api/tenants/comparison` | Response body: does the JSON array have **12** or **24** elements? If 24, then either (a) `tenant_id` has two distinct values per logical tenant in the DB, or (b) the list is duplicated before return. |
| **Frontend** before chart | Is `tenants` ever merged or concatenated with another list (e.g. two sources of tenants)? Current code shows a single source (`tenantsQuery.data`), but worth confirming no other code path assigns or appends to the same `tenants` reference. |
| **Recharts** (only if data length is 12) | If you **log** `tenants.length` and `data.length` in TenantComparisonChart and both are **12** but the Y-axis still shows 24 labels, then the bug would be inside Recharts (e.g. category axis or layout="vertical"). This is the least likely given the library’s logic above. |

---

## 7. How to confirm (no code changes)

1. **Network:** Open DevTools → Network, (re)load or change date so `/api/tenants/comparison` is requested. Inspect the JSON array length and the `tenant_id` values. If the array has 24 elements and you see repeated `tenant_id`s (e.g. two `"Kunde1"` rows), the issue is **backend or data** (duplicate tenant_ids in DB or in the built list).
2. **Frontend:** In `TenantComparisonChart`, at the top of the component, log e.g. `console.log('tenants.length', tenants.length, tenants.map(t => t.id))`. If you see 24 and repeated ids, the duplication is already in `tenants` (hence from API or from whatever builds `tenants`). If you see 12, the duplication is not in the data and would point to Recharts (unexpected).
3. **Backend:** If the API returns 24, run a quick check in the DB or in analytics: `SELECT tenant_id, COUNT(*) FROM daily_meter_consumption WHERE ... GROUP BY tenant_id` and see if any `tenant_id` appears in two different forms (e.g. trailing space, case).

---

## 8. Summary

- **Root cause:** The chart shows each Kunde twice because it is given **24 data points** (two per tenant). Recharts draws one Y-axis label per data point; the custom `<rect>` children in Bar do not add extra points.
- **Exact place:** The length is determined by **tenants.length**, which equals the length of the **comparison** array from **GET /api/tenants/comparison**. So the duplication is either (1) **in that API response** (24 items or duplicate tenant_ids), or (2) **in the frontend** when building/assigning `tenants` (no evidence in current code), or (3) **in Recharts** only if `tenants.length` and `data.length` are 12 (unlikely).
- **Next step:** Inspect the `/api/tenants/comparison` response and `tenants.length` / `tenants.map(t => t.id)` in the chart. That will pinpoint whether the bug is backend, frontend data pipeline, or (rarely) Recharts.

---

## 9. Backend fix that was implemented

- **Ingestion** (`backend/app/services/ingestion.py`): `classify_sheet` now normalizes tenant IDs with `int(m.group(1))`, so sheet names like `Kunde01` and `Kunde1` both become `"Kunde1"` for **new** imports. This only affects data ingested **after** the change.
- **Constants** (`backend/app/core/constants.py`): Added `canonical_tenant_id(tenant_id)` — for strings like `KundeN` or `Kunde0N` it returns `"Kunde{n}"` (e.g. `Kunde01` → `"Kunde1"`). Non‑matching strings (e.g. no `"Kunde"` prefix or non‑numeric suffix) are returned unchanged.
- **Analytics** (`backend/app/services/analytics.py`):
  - `tenants_comparison`: After building `items` from the DB query, rows are grouped by `canonical_tenant_id(tenant_id)`, then merged (sum consumption and active_days, one row per canonical id, recompute averages). Result is sorted and returned.
  - `sharing_aggregates`: Same collapse-by-canonical-id logic applied after the group_by query.

So the API **should** return at most one row per canonical tenant (e.g. 12 rows for Kunde1–Kunde12 if Kunde7 is missing). If you still see two labels per Kunde, the cause is one of the following.

---

## 10. Why you may still see two labels per Kunde (deep investigation)

### 10.1 Backend process not restarted

- The collapse logic runs in the **running** Python process. If the backend was not restarted after the code change, the old code (no collapse) is still serving requests.
- **Check:** Restart the backend (e.g. stop uvicorn and start again). Reload (`--reload`) only picks up changes when files are saved and the process restarts; confirm the process actually restarted (e.g. check logs for “Application startup complete” after your last edit).

### 10.2 Case sensitivity in `canonical_tenant_id`

- `canonical_tenant_id` only normalizes when the string **starts with** `"Kunde"` (capital K). It does **not** lower-case the id.
- If the DB has both `"Kunde1"` and `"kunde1"` (lowercase), then:
  - `canonical_tenant_id("Kunde1")` → `"Kunde1"`
  - `canonical_tenant_id("kunde1")` → `"kunde1"` (unchanged, because `"kunde1".startswith("Kunde")` is False).
- So those two ids would **not** be collapsed and the API would return **two rows** (Kunde1 and kunde1), and the chart would show two Y-axis labels.
- **Check:** In the DB, run something like:  
  `SELECT DISTINCT tenant_id FROM daily_meter_consumption WHERE meter_type = 'tenant' AND import_batch_id = (SELECT MAX(id) FROM import_batch) ORDER BY 1;`  
  Look for any pair that differs only by case (e.g. `Kunde1` and `kunde1`).

### 10.3 Other tenant_id variants that do not collapse

- The canonical form is only applied when the id matches the pattern: `"Kunde"` followed by digits (with optional leading zeros). Anything else is returned as-is.
- Examples that would **not** be merged with `"Kunde1"`:
  - Typo: `"Kunde 1"` (space) → `s[5:]` is `" 1"`, `int(" 1")` = 1 → actually **would** become `"Kunde1"` (strip removes the space).
  - `"Kunde1a"` → `int("1a")` raises `ValueError` → returns `"Kunde1a"` (unchanged). So that would be a separate row.
  - Trailing space in DB: `"Kunde1 "` → after strip `"Kunde1"`, so collapses correctly.
- So the only likely “same logical tenant, different row” cases that **survive** the collapse are: **case differences** (e.g. Kunde1 vs kunde1) or **typos/suffixes** (e.g. Kunde1 vs Kunde1a). Checking distinct `tenant_id` values in the DB (as above) will show these.

### 10.4 Frontend cache (React Query)

- `tenantsQuery` uses `staleTime: 60_000` (60 seconds). So after a backend fix, the frontend may still show the **previous** response (24 items) until:
  - 60 seconds pass and a refetch occurs, or
  - The user triggers a refetch (e.g. change date range, full page reload, or invalidate the query).
- **Check:** Do a **hard refresh** (e.g. Ctrl+Shift+R) or change the date range and see if the duplicates disappear. If they do after refresh but not before, the backend is likely returning 12 and the cache was showing old 24-item data.

### 10.5 Confirming where the length comes from

- The chart’s Y-axis has **one label per element** of the `data` array passed to `BarChart`.  
  `data = tenants.map(t => ({ name: \`${t.unit} · ${t.name}\`, value: ..., fill: t.fill }))`.  
  So **number of Y-axis labels = `tenants.length`**.
- `tenants` comes only from `fetchTenants` → `fetchTenantsComparison` → **GET /api/tenants/comparison**. There is no other source or merge in the frontend that could double the list.
- So if you see 24 labels, **somewhere** you have 24 entries in `tenants`; the only source for that is the comparison API response having 24 elements (or a cached version of it).

### 10.6 Recommended verification steps (no code changes)

1. **API response**
   - Open DevTools → Network. Reload or change date so **GET /api/tenants/comparison** is requested.
   - Open the response: check the **array length** and the list of `tenant_id` values.
   - If you see **24 elements** and e.g. two entries with `"Kunde1"` (or `"Kunde1"` and `"kunde1"`), the backend is still returning duplicates (collapse not applied, or case/typo variants as above).
   - If you see **12 elements** and no repeated `tenant_id`, the backend is fixed; if the UI still shows 24 labels, the frontend is showing cached data (see 10.4).

2. **Backend process**
   - Confirm the backend was restarted after the analytics/constants changes. Check server logs for a recent “Application startup complete” after your edits.

3. **Database**
   - Run:  
     `SELECT DISTINCT tenant_id FROM daily_meter_consumption WHERE meter_type = 'tenant' AND import_batch_id = (SELECT MAX(id) FROM import_batch) ORDER BY tenant_id;`  
   - If you see both `Kunde1` and `Kunde01`, the collapse logic should merge them; if you see `Kunde1` and `kunde1`, they will not be merged unless the backend is changed to normalize case.

4. **Frontend**
   - Temporarily in `TenantComparisonChart`, log:  
     `console.log('tenants.length', tenants.length, tenants.map(t => t.id));`  
   - If this shows 24 and repeated ids, the duplication is in the data passed from the API (or cache). If it shows 12, the duplication is not in the data and would point to something else (e.g. Recharts or layout); that case is unlikely given the current code.

---

## 11. Summary: why duplicates can persist after the fix

| Cause | What happens | How to confirm |
|-------|----------------|-----------------|
| Backend not restarted | Old code (no collapse) still runs; API returns 24 rows. | Restart backend; check API response length. |
| Case sensitivity | DB has e.g. `Kunde1` and `kunde1`; only `Kunde*` is normalized, so two rows remain. | Inspect distinct `tenant_id` in DB; check response for both. |
| Frontend cache | API now returns 12, but React Query serves cached 24 for up to 60s. | Hard refresh or change date; see if labels drop to 12. |
| Other id variants | Rare typos/suffixes (e.g. `Kunde1a`) stay separate. | Same DB/API checks as above. |

The chart always shows **one Y-axis label per item in `tenants`**; `tenants` length equals the **comparison API response length** (or cached value). So verifying the **actual comparison response** and **distinct tenant_id in the DB** will pinpoint the remaining cause.
