"""
에이전트 A — 데이터 분석
- Excel 파싱 데이터 수신
- 전월 대비 KPI 계산
- 이상치 탐지
- 콘텐츠 유형별 성과 분리
"""

import json
from backend.agents.base_agent import BaseAgent


class DataAnalysisAgent(BaseAgent):
    agent_name = "data_analysis"
    data_type_output = "agent_a_output"

    @property
    def system_prompt(self) -> str:
        return """당신은 소셜 미디어 데이터 분석 전문가입니다.
한국 브랜드 마케팅 에이전시의 SNS 운영 보고서 작성을 위해
월간 데이터를 분석하고 구조화된 JSON을 출력합니다.

분석 원칙:
1. 수치는 반올림 없이 정확하게 처리
2. 전월 대비 변화율은 소수점 둘째 자리까지 계산
3. 이상값(anomaly)은 월간 평균 대비 200% 초과 시 플래그
4. 콘텐츠 유형별(피드/스토리/릴스) 분리 분석 필수
5. 광고 효율 지표(CPC, CPV)는 반드시 포함
6. top_content는 총 인터랙션 기준 상위 3개

출력 형식: JSON만 출력, 설명 텍스트 없음
JSON 구조:
{
  "agent": "data_analysis",
  "report_month": "...",
  "kpi_summary": { "followers": {...}, "engagement": {...}, "impressions": {...}, "ad_spend": {...} },
  "top_content": [ { "rank":1, "upload_date":"...", "content_type":"...", "content_subtype":"...", "total_interactions":0, "engagement_rate":0.0, "standout_reason":"..." } ],
  "anomalies": [ { "type":"spike|drop", "metric":"...", "date":"...", "value":0, "baseline":0, "significance":"high|medium|low", "note":"..." } ],
  "content_type_breakdown": { "feed": {"count":0,"total_interactions":0,"avg_engagement_rate":0.0}, "story": {...}, "reel": {...} },
  "ad_breakdown": { "feed": {"spend":0,"impressions":0,"cpc":0}, "story": {"spend":0,"impressions":0,"cpv":0}, "reel": {"spend":0,"impressions":0,"cpv":0} },
  "mom_narrative_flags": { "highlight":"...", "caution":"...", "watch":"..." }
}"""

    def build_user_prompt(self, input_data: dict) -> str:
        return f"""다음 월간 소셜 미디어 데이터를 분석해주세요.

[입력 데이터]
{json.dumps(input_data, ensure_ascii=False, indent=2)}

[분석 요구사항]
- 보고 월: {input_data.get('meta', {}).get('report_month', '미상')}
- 클라이언트: {input_data.get('meta', {}).get('client', 'HIZ-NDG')}
- 전월 데이터 포함 여부: {'예' if input_data.get('previous_month') else '아니오'}

위 JSON 구조 형식으로만 출력하세요. 다른 텍스트는 절대 포함하지 마세요."""
