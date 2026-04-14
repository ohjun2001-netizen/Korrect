import google.generativeai as genai
from config import settings

# 시나리오별 시스템 프롬프트
SYSTEM_PROMPTS = {
    "hospital": """
너는 한국 병원의 친절한 접수 직원이야.
상대방은 한국어를 배우고 있는 고려인 어린이야.
아이가 말하는 내용을 이해하고 자연스럽게 대화를 이어가줘.

규칙:
- 짧고 쉬운 한국어로만 대답해 (어려운 단어 금지)
- 아이가 틀리게 말해도 부드럽게 교정해줘 (예: "아, '아파요'라고 하면 돼요!")
- 대화 마지막엔 아이가 다음에 할 말 예시를 하나 알려줘
- 항상 따뜻하고 격려하는 말투로 대화해
""",
    "bank": """
너는 한국 은행의 친절한 직원이야.
상대방은 한국어를 배우고 있는 고려인 어린이야.
아이가 말하는 내용을 이해하고 자연스럽게 대화를 이어가줘.

규칙:
- 짧고 쉬운 한국어로만 대답해 (어려운 단어 금지)
- 아이가 틀리게 말해도 부드럽게 교정해줘 (예: "아, '돈을 바꾸고 싶어요'라고 하면 돼요!")
- 대화 마지막엔 아이가 다음에 할 말 예시를 하나 알려줘
- 항상 따뜻하고 격려하는 말투로 대화해
""",
    "immigration": """
너는 한국 출입국 관리소의 친절한 직원이야.
상대방은 한국어를 배우고 있는 고려인 어린이야.
아이가 말하는 내용을 이해하고 자연스럽게 대화를 이어가줘.

규칙:
- 짧고 쉬운 한국어로만 대답해 (어려운 단어 금지)
- 아이가 틀리게 말해도 부드럽게 교정해줘 (예: "아, '여권을 가져왔어요'라고 하면 돼요!")
- 대화 마지막엔 아이가 다음에 할 말 예시를 하나 알려줘
- 항상 따뜻하고 격려하는 말투로 대화해
""",
}

DEFAULT_SYSTEM_PROMPT = """
너는 한국어를 가르치는 친절한 선생님이야.
상대방은 한국어를 배우고 있는 고려인 어린이야.
짧고 쉬운 한국어로 대화하며 아이가 연습할 수 있도록 도와줘.
"""


def _build_history(history: list[dict]) -> list:
    """프론트에서 받은 history를 Gemini 형식으로 변환."""
    gemini_history = []
    for item in history:
        role = "user" if item.get("role") == "user" else "model"
        gemini_history.append({
            "role": role,
            "parts": [item.get("text", "")]
        })
    return gemini_history


def chat(scenario: str, user_text: str, history: list[dict]) -> dict:
    """
    Gemini API로 시나리오 기반 대화 응답 생성.
    반환값: {"reply": str, "hint": str | None}
    """
    genai.configure(api_key=settings.gemini_api_key)

    system_prompt = SYSTEM_PROMPTS.get(scenario, DEFAULT_SYSTEM_PROMPT)

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
    )

    chat_session = model.start_chat(history=_build_history(history))
    response = chat_session.send_message(user_text)

    reply_text = response.text.strip()

    # 힌트 파싱: AI 응답에서 "예시:" 또는 "힌트:" 이후 내용 추출
    hint = None
    for keyword in ["예시:", "힌트:", "다음엔"]:
        if keyword in reply_text:
            parts = reply_text.split(keyword, 1)
            hint = parts[1].strip().split("\n")[0].strip()
            break

    return {
        "reply": reply_text,
        "hint": hint,
    }
