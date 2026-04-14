"""
이태경 담당 - 운율 분석 테스트
pytest로 실행: pytest tests/test_prosody.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import soundfile as sf
import io
import pytest


def _make_flat_pitch_wav(sr: int = 16000, duration: float = 1.5) -> bytes:
    """평탄한 피치(러시아어 억양 패턴) 시뮬레이션 - 단일 주파수."""
    t = np.linspace(0, duration, int(sr * duration))
    # 200Hz 단일 주파수 = 평탄한 억양
    samples = (np.sin(2 * np.pi * 200 * t) * 0.5).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, samples, sr, format="WAV")
    return buf.getvalue()


def _make_varying_pitch_wav(sr: int = 16000, duration: float = 1.5) -> bytes:
    """변화하는 피치(한국어 억양 패턴) 시뮬레이션 - 주파수 변화."""
    t = np.linspace(0, duration, int(sr * duration))
    # 150~350Hz로 변화하는 주파수 = 억양 변화
    freq = 150 + 200 * np.sin(2 * np.pi * 1.5 * t)
    phase = np.cumsum(2 * np.pi * freq / sr)
    samples = (np.sin(phase) * 0.5).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, samples, sr, format="WAV")
    return buf.getvalue()


class TestPitchExtraction:
    def test_extract_pitch_returns_array(self):
        """피치 추출 결과가 numpy 배열인지 확인."""
        from services.prosody_service import extract_pitch
        audio = _make_flat_pitch_wav()
        pitch = extract_pitch(audio)
        assert isinstance(pitch, np.ndarray)

    def test_extract_pitch_not_empty(self):
        """피치 배열이 비어있지 않은지 확인."""
        from services.prosody_service import extract_pitch
        audio = _make_flat_pitch_wav()
        pitch = extract_pitch(audio)
        assert len(pitch) > 0

    def test_extract_pitch_no_negatives(self):
        """피치 값에 음수가 없는지 확인 (무성음은 0으로 처리)."""
        from services.prosody_service import extract_pitch
        audio = _make_flat_pitch_wav()
        pitch = extract_pitch(audio)
        assert np.all(pitch >= 0), "피치 값에 음수가 있음"


class TestRussianAccentDetection:
    def test_flat_pitch_detected(self):
        """평탄한 피치가 러시아어 패턴으로 감지되는지 확인."""
        from services.prosody_service import detect_russian_accent
        # 평탄한 피치 배열 생성
        flat_pitch = np.full(200, 200.0)  # 200Hz 고정
        flat_pitch[:20] = 0  # 일부 무성음
        result = detect_russian_accent(flat_pitch)
        assert "is_russian_pattern" in result
        assert "pitch_variance" in result
        assert "feedback" in result

    def test_feedback_is_string(self):
        """피드백이 문자열인지 확인."""
        from services.prosody_service import detect_russian_accent
        pitch = np.full(200, 200.0)
        result = detect_russian_accent(pitch)
        assert isinstance(result["feedback"], str)

    def test_short_pitch_handled(self):
        """너무 짧은 피치 배열도 오류 없이 처리되는지 확인."""
        from services.prosody_service import detect_russian_accent
        short_pitch = np.array([0.0, 0.0, 100.0])
        result = detect_russian_accent(short_pitch)
        assert "feedback" in result


class TestDTWScoring:
    def test_score_range(self):
        """점수가 0~100 범위인지 확인."""
        from services.prosody_service import compute_score
        user_pitch = np.array([100.0, 150.0, 200.0, 180.0, 120.0])
        ref_pitch = np.array([110.0, 160.0, 210.0, 170.0, 130.0])
        result = compute_score(user_pitch, ref_pitch)
        assert 0.0 <= result["score"] <= 100.0

    def test_identical_pitch_high_score(self):
        """동일한 피치는 높은 점수를 받아야 함."""
        from services.prosody_service import compute_score
        pitch = np.array([100.0, 150.0, 200.0, 180.0, 120.0] * 10)
        result = compute_score(pitch, pitch.copy())
        assert result["score"] >= 90.0, f"동일 피치인데 점수가 낮음: {result['score']}"

    def test_different_pitch_lower_score(self):
        """많이 다른 피치는 낮은 점수를 받아야 함."""
        from services.prosody_service import compute_score
        user_pitch = np.full(50, 100.0)
        ref_pitch = np.full(50, 300.0)
        result = compute_score(user_pitch, ref_pitch)
        assert result["score"] < 80.0, f"다른 피치인데 점수가 너무 높음: {result['score']}"

    def test_dtw_distance_positive(self):
        """DTW 거리는 항상 양수여야 함."""
        from services.prosody_service import compute_score
        user_pitch = np.array([100.0, 200.0, 150.0])
        ref_pitch = np.array([120.0, 180.0, 160.0])
        result = compute_score(user_pitch, ref_pitch)
        assert result["dtw_distance"] >= 0
