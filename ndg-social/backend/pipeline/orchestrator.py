"""
PipelineOrchestrator — 에이전트 실행 상태 머신
상태 흐름:
  draft → data_uploaded → analyzing → generating → paused_bc
  → reviewing → paused_d → assembling → pending_review → approved → exported

에이전트 B와 C는 asyncio.gather()로 병렬 실행
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.database import Report, ReportData
from backend.agents.data_analysis_agent import DataAnalysisAgent
from backend.agents.sentence_gen_agent import SentenceGenAgent
from backend.agents.insight_agent import InsightAgent
from backend.agents.review_agent import ReviewAgent
from backend.agents.structure_agent import StructureAgent

logger = logging.getLogger(__name__)

# 상태 순서 및 진행률 매핑
PIPELINE_STAGES = {
    "draft":          0,
    "data_uploaded":  10,
    "analyzing":      20,
    "generating":     40,
    "paused_bc":      50,   # 사람 검토 대기
    "reviewing":      60,
    "paused_d":       70,   # change_log 수락/거절 대기
    "assembling":     80,
    "pending_review": 90,
    "approved":       95,
    "exported":       100,
    "failed":         -1,
}


def get_progress(status: str) -> int:
    return PIPELINE_STAGES.get(status, 0)


def _get_latest_data(report_id: int, data_type: str, db: Session) -> dict | None:
    record = (
        db.query(ReportData)
        .filter(ReportData.report_id == report_id, ReportData.data_type == data_type)
        .order_by(ReportData.id.desc())
        .first()
    )
    if record:
        return json.loads(record.data_json)
    return None


def _set_status(report_id: int, status: str, db: Session):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report:
        report.status = status
        report.updated_at = datetime.now(timezone.utc)
        db.commit()


async def run_agent_a(report_id: int, db: Session) -> dict:
    """에이전트 A: 데이터 분석"""
    _set_status(report_id, "analyzing", db)
    raw_data = _get_latest_data(report_id, "raw_excel", db)
    if not raw_data:
        raise ValueError("raw_excel 데이터가 없습니다. 먼저 Excel을 업로드하세요.")
    agent = DataAnalysisAgent()
    return await agent.run(report_id, raw_data, db)


async def run_agents_bc(report_id: int, db: Session) -> tuple[dict, dict]:
    """에이전트 B + C 병렬 실행"""
    _set_status(report_id, "generating", db)
    analysis = _get_latest_data(report_id, "agent_a_output", db)
    raw_data = _get_latest_data(report_id, "raw_excel", db)
    if not analysis:
        raise ValueError("에이전트 A 결과가 없습니다.")

    report = db.query(Report).filter(Report.id == report_id).first()
    report_month = report.report_month if report else ""
    client = report.client_name if report else "HIZ-NDG"

    agent_b = SentenceGenAgent()
    agent_c = InsightAgent()

    b_input = {"analysis": analysis, "report_month": report_month, "client": client}
    c_input = {"analysis": analysis, "report_month": report_month}

    result_b, result_c = await asyncio.gather(
        agent_b.run(report_id, b_input, db),
        agent_c.run(report_id, c_input, db),
    )
    _set_status(report_id, "paused_bc", db)
    return result_b, result_c


async def run_agent_d(report_id: int, db: Session) -> dict:
    """에이전트 D: 검토/교정"""
    _set_status(report_id, "reviewing", db)
    b_output = _get_latest_data(report_id, "agent_b_output", db)
    c_output = _get_latest_data(report_id, "agent_c_output", db)
    analysis = _get_latest_data(report_id, "agent_a_output", db)

    if not b_output or not c_output:
        raise ValueError("에이전트 B/C 결과가 없습니다.")

    d_input = {
        "slides_text": b_output.get("slides", {}),
        "insights": c_output.get("insights", []),
        "analysis": analysis,
    }
    agent = ReviewAgent()
    result = await agent.run(report_id, d_input, db)
    _set_status(report_id, "paused_d", db)
    return result


def _get_prev_kpi_trend(report_id: int, db: Session) -> list:
    """현재 보고서 이전 최대 5개월의 팔로워 추이 수집 (KPI 차트용)"""
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
        .limit(5)
        .all()
    )
    trend = []
    for r in reversed(past_reports):
        a_out = _get_latest_data(r.id, "agent_a_output", db)
        if not a_out:
            continue
        followers = a_out.get("kpi_summary", {}).get("followers", {}).get("current", 0)
        try:
            month_label = str(int(r.report_month.split("-")[1])) + "월"
        except Exception:
            month_label = r.report_month
        trend.append({"label": month_label, "value": followers, "target": 0})
    return trend


async def run_agent_e(report_id: int, db: Session) -> dict:
    """에이전트 E: 구조 조립"""
    _set_status(report_id, "assembling", db)
    raw_data = _get_latest_data(report_id, "raw_excel", db)
    analysis = _get_latest_data(report_id, "agent_a_output", db)
    d_output = _get_latest_data(report_id, "agent_d_output", db)

    if not d_output:
        raise ValueError("에이전트 D 결과가 없습니다.")

    report = db.query(Report).filter(Report.id == report_id).first()

    # raw_excel kpi_trend → previous_kpi_trend로 주입 (KPI 차트 monthly_trend 생성용)
    if analysis is not None:
        kpi_trend_list = []
        if raw_data:
            kpi_raw = raw_data.get("kpi_trend", {})
            trend_entries = kpi_raw.get("trend", []) if isinstance(kpi_raw, dict) else []
            kpi_trend_list = [
                {
                    "label":        t.get("label", ""),
                    "value":        t.get("followers", 0),
                    "followers":    t.get("followers", 0),
                    "interactions": t.get("interactions", 0),
                    "reach":        t.get("reach", 0),
                    "ad_spend":     t.get("ad_spend", 0),
                    "target":       0,
                }
                for t in trend_entries
            ]
        # raw_excel에 없으면 과거 보고서에서 폴백
        if not kpi_trend_list:
            kpi_trend_list = _get_prev_kpi_trend(report_id, db)
        if kpi_trend_list:
            analysis = dict(analysis)
            analysis["previous_kpi_trend"] = kpi_trend_list

    e_input = {
        "raw_data": raw_data or {},
        "analysis": analysis or {},
        "reviewed_text": d_output.get("reviewed_slides", {}),
        "reviewed_insights": d_output.get("reviewed_insights", []),
        "report_id": str(report_id),
        "report_month": report.report_month if report else "",
        "client": report.client_name if report else "HIZ-NDG",
    }
    agent = StructureAgent()
    result = await agent.run(report_id, e_input, db)
    _set_status(report_id, "pending_review", db)
    return result


async def run_full_pipeline(report_id: int, db: Session):
    """전체 파이프라인 실행 (A → B+C → D → E)
    paused_bc, paused_d에서 자동 중단 없이 일괄 실행 (API 호출 시 전체 실행 옵션)
    """
    try:
        await run_agent_a(report_id, db)
        await run_agents_bc(report_id, db)
        await run_agent_d(report_id, db)
        await run_agent_e(report_id, db)
    except Exception as e:
        logger.error(f"파이프라인 실패 (report {report_id}): {e}")
        _set_status(report_id, "failed", db)
        raise


def get_pipeline_status(report_id: int, db: Session) -> dict:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"error": "보고서를 찾을 수 없습니다"}

    from backend.database import PipelineRun
    runs = (
        db.query(PipelineRun)
        .filter(PipelineRun.report_id == report_id)
        .order_by(PipelineRun.id.asc())
        .all()
    )

    # 현재 실행 중인 에이전트 이름
    current_agent = None
    for r in runs:
        if r.status == "running":
            current_agent = r.agent_name
            break

    return {
        "report_id": report_id,
        "status": report.status,
        "current_agent": current_agent,
        "progress_pct": get_progress(report.status),
        "runs": [
            {
                "agent_name": r.agent_name,
                "status": r.status,
                "tokens_used": r.tokens_used,
                "error_message": r.error_message,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in runs
        ],
    }
