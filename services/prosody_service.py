import tempfile
import os
import numpy as np
import librosa
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean


# 피치 추출 파라미터
FRAME_LENGTH = 2048
HOP_LENGTH = 512
FMIN = 75    # Hz - 사람 목소리 최소 주파수
FMAX = 400   # Hz - 사람 목소리 최대 주파수


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
        # NaN(무성음) → 0
        f0 = np.nan_to_num(f0, nan=0.0)
        return f0
    finally:
        os.unlink(tmp_path)


def compute_score(user_pitch: np.ndarray, ref_pitch: np.ndarray) -> dict:
    """
    사용자 피치와 레퍼런스 피치를 비교해 DTW 거리 및 0~100 점수 반환.
    반환값: {"score": float, "dtw_distance": float}
    """
    # DTW는 1D 배열을 2D로 변환 필요
    user_2d = user_pitch.reshape(-1, 1)
    ref_2d = ref_pitch.reshape(-1, 1)

    distance, _ = fastdtw(user_2d, ref_2d, dist=euclidean)

    # 길이로 정규화
    norm_distance = distance / max(len(user_pitch), len(ref_pitch))

    # 거리 → 0~100 점수 (경험적 임계값으로 조정 가능)
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
