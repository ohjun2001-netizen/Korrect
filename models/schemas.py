from pydantic import BaseModel
from typing import Optional


# ── STT ──────────────────────────────────────────────────────────────
class STTResponse(BaseModel):
    text: str                      # 인식된 텍스트
    language: str                  # 감지된 언어 코드


# ── 운율 분석 ─────────────────────────────────────────────────────────
class ProsodyResponse(BaseModel):
    pitch_contour: list[float]     # 사용자 피치 곡선 (Hz)
    ref_pitch_contour: list[float] # 원어민 레퍼런스 피치 곡선 (Hz)
    score: float                   # 유사도 점수 0~100
    dtw_distance: float            # DTW 거리 (낮을수록 좋음)


# ── AI 대화 ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    scenario: str                  # 시나리오 ID (hospital / bank / immigration)
    user_text: str                 # STT로 인식된 사용자 발화
    history: list[dict] = []       # 이전 대화 기록 [{"role": "user/model", "text": "..."}]


class ChatResponse(BaseModel):
    reply: str                     # AI 답변 텍스트
    hint: Optional[str] = None     # 발화 힌트 (다음에 말할 수 있는 예시)


# ── 통합 파이프라인 ────────────────────────────────────────────────────
class ProcessResponse(BaseModel):
    stt: STTResponse
    prosody: Optional[ProsodyResponse] = None  # 레퍼런스 없으면 None
    chat: ChatResponse
    total_score: Optional[float] = None        # 종합 점수 0~100
