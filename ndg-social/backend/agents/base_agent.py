"""
BaseAgent — Claude API 래퍼
- JSON 전용 출력 강제
- 재시도 3회 (지수 백오프)
- 토큰 추적 및 DB 저장
- 모든 에이전트 공통 부모 클래스
"""

import asyncio
import json
import re
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import anthropic
from sqlalchemy.orm import Session

from backend.config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS, CLAUDE_TEMPERATURE, MOCK_AGENTS
from backend.database import PipelineRun, ReportData

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    agent_name: str = "base"
    data_type_output: str = "agent_base_output"

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        ...

    @abstractmethod
    def build_user_prompt(self, input_data: dict) -> str:
        ...

    async def run(self, report_id: int, input_data: dict, db: Session) -> dict:
        """에이전트 실행 → ReportData 저장 → 결과 dict 반환"""
        run_record = PipelineRun(
            report_id=report_id,
            agent_name=self.agent_name,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add(run_record)
        db.commit()
        db.refresh(run_record)

        start_ms = int(time.time() * 1000)
        result = None
        error_msg = None

        if MOCK_AGENTS:
            from backend.agents.mock_responses import build_mock_response
            result = build_mock_response(self.data_type_output, input_data)
            tokens_used = 0
            logger.info(f"[MOCK] {self.agent_name} — 입력 데이터 기반 mock 응답 반환")

        for attempt in range(3 if not MOCK_AGENTS else 0):
            try:
                user_prompt = self.build_user_prompt(input_data)
                response = await self.client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=CLAUDE_MAX_TOKENS,
                    temperature=CLAUDE_TEMPERATURE,
                    system=self.system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                raw_text = response.content[0].text
                result = self._parse_json(raw_text)
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
                break
            except json.JSONDecodeError as e:
                error_msg = f"JSON 파싱 실패 (시도 {attempt+1}): {e}"
                logger.warning(error_msg)
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
            except anthropic.APIError as e:
                error_msg = f"API 오류 (시도 {attempt+1}): {e}"
                logger.warning(error_msg)
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)

        elapsed_ms = int(time.time() * 1000) - start_ms

        if result is None:
            run_record.status = "failed"
            run_record.error_message = error_msg
            run_record.completed_at = datetime.now(timezone.utc)
            db.commit()
            raise RuntimeError(f"{self.agent_name} 실패: {error_msg}")

        # ReportData 저장
        data_record = ReportData(
            report_id=report_id,
            data_type=self.data_type_output,
            data_json=json.dumps(result, ensure_ascii=False),
            agent_model=CLAUDE_MODEL,
            processing_ms=elapsed_ms,
            tokens_used=tokens_used,
        )
        db.add(data_record)
        db.commit()
        db.refresh(data_record)

        run_record.status = "completed"
        run_record.output_data_id = data_record.id
        run_record.completed_at = datetime.now(timezone.utc)
        run_record.tokens_used = tokens_used
        db.commit()

        return result

    def _parse_json(self, text: str) -> dict:
        """코드 블록 래퍼 제거 후 JSON 파싱"""
        text = text.strip()
        # ```json ... ``` 또는 ``` ... ``` 제거
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
