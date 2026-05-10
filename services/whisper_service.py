"""
STT service.
Supports local Whisper, OpenAI/Groq Whisper APIs, and Google STT.
"""
import io
import math
import os
import tempfile
from pathlib import Path

from config import settings

_local_model = None
_TOO_QUIET_RMS_THRESHOLD = 8
_TOO_QUIET_DBFS_THRESHOLD = -55.0


def _get_local_model():
    global _local_model
    if _local_model is None:
        import whisper

        print(f"[Whisper] 로컬 모델 로딩 중: {settings.whisper_model_size}")
        _local_model = whisper.load_model(settings.whisper_model_size)
        print("[Whisper] 모델 로딩 완료")
    return _local_model


def transcribe(audio_bytes: bytes, filename: str = "audio.wav") -> dict:
    """
    Return {"text": str, "language": str, "words": list[{"word", "start", "end"}]}.
    """
    mode = settings.whisper_mode
    if mode == "api":
        return _transcribe_openai_api(audio_bytes, filename)
    if mode == "google":
        return _transcribe_google(audio_bytes)
    if mode == "groq":
        return _transcribe_groq(audio_bytes, filename)
    return _transcribe_local(audio_bytes, filename)


def _real_suffix(audio_bytes: bytes, filename: str) -> str:
    """magic bytes 우선, 그다음 확장자 폴백."""
    if audio_bytes[:4] == b'\x1a\x45\xdf\xa3':
        return '.webm'
    if len(audio_bytes) > 8 and audio_bytes[4:8] == b'ftyp':
        return '.mp4'
    if audio_bytes[:4] == b'RIFF':
        return '.wav'
    return Path(filename).suffix or '.wav'


def _decode_audio(audio_bytes: bytes, filename: str = "audio.wav"):
    from pydub import AudioSegment

    suffix = _real_suffix(audio_bytes, filename)
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp.write(audio_bytes)
        tmp.close()
        return AudioSegment.from_file(tmp.name)
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


def _audio_level_stats(audio) -> dict:
    return {
        "dBFS": audio.dBFS,
        "max_dBFS": audio.max_dBFS,
        "rms": int(audio.rms),
        "max": int(audio.max),
    }


def _is_effectively_silent(stats: dict) -> bool:
    if stats["rms"] <= _TOO_QUIET_RMS_THRESHOLD:
        return True
    dBFS = stats["dBFS"]
    if dBFS == float("-inf"):
        return True
    return math.isfinite(dBFS) and dBFS < _TOO_QUIET_DBFS_THRESHOLD


def _write_normalized_audio(audio_bytes: bytes, filename: str) -> str:
    """
    Convert uploaded audio into a real 16kHz mono WAV for local Whisper.
    """
    try:
        audio = _decode_audio(audio_bytes, filename)
        original_dBFS = audio.dBFS
        if original_dBFS != float("-inf") and original_dBFS < -20:
            audio = audio.normalize()
            print(f"[Whisper] 음량 정규화 적용 ({original_dBFS:.1f} dBFS → 0 dBFS)")
        audio = audio.set_frame_rate(16000).set_channels(1)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        audio.export(tmp.name, format="wav")
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"[Whisper] 오디오 변환 실패, 원본으로 재시도: {e}")
        fallback_suffix = Path(filename or "audio.wav").suffix or ".wav"
        tmp = tempfile.NamedTemporaryFile(suffix=fallback_suffix, delete=False)
        tmp.write(audio_bytes)
        tmp.close()
        return tmp.name


def _transcribe_local(audio_bytes: bytes, filename: str) -> dict:
    debug_suffix = Path(filename or "audio.wav").suffix or ".wav"
    debug_path = os.path.join(tempfile.gettempdir(), f"korrect_last_recording{debug_suffix}")
    with open(debug_path, "wb") as f:
        f.write(audio_bytes)
    print(f"[Whisper] 입력 파일 크기: {len(audio_bytes)}B")
    print(f"[Whisper] 디버깅용 복사본: {debug_path}")

    try:
        level_stats = _audio_level_stats(_decode_audio(audio_bytes, filename))
        print(
            "[Whisper] 원본 레벨 "
            f"(dBFS={level_stats['dBFS']:.1f}, max_dBFS={level_stats['max_dBFS']:.1f}, "
            f"rms={level_stats['rms']}, max={level_stats['max']})"
        )
        if _is_effectively_silent(level_stats):
            print("[Whisper] 입력이 사실상 무음 수준이라 STT를 건너뜁니다")
            return {"text": "", "language": "ko", "words": []}
    except Exception as e:
        print(f"[Whisper] 입력 레벨 분석 실패, 계속 진행합니다: {e}")

    model = _get_local_model()
    tmp_path = _write_normalized_audio(audio_bytes, filename)
    try:
        use_word_ts = os.environ.get("WHISPER_WORD_TIMESTAMPS", "1") == "1"
        try:
            result = model.transcribe(tmp_path, language="ko", word_timestamps=use_word_ts)
        except Exception as e:
            print(f"[Whisper] word_timestamps 실패, 재시도: {e}")
            result = model.transcribe(tmp_path, language="ko")

        text = result["text"].strip()
        print(f"[Whisper] 인식 결과: '{text}' (language={result.get('language')})")
        words: list[dict] = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []) or []:
                words.append(
                    {
                        "word": w.get("word", "").strip(),
                        "start": float(w.get("start", 0.0)),
                        "end": float(w.get("end", 0.0)),
                    }
                )
        return {
            "text": text,
            "language": result.get("language", "ko"),
            "words": words,
        }
    finally:
        os.unlink(tmp_path)


def _transcribe_openai_api(audio_bytes: bytes, filename: str) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="ko",
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )
    return {
        "text": transcript.text.strip(),
        "language": "ko",
        "words": _extract_words(transcript),
    }


def _transcribe_groq(audio_bytes: bytes, filename: str) -> dict:
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    transcript = client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=audio_file,
        language="ko",
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )
    return {
        "text": transcript.text.strip(),
        "language": "ko",
        "words": _extract_words(transcript),
    }


def _extract_words(transcript) -> list[dict]:
    words_raw = getattr(transcript, "words", None) or []
    return [
        {
            "word": (getattr(w, "word", "") or "").strip(),
            "start": float(getattr(w, "start", 0.0)),
            "end": float(getattr(w, "end", 0.0)),
        }
        for w in words_raw
    ]


def _transcribe_google(audio_bytes: bytes) -> dict:
    from google.cloud import speech

    if settings.google_credentials_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_credentials_path

    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ko-KR",
        enable_automatic_punctuation=True,
        alternative_language_codes=["ru-RU"],
    )
    response = client.recognize(config=config, audio=audio)
    text = " ".join(
        result.alternatives[0].transcript
        for result in response.results
        if result.alternatives
    )
    return {
        "text": text.strip(),
        "language": "ko",
        "words": [],
    }


def compare_stt_modes(audio_bytes: bytes) -> dict:
    results = {}

    try:
        results["local"] = _transcribe_local(audio_bytes, "compare.wav")
    except Exception as e:
        results["local"] = {"error": str(e)}

    if settings.openai_api_key:
        try:
            results["api"] = _transcribe_openai_api(audio_bytes, "compare.wav")
        except Exception as e:
            results["api"] = {"error": str(e)}

    return results
