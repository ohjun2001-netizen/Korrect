"""
Damisola 담당 - 운율 분석 서비스
librosa(+Praat/parselmouth) 기반 피치 · 리듬 · 강세 · 음색(MFCC)을 추출하고
DTW / Cosine 유사도로 원어민 대비 점수를 산출한다.
"""
import os
import tempfile
from pathlib import Path
import numpy as np
import librosa
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean, cosine

# ── 러시아 억양 프로필 로드 ────────────────────────────────────────────
_RUSSIAN_PROFILE_PATH = Path(__file__).parent.parent / "data" / "russian_accent_profile.npy"
_russian_profile: np.ndarray | None = None

def _get_russian_profile() -> np.ndarray | None:
    global _russian_profile
    if _russian_profile is None and _RUSSIAN_PROFILE_PATH.exists():
        _russian_profile = np.load(_RUSSIAN_PROFILE_PATH)
    return _russian_profile

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
DTW_FORMANT_NORM_MAX = 1.5   # z-score 단위 — 화자 독립적 정규화 후 DTW 거리 기준

# 말하기 속도 / 쉼표 파라미터
RMS_SILENCE_THRESHOLD = 0.01   # RMS 이하면 묵음으로 판단
MIN_PAUSE_DURATION = 0.15      # 이 초 이상 연속 묵음이어야 pause로 집계


# ── 내부 유틸 ─────────────────────────────────────────────────────────
def _with_tempfile(audio_bytes: bytes) -> str:
    """오디오 바이트를 실제 WAV(16kHz mono)로 변환해 임시 파일로 저장."""
    from pydub import AudioSegment
    import io
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio = audio.set_frame_rate(16000).set_channels(1)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        audio.export(tmp.name, format="wav")
        tmp.close()
        return tmp.name
    except Exception:
        # 변환 실패 시 원본 바이트를 그대로 저장
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
    except Exception:
        return np.array([])
    finally:
        os.unlink(tmp_path)


def _normalize_voiced(arr: np.ndarray) -> np.ndarray:
    """유성 프레임(>0)만 z-score 정규화. 무성(0)은 0으로 유지."""
    voiced = arr[arr > 0]
    if len(voiced) < 3:
        return arr
    mu, sigma = voiced.mean(), voiced.std()
    if sigma < 1e-6:
        return np.zeros_like(arr, dtype=float)
    result = arr.copy().astype(float)
    result[result > 0] = (result[result > 0] - mu) / sigma
    return result


def extract_formants(audio_bytes: bytes) -> tuple[np.ndarray, np.ndarray]:
    """Praat 기반 F1/F2 포먼트 추출. Praat 미설치 시 빈 배열 반환."""
    if not PRAAT_AVAILABLE:
        return np.array([]), np.array([])
    tmp_path = _with_tempfile(audio_bytes)
    try:
        sound = parselmouth.Sound(tmp_path)
        formant = sound.to_formant_burg(
            time_step=HOP_LENGTH / 16000,
            max_number_of_formants=2,
            maximum_formant=5500,
        )
        times = formant.xs()
        f1 = np.array([formant.get_value_at_time(1, t) for t in times])
        f2 = np.array([formant.get_value_at_time(2, t) for t in times])
        return np.nan_to_num(f1, nan=0.0), np.nan_to_num(f2, nan=0.0)
    except Exception:
        return np.array([]), np.array([])
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


def extract_speech_rate(audio_bytes: bytes) -> dict:
    """
    말하기 속도: 음절 수(onset 개수) / 발화 시간(초).
    유성 구간만 기준으로 하여 앞뒤 묵음은 제외.
    """
    tmp_path = _with_tempfile(audio_bytes)
    try:
        y, sr = librosa.load(tmp_path, sr=None)
        total_dur = librosa.get_duration(y=y, sr=sr)

        onsets = librosa.onset.onset_detect(
            y=y, sr=sr, units='time', hop_length=HOP_LENGTH,
        )
        syllable_count = max(len(onsets), 1)

        # 유성 구간(RMS > 임계치) 길이만 발화 시간으로 사용
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
        voiced_frames = np.sum(rms > RMS_SILENCE_THRESHOLD)
        voiced_dur = float(voiced_frames * HOP_LENGTH / sr)
        if voiced_dur < 0.1:
            voiced_dur = total_dur  # 전부 묵음이면 전체 길이로 대체

        rate = round(syllable_count / voiced_dur, 2)
        return {"syllable_count": syllable_count, "voiced_duration": round(voiced_dur, 3), "rate": rate}
    finally:
        os.unlink(tmp_path)


def extract_pause_pattern(audio_bytes: bytes) -> dict:
    """
    묵음 구간 감지: RMS < 임계치인 연속 프레임을 pause로 집계.
    Returns: pause_count, pause_durations(초 목록), total_pause_duration
    """
    tmp_path = _with_tempfile(audio_bytes)
    try:
        y, sr = librosa.load(tmp_path, sr=None)
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]

        frame_dur = HOP_LENGTH / sr
        in_pause = False
        pause_len = 0
        pauses: list[float] = []

        for val in rms:
            if val < RMS_SILENCE_THRESHOLD:
                in_pause = True
                pause_len += 1
            else:
                if in_pause and pause_len * frame_dur >= MIN_PAUSE_DURATION:
                    pauses.append(round(pause_len * frame_dur, 3))
                in_pause = False
                pause_len = 0
        if in_pause and pause_len * frame_dur >= MIN_PAUSE_DURATION:
            pauses.append(round(pause_len * frame_dur, 3))

        return {
            "pause_count": len(pauses),
            "pause_durations": pauses,
            "total_pause_duration": round(sum(pauses), 3),
        }
    finally:
        os.unlink(tmp_path)


def generate_rhythm_feedback(
    user_rate: float,
    ref_rate: float,
    user_pauses: dict,
    ref_pauses: dict,
    rhythm_score: float,
) -> str:
    """말하기 속도·쉼표 비교 기반 한국어 피드백 텍스트 생성."""
    feedbacks: list[str] = []

    if ref_rate > 0:
        ratio = user_rate / ref_rate
        if ratio > 1.25:
            feedbacks.append("조금 천천히 말해봐요! 서두르지 않아도 돼요.")
        elif ratio < 0.75:
            feedbacks.append("조금 더 빠르게 말해봐요! 자신 있게 해봐요!")
        else:
            feedbacks.append("말하기 속도가 딱 맞아요!")

    pause_diff = user_pauses["pause_count"] - ref_pauses["pause_count"]
    if pause_diff > 1:
        feedbacks.append("쉬지 않고 이어서 말해봐요!")
    elif pause_diff < -1:
        feedbacks.append("중간에 잠깐 쉬어봐요!")

    if rhythm_score < 40:
        feedbacks.append("'원어민 발음 듣기' 버튼을 눌러서 다시 들어봐요!")
    elif rhythm_score < 70:
        feedbacks.append("리듬이 거의 맞아요! 조금만 더 하면 완벽해요!")

    return " ".join(feedbacks) if feedbacks else "리듬이 딱 맞아요! 최고예요!"


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
            "feedback": "조금 더 길게 말해봐요! 다시 한번 해볼까요?",
        }

    variance = float(np.var(voiced))
    is_flat = variance < FLAT_PITCH_THRESHOLD

    if is_flat:
        feedback = (
            "목소리를 위아래로 움직여봐요! "
            "'안녕하세요'처럼 높았다가 낮아지는 게 한국어예요."
        )
    else:
        feedback = "목소리 높낮이가 정말 좋아요! 잘하고 있어요!"

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


def compute_two_sided_accent_score(user_mfcc: np.ndarray, native_mfcc: np.ndarray) -> float | None:
    """
    원어민 MFCC와 러시아 억양 프로필 MFCC 사이에서 사용자 위치를 0~100으로 환산.
    100 = 원어민에 가까움, 0 = 러시아 억양에 가까움.
    러시아 프로필이 없으면 None 반환.
    """
    russian_profile = _get_russian_profile()
    if russian_profile is None or len(user_mfcc) == 0 or len(native_mfcc) == 0:
        return None

    d_native = float(cosine(user_mfcc, native_mfcc))
    d_russian = float(cosine(user_mfcc, russian_profile))
    total = d_native + d_russian
    if total == 0:
        return 50.0
    score = (d_russian / total) * 100.0
    return round(score, 1)


# ── 단어별 점수 ───────────────────────────────────────────────────────
def compute_pitch_slope_score(user_pitch: np.ndarray, ref_pitch: np.ndarray) -> dict:
    """피치 방향성(기울기) 유사도 — Pearson 상관계수 → 0~100."""
    user_voiced = user_pitch[user_pitch > 0]
    ref_voiced = ref_pitch[ref_pitch > 0]
    if len(user_voiced) < 5 or len(ref_voiced) < 5:
        return {"score": None}
    target = 50
    u = np.interp(np.linspace(0, 1, target), np.linspace(0, 1, len(user_voiced)), user_voiced)
    r = np.interp(np.linspace(0, 1, target), np.linspace(0, 1, len(ref_voiced)), ref_voiced)
    corr = float(np.corrcoef(u, r)[0, 1])
    if np.isnan(corr):
        return {"score": None}
    score = max(0.0, min(100.0, (corr + 1.0) / 2.0 * 100.0))
    return {"score": round(score, 1)}


def compute_voiced_ratio_score(user_pitch: np.ndarray, ref_pitch: np.ndarray) -> dict:
    """유성 구간 비율 유사도 — 원어민 대비 발성 명료도.
    앞뒤 묵음을 제거한 발화 구간 안에서만 비율을 비교해 녹음 길이 영향을 없앤다.
    """
    def _ratio_in_speech(pitch: np.ndarray) -> float | None:
        voiced_idx = np.where(pitch > 0)[0]
        if len(voiced_idx) == 0:
            return None
        segment = pitch[voiced_idx[0]: voiced_idx[-1] + 1]
        return float(np.sum(segment > 0) / len(segment))

    if len(user_pitch) == 0 or len(ref_pitch) == 0:
        return {"score": None}
    user_ratio = _ratio_in_speech(user_pitch)
    ref_ratio = _ratio_in_speech(ref_pitch)
    if user_ratio is None or ref_ratio is None:
        return {"score": None}
    diff = abs(user_ratio - ref_ratio)
    score = max(0.0, min(100.0, 100.0 - diff * 150.0))
    return {"score": round(score, 1)}


def score_words(audio_bytes: bytes, words: list[dict]) -> list[dict]:
    """
    Whisper 단어 타임스탬프 기준으로 각 단어 구간의 피치 분산을 계산해
    0~100 점수 반환 (높을수록 한국어다운 억양 변화).
    """
    if not words:
        return []
    pitch = extract_pitch(audio_bytes)
    if len(pitch) == 0:
        return [{"word": w["word"], "start": w["start"], "end": w["end"], "score": None} for w in words]

    frames_per_sec = 16000 / HOP_LENGTH  # librosa.load(sr=None) → wav가 16kHz면 31.25
    results = []
    for w in words:
        s = max(0, int(w["start"] * frames_per_sec))
        e = min(len(pitch), int(w["end"] * frames_per_sec))
        slice_ = pitch[s:e]
        voiced = slice_[slice_ > 0]
        if len(voiced) < 3:
            score = None
        else:
            variance = float(np.var(voiced))
            score = round(min(100.0, max(0.0, variance / 5.0)), 1)
        results.append({
            "word": w["word"],
            "start": round(w["start"], 3),
            "end": round(w["end"], 3),
            "score": score,
        })
    return results


# ── 통합 분석 ─────────────────────────────────────────────────────────
def analyze(user_audio_bytes: bytes, ref_audio_bytes: bytes) -> dict:
    """
    사용자 ↔ 원어민 오디오를 네 가지 관점에서 비교:
    피치(F0) · 리듬(onset 간격 + 말하기 속도 + 쉼표) · 강세(RMS) · 음색(MFCC cosine).
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

    user_rate_info = extract_speech_rate(user_audio_bytes)
    ref_rate_info = extract_speech_rate(ref_audio_bytes)
    user_pause_info = extract_pause_pattern(user_audio_bytes)
    ref_pause_info = extract_pause_pattern(ref_audio_bytes)

    pitch_result = compute_score(user_pitch, ref_pitch)
    rhythm_result = compute_rhythm_score(user_rhythm, ref_rhythm)
    stress_result = compute_stress_score(user_energy, ref_energy)
    mfcc_result = compute_mfcc_cosine(user_mfcc, ref_mfcc)

    pitch_score_praat = None
    formant_score_val = None
    if PRAAT_AVAILABLE:
        up = extract_pitch_praat(user_audio_bytes)
        rp = extract_pitch_praat(ref_audio_bytes)
        pitch_score_praat = compute_score(up, rp)["score"]
        user_f1, user_f2 = extract_formants(user_audio_bytes)
        ref_f1, ref_f2 = extract_formants(ref_audio_bytes)
        if len(user_f1) > 0 and len(ref_f1) > 0:
            f1_score = _dtw_score(
                _normalize_voiced(user_f1), _normalize_voiced(ref_f1), DTW_FORMANT_NORM_MAX
            )["score"]
            f2_score = _dtw_score(
                _normalize_voiced(user_f2), _normalize_voiced(ref_f2), DTW_FORMANT_NORM_MAX
            )["score"]
            formant_score_val = round((f1_score + f2_score) / 2, 1)

    # 음절 수 비교 (speech_rate에서 이미 계산된 syllable_count 재사용)
    user_syllable = user_rate_info["syllable_count"]
    ref_syllable = ref_rate_info["syllable_count"]
    syllable_score_val = round(
        min(user_syllable, ref_syllable) / max(user_syllable, ref_syllable) * 100.0, 1
    ) if ref_syllable > 0 else None

    voiced_result = compute_voiced_ratio_score(user_pitch, ref_pitch)
    slope_result = compute_pitch_slope_score(user_pitch, ref_pitch)

    composite = round(
        (pitch_result["score"] + rhythm_result["score"]
         + stress_result["score"] + mfcc_result["score"]) / 4.0,
        1,
    )

    accent_score = compute_two_sided_accent_score(user_mfcc, ref_mfcc)

    rhythm_feedback = generate_rhythm_feedback(
        user_rate=user_rate_info["rate"],
        ref_rate=ref_rate_info["rate"],
        user_pauses=user_pause_info,
        ref_pauses=ref_pause_info,
        rhythm_score=rhythm_result["score"],
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
        "accent_score": accent_score,
        "speech_rate_user": user_rate_info["rate"],
        "speech_rate_ref": ref_rate_info["rate"],
        "pause_count_user": user_pause_info["pause_count"],
        "pause_count_ref": ref_pause_info["pause_count"],
        "rhythm_feedback": rhythm_feedback,
        "formant_score": formant_score_val,
        "syllable_score": syllable_score_val,
        "syllable_count_user": user_syllable,
        "syllable_count_ref": ref_syllable,
        "voiced_ratio_score": voiced_result["score"],
        "pitch_slope_score": slope_result["score"],
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
        "accent_score": None,
        "speech_rate_user": None,
        "speech_rate_ref": None,
        "pause_count_user": None,
        "pause_count_ref": None,
        "rhythm_feedback": None,
        "formant_score": None,
        "syllable_score": None,
        "syllable_count_user": None,
        "syllable_count_ref": None,
        "voiced_ratio_score": None,
        "pitch_slope_score": None,
    }

    if ref_audio_bytes:
        full = analyze(user_audio_bytes, ref_audio_bytes)
        for key in (
            "score", "dtw_distance", "ref_pitch_contour",
            "pitch_score_praat", "rhythm_score", "stress_score",
            "mfcc_cosine_score", "composite_score", "accent_score",
            "speech_rate_user", "speech_rate_ref",
            "pause_count_user", "pause_count_ref", "rhythm_feedback",
            "formant_score", "syllable_score", "syllable_count_user",
            "syllable_count_ref", "voiced_ratio_score", "pitch_slope_score",
        ):
            result[key] = full[key]

    return result
