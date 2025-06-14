from fastapi import FastAPI
from app.routes import router as stats_router

app = FastAPI()
app.include_router(stats_router)
