from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

@app.get("/")
@app.get("/api")
@app.get("/api/")
def root():
    return {
        "app": settings.app_name,
        "tagline": settings.tagline,
        "docs": "/docs",
        "health": "/api/health",
        "scenarios": "/api/scenarios",
        "tools": "/api/tools",
    }
