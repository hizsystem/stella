import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import Report, ReportData, get_db, SessionLocal
from backend.routers.auth import get_current_user
from backend.database import User

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])
logger = logging.getLogger(__name__)


# ── 슬라이드 직접 생성 (AI 없음) ────────────────────────────────────

def _build_and_save(report_id: int, db: Session):
    """raw_excel → slides_builder → agent_e_output 저장"""
    from backend.pipeline.slides_builder import build_slides

    logger.info(f"슬라이드 빌드 시작: report_id={report_id}")
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return

    raw_record = (
        db.query(ReportData)
        .filter(ReportData.report_id == report_id, ReportData.data_type == "raw_excel")
        .order_by(ReportData.id.desc())
        .first()
    )
    if not raw_record:
        report.status = "failed"
        db.commit()
        return

    raw_excel = json.loads(raw_record.data_json)

    # kpi_trend: 현재 raw_excel 우선 → 없으면 전체 raw_excel 합산
    kpi_trend = raw_excel.get("kpi_trend")
    trend_list = kpi_trend.get("trend", []) if isinstance(kpi_trend, dict) else (kpi_trend or [])
    if not trend_list:
        kpi_trend = _get_global_kpi_trend(db)

    result = build_slides(
        raw_excel=raw_excel,
        report_month=report.report_month or "",
        client=report.client_name or "HIZ-NDG",
        previous_kpi_trend=kpi_trend,
    )

    # agent_e_output으로 저장
    data_record = ReportData(
        report_id=report_id,
        data_type="agent_e_output",
        data_json=json.dumps(result, ensure_ascii=False),
    )
    db.add(data_record)
    report.status = "pending_review"
    report.updated_at = datetime.now(timezone.utc)
    db.commit()


def _get_global_kpi_trend(db: Session) -> dict:
    """모든 raw_excel에서 월별 kpi_trend를 합산 (가장 최신 값 우선)"""
    all_raws = (
        db.query(ReportData)
        .filter(ReportData.data_type == "raw_excel")
        .order_by(ReportData.id.asc())
        .all()
    )
    merged = {}
    for row in all_raws:
        try:
            data = json.loads(row.data_json)
            kt = data.get("kpi_trend", {})
            entries = kt.get("trend", []) if isinstance(kt, dict) else []
            for t in entries:
                label = t.get("label", "")
                if label:
                    merged[label] = t
        except Exception:
            continue
    if not merged:
        return {}
    target = 0
    for row in all_raws:
        try:
            data = json.loads(row.data_json)
            kt = data.get("kpi_trend", {})
            if isinstance(kt, dict) and kt.get("target"):
                target = kt["target"]
        except Exception:
            continue
    return {"target": target, "trend": list(merged.values())}


def _get_prev_kpi_trend(report_id: int, db: Session) -> list:
    current = db.query(Report).filter(Report.id == report_id).first()
    if not current:
        return []
    past_reports = (
        db.query(Report)
        .filter(
            Report.client_name == current.client_name,
            Report.report_month < current.report_month,
            Report.status.in_(["pending_review", "approved", "exported"]),
        )
        .order_by(Report.report_month.desc())
        .limit(9)  # 최대 9개월 (2025-07~현재)
        .all()
    )
    trend = []
    for r in reversed(past_reports):
        rec = (
            db.query(ReportData)
            .filter(ReportData.report_id == r.id,
                    ReportData.data_type.in_(["agent_e_output"]))
            .order_by(ReportData.id.desc())
            .first()
        )
        if not rec:
            # raw_excel에서 직접 추출 시도
            raw_rec = (
                db.query(ReportData)
                .filter(ReportData.report_id == r.id, ReportData.data_type == "raw_excel")
                .order_by(ReportData.id.desc())
                .first()
            )
            if raw_rec:
                raw = json.loads(raw_rec.data_json)
                s = raw.get("current_month", {}).get("summary", {})
                label = f"{int(r.report_month.split('-')[1])}월"
                posts = raw.get("current_month", {}).get("posts", [])
                total_cnt = len(posts)
                ti = s.get("total_interactions", 0)
                trend.append({
                    "label": label,
                    "followers": s.get("followers_end", 0),
                    "interactions": ti,
                    "avg_interactions": round(ti / total_cnt) if total_cnt else 0,
                    "reach": s.get("total_reach", 0),
                    "ad_spend": s.get("total_ad_spend", 0),
                })
            continue
        d = json.loads(rec.data_json)
        slides = d.get("slides", [])
        kpi_slide = next((s for s in slides if s.get("template") == "kpi"), None)
        if kpi_slide:
            metrics = kpi_slide.get("data", {}).get("metrics", [])
            def _mv(label_candidates):
                for lbl in label_candidates:
                    m = next((m for m in metrics if m.get("label") == lbl), None)
                    if m:
                        return m.get("current", 0)
                return 0
            label = f"{int(r.report_month.split('-')[1])}월"
            trend.append({
                "label":             label,
                "followers":         _mv(["총 팔로워", "팔로워"]),
                "interactions":      _mv(["총 인터랙션"]),
                "avg_interactions":  _mv(["평균 인터랙션"]),
                "reach":             _mv(["도달"]),
                "ad_spend":          _mv(["광고비"]),
            })
    return trend


async def _run_with_own_db(report_id: int):
    """백그라운드 태스크용: 독립 DB 세션"""
    db = SessionLocal()
    try:
        _build_and_save(report_id, db)
        logger.info(f"슬라이드 빌드 완료: report_id={report_id}")
    except Exception as e:
        logger.error(f"slides_builder 오류 (report {report_id}): {e}", exc_info=True)
        # 실패 상태로 업데이트 (새 세션 사용)
        try:
            db2 = SessionLocal()
            r = db2.query(Report).filter(Report.id == report_id).first()
            if r and r.status not in ("pending_review", "approved", "exported"):
                r.status = "failed"
                r.updated_at = datetime.now(timezone.utc)
                db2.commit()
            db2.close()
        except Exception:
            pass
    finally:
        db.close()


# ── 엔드포인트 ──────────────────────────────────────────────────────

@router.post("/{report_id}/start")
async def start_pipeline(
    report_id: int,
    background_tasks: BackgroundTasks,
    full: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다")
    if report.status not in ["data_uploaded", "draft", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"현재 상태({report.status})에서는 생성을 시작할 수 없습니다",
        )
    background_tasks.add_task(_run_with_own_db, report_id)
    return {"message": "보고서 생성 시작 (백그라운드 실행)"}


@router.post("/{report_id}/restart")
async def restart_pipeline(
    report_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다")

    raw = (
        db.query(ReportData)
        .filter(ReportData.report_id == report_id, ReportData.data_type == "raw_excel")
        .first()
    )
    if not raw:
        raise HTTPException(status_code=400, detail="업로드된 데이터가 없습니다. 먼저 Excel을 업로드하세요.")

    # 이전 user_edited 레코드 삭제 (재생성 시 새 데이터 사용)
    db.query(ReportData).filter(
        ReportData.report_id == report_id,
        ReportData.data_type == "user_edited",
    ).delete()

    report.status = "data_uploaded"
    report.updated_at = datetime.now(timezone.utc)
    db.commit()

    background_tasks.add_task(_run_with_own_db, report_id)
    return {"message": "보고서 재생성 시작 (백그라운드 실행)"}


@router.get("/{report_id}/status")
def get_pipeline_status(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"error": "보고서를 찾을 수 없습니다"}
    return {
        "report_id":    report_id,
        "status":       report.status,
        "progress_pct": _progress(report.status),
    }


def _progress(status: str) -> int:
    return {
        "draft": 0, "data_uploaded": 10, "failed": -1,
        "pending_review": 90, "approved": 95, "exported": 100,
    }.get(status, 50)
