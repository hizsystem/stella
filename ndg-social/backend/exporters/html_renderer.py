"""
HTMLRenderer — 에이전트 E 최종 JSON → HTML 슬라이드 렌더링
Jinja2 템플릿 기반, 1920×1080 16:9 슬라이드 출력
"""

import json
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "report_slides"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _format_number(value: int | float) -> str:
    """숫자를 한국식 천 단위 콤마 포맷으로 변환"""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


def _delta_arrow(direction: str) -> str:
    return "▲" if direction == "up" else "▼"


def _delta_class(direction: str) -> str:
    return "trend-up" if direction == "up" else "trend-down"


env.filters["format_number"] = _format_number
env.filters["delta_arrow"] = _delta_arrow
env.globals["delta_class"] = _delta_class


def render_report_html(report_structure: dict) -> str:
    """
    에이전트 E 출력 JSON → 전체 보고서 HTML 문자열 반환
    각 슬라이드를 해당 템플릿으로 렌더링하여 합쳐 반환
    """
    slides = report_structure.get("slides", [])
    report_month = report_structure.get("report_month", "")
    client = report_structure.get("client", "HIZ-NDG")

    base_tmpl = env.get_template("base.html")

    rendered_slides = []
    for slide in slides:
        template_name = slide.get("template", "title")
        slide_number = slide.get("slide_number", 1)
        data = slide.get("data", {})

        try:
            tmpl = env.get_template(f"slide_{slide_number:02d}_{template_name}.html")
            rendered = tmpl.render(
                slide=slide,
                data=data,
                report_month=report_month,
                client=client,
                format_number=_format_number,
                delta_arrow=_delta_arrow,
                delta_class=_delta_class,
            )
            rendered_slides.append({
                "number": slide_number,
                "template": template_name,
                "html": rendered,
            })
        except Exception as e:
            rendered_slides.append({
                "number": slide_number,
                "template": template_name,
                "html": f'<div class="slide-error">슬라이드 {slide_number} 렌더링 오류: {e}</div>',
            })

    return base_tmpl.render(
        slides=rendered_slides,
        report_month=report_month,
        client=client,
        report_structure=report_structure,
    )


def render_single_slide(slide: dict, report_month: str = "", client: str = "HIZ-NDG") -> str:
    """단일 슬라이드 HTML 반환 (에디터 미리보기용)"""
    template_name = slide.get("template", "title")
    slide_number = slide.get("slide_number", 1)
    data = slide.get("data", {})

    try:
        tmpl = env.get_template(f"slide_{slide_number:02d}_{template_name}.html")
        return tmpl.render(
            slide=slide,
            data=data,
            report_month=report_month,
            client=client,
            format_number=_format_number,
            delta_arrow=_delta_arrow,
            delta_class=_delta_class,
        )
    except Exception as e:
        return f'<div class="slide-error">렌더링 오류: {e}</div>'
