from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from lobster_assessment.application.algo import (
    ActivityTimeseries,
    ActivityTracker,
    Fee,
    FeeCalculator,
    FeeTimeseries,
)
from lobster_assessment.application.math import compute_usd_apr
from lobster_assessment.application.rebalancing import RebalancingStrategy
from lobster_assessment.domain.models import (
    Position,
    Swap,
    SwapSeries,
)


class BacktestResult(BaseModel):
    total_fees_token0: Decimal
    total_fees_token1: Decimal
    apr: Decimal


class MultiPositionBacktestRunner:
    def __init__(
        self,
        positions: list[Position],
        swap_series_list: list[list[Swap]],
        trackers: list[ActivityTracker],
        calculators: list[FeeCalculator],
        rebalancers: list[RebalancingStrategy],
        rebalance_bias: float,
    ):
        if len(positions) != len(swap_series_list):
            raise ValueError("Each position must have a corresponding swap series.")

        self.runners: list[BacktestRunner] = []

        for i, (pos, swaps) in enumerate(zip(positions, swap_series_list)):
            tracker = trackers[i] if trackers else ActivityTracker(position=pos)
            calculator = calculators[i] if calculators else FeeCalculator(position=pos)
            rebalancer = rebalancers[i] if rebalancers else None

            self.runners.append(
                BacktestRunner(
                    position=pos,
                    swaps=swaps,
                    tracker=tracker,
                    calculator=calculator,
                    rebalancer=rebalancer,
                    rebalance_bias=rebalance_bias,
                )
            )

    def run(self) -> list[BacktestResult]:
        return [runner.run() for runner in self.runners]


class BacktestRunner:
    def __init__(
        self,
        position: Position,
        swaps: list[Swap],
        tracker: ActivityTracker,
        calculator: FeeCalculator,
        rebalance_bias: float,
        created_at: datetime | None = None,
        rebalancer: RebalancingStrategy | None = None,
    ):
        self.position = position
        self.tracker = tracker
        self.calculator = calculator
        self.rebalancer = rebalancer
        self.rebalance_bias = rebalance_bias
        self.swap_series = SwapSeries(swaps=swaps)
        self.created_at = created_at or self.swap_series.timestamps[0]

        # Internal tracking
        self.total_fees = Fee(token0=Decimal("0"), token1=Decimal("0"))
        self.activity_series: ActivityTimeseries
        self.fee_series: FeeTimeseries

    def run(self) -> BacktestResult:
        activities: list[bool] = []
        fees: list[Fee] = []

        initial_token0, initial_token1 = self.position.amount0, self.position.amount1

        for swap in self.swap_series.swaps:
            if self.rebalancer and self.rebalancer.should_rebalance(
                tick=swap.tick,
                timestamp=swap.timestamp,
                tick_lower=self.position.tick_lower,
                tick_upper=self.position.tick_upper,
                created_at=self.created_at,
            ):
                new_lower, new_upper = self.rebalancer.rebalance(
                    tick=swap.tick,
                    tick_lower=self.position.tick_lower,
                    tick_upper=self.position.tick_upper,
                    bias=self.rebalance_bias,
                )
                self.position.tick_lower = new_lower
                self.position.tick_upper = new_upper

            is_active = self.tracker.is_active(swap.tick)
            activities.append(is_active)

            fee = self.calculator.compute_fee_for_swap(swap)
            fees.append(fee)

            if is_active:
                self.total_fees.token0 += fee.token0
                self.total_fees.token1 += fee.token1

        self.activity_series = ActivityTimeseries(
            timestamps=self.swap_series.timestamps,
            activity=activities,
        )
        self.fee_series = FeeTimeseries(
            timestamps=self.swap_series.timestamps,
            fees=fees,
        )

        end_token0 = initial_token0 + self.total_fees.token0
        end_token1 = initial_token1 + self.total_fees.token1

        sqrt_start = self.swap_series.swaps[0].sqrt_price_x96
        sqrt_end = self.swap_series.swaps[-1].sqrt_price_x96
        price0_start = sqrt_start**2
        price0_end = sqrt_end**2
        price1_start = Decimal("1")
        price1_end = Decimal("1")

        duration = (
            self.swap_series.timestamps[-1] - self.swap_series.timestamps[0]
        ).days or 1

        apr = compute_usd_apr(
            token0_start=initial_token0,
            token0_end=end_token0,
            token1_start=initial_token1,
            token1_end=end_token1,
            price0_start=price0_start,
            price0_end=price0_end,
            price1_start=price1_start,
            price1_end=price1_end,
            duration_days=duration,
        )

        return BacktestResult(
            total_fees_token0=self.total_fees.token0,
            total_fees_token1=self.total_fees.token1,
            apr=apr,
        )
