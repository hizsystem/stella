"""
에이전트 B — 문장 생성
- 에이전트 A 분석 결과 기반
- 슬라이드별 텍스트 필드 생성
- 명사형 종결 강제
"""

import json
from backend.agents.base_agent import BaseAgent


class SentenceGenAgent(BaseAgent):
    agent_name = "sentence_generation"
    data_type_output = "agent_b_output"

    @property
    def system_prompt(self) -> str:
        return """당신은 한국 브랜드 마케팅 보고서 전문 카피라이터입니다.
소셜 미디어 운영 보고서의 각 슬라이드 텍스트를 생성합니다.

문체 원칙 (반드시 준수):
1. 명사형 종결: "~달성", "~확인", "~필요", "~유지", "~확보", "~기록" 등으로 끝냄
2. 과장 금지: "대박", "폭발적", "역대급", "놀라운" 등 사용 불가
3. 실무적 어조: 정확한 수치 기반의 간결한 서술
4. 길이 제한: 한 문장 최대 45자 이내
5. 허용 표현: "~중심의 ~확보", "~대비 ~유지", "~통한 ~달성", "~기반의 ~개선"

올바른 예시:
- "이벤트 콘텐츠 중심의 높은 참여 확보" (O)
- "전월 대비 인터랙션 12.9% 증가 달성" (O)
- "광고 효율 안정적 유지" (O)

잘못된 예시:
- "대박 성과 달성!" (X - 과장)
- "매우 훌륭한 결과를 얻었습니다" (X - 서술형)
- "성과가 좋았습니다" (X - 모호)

출력 형식: JSON만 출력, 설명 텍스트 없음"""

    def build_user_prompt(self, input_data: dict) -> str:
        analysis = input_data.get("analysis", {})
        report_month = input_data.get("report_month", "")
        client = input_data.get("client", "HIZ-NDG")

        return f"""다음 분석 결과를 바탕으로 슬라이드별 텍스트를 생성해주세요.

[분석 결과]
{json.dumps(analysis, ensure_ascii=False, indent=2)}

[보고서 정보]
- 보고 월: {report_month}
- 클라이언트: {client}

[출력 JSON 구조]
{{
  "agent": "sentence_generation",
  "report_month": "{report_month}",
  "slides": {{
    "slide_01_title": {{
      "main_title": "NDG 소셜 미디어 운영 보고서",
      "sub_title": "YYYY년 MM월",
      "client_name": "{client}",
      "prepared_by": "소셜 미디어 운영팀"
    }},
    "slide_02_calendar": {{
      "section_title": "월간 콘텐츠 캘린더",
      "summary_sentence": "총 N개 콘텐츠 운영 (피드 N, 스토리 N, 릴스 N)",
      "highlight_note": "..."
    }},
    "slide_03_kpi": {{
      "section_title": "KPI 성과 현황",
      "table_caption": "YYYY년 MM월 주요 지표",
      "mom_note": "전월 대비 ...",
      "summary_sentence": "..."
    }},
    "slide_04_engagement": {{
      "section_title": "인게이지먼트 분석",
      "top_content_intro": "이달의 주요 콘텐츠 성과",
      "mom_comparison_title": "전월 대비 지표 변화",
      "summary_sentence": "...",
      "engagement_breakdown": "피드 XX%, 릴스 XX%, 스토리 XX% 비중"
    }},
    "slide_05_popular": {{
      "section_title": "인기 콘텐츠 분석",
      "rank1_label": "이달의 1위 콘텐츠",
      "rank1_description": "...",
      "rank2_label": "이달의 2위 콘텐츠",
      "rank2_description": "...",
      "rank3_label": "이달의 3위 콘텐츠",
      "rank3_description": "...",
      "insight_line": "..."
    }},
    "slide_06_story": {{
      "section_title": "스토리 광고 성과",
      "performance_summary": "스토리 광고 노출 N회, CPV N원 유지",
      "efficiency_note": "...",
      "caution_note": "..."
    }},
    "slide_07_review": {{
      "section_title": "오퍼레이션 리뷰"
    }},
    "slide_08_closing": {{
      "closing_statement": "다음 달 운영 방향 및 개선 사항은 별도 전략 보고서에서 제공 예정",
      "prepared_by": "NDG 소셜 미디어 운영팀"
    }}
  }}
}}

모든 텍스트 필드를 채워 완전한 JSON을 출력하세요. 다른 텍스트는 절대 포함하지 마세요."""
