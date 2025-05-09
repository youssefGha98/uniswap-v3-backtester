from lobster_assessment.application.algo import ActivityTracker
from lobster_assessment.domain.models import SwapSeries


def test_is_active_boundaries(position):
    tracker = ActivityTracker(position=position)
    assert tracker.is_active(1000)
    assert tracker.is_active(1500)
    assert tracker.is_active(2000)


def test_is_active_outside(position):
    tracker = ActivityTracker(position=position)
    assert not tracker.is_active(999)
    assert not tracker.is_active(2001)


def test_track_timeseries(position, swap_series):
    tracker = ActivityTracker(position=position)
    timeseries = tracker.track(swap_series)

    expected = [
        False,  # tick = 950
        True,  # tick = 1500
        False,  # tick = 2100
    ]

    assert timeseries.activity == expected
    assert timeseries.timestamps == swap_series.timestamps


def test_track_empty_series(position):
    tracker = ActivityTracker(position=position)
    empty_series = SwapSeries(swaps=[])
    result = tracker.track(empty_series)
    assert result.activity == []
    assert result.timestamps == []
