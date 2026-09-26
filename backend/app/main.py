import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import settings
from .api.routes import router

app = FastAPI(
    title=settings.app_name,
    description=settings.tagline,
    version=settings.version,
)

# CORS middleware for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes with /api prefix and fallback without prefix for Vercel/proxies
app.include_router(router, prefix="/api")
app.include_router(router)

@app.get("/api")
@app.get("/api/")
@app.get("/api/info")
def api_info():
    return {
        "app": settings.app_name,
        "tagline": settings.tagline,
        "docs": "/docs",
        "health": "/api/health",
        "scenarios": "/api/scenarios",
        "tools": "/api/tools",
    }

# Find frontend dist path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
frontend_dist = os.path.join(root_dir, "frontend", "dist")

if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
def read_root():
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "app": settings.app_name,
        "tagline": settings.tagline,
        "docs": "/docs",
        "health": "/api/health",
        "scenarios": "/api/scenarios",
        "tools": "/api/tools",
    }

@app.get("/{full_path:path}")
def catch_all(full_path: str):
    # Don't intercept API routes or docs
    if full_path.startswith("api/") or full_path == "api" or full_path.startswith("docs") or full_path.startswith("openapi.json"):
        return {"detail": "Not Found"}
    
    file_path = os.path.join(frontend_dist, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
        
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
        
    return {"detail": "Not Found"}
