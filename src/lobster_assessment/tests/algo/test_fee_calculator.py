from datetime import datetime
from decimal import Decimal

import pytest

from lobster_assessment.application.algo import FeeCalculator
from lobster_assessment.domain.models import Position, Swap, SwapSeries


def test_compute_fee_for_swap_half_share(position, swap_series):
    calc = FeeCalculator(position=position)
    swap = swap_series.swaps[1]  # in-range swap
    fee = calc.compute_fee_for_swap(swap)

    assert fee.token0 == pytest.approx(Decimal("0.009495"), 8)
    assert fee.token1 == pytest.approx(Decimal("0.01582"), 8)


def test_compute_fee_for_swap_zero_position_liquidity(pool):
    position = Position(
        tick_lower=1000,
        tick_upper=2000,
        amount0=Decimal("0"),
        amount1=Decimal("0"),
        pool=pool,
    )

    swap = Swap(
        tick=1500,
        volume_token0=Decimal("100"),
        volume_token1=Decimal("200"),
        liquidity=Decimal("10000"),
        sqrt_price_x96=Decimal("1.0"),
        timestamp=datetime.now(),
    )

    calc = FeeCalculator(position=position)
    fee = calc.compute_fee_for_swap(swap)
    assert fee.token0 == Decimal("0")
    assert fee.token1 == Decimal("0")


def test_compute_fee_for_swap_zero_swap_liquidity(position):
    swap = Swap(
        tick=1500,
        volume_token0=Decimal("100"),
        volume_token1=Decimal("200"),
        liquidity=Decimal("0"),
        sqrt_price_x96=Decimal("1.0"),
        timestamp=datetime.now(),
    )

    calc = FeeCalculator(position=position)
    fee = calc.compute_fee_for_swap(swap)

    total_fee_0 = swap.volume_token0 * position.pool.fee
    total_fee_1 = swap.volume_token1 * position.pool.fee

    assert fee.token0 == total_fee_0
    assert fee.token1 == total_fee_1


def test_track_fee_timeseries(position, swap_series):
    calc = FeeCalculator(position=position)
    result = calc.track(swap_series)

    assert len(result.fees) == len(swap_series.swaps)
    assert len(result.fees) == len(result.timestamps)
    assert set(result.timestamps) == set(swap_series.timestamps)


def test_track_fee_timeseries_empty(position):
    empty_series = SwapSeries(swaps=[])
    calc = FeeCalculator(position=position)
    result = calc.track(empty_series)
    assert result.fees == []
    assert result.timestamps == []
