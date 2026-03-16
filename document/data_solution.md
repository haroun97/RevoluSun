
# Handling Irregular Timestamps in Cumulative Meter Data

## Problem Description

The dataset used in the Energy Sharing Dashboard contains electricity meter readings collected from multiple sources, including tenant meters, a building-level meter, and a photovoltaic (PV) production meter. These readings represent **cumulative energy measurements**, meaning each value reflects the total energy recorded by the meter since it started operating.

A key challenge in the dataset is that **timestamps are not evenly distributed**. This introduces several data processing issues that must be addressed before meaningful analytics can be performed.

### Primary Problems

#### 1. Irregular Time Intervals

Meter readings are not recorded at consistent time intervals.

Example:

| Timestamp | Meter Reading (kWh) |
|-----------|---------------------|
| 08:03 | 500 |
| 10:41 | 520 |
| 15:17 | 580 |

The time between readings varies significantly, making it impossible to assume a fixed sampling frequency.

#### 2. Data Gaps

There may be extended periods where no readings are recorded.

Example:

| Timestamp | Meter Reading |
|-----------|---------------|
| Jan 1 | 1000 |
| Jan 2 | 1020 |
| Jan 10 | 1100 |

Here there is an eight-day gap between measurements. The dataset only indicates the **total consumption across the interval**, without revealing how usage was distributed during that time.

#### 3. Different Meter Start Dates

Not all meters begin recording data at the same time. Some tenants may appear later in the dataset due to installation timing or occupancy changes.

Example:

Tenant A

| Timestamp | Reading |
|-----------|---------|
| Jan 1 | 200 |
| Jan 5 | 260 |

Tenant B

| Timestamp | Reading |
|-----------|---------|
| Jan 15 | 100 |
| Jan 20 | 130 |

Because of this, direct comparisons across tenants must account for **different coverage periods**.

#### 4. Cumulative Readings Instead of Direct Consumption

Meters store **cumulative totals rather than interval consumption values**. Therefore the dataset does not directly record how much electricity was consumed during each time interval.

Instead, consumption must be calculated by subtracting consecutive readings.

---

# Solution Approach

To address these issues, the application implements a **structured data processing pipeline** designed to transform the raw cumulative readings into usable energy consumption metrics.

## Step 1 – Sorting the Data

Meter readings must first be sorted by:

- meter identifier
- timestamp

This ensures consecutive measurements are processed in chronological order.

## Step 2 – Calculating Consumption from Cumulative Readings

Consumption between two timestamps is derived by computing the difference between consecutive readings.

```
consumption = current_reading − previous_reading
```

Example:

| Timestamp | Reading | Consumption |
|-----------|--------|-------------|
| 08:03 | 500 | — |
| 10:41 | 520 | 20 |
| 15:17 | 580 | 60 |

This converts cumulative readings into **interval-based consumption values**.

## Step 3 – Handling Irregular Timestamps

Because readings occur at irregular intervals, the consumption value represents the **energy used between the two timestamps**.

For the MVP implementation, the consumption value is assigned to the **timestamp of the newer reading**.

More advanced systems may distribute consumption across the interval using interpolation, but this was intentionally avoided due to time constraints.

## Step 4 – Aggregating Data to Daily Metrics

To reduce the impact of irregular timestamps, the data is aggregated to **daily granularity**.

Example result:

| Meter | Date | Daily Consumption |
|------|------|------------------|
| Tenant A | Jan 1 | 50 kWh |
| Tenant A | Jan 2 | 45 kWh |

Daily aggregation provides a stable time resolution suitable for visualization and analysis.

## Step 5 – Applying Conversion Factors

The dataset specifies that:

- Building meter (Summenzähler) → **conversion factor = 50**
- Tenant meters → **factor = 1**
- PV meter → **factor = 1**

All readings must be multiplied by their factor before calculating consumption deltas.

## Step 6 – Handling Data Quality Issues

Negative deltas can occur due to meter resets, data corruption, or timestamp inconsistencies. Since cumulative energy meters cannot physically decrease, negative deltas are treated as anomalies. These values are flagged in the data quality checks and excluded from consumption aggregation.

Several checks help detect inconsistencies:

- Negative consumption values
- Large gaps between readings
- Meters with limited coverage periods
- Differences between building consumption and tenant totals

These checks ensure anomalies are visible during analysis.

## Result

After processing, the system converts irregular cumulative readings into a structured dataset of **daily energy consumption and production values**.

This enables the dashboard to provide insights such as:

- Total building electricity consumption
- Photovoltaic production over time
- Tenant consumption comparisons
- Estimation of shared PV energy versus surplus production

Despite irregularities in the raw data, the pipeline produces reliable aggregated metrics suitable for analysis.

---

# Handling Customers with Different Data Coverage Periods

## Problem Description

The dataset contains electricity meter readings for multiple tenants. However, **not all customers have data covering the same time period**.

This can happen due to:

- tenants moving in or out
- meter installation dates
- data collection gaps
- system upgrades

Example:

| Customer | First Reading | Last Reading |
|----------|--------------|--------------|
| Customer A | Jan 1 | Dec 31 |
| Customer B | Mar 15 | Dec 31 |
| Customer C | Jun 1 | Sep 30 |

Directly comparing total consumption becomes misleading because tenants with longer coverage naturally show higher totals.

## Solution Approach

### 1. Identify the Active Period

For each meter determine:

- first timestamp
- last timestamp
- active days

Example:

| Customer | Start Date | End Date | Active Days |
|----------|------------|----------|------------|
| A | Jan 1 | Dec 31 | 365 |
| B | Mar 15 | Dec 31 | 292 |
| C | Jun 1 | Sep 30 | 122 |

### 2. Compute Consumption Only Within Available Data

Consumption calculations are only performed within the period where readings exist.

Missing periods are **not filled with zeros**.

### 3. Normalize Consumption Metrics

To compare tenants fairly, normalized metrics are used such as:

- average daily consumption
- average weekly consumption

Example:

| Customer | Total Consumption | Active Days | Avg Daily |
|----------|------------------|-------------|----------|
| A | 1200 kWh | 120 | 10 kWh/day |
| B | 900 kWh | 60 | 15 kWh/day |

### 4. Handle Portfolio-Level Analysis

When aggregating building metrics:

- include only dates where readings exist
- exclude tenants outside their coverage window

### 5. Surface Data Coverage

The dashboard reports coverage periods so users understand potential comparison limitations.

## Result

This approach ensures consumption comparisons remain accurate and avoids misleading conclusions caused by unequal measurement periods.

---

# Handling Missing Client Data (Client 7)

## Problem

In the dataset, tenants are labeled **Kunde1–Kunde13**, but **Kunde7 does not exist in the workbook**.

Assuming this tenant has zero consumption would produce incorrect analytics.

### Risks

- Artificially lowering averages
- Misleading comparisons
- Incorrect consistency checks
- Faulty energy sharing calculations

## Correct Interpretation

Client 7 should be treated as **missing data**, not as a tenant with zero usage.

## Solution

1. Do not generate artificial values for the missing tenant.
2. Mark the tenant status as **missing** or **not_available**.
3. Exclude the tenant from tenant-level analytics.
4. Account for missing tenants in building consistency checks.
5. Document the limitation clearly.

## Recommended Documentation Note

Client 7 (Kunde7) is not present in the provided dataset. The system treats this tenant as unavailable rather than assuming zero consumption. All tenant-level analytics include only tenants with available data.
