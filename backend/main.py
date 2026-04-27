from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.players import router as players_router
from routes.matches import router as matches_router

app = FastAPI(
    title="Pressure Index Engine",
    description="Cricket clutch performance analytics API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://*.vercel.app",        # Vercel frontend
        "https://*.railway.app",       # Railway
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players_router)
app.include_router(matches_router)

@app.get("/")
def root():
    return {
        "message" : "Pressure Index Engine API",
        "docs"    : "/docs",
        "version" : "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "ok"}