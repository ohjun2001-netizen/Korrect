from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import STTResponse
from services import whisper_service

router = APIRouter(prefix="/stt", tags=["STT"])


@router.post("", response_model=STTResponse)
async def speech_to_text(audio: UploadFile = File(...)):
    """
    오디오 파일을 업로드하면 한국어 텍스트로 변환.
    지원 포맷: wav, mp3, m4a, webm
    """
    allowed = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/webm", "audio/x-wav"}
    if audio.content_type and audio.content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식: {audio.content_type}")

    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="빈 오디오 파일입니다.")

    result = whisper_service.transcribe(audio_bytes, audio.filename or "audio.wav")
    return STTResponse(text=result["text"], language=result["language"])
