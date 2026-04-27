import os
import yaml
import pandas as pd
from sqlalchemy.orm import Session
from db import SessionLocal, engine
from schema import Delivery, Base

Base.metadata.create_all(bind=engine)

DATA_DIRS = {
    "ipl"  : "../data/raw/ipl",
    "t20"  : "../data/raw/t20s",
    "odi"  : "../data/raw/odis",
    "test" : "../data/raw/tests",
}

def parse_match(filepath: str, fmt: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        match = yaml.safe_load(f)

    match_id   = os.path.basename(filepath).replace(".yaml", "")
    match_date = match.get("info", {}).get("dates", [None])[0]
    teams      = match.get("info", {}).get("teams", ["", ""])
    rows       = []

    for i, inning_block in enumerate(match.get("innings", [])):
        inning_key  = list(inning_block.keys())[0]
        inning_info = inning_block[inning_key]

        team_batting = inning_info.get("team", "")
        team_bowling = [t for t in teams if t != team_batting]
        team_bowling = team_bowling[0] if team_bowling else ""

        target = None
        if i == 1:
            t = inning_info.get("target", None)
            if isinstance(t, dict):
                target = t.get("runs", None)
            elif isinstance(t, int):
                target = t

        deliveries_raw = inning_info.get("deliveries", [])

        for delivery_block in deliveries_raw:
            # ---- NEW FORMAT ----
            # {"batter": ..., "bowler": ..., "runs": {...}, "wickets": [...]}
            if isinstance(delivery_block, dict):
                keys = list(delivery_block.keys())

                # Old format key looks like "0.1", "1.3" etc (over.ball)
                if len(keys) == 1 and "." in str(keys[0]):
                    ball_key = keys[0]
                    delivery = delivery_block[ball_key]

                    parts    = str(ball_key).split(".")
                    over_num = int(parts[0])
                    ball_num = int(parts[1]) if len(parts) > 1 else 1

                    batter      = delivery.get("batsman", delivery.get("batter", ""))
                    bowler      = delivery.get("bowler", "")
                    runs_scored = delivery.get("runs", {}).get("batsman",
                                  delivery.get("runs", {}).get("batter", 0))

                    wicket_info = delivery.get("wicket", {})
                    is_wicket   = 1 if wicket_info else 0
                    wicket_kind = wicket_info.get("kind", "") if isinstance(wicket_info, dict) else ""

                # New format: delivery is the dict itself with "batter", "bowler" keys
                else:
                    # New format deliveries are inside overs blocks
                    # Skip — handled below
                    continue

                rows.append({
                    "match_id"          : match_id,
                    "format"            : fmt,
                    "innings"           : i + 1,
                    "over"              : over_num,
                    "ball"              : ball_num,
                    "batter"            : batter,
                    "bowler"            : bowler,
                    "runs_scored"       : runs_scored,
                    "is_wicket"         : is_wicket,
                    "wicket_kind"       : wicket_kind,
                    "team_batting"      : team_batting,
                    "team_bowling"      : team_bowling,
                    "target"            : target,
                    "match_date"        : match_date,
                    "total_runs_so_far" : 0,
                    "wickets_fallen"    : 0,
                })

        # ---- NEW FORMAT: overs-based structure ----
        # {"overs": [{"over": 0, "deliveries": [{...}, ...]}, ...]}
        if not rows or (rows and rows[-1]["match_id"] != match_id):
            for over_block in inning_info.get("overs", []):
                over_num  = over_block.get("over", 0)
                for ball_num, delivery in enumerate(over_block.get("deliveries", [])):
                    batter      = delivery.get("batter", delivery.get("batsman", ""))
                    bowler      = delivery.get("bowler", "")
                    runs_scored = delivery.get("runs", {}).get("batter",
                                  delivery.get("runs", {}).get("batsman", 0))

                    wickets     = delivery.get("wickets", [])
                    is_wicket   = 1 if wickets else 0
                    wicket_kind = wickets[0].get("kind", "") if wickets else ""

                    rows.append({
                        "match_id"          : match_id,
                        "format"            : fmt,
                        "innings"           : i + 1,
                        "over"              : over_num,
                        "ball"              : ball_num + 1,
                        "batter"            : batter,
                        "bowler"            : bowler,
                        "runs_scored"       : runs_scored,
                        "is_wicket"         : is_wicket,
                        "wicket_kind"       : wicket_kind,
                        "team_batting"      : team_batting,
                        "team_bowling"      : team_bowling,
                        "target"            : target,
                        "match_date"        : match_date,
                        "total_runs_so_far" : 0,
                        "wickets_fallen"    : 0,
                    })

    if not rows:
        return []

    df = pd.DataFrame(rows)
    df["total_runs_so_far"] = df.groupby("innings")["runs_scored"].cumsum()
    df["wickets_fallen"]    = df.groupby("innings")["is_wicket"].cumsum()

    return df.to_dict(orient="records")


def ingest_all():
    db: Session = SessionLocal()
    total = 0

    for fmt, folder in DATA_DIRS.items():
        if not os.path.exists(folder):
            print(f"⚠️  Folder not found: {folder}, skipping.")
            continue

        files = [f for f in os.listdir(folder) if f.endswith(".yaml")]
        print(f"\n📂 Ingesting {len(files)} {fmt.upper()} files...")

        for idx, filename in enumerate(files):
            filepath = os.path.join(folder, filename)
            try:
                rows = parse_match(filepath, fmt)
                if rows:
                    db.bulk_insert_mappings(Delivery, rows)
                    db.commit()
                    total += len(rows)

                if (idx + 1) % 100 == 0:
                    print(f"  ✅ {idx+1}/{len(files)} files done — {total:,} rows inserted")

            except Exception as e:
                db.rollback()
                print(f"  ❌ Error in {filename}: {e}")

    db.close()
    print(f"\n🏁 Ingestion complete. Total rows inserted: {total:,}")


if __name__ == "__main__":
    ingest_all()