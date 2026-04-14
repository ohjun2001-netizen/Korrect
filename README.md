# Korrect Backend

고려인 아동 한국어 말하기 학습 앱 백엔드

## 시작하기

### 1. 환경 설정
```bash
pip install -r requirements.txt
```

### 2. .env 파일 생성
```bash
cp .env.example .env
```
`.env` 파일에 API 키 입력:
```
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
WHISPER_MODE=local
WHISPER_MODEL_SIZE=small
```

### 3. 서버 실행
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. API 문서 확인
브라우저에서 http://localhost:8000/docs

---

## API 구조

| 엔드포인트 | 메서드 | 설명 |
|---|---|---|
| `/api/stt` | POST | 오디오 → 텍스트 변환 |
| `/api/prosody` | POST | 사용자 vs 원어민 운율 비교 |
| `/api/prosody/pitch-only` | POST | 피치 곡선만 추출 |
| `/api/chat` | POST | Gemini AI 대화 |
| `/api/scenario` | GET | 시나리오 목록 |
| `/api/scenario/{id}` | GET | 시나리오 상세 |
| `/api/scenario/{id}/process` | POST | **메인 파이프라인** (STT+운율+AI 한번에) |

---

## 메인 파이프라인 (`/api/scenario/{id}/process`)

Flutter 앱은 이 엔드포인트 하나만 호출하면 됨.

**요청:**
- `audio`: 오디오 파일 (wav/mp3/m4a)
- `history`: 이전 대화 기록 JSON 문자열
- `turn_index`: 현재 턴 번호 (운율 레퍼런스 매칭용)

**응답:**
```json
{
  "stt": { "text": "배가 아파요", "language": "ko" },
  "prosody": { "pitch_contour": [...], "ref_pitch_contour": [...], "score": 82.5, "dtw_distance": 12.3 },
  "chat": { "reply": "아이고, 많이 아팠겠네요...", "hint": "어제부터 아팠어요." },
  "total_score": 82.5
}
```

---

## 레퍼런스 오디오 추가 방법

원어민 발화 파일을 아래 경로에 저장:
```
data/references/{scenario_id}/{turn_index}.wav
```
예시:
```
data/references/hospital/0.wav   ← "배가 아파요" 원어민 녹음
data/references/hospital/1.wav   ← "어제부터 아팠어요" 원어민 녹음
```

파일이 없으면 운율 분석은 건너뛰고 STT + AI 대화만 동작함.

---

## 팀 역할

| 담당 | 파일 |
|---|---|
| 권오준 (STT/백엔드) | `main.py`, `config.py`, `services/whisper_service.py`, `routers/stt.py` |
| Damisola (운율 분석) | `services/prosody_service.py`, `services/scoring_service.py`, `routers/prosody.py` |
| Batkhuu (AI 대화/유사도) | `services/gemini_service.py`, `routers/chat.py` |
