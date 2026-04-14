import io
import tempfile
import os
from pathlib import Path

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
    if settings.whisper_mode == "api":
        return _transcribe_api(audio_bytes, filename)
    else:
        return _transcribe_local(audio_bytes)


def _transcribe_local(audio_bytes: bytes) -> dict:
    import whisper

    model = _get_local_model()

    # 임시 파일에 저장 후 인식 (whisper는 파일 경로로 동작)
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


def _transcribe_api(audio_bytes: bytes, filename: str) -> dict:
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
