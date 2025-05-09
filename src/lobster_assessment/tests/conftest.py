from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from lobster_assessment.domain.models import Pool, Position, Swap, SwapSeries


@pytest.fixture
def basic_pool():
    return Pool(
        address="0xabc",
        token0="ETH",
        token1="USDC",
        fee=Decimal("0.003"),
    )


@pytest.fixture
def basic_position(basic_pool):
    return Position(
        tick_lower=100,
        tick_upper=200,
        amount0=Decimal("10"),
        amount1=Decimal("20000"),
        pool=basic_pool,
    )


@pytest.fixture
def swap_series():
    base_time = datetime(2023, 1, 1)
    return SwapSeries(
        swaps=[
            Swap(
                tick=150,
                volume_token0=Decimal("1.0"),
                volume_token1=Decimal("2000.0"),
                liquidity=Decimal("100000"),
                sqrt_price_x96=Decimal("1.0").sqrt() * (2**96),
                timestamp=base_time + timedelta(days=i),
            )
            for i in range(2)
        ]
    )
