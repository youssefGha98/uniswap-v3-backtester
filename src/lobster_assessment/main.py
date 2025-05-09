from lobster_assessment.analytics import run_orm_query, run_uniswap_query

if __name__ == "__main__":
    pool = "0x149e36e72726e0bcea5c59d40df2c43f60f5a22d"
    start = "2021-12-09"
    end = "2021-12-10"
    # run_uniswap_query(pool, start, end)
    run_orm_query(pool, start, end)
