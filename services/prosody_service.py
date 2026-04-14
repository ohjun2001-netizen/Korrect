"""
Damisola 담당 - 운율 분석 서비스
librosa를 사용한 피치 추출, 러시아어 억양 패턴 감지, DTW 채점
"""
import os
import tempfile
import numpy as np
import librosa
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

# 피치 추출 파라미터
FRAME_LENGTH = 2048
HOP_LENGTH = 512
FMIN = 75    # Hz - 사람 목소리 최소 주파수
FMAX = 400   # Hz - 사람 목소리 최대 주파수

# 러시아어 억양 감지 임계값
# 한국어는 높은 피치 변화율, 러시아어는 상대적으로 평탄
KOREAN_MIN_PITCH_VARIANCE = 500.0  # 정상 한국어 발화의 최소 분산 (실험값)
FLAT_PITCH_THRESHOLD = 300.0       # 이 이하면 억양이 평탄(러시아어 패턴 의심)


def extract_pitch(audio_bytes: bytes) -> np.ndarray:
    """오디오 바이트에서 피치 곡선(F0) 추출. 무성음 구간은 0으로 처리."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        y, sr = librosa.load(tmp_path, sr=None)
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=FMIN,
            fmax=FMAX,
            sr=sr,
            frame_length=FRAME_LENGTH,
            hop_length=HOP_LENGTH,
        )
        f0 = np.nan_to_num(f0, nan=0.0)
        return f0
    finally:
        os.unlink(tmp_path)


def detect_russian_accent(pitch: np.ndarray) -> dict:
    """
    피치 곡선에서 러시아어 억양 패턴을 감지.
    러시아어 특징: 평탄한 피치(낮은 분산), 억양 변화 부족.
    반환값: {"is_russian_pattern": bool, "pitch_variance": float, "feedback": str}
    """
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


def compute_score(user_pitch: np.ndarray, ref_pitch: np.ndarray) -> dict:
    """
    사용자 피치와 레퍼런스 피치를 DTW로 비교해 0~100 점수 반환.
    반환값: {"score": float, "dtw_distance": float}
    """
    user_2d = user_pitch.reshape(-1, 1)
    ref_2d = ref_pitch.reshape(-1, 1)

    distance, _ = fastdtw(user_2d, ref_2d, dist=euclidean)
    norm_distance = distance / max(len(user_pitch), len(ref_pitch))

    MAX_DISTANCE = 150.0
    score = max(0.0, 100.0 - (norm_distance / MAX_DISTANCE) * 100.0)

    return {
        "score": round(score, 1),
        "dtw_distance": round(norm_distance, 4),
    }


def analyze(user_audio_bytes: bytes, ref_audio_bytes: bytes) -> dict:
    """
    사용자 오디오와 레퍼런스 오디오를 비교 분석.
    반환값: {"pitch_contour", "ref_pitch_contour", "score", "dtw_distance"}
    """
    user_pitch = extract_pitch(user_audio_bytes)
    ref_pitch = extract_pitch(ref_audio_bytes)
    result = compute_score(user_pitch, ref_pitch)

    return {
        "pitch_contour": user_pitch.tolist(),
        "ref_pitch_contour": ref_pitch.tolist(),
        "score": result["score"],
        "dtw_distance": result["dtw_distance"],
    }


def analyze_with_feedback(user_audio_bytes: bytes, ref_audio_bytes: bytes = None) -> dict:
    """
    피치 분석 + 러시아어 억양 감지 + 피드백 텍스트를 한번에 반환.
    ref_audio_bytes가 없으면 DTW 점수 없이 억양 패턴 분석만 수행.
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
    }

    if ref_audio_bytes:
        ref_pitch = extract_pitch(ref_audio_bytes)
        score_result = compute_score(user_pitch, ref_pitch)
        result["score"] = score_result["score"]
        result["dtw_distance"] = score_result["dtw_distance"]
        result["ref_pitch_contour"] = ref_pitch.tolist()

    return result
