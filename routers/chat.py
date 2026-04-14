from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from services import gemini_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    시나리오 기반 AI 대화.
    - scenario: hospital / bank / immigration
    - user_text: STT로 인식된 아동 발화
    - history: 이전 대화 기록 (선택)
    """
    if not request.user_text.strip():
        raise HTTPException(status_code=400, detail="발화 텍스트가 비어있습니다.")

    result = gemini_service.chat(
        scenario=request.scenario,
        user_text=request.user_text,
        history=request.history,
    )
    return ChatResponse(**result)
