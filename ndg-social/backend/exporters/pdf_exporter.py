"""
PDFExporter — Playwright를 이용한 HTML → PDF 변환
1920×1080 기준, A4 landscape 또는 커스텀 크기 출력
"""

import asyncio
import os
from pathlib import Path

EXPORTS_DIR = Path(__file__).parent.parent.parent / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)


async def export_pdf(html_content: str, filename: str) -> Path:
    """
    HTML 문자열 → PDF 파일 저장 후 경로 반환
    Playwright 미설치 시 fallback 오류 메시지 반환
    """
    output_path = EXPORTS_DIR / filename

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                viewport={"width": 1920, "height": 1080}
            )
            await page.set_content(html_content, wait_until="networkidle")

            # 폰트 로드 대기
            await page.wait_for_timeout(1000)

            await page.pdf(
                path=str(output_path),
                width="297mm",       # A4 landscape
                height="210mm",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            await browser.close()

    except ImportError:
        raise RuntimeError(
            "Playwright가 설치되지 않았습니다.\n"
            "다음 명령을 실행하세요:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        )

    return output_path


def export_pdf_sync(html_content: str, filename: str) -> Path:
    """동기 래퍼 (FastAPI BackgroundTasks용)"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, export_pdf(html_content, filename))
                return future.result()
        else:
            return loop.run_until_complete(export_pdf(html_content, filename))
    except RuntimeError:
        return asyncio.run(export_pdf(html_content, filename))
