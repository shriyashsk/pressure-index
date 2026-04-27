import pandas as pd
import numpy as np
from db import engine

def load_deliveries() -> pd.DataFrame:
    print("📦 Loading deliveries from database...")
    df = pd.read_sql("SELECT * FROM deliveries ORDER BY match_id, innings, over, ball", engine)
    print(f"✅ Loaded {len(df):,} rows")
    return df

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    print("⚙️  Computing features...")

    group_keys = ["match_id", "innings"]

    # --- Clean target column first ---
    df["target"] = pd.to_numeric(df["target"], errors="coerce")

    # --- Balls bowled so far (within innings) ---
    df["balls_bowled"] = df.groupby(group_keys).cumcount() + 1

    # --- Wickets remaining ---
    df["wickets_remaining"] = 10 - df["wickets_fallen"]

    # --- Match phase ---
    def assign_phase(row):
        fmt  = row["format"]
        over = row["over"]
        if fmt == "test":
            return 1
        elif fmt == "odi":
            if over < 10:   return 0
            elif over < 40: return 1
            else:           return 2
        else:
            if over < 6:    return 0
            elif over < 15: return 1
            else:           return 2

    df["phase"] = df.apply(assign_phase, axis=1)

    # --- Total balls by format ---
    def total_balls(fmt):
        if fmt == "test":  return 450
        elif fmt == "odi": return 300
        else:              return 120

    df["total_balls"]          = df["format"].apply(total_balls)
    df["balls_remaining"]      = (df["total_balls"] - df["balls_bowled"]).clip(lower=0)
    df["balls_remaining_norm"] = df["balls_remaining"] / df["total_balls"]

    # --- Current Run Rate ---
    df["overs_bowled"] = df["balls_bowled"] / 6
    df["crr"] = (
        df["total_runs_so_far"] / df["overs_bowled"].clip(lower=0.1)
    ).round(4)

    # --- Required Run Rate (2nd innings only) ---
    df["rrr"] = 0.0
    mask = (
        (df["innings"] == 2) &
        (df["target"].notna()) &
        (df["balls_remaining"] > 0)
    )
    df.loc[mask, "rrr"] = (
        (df.loc[mask, "target"] - df.loc[mask, "total_runs_so_far"]) /
        (df.loc[mask, "balls_remaining"] / 6).clip(lower=0.1)
    ).clip(lower=0).round(4)

    # --- Run Rate Pressure ---
    df["run_rate_pressure"] = 0.0
    df.loc[mask, "run_rate_pressure"] = (
        df.loc[mask, "rrr"] / df.loc[mask, "crr"].clip(lower=0.1)
    ).clip(upper=10).round(4)

    # --- Wicket pressure ---
    df["wicket_pressure"] = (df["wickets_fallen"] / 10).round(4)

    # --- Partnership balls ---
    def partnership_balls(group):
        balls_since = []
        count = 0
        for w in group["is_wicket"]:
            balls_since.append(count)
            if w == 1:
                count = 0
            else:
                count += 1
        return pd.Series(balls_since, index=group.index)

    df["partnership_balls"] = (
        df.groupby(group_keys, group_keys=False)
        .apply(partnership_balls)
        .fillna(0)
        .astype(int)
    )

    # --- Score deficit ---
    df["score_deficit"] = 0.0
    df.loc[df["innings"] == 2, "score_deficit"] = (
        (
            pd.to_numeric(
                df.loc[df["innings"] == 2, "target"], errors="coerce"
            ).fillna(0) -
            df.loc[df["innings"] == 2, "total_runs_so_far"]
        ).clip(lower=0)
    )

# --- Pressure outcome label (balanced definition) ---
    df["pressure_outcome"] = (
        # Wicket fell
        (df["is_wicket"] == 1) |

        # 2nd innings: chasing and behind on run rate
        (
            (df["innings"] == 2) &
            (df["rrr"] > df["crr"])
        ) |

        # Death overs dot ball (phase 2, any innings)
        (
            (df["runs_scored"] == 0) &
            (df["phase"] == 2)
        ) |

        # Middle overs dot ball with fewer than 5 wickets remaining
        (
            (df["runs_scored"] == 0) &
            (df["phase"] == 1) &
            (df["wickets_remaining"] < 5)
        ) |

        # Any innings, 3 or fewer wickets remaining
        (df["wickets_remaining"] <= 3) |

        # Last 12 balls of T20/IPL innings
        (
            (df["format"].isin(["t20", "ipl"])) &
            (df["balls_remaining"] <= 12)
        )
    ).astype(int)

    print(
        f"✅ Features computed. "
        f"Pressure outcome rate: {df['pressure_outcome'].mean()*100:.2f}%"
    )
    return df


def save_features(df: pd.DataFrame):
    print("💾 Saving features back to database...")

    feature_cols = [
        "id", "phase", "balls_bowled", "balls_remaining", "balls_remaining_norm",
        "wickets_remaining", "crr", "rrr", "run_rate_pressure",
        "wicket_pressure", "partnership_balls", "score_deficit", "pressure_outcome"
    ]

    df_save = df[feature_cols].copy()

    df_save.to_sql(
        "delivery_features",
        engine,
        if_exists="replace",
        index=False,
        chunksize=10000,
        method="multi"
    )
    print(f"✅ Saved {len(df_save):,} rows to 'delivery_features' table")


if __name__ == "__main__":
    df = load_deliveries()
    df = compute_features(df)
    save_features(df)
    print("\n🏁 Phase 2 complete. Ready for model training.")