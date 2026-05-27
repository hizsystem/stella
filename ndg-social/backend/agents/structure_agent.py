"""
에이전트 E — 보고서 구조 생성
- 모든 에이전트 결과를 8슬라이드 최종 JSON으로 조립
- 필수 필드 완전성 검증
- validation 섹션 포함
"""

import json
from backend.agents.base_agent import BaseAgent


class StructureAgent(BaseAgent):
    agent_name = "structure_assembly"
    data_type_output = "agent_e_output"

    @property
    def system_prompt(self) -> str:
        return """당신은 보고서 구조 조립 전문가입니다.
모든 에이전트의 출력물을 통합하여 최종 8슬라이드 보고서 JSON을 생성합니다.

조립 원칙:
1. 슬라이드 번호 1→8 순서 고정
2. 필수 필드 완전성 검증 — 누락 시 warnings에 기록
3. 데이터 수치와 텍스트 간 최종 일관성 확인
4. template 값은 정해진 것만 허용:
   title, calendar, kpi, engagement, popular_content, story_strategy, operating_review, closing
5. validation 섹션 반드시 포함

출력 형식: JSON만 출력, 설명 텍스트 없음"""

    def build_user_prompt(self, input_data: dict) -> str:
        raw_data = input_data.get("raw_data", {})
        analysis = input_data.get("analysis", {})
        reviewed_text = input_data.get("reviewed_text", {})
        reviewed_insights = input_data.get("reviewed_insights", [])
        report_id = input_data.get("report_id", "")
        report_month = input_data.get("report_month", "")
        client = input_data.get("client", "HIZ-NDG")

        return f"""다음 모든 데이터를 통합하여 최종 8슬라이드 보고서 JSON을 생성해주세요.

[원본 데이터 요약]
{json.dumps(raw_data.get('current_month', {}).get('summary', {}), ensure_ascii=False, indent=2)}

[분석 결과 (에이전트 A)]
{json.dumps(analysis, ensure_ascii=False, indent=2)}

[교정된 슬라이드 텍스트 (에이전트 D)]
{json.dumps(reviewed_text, ensure_ascii=False, indent=2)}

[교정된 인사이트 (에이전트 D)]
{json.dumps(reviewed_insights, ensure_ascii=False, indent=2)}

[보고서 메타]
report_id: {report_id}
report_month: {report_month}
client: {client}

[출력 JSON 구조]
{{
  "agent": "structure_assembly",
  "report_id": "{report_id}",
  "report_month": "{report_month}",
  "client": "{client}",
  "validation": {{
    "all_slides_complete": true,
    "missing_fields": [],
    "warnings": []
  }},
  "slides": [
    {{
      "slide_number": 1,
      "template": "title",
      "data": {{
        "main_title": "NDG 소셜 미디어 운영 보고서",
        "sub_title": "YYYY년 MM월",
        "client_name": "{client}",
        "prepared_by": "소셜 미디어 운영팀"
      }}
    }},
    {{
      "slide_number": 2,
      "template": "calendar",
      "data": {{
        "section_title": "월간 콘텐츠 캘린더",
        "summary": "...",
        "calendar_entries": [],
        "highlight_note": "..."
      }}
    }},
    {{
      "slide_number": 3,
      "template": "kpi",
      "data": {{
        "section_title": "KPI 성과 현황",
        "table_caption": "...",
        "metrics": [
          {{"label":"팔로워","current":0,"delta":0,"delta_direction":"up","formatted":"..."}},
          {{"label":"총 인터랙션","current":0,"delta":0,"delta_direction":"up","formatted":"..."}},
          {{"label":"노출수","current":0,"delta":0,"delta_direction":"up","formatted":"..."}}
        ],
        "summary_sentence": "..."
      }}
    }},
    {{
      "slide_number": 4,
      "template": "engagement",
      "data": {{
        "section_title": "인게이지먼트 분석",
        "summary_sentence": "...",
        "mom_comparison": [],
        "content_breakdown": []
      }}
    }},
    {{
      "slide_number": 5,
      "template": "popular_content",
      "data": {{
        "section_title": "인기 콘텐츠 분석",
        "top_posts": [],
        "insight_line": "..."
      }}
    }},
    {{
      "slide_number": 6,
      "template": "story_strategy",
      "data": {{
        "section_title": "스토리 광고 성과",
        "performance_summary": "...",
        "ad_metrics": [],
        "efficiency_note": "...",
        "caution_note": "..."
      }}
    }},
    {{
      "slide_number": 7,
      "template": "operating_review",
      "data": {{
        "section_title": "오퍼레이션 리뷰",
        "insights": []
      }}
    }},
    {{
      "slide_number": 8,
      "template": "closing",
      "data": {{
        "closing_statement": "다음 달 운영 방향 및 개선 사항은 별도 전략 보고서에서 제공 예정",
        "prepared_by": "NDG 소셜 미디어 운영팀",
        "report_date": "{report_month}"
      }}
    }}
  ]
}}

모든 필드를 완성하고 validation을 정확히 채워주세요. JSON만 출력하세요."""
