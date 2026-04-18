"""
Damisola 담당 - 운율 분석 서비스
librosa(+Praat/parselmouth) 기반 피치 · 리듬 · 강세 · 음색(MFCC)을 추출하고
DTW / Cosine 유사도로 원어민 대비 점수를 산출한다.
"""
import os
import tempfile
import numpy as np
import librosa
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean, cosine

# Praat bindings (선택적 의존성)
try:
    import parselmouth  # praat-parselmouth
    PRAAT_AVAILABLE = True
except ImportError:
    PRAAT_AVAILABLE = False

# ── 분석 파라미터 ──────────────────────────────────────────────────────
FRAME_LENGTH = 2048
HOP_LENGTH = 512
FMIN = 75    # Hz - 사람 목소리 최소 주파수
FMAX = 400   # Hz - 사람 목소리 최대 주파수
N_MFCC = 13

# 러시아어 억양 감지 임계값
KOREAN_MIN_PITCH_VARIANCE = 500.0
FLAT_PITCH_THRESHOLD = 300.0

# DTW 정규화 거리 기준 (튜닝 대상)
DTW_PITCH_MAX = 150.0    # Hz
DTW_RHYTHM_MAX = 0.5     # seconds (onset 간격)
DTW_STRESS_MAX = 0.1     # RMS amplitude


# ── 내부 유틸 ─────────────────────────────────────────────────────────
def _with_tempfile(audio_bytes: bytes):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(audio_bytes)
    tmp.close()
    return tmp.name


# ── 피처 추출 ─────────────────────────────────────────────────────────
def extract_pitch(audio_bytes: bytes) -> np.ndarray:
    """librosa.pyin 기반 F0 곡선. 무성음은 0."""
    tmp_path = _with_tempfile(audio_bytes)
    try:
        y, sr = librosa.load(tmp_path, sr=None)
        f0, _, _ = librosa.pyin(
            y, fmin=FMIN, fmax=FMAX, sr=sr,
            frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH,
        )
        return np.nan_to_num(f0, nan=0.0)
    finally:
        os.unlink(tmp_path)


def extract_pitch_praat(audio_bytes: bytes) -> np.ndarray:
    """Praat(parselmouth) 기반 F0. librosa 결과 교차 검증용."""
    if not PRAAT_AVAILABLE:
        return np.array([])
    tmp_path = _with_tempfile(audio_bytes)
    try:
        sound = parselmouth.Sound(tmp_path)
        pitch = sound.to_pitch(pitch_floor=FMIN, pitch_ceiling=FMAX)
        values = pitch.selected_array['frequency']
        return np.nan_to_num(values, nan=0.0)
    finally:
        os.unlink(tmp_path)


def extract_rhythm(audio_bytes: bytes) -> np.ndarray:
    """onset 감지 후 인접 onset 시간 간격(초) 배열 반환."""
    tmp_path = _with_tempfile(audio_bytes)
    try:
        y, sr = librosa.load(tmp_path, sr=None)
        onsets = librosa.onset.onset_detect(
            y=y, sr=sr, units='time', hop_length=HOP_LENGTH,
        )
        if len(onsets) < 2:
            return np.array([])
        return np.diff(onsets)
    finally:
        os.unlink(tmp_path)


def extract_energy(audio_bytes: bytes) -> np.ndarray:
    """RMS 에너지 곡선 — 강세 패턴 근사치."""
    tmp_path = _with_tempfile(audio_bytes)
    try:
        y, _ = librosa.load(tmp_path, sr=None)
        return librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
    finally:
        os.unlink(tmp_path)


def extract_mfcc(audio_bytes: bytes) -> np.ndarray:
    """MFCC 13차원 평균 벡터 (발음/음색 특징)."""
    tmp_path = _with_tempfile(audio_bytes)
    try:
        y, sr = librosa.load(tmp_path, sr=None)
        mfcc = librosa.feature.mfcc(
            y=y, sr=sr, n_mfcc=N_MFCC, hop_length=HOP_LENGTH,
        )
        return mfcc.mean(axis=1)
    finally:
        os.unlink(tmp_path)


# ── 러시아어 억양 감지 (기존) ─────────────────────────────────────────
def detect_russian_accent(pitch: np.ndarray) -> dict:
    voiced = pitch[pitch > 0]
    if len(voiced) < 10:
        return {
            "is_russian_pattern": False,
            "pitch_variance": 0.0,
            "feedback": "발화가 너무 짧아요. 더 길게 말해봐요!",
        }

    variance = float(np.var(voiced))
    is_flat = variance < FLAT_PITCH_THRESHOLD

    if is_flat:
        feedback = (
            "억양이 조금 평탄해요. 한국어는 높낮이 변화가 많아요! "
            "예를 들어 '안녕하세요'를 말할 때 '안'은 낮게, '녕'은 높게 말해봐요."
        )
    else:
        feedback = "억양이 자연스러워요! 잘하고 있어요."

    return {
        "is_russian_pattern": is_flat,
        "pitch_variance": round(variance, 2),
        "feedback": feedback,
    }


# ── 점수 계산 ─────────────────────────────────────────────────────────
def _dtw_score(user_seq: np.ndarray, ref_seq: np.ndarray, max_norm: float) -> dict:
    """공통 DTW 유사도 → 0~100 정규화."""
    if len(user_seq) == 0 or len(ref_seq) == 0:
        return {"score": 0.0, "dtw_distance": 0.0}
    distance, _ = fastdtw(
        user_seq.reshape(-1, 1),
        ref_seq.reshape(-1, 1),
        dist=euclidean,
    )
    norm = distance / max(len(user_seq), len(ref_seq))
    score = max(0.0, 100.0 - (norm / max_norm) * 100.0)
    return {"score": round(score, 1), "dtw_distance": round(norm, 4)}


def compute_score(user_pitch: np.ndarray, ref_pitch: np.ndarray) -> dict:
    """피치 DTW 점수 (하위호환 이름 유지)."""
    return _dtw_score(user_pitch, ref_pitch, DTW_PITCH_MAX)


def compute_rhythm_score(user_intervals: np.ndarray, ref_intervals: np.ndarray) -> dict:
    return _dtw_score(user_intervals, ref_intervals, DTW_RHYTHM_MAX)


def compute_stress_score(user_energy: np.ndarray, ref_energy: np.ndarray) -> dict:
    return _dtw_score(user_energy, ref_energy, DTW_STRESS_MAX)


def compute_mfcc_cosine(user_mfcc: np.ndarray, ref_mfcc: np.ndarray) -> dict:
    """MFCC 평균 벡터 간 cosine 유사도 → 0~100."""
    if len(user_mfcc) == 0 or len(ref_mfcc) == 0:
        return {"score": 0.0, "cosine_distance": 0.0}
    dist = float(cosine(user_mfcc, ref_mfcc))  # 0~2
    sim = 1.0 - dist                            # -1~1
    score = max(0.0, min(100.0, (sim + 1.0) / 2.0 * 100.0))
    return {"score": round(score, 1), "cosine_distance": round(dist, 4)}


# ── 통합 분석 ─────────────────────────────────────────────────────────
def analyze(user_audio_bytes: bytes, ref_audio_bytes: bytes) -> dict:
    """
    사용자 ↔ 원어민 오디오를 네 가지 관점에서 비교:
    피치(F0) · 리듬(onset 간격) · 강세(RMS) · 음색(MFCC cosine).
    Praat 피치는 설치돼 있으면 교차검증 값으로 함께 반환.
    """
    user_pitch = extract_pitch(user_audio_bytes)
    ref_pitch = extract_pitch(ref_audio_bytes)
    user_rhythm = extract_rhythm(user_audio_bytes)
    ref_rhythm = extract_rhythm(ref_audio_bytes)
    user_energy = extract_energy(user_audio_bytes)
    ref_energy = extract_energy(ref_audio_bytes)
    user_mfcc = extract_mfcc(user_audio_bytes)
    ref_mfcc = extract_mfcc(ref_audio_bytes)

    pitch_result = compute_score(user_pitch, ref_pitch)
    rhythm_result = compute_rhythm_score(user_rhythm, ref_rhythm)
    stress_result = compute_stress_score(user_energy, ref_energy)
    mfcc_result = compute_mfcc_cosine(user_mfcc, ref_mfcc)

    pitch_score_praat = None
    if PRAAT_AVAILABLE:
        up = extract_pitch_praat(user_audio_bytes)
        rp = extract_pitch_praat(ref_audio_bytes)
        pitch_score_praat = compute_score(up, rp)["score"]

    composite = round(
        (pitch_result["score"] + rhythm_result["score"]
         + stress_result["score"] + mfcc_result["score"]) / 4.0,
        1,
    )

    return {
        "pitch_contour": user_pitch.tolist(),
        "ref_pitch_contour": ref_pitch.tolist(),
        "score": pitch_result["score"],
        "dtw_distance": pitch_result["dtw_distance"],
        "pitch_score_praat": pitch_score_praat,
        "rhythm_score": rhythm_result["score"],
        "stress_score": stress_result["score"],
        "mfcc_cosine_score": mfcc_result["score"],
        "composite_score": composite,
    }


def analyze_with_feedback(user_audio_bytes: bytes, ref_audio_bytes: bytes = None) -> dict:
    """
    피치 분석 + 러시아어 억양 감지 + 피드백 텍스트.
    ref_audio_bytes가 있으면 전체 유사도(analyze)도 함께 계산.
    """
    user_pitch = extract_pitch(user_audio_bytes)
    accent_info = detect_russian_accent(user_pitch)

    result = {
        "pitch_contour": user_pitch.tolist(),
        "pitch_variance": accent_info["pitch_variance"],
        "is_russian_pattern": accent_info["is_russian_pattern"],
        "feedback": accent_info["feedback"],
        "score": None,
        "dtw_distance": None,
        "ref_pitch_contour": [],
        "pitch_score_praat": None,
        "rhythm_score": None,
        "stress_score": None,
        "mfcc_cosine_score": None,
        "composite_score": None,
    }

    if ref_audio_bytes:
        full = analyze(user_audio_bytes, ref_audio_bytes)
        for key in (
            "score", "dtw_distance", "ref_pitch_contour",
            "pitch_score_praat", "rhythm_score", "stress_score",
            "mfcc_cosine_score", "composite_score",
        ):
            result[key] = full[key]

    return result
