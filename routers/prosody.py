from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import ProsodyResponse
from services import prosody_service

router = APIRouter(prefix="/prosody", tags=["Prosody"])


@router.post("", response_model=ProsodyResponse)
async def analyze_prosody(
    user_audio: UploadFile = File(...),
    ref_audio: UploadFile = File(...),
):
    """
    사용자 오디오와 레퍼런스 오디오를 비교해 운율 점수 반환.
    - user_audio: 아동이 녹음한 오디오
    - ref_audio: 원어민 레퍼런스 오디오
    """
    user_bytes = await user_audio.read()
    ref_bytes = await ref_audio.read()

    if len(user_bytes) == 0 or len(ref_bytes) == 0:
        raise HTTPException(status_code=400, detail="오디오 파일이 비어있습니다.")

    result = prosody_service.analyze(user_bytes, ref_bytes)
    return ProsodyResponse(**result)


@router.post("/pitch-only", tags=["Prosody"])
async def extract_pitch_only(audio: UploadFile = File(...)):
    """
    오디오에서 피치 곡선만 추출 (레퍼런스 없이 시각화용).
    """
    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="빈 오디오 파일입니다.")

    import numpy as np
    pitch = prosody_service.extract_pitch(audio_bytes)
    return {"pitch_contour": pitch.tolist()}
