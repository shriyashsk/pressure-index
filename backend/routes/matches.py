from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from db import get_db
from typing import Optional

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/")
def list_matches(
    format  : Optional[str] = Query(None),
    team    : Optional[str] = Query(None),
    page    : int = Query(1,  ge=1),
    limit   : int = Query(20, ge=1, le=100),
    db      : Session = Depends(get_db)
):
    filters = ["1=1"]
    params  = {}

    if format:
        filters.append("format = :format")
        params["format"] = format
    if team:
        filters.append(
            "(team_batting ILIKE :team OR team_bowling ILIKE :team)"
        )
        params["team"] = f"%{team}%"

    where  = " AND ".join(filters)
    offset = (page - 1) * limit
    params["limit"]  = limit
    params["offset"] = offset

    query = text(f"""
        SELECT DISTINCT match_id, format, match_date,
               team_batting, team_bowling
        FROM deliveries
        WHERE {where}
        ORDER BY match_date DESC
        LIMIT :limit OFFSET :offset
    """)

    rows = db.execute(query, params).fetchall()
    return {
        "page"    : page,
        "limit"   : limit,
        "results" : [dict(r._mapping) for r in rows]
    }


@router.get("/{match_id}/timeline")
def get_match_timeline(
    match_id : str,
    innings  : int = Query(1, ge=1, le=4),
    db       : Session = Depends(get_db)
):
    query = text("""
        SELECT d.over, d.ball, d.batter, d.bowler,
               d.runs_scored, d.is_wicket, d.wicket_kind,
               d.total_runs_so_far, d.wickets_fallen,
               df.pressure_index, df.crr, df.rrr,
               df.phase, df.wickets_remaining
        FROM deliveries d
        JOIN delivery_features df ON d.id = df.id
        WHERE d.match_id = :match_id
          AND d.innings  = :innings
        ORDER BY d.over, d.ball
    """)

    rows = db.execute(query, {
        "match_id": match_id,
        "innings" : innings
    }).fetchall()

    if not rows:
        return {"error": "Match or innings not found"}

    deliveries = [dict(r._mapping) for r in rows]

    # Find peak pressure moments
    sorted_by_pressure = sorted(
        deliveries,
        key=lambda x: x["pressure_index"] or 0,
        reverse=True
    )
    peak_moments = sorted_by_pressure[:5]

    return {
        "match_id"     : match_id,
        "innings"      : innings,
        "total_balls"  : len(deliveries),
        "peak_pressure_moments" : peak_moments,
        "timeline"     : deliveries,
    }