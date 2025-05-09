from datetime import datetime, timedelta

import pytest

from lobster_assessment.application.rebalancing import (
    LogicMode,
    MultiConditionRebalancer,
    OutOfRangeDurationRebalancer,
    OutOfRangeRebalancer,
    RebalancingStrategy,
    TimeTriggeredRebalancer,
    compute_tick_range,
)

now = datetime.now()


def test_tick_range_with_bias():
    center = 1500
    width = 100
    lower, upper = compute_tick_range(center, width, bias=0.25)
    assert lower == 1475 and upper == 1575


def test_bias_validation_failure():
    strat = TimeTriggeredRebalancer(interval=timedelta(minutes=1))
    with pytest.raises(ValueError):
        strat.rebalance(1500, 1400, 1600, -0.1)
    with pytest.raises(ValueError):
        strat.rebalance(1500, 1400, 1600, 1.1)


def test_base_strategy_interface():
    class DummyStrategy(RebalancingStrategy):
        pass

    strat = DummyStrategy()
    with pytest.raises(NotImplementedError):
        strat.should_rebalance(1500, now, 1000, 2000, now)
    with pytest.raises(NotImplementedError):
        strat.rebalance(1500, 1000, 2000, 0.5)


def test_time_triggered_rebalance(position):
    strat = TimeTriggeredRebalancer(interval=timedelta(minutes=1))
    tick, lower, upper = 1500, position.tick_lower, position.tick_upper

    timestamp1 = now
    timestamp2 = timestamp1 + timedelta(minutes=2)

    assert not strat.should_rebalance(tick, timestamp1, lower, upper, now)
    strat.rebalance(tick, lower, upper, 0.5)
    assert not strat.should_rebalance(
        tick, timestamp1 + timedelta(minutes=1), lower, upper, now
    )
    assert strat.should_rebalance(tick, timestamp2, lower, upper, now)


def test_out_of_range_rebalancer(position):
    strat = OutOfRangeRebalancer()
    lower, upper = position.tick_lower, position.tick_upper

    assert strat.should_rebalance(950, now, lower, upper, now)
    assert not strat.should_rebalance(1500, now, lower, upper, now)
    assert strat.should_rebalance(2100, now, lower, upper, now)

    new_lower, new_upper = strat.rebalance(2100, lower, upper, 0.5)
    assert new_lower != lower and new_upper != upper


def test_out_of_range_duration_rebalancer(position):
    strat = OutOfRangeDurationRebalancer(duration=timedelta(seconds=30))
    lower, upper = position.tick_lower, position.tick_upper

    timestamp_0 = now + timedelta(seconds=0)
    timestamp_1 = now + timedelta(seconds=20)
    timestamp_2 = now + timedelta(seconds=40)

    assert not strat.should_rebalance(950, timestamp_0, lower, upper, now)
    assert not strat.should_rebalance(1500, timestamp_1, lower, upper, now)
    assert strat.should_rebalance(2100, timestamp_2, lower, upper, now)


def test_multi_condition_or_mode(position):
    strat = MultiConditionRebalancer(
        strategies=[
            OutOfRangeRebalancer(),
            TimeTriggeredRebalancer(interval=timedelta(seconds=0)),
        ],
        mode=LogicMode.OR,
    )
    assert strat.should_rebalance(
        950, now, position.tick_lower, position.tick_upper, now
    )


def test_multi_condition_and_mode(position):
    ttr = TimeTriggeredRebalancer(interval=timedelta(seconds=0))
    strat = MultiConditionRebalancer(
        strategies=[OutOfRangeRebalancer(), ttr],
        mode=LogicMode.AND,
    )
    ttr.rebalance(950, position.tick_lower, position.tick_upper, 0.5)
    assert not strat.should_rebalance(
        1500, now + timedelta(seconds=1), position.tick_lower, position.tick_upper, now
    )


def test_time_triggered_negative_interval():
    with pytest.raises(ValueError):
        TimeTriggeredRebalancer(interval=timedelta(seconds=-1))


def test_time_triggered_exact_same_timestamp(position):
    strat = TimeTriggeredRebalancer(interval=timedelta(seconds=60))
    tick, lower, upper = 1500, position.tick_lower, position.tick_upper
    timestamp = now

    strat.rebalance(tick, lower, upper, 0.5)
    assert not strat.should_rebalance(tick, timestamp, lower, upper, now)


def test_out_of_range_edge_ticks(position):
    strat = OutOfRangeRebalancer()
    lower, upper = position.tick_lower, position.tick_upper
    assert not strat.should_rebalance(lower, now, lower, upper, now)
    assert not strat.should_rebalance(upper, now, lower, upper, now)


def test_out_of_range_large_range():
    strat = OutOfRangeRebalancer()
    tick = 10**10
    assert strat.should_rebalance(tick, now, -(10**5), 10**5, now)


def test_out_of_range_duration_zero_duration(position):
    strat = OutOfRangeDurationRebalancer(duration=timedelta(seconds=0))
    lower, upper = position.tick_lower, position.tick_upper

    assert strat.should_rebalance(950, now, lower, upper, now)


def test_out_of_range_never_recovers(position):
    strat = OutOfRangeDurationRebalancer(duration=timedelta(seconds=30))
    lower, upper = position.tick_lower, position.tick_upper
    ts = now
    assert not strat.should_rebalance(950, ts, lower, upper, now)
    assert not strat.should_rebalance(
        950, ts + timedelta(seconds=15), lower, upper, now
    )
    assert strat.should_rebalance(950, ts + timedelta(seconds=31), lower, upper, now)


def test_multi_condition_empty_strategy_list(position):
    strat = MultiConditionRebalancer(strategies=[], mode=LogicMode.OR)
    assert not strat.should_rebalance(
        1500, now, position.tick_lower, position.tick_upper, now
    )
