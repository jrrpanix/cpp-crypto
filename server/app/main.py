from app.routes import router as stats_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()
app.include_router(stats_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
frontend_path = "/workspace/frontend"
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    # Serve index.html at root
    @app.get("/")
    async def serve_index():
        return FileResponse(f"{frontend_path}/index.html")
    
    # Serve dashboard.html 
    @app.get("/dashboard.html")
    async def serve_dashboard():
        return FileResponse(f"{frontend_path}/dashboard.html")
