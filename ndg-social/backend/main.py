"""
NDG Report System — FastAPI 진입점
실행: uvicorn backend.main:app --reload --port 8000
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, Response

from backend.database import create_tables
from backend.routers import auth, reports, pipeline, export

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NDG SNS 보고서 자동화 시스템",
    description="AI 에이전트 기반 월간 SNS 운영 보고서 제작 시스템",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 테이블 생성
create_tables()

# 라우터 등록
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(pipeline.router)
app.include_router(export.router)

# 프론트엔드 정적 파일 서빙
# os.path.abspath 사용 — 한글 경로 포함 Windows 환경에서 안전
_this_file   = os.path.abspath(__file__)           # .../backend/main.py
_backend_dir = os.path.dirname(_this_file)         # .../backend
_project_dir = os.path.dirname(_backend_dir)       # .../ndg-report-system
FRONTEND_DIR = Path(os.path.join(_project_dir, "frontend"))
logger.info(f"FRONTEND_DIR: {FRONTEND_DIR} | exists={FRONTEND_DIR.exists()}")

try:
    # 업로드 이미지 디렉토리 (우선 마운트 — /static/uploads/images/)
    _uploads_img = Path(os.path.join(_project_dir, "uploads", "images"))
    _uploads_img.mkdir(parents=True, exist_ok=True)
    app.mount("/static/uploads/images", StaticFiles(directory=str(_uploads_img)), name="uploaded_images")
    # 프론트엔드 정적 파일
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    logger.info("StaticFiles mounted OK")
except Exception as e:
    logger.error(f"StaticFiles mount failed: {e}")


NO_CACHE_HEADERS = {"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"}

@app.get("/")
def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"), headers=NO_CACHE_HEADERS)

@app.get("/login")
def serve_login():
    return FileResponse(str(FRONTEND_DIR / "login.html"), headers=NO_CACHE_HEADERS)

@app.get("/login.html")
def serve_login_html():
    return RedirectResponse(url="/login")

@app.get("/new")
def serve_new():
    return FileResponse(str(FRONTEND_DIR / "new.html"), headers=NO_CACHE_HEADERS)

@app.get("/report/{report_id}")
def serve_report(report_id: int):
    return FileResponse(str(FRONTEND_DIR / "report.html"), headers=NO_CACHE_HEADERS)

@app.get("/preview/{report_id}")
def serve_preview(report_id: int):
    return FileResponse(str(FRONTEND_DIR / "preview.html"), headers=NO_CACHE_HEADERS)


@app.get("/health")
def health():
    return {"status": "ok", "service": "NDG Report System"}

@app.get("/debug-path")
def debug_path():
    import os
    return {
        "cwd": os.getcwd(),
        "file": str(Path(__file__)),
        "file_abs": str(Path(__file__).absolute()),
        "frontend_dir": str(FRONTEND_DIR),
        "frontend_exists": FRONTEND_DIR.exists(),
        "frontend_contents": [f.name for f in FRONTEND_DIR.iterdir()] if FRONTEND_DIR.exists() else [],
    }
