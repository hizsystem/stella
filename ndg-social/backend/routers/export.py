import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from backend.database import Report, ReportData, get_db
from backend.routers.auth import get_current_user
from backend.database import User
from backend.exporters.html_renderer import render_report_html
from backend.exporters.pdf_exporter import export_pdf_sync
from backend.exporters.pptx_exporter import export_pptx_sync
from backend.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/export", tags=["export"])


def _get_final_structure(report_id: int, db: Session) -> dict:
    """user_edited → agent_e_output 순으로 최신 구조 데이터 조회"""
    for data_type in ["user_edited", "agent_e_output"]:
        record = (
            db.query(ReportData)
            .filter(ReportData.report_id == report_id, ReportData.data_type == data_type)
            .order_by(ReportData.id.desc())
            .first()
        )
        if record:
            return json.loads(record.data_json)
    return {}


@router.get("/{report_id}/print", response_class=HTMLResponse)
def export_print_page(
    report_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Playwright가 캡처하는 슬라이드 렌더링 페이지 (slides.js 동일 사용)"""
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") is None:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)

    structure = _get_final_structure(report_id, db)
    if not structure:
        raise HTTPException(status_code=404, detail="보고서 데이터가 없습니다")

    data_json = json.dumps(structure, ensure_ascii=False)
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <link rel="preconnect" href="https://cdn.jsdelivr.net">
  <link rel="stylesheet" as="style" crossorigin
    href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css">
  <link rel="stylesheet" href="/static/css/tokens.css">
  <link rel="stylesheet" href="/static/css/slides.css">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #fff; }}
    .slide-print-page {{
      width: 1920px; height: 1080px;
      position: relative; overflow: hidden;
      display: block;
    }}
  </style>
</head>
<body>
  <div id="container"></div>
  <script>const __REPORT__ = {data_json};</script>
  <script src="/static/js/slides.js?v=37"></script>
  <script>
    document.addEventListener('DOMContentLoaded', () => {{
      const c = document.getElementById('container');
      (__REPORT__.slides || []).forEach(slide => {{
        const page = document.createElement('div');
        page.className = 'slide-print-page slide-canvas';
        page.dataset.slideNumber = slide.slide_number;
        page.innerHTML = buildSlideHtml(slide);
        c.appendChild(page);
      }});
      document.title = 'slides-ready';
    }});
  </script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/{report_id}/html", response_class=HTMLResponse)
def export_html(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다")

    structure = _get_final_structure(report_id, db)
    if not structure:
        raise HTTPException(status_code=404, detail="보고서 구조 데이터가 없습니다. 파이프라인을 먼저 실행하세요.")

    html = render_report_html(structure)
    return HTMLResponse(content=html)


@router.get("/{report_id}/pdf")
def export_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다")
    if report.status not in ["approved", "pending_review", "exported"]:
        raise HTTPException(
            status_code=400,
            detail="승인된 보고서만 PDF로 내보낼 수 있습니다"
        )

    structure = _get_final_structure(report_id, db)
    if not structure:
        raise HTTPException(status_code=404, detail="보고서 구조 데이터가 없습니다")

    html = render_report_html(structure)
    filename = f"NDG_{report.report_month}_{report.client_name}_보고서.pdf"

    try:
        pdf_path = export_pdf_sync(html, filename)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 상태 업데이트
    from datetime import datetime, timezone
    report.status = "exported"
    report.updated_at = datetime.now(timezone.utc)
    db.commit()

    return FileResponse(
        path=str(pdf_path),
        filename=filename,
        media_type="application/pdf",
    )


@router.get("/{report_id}/pptx")
def export_pptx(
    report_id: int,
    request: "Request",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다")

    structure = _get_final_structure(report_id, db)
    if not structure:
        raise HTTPException(status_code=404, detail="보고서 구조 데이터가 없습니다.")

    # 현재 사용자 토큰 재생성 (Playwright가 print 페이지 접근용)
    from backend.routers.auth import create_access_token
    tmp_token = create_access_token({"sub": str(current_user.id)})
    base_url = str(request.base_url).rstrip("/")
    print_url = f"{base_url}/api/export/{report_id}/print?token={tmp_token}"

    filename = f"NDG_{report.report_month}_{report.client_name}_보고서.pptx"

    try:
        pptx_path = export_pptx_sync(print_url, filename)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FileResponse(
        path=str(pptx_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
