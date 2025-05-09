from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from lobster_assessment.domain.models import Position, Swap, SwapSeries


class ActivityTimeseries(BaseModel):
    timestamps: list[datetime]
    activity: list[bool]


class ActivityTracker(BaseModel):
    position: Position

    def is_active(self, tick: int) -> bool:
        return self.position.tick_lower <= tick <= self.position.tick_upper

    def track(self, swap_series: SwapSeries) -> ActivityTimeseries:
        return ActivityTimeseries(
            timestamps=swap_series.timestamps,
            activity=[self.is_active(s.tick) for s in swap_series.swaps],
        )


class Fee(BaseModel):
    token0: Decimal
    token1: Decimal


class FeeTimeseries(BaseModel):
    timestamps: list[datetime]
    fees: list[Fee]


class FeeCalculator(BaseModel):
    position: Position

    def compute_fee_for_swap(self, swap: Swap) -> Fee:
        total_liquidity = swap.liquidity + self.position.liquidity
        total_fee_0 = swap.volume_token0 * self.position.pool.fee
        total_fee_1 = swap.volume_token1 * self.position.pool.fee
        return Fee(
            token0=(self.position.liquidity / total_liquidity) * total_fee_0,
            token1=(self.position.liquidity / total_liquidity) * total_fee_1,
        )

    def track(self, swap_series: SwapSeries) -> FeeTimeseries:
        return FeeTimeseries(
            timestamps=swap_series.timestamps,
            fees=[self.compute_fee_for_swap(s) for s in swap_series.swaps],
        )
