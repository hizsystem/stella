"""
에이전트 C — 인사이트 도출
- 에이전트 A 분석 결과 기반
- 슬라이드 7 오퍼레이션 리뷰용 3개 인사이트 생성
- 성과 / 효율 / 개선 구조
"""

import json
from backend.agents.base_agent import BaseAgent


class InsightAgent(BaseAgent):
    agent_name = "insight_generation"
    data_type_output = "agent_c_output"

    @property
    def system_prompt(self) -> str:
        return """당신은 소셜 미디어 운영 전략가입니다.
월간 데이터를 종합하여 3개의 오퍼레이션 인사이트를 도출합니다.

인사이트 구성 원칙 (반드시 준수):
1. 반드시 3개: ① 성과(what worked), ② 효율(efficiency), ③ 개선(what to improve)
2. 각 인사이트는 구체적 수치 근거 필수 포함
3. 명사형 종결 문장 사용 (서술형 금지)
4. 문장 길이: 35자 이상 50자 이내
5. 인사이트 ③(개선)은 반드시 문제 현상 + 수치 근거 + 개선 방향 포함

올바른 인사이트 형식:
- "이벤트 참여 유도형 피드 운영을 통한 인터랙션 12.9% 증가 달성"
- "광고비 증가 대비 CPV 7원 수준 유지로 광고 효율 안정성 확보"
- "스토리 저장 수 전월 대비 8% 감소에 따른 포맷 재검토 필요"

출력 형식: JSON만 출력, 설명 텍스트 없음"""

    def build_user_prompt(self, input_data: dict) -> str:
        analysis = input_data.get("analysis", {})
        report_month = input_data.get("report_month", "")

        return f"""다음 월간 분석 결과를 바탕으로 오퍼레이션 리뷰 인사이트 3개를 생성해주세요.

[분석 결과]
{json.dumps(analysis, ensure_ascii=False, indent=2)}

[보고 월]
{report_month}

[출력 JSON 구조]
{{
  "agent": "insight_generation",
  "report_month": "{report_month}",
  "insights": [
    {{
      "number": 1,
      "category": "성과",
      "headline": "15자 이내 소제목",
      "full_sentence": "명사형 종결 완성 문장 (35~50자)",
      "supporting_data": {{ "metric": "...", "current": 0, "previous": 0, "delta_pct": 0.0 }},
      "confidence": "high"
    }},
    {{
      "number": 2,
      "category": "효율",
      "headline": "...",
      "full_sentence": "...",
      "supporting_data": {{ "metric": "...", "current": 0, "previous": 0 }},
      "confidence": "high"
    }},
    {{
      "number": 3,
      "category": "개선",
      "headline": "...",
      "full_sentence": "...",
      "supporting_data": {{ "metric": "...", "delta_pct": 0.0, "note": "..." }},
      "confidence": "medium"
    }}
  ]
}}

반드시 3개 인사이트를 모두 생성하고, JSON만 출력하세요."""
