import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from models.schemas import ProcessResponse, STTResponse, ChatResponse
from services import whisper_service, prosody_service, gemini_service, scoring_service

router = APIRouter(prefix="/scenario", tags=["Scenario"])

DATA_DIR = Path(__file__).parent.parent / "data" / "scenarios"
REF_DIR = Path(__file__).parent.parent / "data" / "references"


@router.get("")
async def list_scenarios():
    """사용 가능한 시나리오 목록 반환."""
    scenarios = []
    for f in DATA_DIR.glob("*.json"):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        scenarios.append({
            "id": f.stem,
            "title": data.get("title", f.stem),
            "description": data.get("description", ""),
        })
    return {"scenarios": scenarios}


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str):
    """특정 시나리오의 상세 정보(스크립트) 반환."""
    path = DATA_DIR / f"{scenario_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"시나리오를 찾을 수 없습니다: {scenario_id}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.post("/{scenario_id}/process", response_model=ProcessResponse)
async def process_turn(
    scenario_id: str,
    audio: UploadFile = File(...),
    history: str = "[]",                # JSON 문자열로 전달
    turn_index: int = 0,                # 현재 대화 턴 번호 (레퍼런스 매칭용)
):
    """
    메인 파이프라인: 오디오 → STT → 운율분석 → AI 대화 → 점수 반환.
    Flutter 앱에서 한 번의 요청으로 전체 결과를 받아갈 수 있음.
    """
    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="빈 오디오 파일입니다.")

    # 1. STT
    stt_result = whisper_service.transcribe(audio_bytes, audio.filename or "audio.wav")
    stt = STTResponse(text=stt_result["text"], language=stt_result["language"])

    # 2. 운율 분석 (레퍼런스 파일이 있을 때만)
    prosody = None
    total_score = None
    ref_path = REF_DIR / scenario_id / f"{turn_index}.wav"
    if ref_path.exists():
        ref_bytes = ref_path.read_bytes()
        prosody_result = prosody_service.analyze(audio_bytes, ref_bytes)
        from models.schemas import ProsodyResponse
        prosody = ProsodyResponse(**prosody_result)
        total_score = scoring_service.compute_total_score(prosody.score, None)

    # 3. AI 대화
    history_data = json.loads(history)
    chat_result = gemini_service.chat(
        scenario=scenario_id,
        user_text=stt.text,
        history=history_data,
    )
    chat = ChatResponse(**chat_result)

    return ProcessResponse(
        stt=stt,
        prosody=prosody,
        chat=chat,
        total_score=total_score,
    )
