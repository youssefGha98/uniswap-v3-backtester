from decimal import Decimal

import pytest

from lobster_assessment.application.math import (
    compute_liquidity_from_amounts,
    compute_token0_amount,
    compute_token1_amount,
    compute_token_amounts_from_liquidity,
    compute_token_native_apr,
    compute_usd_apr,
    tick_to_sqrt_price,
)


def test_tick_to_sqrt_given_null_value():
    tick = 0
    expected = Decimal("1")
    result = tick_to_sqrt_price(tick)
    assert result == expected


def test_tick_to_sqrt_given_positive_value():
    tick = 1
    expected = Decimal("1.00004999")
    result = tick_to_sqrt_price(tick)

    assert result == pytest.approx(expected, 8)


def test_tick_to_sqrt_given_negative_value():
    tick = -1
    expected = Decimal("0.99995")
    result = tick_to_sqrt_price(tick)

    assert result == pytest.approx(expected, 8)


def test_tick_to_sqrt_large_tick():
    tick = 100000
    result = tick_to_sqrt_price(tick)
    assert result > 0


def test_tick_to_sqrt_negative_large_tick():
    tick = -100000
    result = tick_to_sqrt_price(tick)
    assert result > 0


def test_compute_liquidity_from_amounts_zero_amounts():
    tick_lower = 100
    tick_upper = 200
    amount0 = Decimal("0")
    amount1 = Decimal("0")
    result = compute_liquidity_from_amounts(tick_lower, tick_upper, amount0, amount1)
    assert result == Decimal("0")


def test_compute_liquidity_from_amounts_invalid_ticks():
    tick_lower = 200
    tick_upper = 100
    with pytest.raises(ValueError):
        compute_liquidity_from_amounts(
            tick_lower, tick_upper, Decimal("1"), Decimal("1")
        )


def test_compute_liquidity_from_amounts_manual():
    tick_lower = 100
    tick_upper = 200
    amount0 = Decimal("1")
    amount1 = Decimal("2000")
    expected_liquidity = Decimal("201.515")

    liquidity = compute_liquidity_from_amounts(tick_lower, tick_upper, amount0, amount1)

    assert liquidity == pytest.approx(expected_liquidity, 8)


def test_compute_token0_amount():
    sqrt_PA = Decimal("1.1")
    sqrt_PB = Decimal("1.3")
    liquidity = Decimal("5000")
    result = compute_token0_amount(liquidity, sqrt_PA, sqrt_PB)
    expected = Decimal("699.3")

    assert result == pytest.approx(expected, 8)


def test_compute_token0_amount_zero_liquidity():
    result = compute_token0_amount(Decimal("0"), Decimal("1.1"), Decimal("1.3"))
    assert result == Decimal("0")


def test_compute_token1_amount():
    sqrt_PA = Decimal("1.1")
    sqrt_PB = Decimal("1.3")
    liquidity = Decimal("5000")
    result = compute_token1_amount(liquidity, sqrt_PA, sqrt_PB)
    expected = Decimal("1000.0")

    assert result == expected


def test_compute_token1_amount_zero_liquidity():
    result = compute_token1_amount(Decimal("0"), Decimal("1.1"), Decimal("1.3"))
    assert result == Decimal("0")


def test_compute_token_amounts_from_liquidity():
    liquidity = Decimal("1000")
    tick_lower = 100
    tick_upper = 120
    amount0, amount1 = compute_token_amounts_from_liquidity(
        liquidity, tick_lower, tick_upper
    )
    expected_0 = Decimal("0.99446")
    expected_1 = Decimal("1.00546")

    assert amount0 == pytest.approx(expected_0, 8)
    assert amount1 == pytest.approx(expected_1, 8)


def test_compute_token_native_apr_zero_duration():
    result = compute_token_native_apr(Decimal("100"), Decimal("110"), 0)
    assert result == Decimal("0")


def test_compute_token_native_apr_zero_start():
    result = compute_token_native_apr(Decimal("0"), Decimal("110"), 30)
    assert result == Decimal("0")


def test_compute_token_native_apr():
    result = compute_token_native_apr(Decimal("100"), Decimal("110"), 365)
    assert result == Decimal("10")


def test_compute_usd_apr_zero_duration():
    result = compute_usd_apr(
        Decimal("1"),
        Decimal("1.1"),
        Decimal("1000"),
        Decimal("950"),
        Decimal("2000"),
        Decimal("2100"),
        Decimal("1"),
        Decimal("1.1"),
        0,
    )
    assert result == Decimal("0")


def test_compute_usd_apr_zero_usd_start():
    result = compute_usd_apr(
        Decimal("0"),
        Decimal("0"),
        Decimal("0"),
        Decimal("0"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        30,
    )
    assert result == Decimal("0")


def test_compute_token_native_apr_manual():
    t0_start = Decimal("1")
    t0_end = Decimal("1.1")
    t1_start = Decimal("1000")
    t1_end = Decimal("950")
    p0_start = Decimal("2000")
    p0_end = Decimal("2100")
    p1_start = Decimal("1")
    p1_end = Decimal("1.1")
    duration = 365

    expected_apr = Decimal("11.833")

    result = compute_usd_apr(
        t0_start, t0_end, t1_start, t1_end, p0_start, p0_end, p1_start, p1_end, duration
    )

    assert result == pytest.approx(expected_apr, 8)
