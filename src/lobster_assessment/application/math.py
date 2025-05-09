from decimal import Decimal


def tick_to_sqrt_price(tick: int) -> Decimal:
    """Convert a tick to its corresponding square root price (P = sqrt(price))."""
    return Decimal(1.0001) ** Decimal(tick / 2)


def compute_liquidity_from_amounts(
    tick_lower: int,
    tick_upper: int,
    amount0: Decimal,
    amount1: Decimal,
) -> Decimal:
    """
    Compute liquidity from token amounts given a tick range.
    Assumes both tokens are deposited at once, so liquidity is limited by the scarcer asset.
    """
    if tick_lower >= tick_upper:
        raise ValueError("tick_lower must be less than tick_upper")

    sqrt_PA = tick_to_sqrt_price(tick_lower)
    sqrt_PB = tick_to_sqrt_price(tick_upper)

    L0 = (amount0 * sqrt_PA * sqrt_PB) / (sqrt_PB - sqrt_PA)
    L1 = amount1 / (sqrt_PB - sqrt_PA)

    return min(L0, L1)


def compute_token0_amount(
    liquidity: Decimal, sqrt_PA: Decimal, sqrt_PB: Decimal
) -> Decimal:
    """Compute required amount0 for given liquidity and price range."""
    return liquidity * (sqrt_PB - sqrt_PA) / (sqrt_PB * sqrt_PA)


def compute_token1_amount(
    liquidity: Decimal, sqrt_PA: Decimal, sqrt_PB: Decimal
) -> Decimal:
    """Compute required amount1 for given liquidity and price range."""
    return liquidity * (sqrt_PB - sqrt_PA)


def compute_token_amounts_from_liquidity(
    liquidity: Decimal, tick_lower: int, tick_upper: int
) -> tuple[Decimal, Decimal]:
    """
    Given liquidity and a tick range, compute the equivalent token0 and token1 amounts.
    Useful for estimating balance at mint or at burn.
    """
    sqrt_PA = tick_to_sqrt_price(tick_lower)
    sqrt_PB = tick_to_sqrt_price(tick_upper)

    amount0 = compute_token0_amount(liquidity, sqrt_PA, sqrt_PB)
    amount1 = compute_token1_amount(liquidity, sqrt_PA, sqrt_PB)

    return amount0, amount1


def compute_token_native_apr(
    token_start: Decimal, token_end: Decimal, duration_days: int
) -> Decimal:
    if token_start == 0 or duration_days == 0:
        return Decimal(0)
    return (
        ((token_end / token_start) - 1) * (Decimal(365) / Decimal(duration_days)) * 100
    )


def compute_usd_apr(
    token0_start: Decimal,
    token0_end: Decimal,
    token1_start: Decimal,
    token1_end: Decimal,
    price0_start: Decimal,
    price0_end: Decimal,
    price1_start: Decimal,
    price1_end: Decimal,
    duration_days: int,
) -> Decimal:
    if duration_days == 0:
        return Decimal(0)

    usd_start = token0_start * price0_start + token1_start * price1_start
    usd_end = token0_end * price0_end + token1_end * price1_end

    if usd_start == 0:
        return Decimal(0)

    performance = usd_end / usd_start
    apr = (performance - 1) * Decimal(365) / Decimal(duration_days) * 100
    return apr
