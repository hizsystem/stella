import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Railway 볼륨(/data) 마운트 시 자동으로 해당 경로 사용
_default_db = (
    "sqlite:////data/ndg_reports.db"
    if os.path.isdir("/data")
    else "sqlite:///./database/ndg_reports.db"
)
DATABASE_URL = os.getenv("DATABASE_URL", _default_db)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

MOCK_AGENTS = os.getenv("MOCK_AGENTS", "false").lower() == "true"

CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 4096
CLAUDE_TEMPERATURE = 0

# 보고서 설정
DEFAULT_CLIENT_NAME = "HIZ-NDG"
SLIDE_COUNT = 8
SLIDE_TEMPLATES = [
    "title", "calendar", "kpi", "engagement",
    "popular_content", "story_strategy", "operating_review", "closing"
]
