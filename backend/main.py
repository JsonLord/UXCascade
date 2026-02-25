from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
  experiments_router,
  fixes_router,
  goals_router,
  issues_router,
  journeys_router,
  runs_router,
  ws_router,
)

app = FastAPI(title="UXCascade API")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:5173"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(experiments_router, prefix="/experiments")
app.include_router(runs_router, prefix="/experiments")
app.include_router(goals_router, prefix="/experiments")
app.include_router(issues_router, prefix="/experiments")
app.include_router(fixes_router, prefix="/experiments")
app.include_router(journeys_router, prefix="/experiments")
app.include_router(ws_router, prefix="/ws/experiments")


@app.get("/")
def read_root():
  return {"message": "UXCascade backend"}
