import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BASE_DIR
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or (os.path.exists("/tmp") and os.name != "nt"):
    DB_PATH = Path("/tmp/opspilot.db")
else:
    DB_PATH = BASE_DIR / "opspilot.db"

class Settings(BaseModel):
    app_name: str = "OpsPilot"
    tagline: str = "Your AI Operator for Payments, Exceptions & Business Operations."
    version: str = "1.0.0"
    debug: bool = True
    db_url: str = f"sqlite:///{DB_PATH}"
    workspace_dir: Path = WORKSPACE_DIR
    demo_mode_default: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

settings = Settings()
