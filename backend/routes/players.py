from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from db import get_db
from typing import Optional

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/batters")
def get_batter_leaderboard(
    format : Optional[str] = Query(None, description="ipl / t20 / odi / test"),
    gender : Optional[str] = Query(None, description="male / female"),
    page   : int = Query(1,  ge=1),
    limit  : int = Query(20, ge=1, le=100),
    db     : Session = Depends(get_db)
):
    filters = ["role = 'batter'"]
    params  = {}

    if format:
        filters.append("format = :format")
        params["format"] = format
    if gender:
        filters.append("gender = :gender")
        params["gender"] = gender

    where = " AND ".join(filters)
    offset = (page - 1) * limit
    params["limit"]  = limit
    params["offset"] = offset

    query = text(f"""
        SELECT player, format, gender, clutch_score,
               high_pressure_balls, runs_under_pressure,
               avg_pressure_faced, total_balls
        FROM player_pressure_stats
        WHERE {where}
        ORDER BY clutch_score DESC
        LIMIT :limit OFFSET :offset
    """)

    total_query = text(f"""
        SELECT COUNT(*) FROM player_pressure_stats WHERE {where}
    """)

    rows  = db.execute(query, params).fetchall()
    total = db.execute(total_query, {k: v for k, v in params.items()
                                     if k not in ("limit", "offset")}).scalar()

    return {
        "page"    : page,
        "limit"   : limit,
        "total"   : total,
        "results" : [dict(r._mapping) for r in rows]
    }


@router.get("/bowlers")
def get_bowler_leaderboard(
    format : Optional[str] = Query(None),
    gender : Optional[str] = Query(None),
    page   : int = Query(1,  ge=1),
    limit  : int = Query(20, ge=1, le=100),
    db     : Session = Depends(get_db)
):
    filters = ["role = 'bowler'"]
    params  = {}

    if format:
        filters.append("format = :format")
        params["format"] = format
    if gender:
        filters.append("gender = :gender")
        params["gender"] = gender

    where  = " AND ".join(filters)
    offset = (page - 1) * limit
    params["limit"]  = limit
    params["offset"] = offset

    query = text(f"""
        SELECT player, format, gender, clutch_score,
               high_pressure_balls, wickets_under_pressure,
               avg_pressure_faced, total_balls
        FROM player_pressure_stats
        WHERE {where}
        ORDER BY clutch_score DESC
        LIMIT :limit OFFSET :offset
    """)

    total_query = text(f"""
        SELECT COUNT(*) FROM player_pressure_stats WHERE {where}
    """)

    rows  = db.execute(query, params).fetchall()
    total = db.execute(total_query, {k: v for k, v in params.items()
                                     if k not in ("limit", "offset")}).scalar()

    return {
        "page"    : page,
        "limit"   : limit,
        "total"   : total,
        "results" : [dict(r._mapping) for r in rows]
    }


@router.get("/compare")
def compare_players(
    p1     : str = Query(..., description="First player name"),
    p2     : str = Query(..., description="Second player name"),
    format : Optional[str] = Query(None),
    gender : Optional[str] = Query(None),
    db     : Session = Depends(get_db)
):
    filters = ["player IN :players"]
    params  = {"players": tuple([p1, p2])}

    if format:
        filters.append("format = :format")
        params["format"] = format
    if gender:
        filters.append("gender = :gender")
        params["gender"] = gender

    where = " AND ".join(filters)
    query = text(f"""
        SELECT player, role, format, gender, clutch_score,
               high_pressure_balls, runs_under_pressure,
               wickets_under_pressure, avg_pressure_faced
        FROM player_pressure_stats
        WHERE {where}
        ORDER BY player, format
    """)

    rows = db.execute(query, params).fetchall()
    return {"results": [dict(r._mapping) for r in rows]}


@router.get("/{player_name}/profile")
def get_player_profile(
    player_name : str,
    db          : Session = Depends(get_db)
):
    # All formats + roles for this player
    query = text("""
        SELECT player, role, format, gender, clutch_score,
               high_pressure_balls, runs_under_pressure,
               wickets_under_pressure, avg_pressure_faced,
               total_balls
        FROM player_pressure_stats
        WHERE player ILIKE :name
        ORDER BY format
    """)
    rows = db.execute(query, {"name": f"%{player_name}%"}).fetchall()

    if not rows:
        return {"error": f"Player '{player_name}' not found"}

    results = [dict(r._mapping) for r in rows]
    player  = results[0]["player"]

    # Aggregate across formats
    total_hp_balls   = sum(r["high_pressure_balls"] for r in results if r["role"] == "batter")
    total_runs_up    = sum(r["runs_under_pressure"] for r in results if r["role"] == "batter")
    overall_clutch   = round(total_runs_up / total_hp_balls, 4) if total_hp_balls > 0 else 0

    return {
        "player"          : player,
        "overall_clutch_score" : overall_clutch,
        "by_format"       : results,
    }