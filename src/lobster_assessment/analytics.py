# analytics.py
from datetime import datetime

import pandas as pd

from lobster_assessment.db import SessionLocal, get_engine
from lobster_assessment.db_models import Block, UniswapV3Swap


def run_uniswap_query(
    pool_address: str,
    start_date: str,
    end_date: str,
    rows_to_fetch: int = 100,
    total_rows: int = 0,
):
    table_swaps = "uniswap_v3_swap_42161"
    table_blocks = "blocks_42161"

    query = f"""
        SELECT s.*, b.block_date AS timestamp
        FROM public.{table_swaps} s
        JOIN public.{table_blocks} b ON s.block_number = b.block_number
        WHERE LOWER(s.pool_address) = LOWER(%s)
        AND b.block_date BETWEEN %s AND %s
        ORDER BY b.block_date DESC
        LIMIT {rows_to_fetch} OFFSET {total_rows}
    """

    engine = get_engine()

    with engine.connect() as connection:
        df = pd.read_sql_query(
            sql=query, con=connection, params=(pool_address, start_date, end_date)
        )
    print(df.head())
    return df


def run_orm_query(pool: str, start: str, end: str):
    session = SessionLocal()
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")

        query = (
            session.query(UniswapV3Swap, Block.block_date.label("timestamp"))
            .join(Block, UniswapV3Swap.block_number == Block.block_number)
            .filter(UniswapV3Swap.pool_address.ilike(pool))
            .filter(Block.block_date.between(start_dt, end_dt))
            .order_by(Block.block_date.desc())
            .limit(100)
        )
        results = query.all()
        for swap, timestamp in results:
            print(swap.tx_hash, timestamp)
    finally:
        session.close()
