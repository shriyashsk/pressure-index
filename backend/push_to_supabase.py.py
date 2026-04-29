import pandas as pd
from sqlalchemy import create_engine, text

LOCAL_URL = "postgresql://postgres:Koro1004@localhost:5433/pressure_index"
SUPABASE_URL = "postgresql://postgres.ulbbuitgikzgcdtmfpru:ACsjY4rbPUtZN4KC@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

local_engine    = create_engine(LOCAL_URL)
supabase_engine = create_engine(SUPABASE_URL)

def push_table(table_name, query, chunk_size=5000):
    print(f"\n📤 Pushing {table_name}...")
    df = pd.read_sql(query, local_engine)
    print(f"   Loaded {len(df):,} rows locally")

    df.to_sql(
        table_name,
        supabase_engine,
        if_exists="replace",
        index=False,
        chunksize=chunk_size,
        method="multi"
    )
    print(f"   ✅ Pushed {len(df):,} rows to Supabase")

if __name__ == "__main__":
    # 1. Player stats — tiny, push first
    push_table(
        "player_pressure_stats",
        "SELECT * FROM player_pressure_stats"
    )

    # 2. Match gender — tiny
    push_table(
        "match_gender",
        "SELECT * FROM match_gender"
    )

    # 3. Slim delivery features — IPL + T20 only
    push_table(
        "delivery_features_slim",
        """
        SELECT 
            d.match_id, d.innings, d.over, d.ball,
            d.batter, d.bowler, d.runs_scored, d.is_wicket,
            d.wicket_kind, d.team_batting, d.team_bowling,
            d.total_runs_so_far, d.match_date, d.format,
            df.pressure_index, df.crr, df.rrr,
            df.phase, df.wickets_remaining
        FROM delivery_features df
        JOIN deliveries d ON d.id = df.id
        WHERE d.format IN ('ipl', 't20')
        """,
        chunk_size=2000
    )

    print("\n🏁 All tables pushed to Supabase successfully!")