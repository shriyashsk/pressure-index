import pandas as pd
import numpy as np
import joblib
import os
from sqlalchemy import text
from db import engine
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, classification_report, confusion_matrix
)

FEATURES = [
    "crr", "rrr", "run_rate_pressure", "phase",
    "wicket_pressure", "balls_remaining_norm",
    "partnership_balls", "score_deficit"
]
TARGET   = "pressure_outcome"
MODEL_PATH = "../models/pressure_model.pkl"

def load_features() -> pd.DataFrame:
    print("📦 Loading features from database...")
    query = f"""
        SELECT df.id, df.pressure_outcome,
               df.crr, df.rrr, df.run_rate_pressure, df.phase,
               df.wicket_pressure, df.balls_remaining_norm,
               df.partnership_balls, df.score_deficit
        FROM delivery_features df
    """
    df = pd.read_sql(query, engine)
    print(f"✅ Loaded {len(df):,} rows")
    return df


def train_model(df: pd.DataFrame):
    print("\n🔧 Preparing training data...")

    X = df[FEATURES].fillna(0)
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"   Train size : {len(X_train):,}")
    print(f"   Test size  : {len(X_test):,}")
    print(f"   Positive rate (train): {y_train.mean()*100:.2f}%")

    print("\n🚀 Training XGBoost model...")
    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
        eval_metric="auc",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50,
    )

    print("\n📊 Evaluating model...")
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred       = (y_pred_proba >= 0.5).astype(int)

    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"\n✅ ROC-AUC Score : {auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["No Pressure", "Pressure"]))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Feature importances
    print("\n🔍 Feature Importances:")
    importances = pd.Series(model.feature_importances_, index=FEATURES)
    for feat, imp in importances.sort_values(ascending=False).items():
        bar = "█" * int(imp * 50)
        print(f"   {feat:<25} {bar} {imp:.4f}")

    return model, X_test, y_test, y_pred_proba


def save_model(model):
    os.makedirs("../models", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\n💾 Model saved to {MODEL_PATH}")


def save_pressure_scores(df: pd.DataFrame, model):
    print("\n📈 Computing pressure scores for all deliveries...")

    X = df[FEATURES].fillna(0)
    df["pressure_index"] = model.predict_proba(X)[:, 1]

    # Save pressure index back to delivery_features
    print("💾 Saving pressure index to database...")
    with engine.connect() as conn:
        for chunk_start in range(0, len(df), 10000):
            chunk = df.iloc[chunk_start:chunk_start + 10000]
            for _, row in chunk.iterrows():
                conn.execute(
                    text("""
                        UPDATE delivery_features
                        SET pressure_index = :pi
                        WHERE id = :id
                    """),
                    {"pi": float(row["pressure_index"]), "id": int(row["id"])}
                )
            conn.commit()
            if (chunk_start // 10000 + 1) % 50 == 0:
                print(f"   Updated {chunk_start + 10000:,} rows...")

    print("✅ Pressure index saved.")


def compute_player_stats(model):
    print("\n🏏 Computing player clutch scores...")

    query = """
        SELECT d.batter, d.bowler, d.runs_scored, d.is_wicket,
               d.innings, d.format,
               i.gender,
               df.crr, df.rrr, df.run_rate_pressure, df.phase,
               df.wicket_pressure, df.balls_remaining_norm,
               df.partnership_balls, df.score_deficit
        FROM deliveries d
        JOIN delivery_features df ON d.id = df.id
        LEFT JOIN (
            SELECT DISTINCT match_id, gender
            FROM match_info
        ) i ON d.match_id = i.match_id
    """

    # match_info table may not exist yet — we'll build gender from file info
    # Instead, infer gender from format label in deliveries
    query = """
        SELECT d.batter, d.bowler, d.runs_scored, d.is_wicket,
               d.innings, d.format, d.match_id,
               df.crr, df.rrr, df.run_rate_pressure, df.phase,
               df.wicket_pressure, df.balls_remaining_norm,
               df.partnership_balls, df.score_deficit
        FROM deliveries d
        JOIN delivery_features df ON d.id = df.id
    """
    df = pd.read_sql(query, engine)
    X  = df[FEATURES].fillna(0)
    df["pressure_index"] = model.predict_proba(X)[:, 1]

    # Load gender info from Cricsheet metadata
    # Gender is stored in the YAML info.gender field — re-read it from DB match_ids
    print("   Loading gender metadata...")
    gender_df = pd.read_sql("SELECT match_id, gender FROM match_gender", engine)
    df = df.merge(gender_df, on="match_id", how="left")
    df["gender"] = df["gender"].fillna("male")  # default to male if missing

    HIGH_PRESSURE = 0.5
    MIN_HP_BALLS  = 200

    all_stats = []

    formats  = df["format"].unique()
    genders  = df["gender"].unique()

    for gender in genders:
        for fmt in formats:
            subset = df[(df["gender"] == gender) & (df["format"] == fmt)]
            if len(subset) < 1000:
                continue

            print(f"   Processing {gender} {fmt}...")

            # Batter stats
            for batter, grp in subset.groupby("batter"):
                hp      = grp[grp["pressure_index"] >= HIGH_PRESSURE]
                hp_balls = len(hp)
                if hp_balls < MIN_HP_BALLS:
                    continue
                runs_up  = hp["runs_scored"].sum()
                wkts_up  = hp["is_wicket"].sum()
                all_stats.append({
                    "player"                 : batter,
                    "role"                   : "batter",
                    "format"                 : fmt,
                    "gender"                 : gender,
                    "total_balls"            : len(grp),
                    "high_pressure_balls"    : hp_balls,
                    "runs_under_pressure"    : int(runs_up),
                    "wickets_under_pressure" : int(wkts_up),
                    "clutch_score"           : round(runs_up / hp_balls, 4),
                    "avg_pressure_faced"     : round(grp["pressure_index"].mean(), 4),
                })

            # Bowler stats
            for bowler, grp in subset.groupby("bowler"):
                hp       = grp[grp["pressure_index"] >= HIGH_PRESSURE]
                hp_balls = len(hp)
                if hp_balls < MIN_HP_BALLS:
                    continue
                runs_con = hp["runs_scored"].sum()
                wkts_tk  = hp["is_wicket"].sum()
                all_stats.append({
                    "player"                 : bowler,
                    "role"                   : "bowler",
                    "format"                 : fmt,
                    "gender"                 : gender,
                    "total_balls"            : len(grp),
                    "high_pressure_balls"    : hp_balls,
                    "runs_under_pressure"    : int(runs_con),
                    "wickets_under_pressure" : int(wkts_tk),
                    "clutch_score"           : round(wkts_tk / hp_balls * 100, 4),
                    "avg_pressure_faced"     : round(grp["pressure_index"].mean(), 4),
                })

    stats_df = pd.DataFrame(all_stats)
    stats_df.to_sql(
        "player_pressure_stats",
        engine,
        if_exists="replace",
        index=False
    )
    print(f"✅ Saved stats for {len(stats_df):,} player-format-gender combinations")

    # Print top 10 per gender per format for batters
    for gender in genders:
        for fmt in formats:
            sub = stats_df[
                (stats_df["gender"] == gender) &
                (stats_df["format"] == fmt) &
                (stats_df["role"] == "batter")
            ].sort_values("clutch_score", ascending=False).head(10)
            if len(sub) == 0:
                continue
            print(f"\n🏆 Top Clutch Batters — {gender.upper()} {fmt.upper()}:")
            print(sub[["player", "clutch_score",
                        "high_pressure_balls",
                        "runs_under_pressure"]].to_string(index=False))

if __name__ == "__main__":
    df             = load_features()
    model, X_test, y_test, y_pred_proba = train_model(df)
    save_model(model)
    compute_player_stats(model)
    print("\n🏁 Phase 3 complete. Ready for FastAPI backend.")