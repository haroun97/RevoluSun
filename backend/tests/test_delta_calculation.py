"""Test delta calculation and negative delta detection."""


def test_delta_from_cumulative():
    cumulative = [100.0, 150.0, 180.0]
    deltas = [cumulative[i] - cumulative[i - 1] for i in range(1, len(cumulative))]
    assert deltas == [50.0, 30.0]


def test_negative_delta_detection():
    cumulative = [100.0, 90.0]  # meter reset or error
    delta = cumulative[1] - cumulative[0]
    assert delta == -10.0
    is_invalid = delta < 0
    assert is_invalid is True


def test_daily_aggregation():
    # Same day, two deltas: 10 and 20 -> total 30
    deltas_per_day = {"2024-06-01": 0.0}
    deltas_per_day["2024-06-01"] += 10.0
    deltas_per_day["2024-06-01"] += 20.0
    assert deltas_per_day["2024-06-01"] == 30.0


def test_negative_delta_excluded_from_aggregation():
    """Negative deltas must not be summed into daily consumption; only valid (>=0) deltas."""
    daily_deltas = {}
    daily_invalid = {}
    # Simulate: day1 +50, day2 -100 (invalid), day2 +40
    for date_str, delta in [("2025-01-01", 50.0), ("2025-01-02", -100.0), ("2025-01-02", 40.0)]:
        d = date_str  # simplified
        if d not in daily_deltas:
            daily_deltas[d] = 0.0
            daily_invalid[d] = False
        if delta >= 0:
            daily_deltas[d] += delta
        else:
            daily_invalid[d] = True
    assert daily_deltas["2025-01-01"] == 50.0
    assert daily_deltas["2025-01-02"] == 40.0  # -100 excluded
    assert daily_invalid["2025-01-02"] is True
