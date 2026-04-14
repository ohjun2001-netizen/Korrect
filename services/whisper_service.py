"""
권오준 담당 - STT 서비스
Whisper 로컬/API 모드 및 Google STT 모드 지원
"""
import io
import os
import tempfile

from config import settings

# 로컬 Whisper 모델은 처음 요청 시 한 번만 로드
_local_model = None


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
    오디오 바이트를 받아 STT 결과를 반환.
    반환값: {"text": str, "language": str}
    """
    mode = settings.whisper_mode
    if mode == "api":
        return _transcribe_openai_api(audio_bytes, filename)
    elif mode == "google":
        return _transcribe_google(audio_bytes)
    else:
        return _transcribe_local(audio_bytes)


# ── 로컬 Whisper ──────────────────────────────────────────────────────
def _transcribe_local(audio_bytes: bytes) -> dict:
    model = _get_local_model()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        result = model.transcribe(tmp_path, language="ko")
        return {
            "text": result["text"].strip(),
            "language": result.get("language", "ko"),
        }
    finally:
        os.unlink(tmp_path)


# ── OpenAI Whisper API ────────────────────────────────────────────────
def _transcribe_openai_api(audio_bytes: bytes, filename: str) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="ko",
    )
    return {
        "text": transcript.text.strip(),
        "language": "ko",
    }


# ── Google Cloud STT ──────────────────────────────────────────────────
def _transcribe_google(audio_bytes: bytes) -> dict:
    import os
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
        # 러시아어 억양 사용자를 위한 대안 언어 힌트
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
    }


# ── STT 정확도 비교 (권오준 3주차 작업) ───────────────────────────────
def compare_stt_modes(audio_bytes: bytes) -> dict:
    """
    Whisper 로컬 vs OpenAI API 결과를 비교해서 반환.
    정확도 테스트 및 모드 선택에 활용.
    """
    results = {}

    original_mode = settings.whisper_mode

    settings.whisper_mode = "local"
    try:
        results["local"] = _transcribe_local(audio_bytes)
    except Exception as e:
        results["local"] = {"error": str(e)}

    if settings.openai_api_key:
        try:
            results["api"] = _transcribe_openai_api(audio_bytes, "compare.wav")
        except Exception as e:
            results["api"] = {"error": str(e)}

    settings.whisper_mode = original_mode
    return results
