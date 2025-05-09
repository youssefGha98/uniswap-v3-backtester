from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, List

from pydantic import BaseModel, Field, field_validator, validate_call


class RebalancingStrategy(BaseModel):
    def should_rebalance(
        self,
        tick: int,
        timestamp: datetime,
        tick_lower: int,
        tick_upper: int,
        created_at: datetime,
    ) -> bool:
        raise NotImplementedError

    @validate_call
    def rebalance(
        self,
        tick: int,
        tick_lower: int,
        tick_upper: int,
        bias: Annotated[float, Field(ge=0.0, le=1.0)],
    ) -> tuple[int, int]:
        raise NotImplementedError


class TimeTriggeredRebalancer(RebalancingStrategy):
    interval: timedelta
    last_rebalanced_at: datetime | None = None

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v: timedelta) -> timedelta:
        if v.total_seconds() < 0:
            raise ValueError("Interval must be non-negative")
        return v

    def should_rebalance(
        self,
        tick: int,
        timestamp: datetime,
        tick_lower: int,
        tick_upper: int,
        created_at: datetime,
    ) -> bool:
        check_tick_upper_greater_than_lower(tick_lower, tick_upper)
        reference_time = self.last_rebalanced_at or created_at
        return (timestamp - reference_time) >= self.interval

    def rebalance(
        self, tick: int, tick_lower: int, tick_upper: int, bias: float
    ) -> tuple[int, int]:
        check_tick_upper_greater_than_lower(tick_lower, tick_upper)
        self.last_rebalanced_at = datetime.now()
        width = tick_upper - tick_lower
        return compute_tick_range(tick, width, bias)


class OutOfRangeRebalancer(RebalancingStrategy):
    def should_rebalance(
        self,
        tick: int,
        timestamp: datetime,
        tick_lower: int,
        tick_upper: int,
        created_at: datetime,
    ) -> bool:
        check_tick_upper_greater_than_lower(tick_lower, tick_upper)
        return not (tick_lower <= tick <= tick_upper)

    def rebalance(
        self, tick: int, tick_lower: int, tick_upper: int, bias: float
    ) -> tuple[int, int]:
        check_tick_upper_greater_than_lower(tick_lower, tick_upper)
        width = tick_upper - tick_lower
        return compute_tick_range(tick, width, bias)


class OutOfRangeDurationRebalancer(RebalancingStrategy):
    duration: timedelta
    out_of_range_since: datetime | None = None

    def should_rebalance(
        self,
        tick: int,
        timestamp: datetime,
        tick_lower: int,
        tick_upper: int,
        created_at: datetime,
    ) -> bool:
        check_tick_upper_greater_than_lower(tick_lower, tick_upper)
        in_range = tick_lower <= tick <= tick_upper

        if in_range:
            self.out_of_range_since = None
            return False
        reference_time = self.out_of_range_since or created_at
        return (timestamp - reference_time) >= self.duration

    def rebalance(
        self, tick: int, tick_lower: int, tick_upper: int, bias: float
    ) -> tuple[int, int]:
        check_tick_upper_greater_than_lower(tick_lower, tick_upper)
        self.out_of_range_since = None
        width = tick_upper - tick_lower
        return compute_tick_range(tick, width, bias)


class LogicMode(Enum):
    AND = "and"
    OR = "or"


class MultiConditionRebalancer(RebalancingStrategy):
    strategies: List[RebalancingStrategy]
    mode: LogicMode

    def should_rebalance(
        self,
        tick: int,
        timestamp: datetime,
        tick_lower: int,
        tick_upper: int,
        created_at: datetime,
    ) -> bool:
        check_tick_upper_greater_than_lower(tick_lower, tick_upper)
        if not self.strategies:
            return False
        checks = [
            s.should_rebalance(tick, timestamp, tick_lower, tick_upper, created_at)
            for s in self.strategies
        ]
        return all(checks) if self.mode == LogicMode.AND else any(checks)

    def rebalance(
        self, tick: int, tick_lower: int, tick_upper: int, bias: float
    ) -> tuple[int, int]:
        check_tick_upper_greater_than_lower(tick_lower, tick_upper)
        return self.strategies[0].rebalance(tick, tick_lower, tick_upper, bias)


def compute_tick_range(tick: int, width: int, bias: float) -> tuple[int, int]:
    """
    Compute new tick_lower and tick_upper from center tick, width, and bias.

    - bias = 0.5 → balanced around tick
    - bias = 0.0 → all above tick (token0-heavy)
    - bias = 1.0 → all below tick (token1-heavy)
    """
    if not 0.0 <= bias <= 1.0:
        raise ValueError("Bias must be between 0.0 and 1.0")

    left = int(width * bias)
    right = width - left
    return tick - left, tick + right


def generate_position_id(tick_lower: int, tick_upper: int, created_at: datetime) -> str:
    return f"{tick_lower:x}_{tick_upper:x}_{int(created_at.timestamp()):x}"


def check_tick_upper_greater_than_lower(tick_lower: int, tick_upper: int) -> None:
    if tick_upper < tick_lower:
        raise ValueError("tick_upper must be >= tick_lower")
