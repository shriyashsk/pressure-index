import os
import yaml
import pandas as pd
from db import engine

DATA_DIRS = {
    "ipl"  : "../data/raw/ipl",
    "t20"  : "../data/raw/t20s",
    "odi"  : "../data/raw/odis",
    "test" : "../data/raw/tests",
}

rows = []
for fmt, folder in DATA_DIRS.items():
    if not os.path.exists(folder):
        continue
    files = [f for f in os.listdir(folder) if f.endswith(".yaml")]
    print(f"Reading gender from {len(files)} {fmt} files...")
    for filename in files:
        match_id = filename.replace(".yaml", "")
        filepath = os.path.join(folder, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            gender = data.get("info", {}).get("gender", "male")
            rows.append({"match_id": match_id, "gender": gender})
        except:
            rows.append({"match_id": match_id, "gender": "male"})

df = pd.DataFrame(rows)
df.to_sql("match_gender", engine, if_exists="replace", index=False)
print(f"✅ Saved gender info for {len(df):,} matches")