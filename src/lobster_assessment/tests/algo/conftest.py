from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from lobster_assessment.application.math import tick_to_sqrt_price
from lobster_assessment.domain.models import Pool, Position, Swap, SwapSeries


@pytest.fixture
def pool() -> Pool:
    return Pool(
        address="0xPool",
        token0="ETH",
        token1="USDC",
        fee=Decimal("0.003"),  # 0.3%
    )


@pytest.fixture
def position(pool: Pool) -> Position:
    return Position(
        tick_lower=1000,
        tick_upper=2000,
        amount0=Decimal("10"),
        amount1=Decimal("20000"),
        pool=pool,
    )


@pytest.fixture
def swap_series() -> SwapSeries:
    now = datetime.now()
    return SwapSeries(
        swaps=[
            Swap(
                tick=950,
                volume_token0=Decimal("100"),
                volume_token1=Decimal("200"),
                liquidity=Decimal("10000"),
                sqrt_price_x96=tick_to_sqrt_price(950),
                timestamp=now,
            ),
            Swap(
                tick=1500,
                volume_token0=Decimal("150"),
                volume_token1=Decimal("250"),
                liquidity=Decimal("10000"),
                sqrt_price_x96=tick_to_sqrt_price(1500),
                timestamp=now + timedelta(minutes=1),
            ),
            Swap(
                tick=2100,
                volume_token0=Decimal("200"),
                volume_token1=Decimal("300"),
                liquidity=Decimal("10000"),
                sqrt_price_x96=tick_to_sqrt_price(2100),
                timestamp=now + timedelta(minutes=2),
            ),
        ]
    )
