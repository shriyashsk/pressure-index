from db import Base, engine
from sqlalchemy import Column, Integer, String, Float, Date

class Delivery(Base):
    __tablename__ = "deliveries"

    id              = Column(Integer, primary_key=True, index=True)
    match_id        = Column(String)
    format          = Column(String)
    innings         = Column(Integer)
    over            = Column(Integer)
    ball            = Column(Integer)
    batter          = Column(String, index=True)
    bowler          = Column(String, index=True)
    runs_scored     = Column(Integer)
    is_wicket       = Column(Integer)
    wicket_kind     = Column(String)
    team_batting    = Column(String)
    team_bowling    = Column(String)
    target          = Column(Integer)
    match_date      = Column(Date)
    total_runs_so_far = Column(Integer)
    wickets_fallen  = Column(Integer)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")