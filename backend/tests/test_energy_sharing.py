"""Test proportional energy sharing formula."""
import pytest


def test_proportional_allocation():
    # One day: pv_total=100, tenant A demand=60, tenant B demand=40 -> total_demand=100
    # allocated_A = min(60, 100 * 60/100) = 60, allocated_B = min(40, 100 * 40/100) = 40
    pv_total = 100.0
    total_demand = 100.0
    demand_a = 60.0
    demand_b = 40.0
    allocated_a = min(demand_a, pv_total * demand_a / total_demand)
    allocated_b = min(demand_b, pv_total * demand_b / total_demand)
    assert allocated_a == 60.0
    assert allocated_b == 40.0
    assert allocated_a + allocated_b == pv_total


def test_proportional_allocation_limited_pv():
    # pv_total=50, tenant A=60, tenant B=40 -> total_demand=100
    # allocated_A = min(60, 50*0.6)=30, allocated_B = min(40, 50*0.4)=20
    pv_total = 50.0
    total_demand = 100.0
    demand_a = 60.0
    demand_b = 40.0
    allocated_a = min(demand_a, pv_total * demand_a / total_demand)
    allocated_b = min(demand_b, pv_total * demand_b / total_demand)
    assert allocated_a == 30.0
    assert allocated_b == 20.0
    assert allocated_a + allocated_b == 50.0


def test_self_sufficiency_ratio():
    demand = 100.0
    allocated = 40.0
    ratio = (allocated / demand) * 100 if demand > 0 else 0
    assert ratio == 40.0
