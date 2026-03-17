import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TenantInsights, getCV } from "./TenantInsights";
import type { TenantData } from "@/types/energy";

describe("getCV", () => {
  it("returns Infinity when tenant has no positive consumption (empty timeSeries)", () => {
    const tenant: TenantData = {
      id: "Kunde1",
      name: "Kunde1",
      unit: "Kunde1",
      totalConsumption: 0,
      avgDailyConsumption: 0,
      avgWeeklyConsumption: 0,
      activeDays: 0,
      color: "#000",
      timeSeries: [],
    };
    expect(getCV(tenant)).toBe(Infinity);
  });

  it("returns Infinity when tenant has only zero consumption", () => {
    const tenant: TenantData = {
      id: "Kunde1",
      name: "Kunde1",
      unit: "Kunde1",
      totalConsumption: 0,
      avgDailyConsumption: 0,
      avgWeeklyConsumption: 0,
      activeDays: 2,
      color: "#000",
      timeSeries: [
        { date: "2025-01-01", consumption: 0 },
        { date: "2025-01-02", consumption: 0 },
      ],
    };
    expect(getCV(tenant)).toBe(Infinity);
  });

  it("returns a finite number when tenant has positive consumption", () => {
    const tenant: TenantData = {
      id: "Kunde1",
      name: "Kunde1",
      unit: "Kunde1",
      totalConsumption: 100,
      avgDailyConsumption: 10,
      avgWeeklyConsumption: 70,
      activeDays: 10,
      color: "#000",
      timeSeries: [
        { date: "2025-01-01", consumption: 10 },
        { date: "2025-01-02", consumption: 20 },
      ],
    };
    const cv = getCV(tenant);
    expect(Number.isFinite(cv)).toBe(true);
    expect(cv).toBeGreaterThanOrEqual(0);
  });
});

describe("TenantInsights", () => {
  it("renders without crashing when one tenant has no positive consumption", () => {
    const tenants: TenantData[] = [
      {
        id: "Kunde1",
        name: "Kunde1",
        unit: "Kunde1",
        totalConsumption: 100,
        avgDailyConsumption: 10,
        avgWeeklyConsumption: 70,
        activeDays: 10,
        color: "#000",
        timeSeries: [{ date: "2025-01-01", consumption: 100 }],
      },
      {
        id: "Kunde2",
        name: "Kunde2",
        unit: "Kunde2",
        totalConsumption: 0,
        avgDailyConsumption: 0,
        avgWeeklyConsumption: 0,
        activeDays: 0,
        color: "#111",
        timeSeries: [],
      },
    ];
    render(<TenantInsights tenants={tenants} />);
    expect(screen.getByText("Highest Demand")).toBeInTheDocument();
    expect(screen.getByText("Most Stable")).toBeInTheDocument();
  });

  it("shows no tenant data message when tenants array is empty", () => {
    render(<TenantInsights tenants={[]} />);
    expect(screen.getByText("No tenant data available")).toBeInTheDocument();
  });
});
