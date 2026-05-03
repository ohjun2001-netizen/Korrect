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
    반환값: {"text": str, "language": str, "words": list[{"word", "start", "end"}]}
    """
    mode = settings.whisper_mode
    if mode == "api":
        return _transcribe_openai_api(audio_bytes, filename)
    elif mode == "google":
        return _transcribe_google(audio_bytes)
    elif mode == "groq":
        return _transcribe_groq(audio_bytes, filename)
    else:
        return _transcribe_local(audio_bytes)


# ── 로컬 Whisper ──────────────────────────────────────────────────────
def _transcribe_local(audio_bytes: bytes) -> dict:
    model = _get_local_model()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        debug_path = os.path.join(tempfile.gettempdir(), "korrect_last_recording.wav")
        with open(debug_path, "wb") as f:
            f.write(audio_bytes)
        print(f"[Whisper] 입력 파일 크기: {len(audio_bytes)}B")
        print(f"[Whisper] 디버깅용 복사본: {debug_path}")
        # word_timestamps는 medium 이상에서 추론 시간을 크게 늘림 → 환경변수로 끌 수 있음
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
                words.append({
                    "word": w.get("word", "").strip(),
                    "start": float(w.get("start", 0.0)),
                    "end": float(w.get("end", 0.0)),
                })
        return {
            "text": text,
            "language": result.get("language", "ko"),
            "words": words,
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
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )
    return {
        "text": transcript.text.strip(),
        "language": "ko",
        "words": _extract_words(transcript),
    }


# ── Groq Whisper API (무료, OpenAI SDK 호환) ──────────────────────────
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
    """OpenAI/Groq verbose_json 응답에서 word 타임스탬프 추출."""
    words_raw = getattr(transcript, "words", None) or []
    return [
        {
            "word": (getattr(w, "word", "") or "").strip(),
            "start": float(getattr(w, "start", 0.0)),
            "end": float(getattr(w, "end", 0.0)),
        }
        for w in words_raw
    ]


# ── Google Cloud STT ──────────────────────────────────────────────────
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
        "words": [],
    }


# ── STT 정확도 비교 (권오준 3주차 작업) ───────────────────────────────
def compare_stt_modes(audio_bytes: bytes) -> dict:
    """
    Whisper 로컬 vs OpenAI API 결과를 비교해서 반환.
    정확도 테스트 및 모드 선택에 활용.
    """
    results = {}

    try:
        results["local"] = _transcribe_local(audio_bytes)
    except Exception as e:
        results["local"] = {"error": str(e)}

    if settings.openai_api_key:
        try:
            results["api"] = _transcribe_openai_api(audio_bytes, "compare.wav")
        except Exception as e:
            results["api"] = {"error": str(e)}

    return results
