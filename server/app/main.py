from fastapi import FastAPI
from app.routes import router as stats_router
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()
app.include_router(stats_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
