import sys
import os

# Configure python path for Vercel serverless functions
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.main import app as fastapi_app

class VercelPathFixASGI:
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            headers = dict(scope.get("headers", []))

            # Vercel passes original matched path in headers
            matched_path = headers.get(b"x-matched-path", b"").decode("utf-8", errors="ignore")
            if not matched_path:
                matched_path = headers.get(b"x-vercel-matched-path", b"").decode("utf-8", errors="ignore")

            if matched_path:
                path = matched_path

            # Strip /api/index.py or /api/index if rewritten by Vercel
            if path.startswith("/api/index.py"):
                path = path[len("/api/index.py"):]
            elif path.startswith("/api/index"):
                path = path[len("/api/index"):]

            if not path:
                path = "/"

            scope["path"] = path
            scope["raw_path"] = path.encode("utf-8")

        await self.asgi_app(scope, receive, send)

app = VercelPathFixASGI(fastapi_app)
handler = app
