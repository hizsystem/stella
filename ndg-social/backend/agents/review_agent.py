"""
에이전트 D — 검토/교정
- 에이전트 B + C 결과 수신
- 명사형 종결 전수 검사
- 수치 일관성 확인
- change_log 생성
"""

import json
from backend.agents.base_agent import BaseAgent


class ReviewAgent(BaseAgent):
    agent_name = "review_correction"
    data_type_output = "agent_d_output"

    @property
    def system_prompt(self) -> str:
        return """당신은 마케팅 보고서 교정 전문가입니다.
생성된 보고서 텍스트를 검토하고 품질을 보장합니다.

검토 항목 (전수 검사):
1. 명사형 종결 준수 여부 — "~달성", "~확인", "~필요", "~유지", "~확보", "~기록" 등으로 끝나야 함
2. 수치 일관성 — 동일 지표가 여러 슬라이드에 나올 때 수치가 모두 일치하는지 확인
3. 중복 문장 — 유사한 내용이 반복되면 다양화
4. 브랜드 언어 — 과장/비하 표현 제거
5. 가독성 — 한 문장에 수치가 3개 이상이면 분리 권장

수정 원칙:
- 원문 의미 최대한 유지
- 수치는 절대 임의 변경 금지
- 모든 변경은 change_log에 기록
- 문제 없으면 original 그대로 유지

출력 형식: JSON만 출력, 설명 텍스트 없음"""

    def build_user_prompt(self, input_data: dict) -> str:
        slides_text = input_data.get("slides_text", {})
        insights = input_data.get("insights", [])
        analysis = input_data.get("analysis", {})

        return f"""다음 보고서 텍스트 초안을 검토하고 교정해주세요.

[슬라이드 텍스트 초안 (에이전트 B 결과)]
{json.dumps(slides_text, ensure_ascii=False, indent=2)}

[인사이트 초안 (에이전트 C 결과)]
{json.dumps(insights, ensure_ascii=False, indent=2)}

[원본 분석 데이터 (수치 검증용)]
{json.dumps(analysis, ensure_ascii=False, indent=2)}

[출력 JSON 구조]
{{
  "agent": "review_correction",
  "reviewed_slides": {{ ...교정된 슬라이드 텍스트 전체 }},
  "reviewed_insights": [ ...교정된 인사이트 전체 ],
  "change_log": [
    {{
      "location": "slide_03_kpi.summary_sentence",
      "original": "원문 텍스트",
      "corrected": "교정된 텍스트",
      "reason": "명사형 종결 미준수"
    }}
  ],
  "quality_score": 85,
  "issues_found": 2
}}

change_log는 실제 수정한 항목만 포함하세요. 수정 없으면 빈 배열.
JSON만 출력하세요."""
