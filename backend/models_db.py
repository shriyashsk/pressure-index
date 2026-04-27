from sqlalchemy import Column, Integer, String, Float, Date
from db import Base

class PlayerPressureStat(Base):
    __tablename__ = "player_pressure_stats"

    id                     = Column(Integer, primary_key=True, autoincrement=True)
    player                 = Column(String, index=True)
    role                   = Column(String)
    format                 = Column(String, index=True)
    gender                 = Column(String, index=True)
    total_balls            = Column(Integer)
    high_pressure_balls    = Column(Integer)
    runs_under_pressure    = Column(Integer)
    wickets_under_pressure = Column(Integer)
    clutch_score           = Column(Float)
    avg_pressure_faced     = Column(Float)


class Delivery(Base):
    __tablename__ = "deliveries"

    id              = Column(Integer, primary_key=True)
    match_id        = Column(String, index=True)
    format          = Column(String)
    innings         = Column(Integer)
    over            = Column(Integer)
    ball            = Column(Integer)
    batter          = Column(String)
    bowler          = Column(String)
    runs_scored     = Column(Integer)
    is_wicket       = Column(Integer)
    wicket_kind     = Column(String)
    team_batting    = Column(String)
    team_bowling    = Column(String)
    target          = Column(Integer)
    match_date      = Column(Date)
    total_runs_so_far = Column(Integer)
    wickets_fallen  = Column(Integer)


class DeliveryFeature(Base):
    __tablename__ = "delivery_features"

    id                  = Column(Integer, primary_key=True)
    phase               = Column(Integer)
    balls_bowled        = Column(Integer)
    balls_remaining     = Column(Integer)
    balls_remaining_norm = Column(Float)
    wickets_remaining   = Column(Integer)
    crr                 = Column(Float)
    rrr                 = Column(Float)
    run_rate_pressure   = Column(Float)
    wicket_pressure     = Column(Float)
    partnership_balls   = Column(Integer)
    score_deficit       = Column(Float)
    pressure_outcome    = Column(Integer)
    pressure_index      = Column(Float)