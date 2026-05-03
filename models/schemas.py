from pydantic import BaseModel
from typing import Optional


# ── STT ──────────────────────────────────────────────────────────────
class WordScore(BaseModel):
    word: str
    start: float
    end: float
    score: Optional[float] = None  # 단어별 억양 점수 0~100


class STTResponse(BaseModel):
    text: str                      # 인식된 텍스트
    language: str                  # 감지된 언어 코드
    words: list[WordScore] = []    # 단어별 타임스탬프 + 점수


# ── 운율 분석 ─────────────────────────────────────────────────────────
class ProsodyResponse(BaseModel):
    pitch_contour: list[float]                  # 사용자 피치 곡선 (Hz, librosa)
    ref_pitch_contour: list[float]              # 원어민 피치 곡선 (Hz, librosa)
    score: float                                # 피치 DTW 점수 0~100
    dtw_distance: float                         # 피치 DTW 거리 (낮을수록 좋음)
    pitch_score_praat: Optional[float] = None   # Praat 기반 피치 점수 (교차검증)
    rhythm_score: Optional[float] = None        # 리듬(onset 간격) DTW 점수
    stress_score: Optional[float] = None        # 강세(RMS 에너지) DTW 점수
    mfcc_cosine_score: Optional[float] = None   # 음색(MFCC) cosine 유사도 점수
    composite_score: Optional[float] = None     # 네 지표 평균
    accent_score: Optional[float] = None        # 억양 점수: 원어민↔러시아 억양 사이 위치 (100=원어민)
    speech_rate_user: Optional[float] = None    # 사용자 말하기 속도 (음절/초)
    speech_rate_ref: Optional[float] = None     # 원어민 말하기 속도 (음절/초)
    pause_count_user: Optional[int] = None      # 사용자 쉼표 횟수
    pause_count_ref: Optional[int] = None       # 원어민 쉼표 횟수
    rhythm_feedback: Optional[str] = None       # 속도·쉼표 기반 피드백 텍스트
    formant_score: Optional[float] = None       # F1/F2 포먼트 DTW 점수 (모음 정확도)
    syllable_score: Optional[float] = None      # 음절 수 일치율 점수
    syllable_count_user: Optional[int] = None   # 사용자 음절(onset) 수
    syllable_count_ref: Optional[int] = None    # 원어민 음절(onset) 수
    voiced_ratio_score: Optional[float] = None  # 유성 구간 비율 유사도 점수
    pitch_slope_score: Optional[float] = None   # 피치 방향성(기울기) 유사도 점수


# ── AI 대화 ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    scenario: str                  # 시나리오 ID (hospital / bank / immigration)
    user_text: str                 # STT로 인식된 사용자 발화
    history: list[dict] = []       # 이전 대화 기록 [{"role": "user/model", "text": "..."}]


class ChatResponse(BaseModel):
    reply: str                     # AI 답변 텍스트
    hint: Optional[str] = None     # 발화 힌트 (다음에 말할 수 있는 예시)
    hint_ru: Optional[str] = None  # 러시아어로 번역된 힌트 (제1언어 보조)


# ── 통합 파이프라인 ────────────────────────────────────────────────────
class ProcessResponse(BaseModel):
    stt: STTResponse
    prosody: Optional[ProsodyResponse] = None  # 레퍼런스 없으면 None
    chat: ChatResponse
    total_score: Optional[float] = None        # 종합 점수 0~100
    prosody_feedback: Optional[str] = None     # 억양 피드백 텍스트
