import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/tts", tags=["TTS"])


@router.get("")
async def text_to_speech(text: str):
    """텍스트를 한국어 TTS로 변환해서 MP3 스트림 반환."""
    from gtts import gTTS
    tts = gTTS(text=text, lang="ko")
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-store"},
    )
