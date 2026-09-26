import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
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

def get_index_html() -> str:
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist", "index.html"),
        os.path.join(os.getcwd(), "frontend", "dist", "index.html"),
        os.path.join(os.getcwd(), "dist", "index.html"),
        "/var/task/frontend/dist/index.html",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
    
    # Embedded production HTML
    return """<!doctype html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23f1763a'><polygon points='12 2 2 7 12 12 22 7 12 2'/><polyline points='2 17 12 22 22 17'/><polyline points='2 12 12 17 22 12'/></svg>" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>OpsPilot | AI Business Operator for Payments & Operations</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script type="module" crossorigin src="/assets/index-Ce3jPiPU.js"></script>
    <link rel="stylesheet" crossorigin href="/assets/index-C4erHcDC.css">
  </head>
  <body class="bg-dark-950 text-slate-100 antialiased min-h-screen selection:bg-brand-500 selection:text-white">
    <div id="root"></div>
  </body>
</html>"""

@app.get("/")
@app.get("/index.html")
@app.get("/api/index.py")
@app.get("/api/index")
@app.get("/command")
@app.get("/admin")
def serve_ui():
    return HTMLResponse(content=get_index_html(), status_code=200)

@app.get("/assets/{file_name}")
def serve_asset(file_name: str):
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist", "assets", file_name),
        os.path.join(os.getcwd(), "frontend", "dist", "assets", file_name),
        os.path.join(os.getcwd(), "dist", "assets", file_name),
        f"/var/task/frontend/dist/assets/{file_name}",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            media_type = "text/javascript" if file_name.endswith(".js") else "text/css" if file_name.endswith(".css") else None
            return FileResponse(p, media_type=media_type)
    return HTMLResponse(content=get_index_html(), status_code=200)

@app.get("/api")
@app.get("/api/")
def api_root():
    return {
        "app": settings.app_name,
        "tagline": settings.tagline,
        "docs": "/docs",
        "health": "/api/health",
        "scenarios": "/api/scenarios",
        "tools": "/api/tools",
    }

# 404 Fallback for SPA routing
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    path = request.url.path
    if path.startswith("/api/") or path == "/api":
        return JSONResponse(status_code=404, content={"detail": f"API route '{path}' not found."})
    return HTMLResponse(content=get_index_html(), status_code=200)
