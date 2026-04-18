# Korrect

**고려인 아동을 위한 AI 한국어 말하기 학습 앱**

한양대학교 ERICA 음성인식 수업 프로젝트. 안산 아리랑 고려인지원센터의 현장 조사를 바탕으로, 러시아어 억양 간섭이 고착화되기 전인 8~12세 고려인 아동이 **판단받지 않고 안전하게 한국어로 말할 수 있는 환경**을 제공한다.

- **STT** (Whisper / Groq / Google) 로 아이 발화를 텍스트화
- **운율 분석**(피치·리듬·강세·음색)으로 원어민 대비 유사도 채점
- **Gemini LLM** 이 시나리오(병원/은행/출입국) 속 상대역을 맡아 실시간 대화

---

## 📁 저장소 구조

```
Korrect/
├── main.py                 # FastAPI 엔트리포인트
├── config.py               # 환경 설정 (pydantic-settings)
├── requirements.txt        # Python 의존성
├── .env.example            # 환경변수 샘플
├── routers/                # API 라우터
│   ├── stt.py              #   POST /api/stt
│   ├── prosody.py          #   POST /api/prosody
│   ├── chat.py             #   POST /api/chat
│   └── scenario.py         #   /api/scenario (+ 통합 파이프라인)
├── services/               # 비즈니스 로직
│   ├── whisper_service.py  #   STT (local/OpenAI/Groq/Google 4모드)
│   ├── prosody_service.py  #   운율 분석 + DTW/Cosine 채점
│   ├── gemini_service.py   #   Gemini 대화 생성
│   └── scoring_service.py  #   종합 점수 산출
├── models/
│   └── schemas.py          # Pydantic 응답 모델
├── data/
│   ├── scenarios/*.json    # 시나리오 스크립트
│   └── references/{id}/*.wav  # 원어민 레퍼런스 오디오
├── tests/                  # pytest 테스트
└── flutter_app/            # Flutter 프론트엔드
    └── lib/
        ├── main.dart
        ├── constants.dart  # API baseUrl 설정
        ├── screens/        # 화면 위젯
        ├── services/       # API 호출 / 오디오 녹음
        ├── widgets/        # 공용 위젯
        └── models/         # DTO
```

---

## 🚀 백엔드 시작하기

### 1. Python 의존성 설치
```bash
pip install -r requirements.txt
```
> `openai-whisper`, `librosa`, `praat-parselmouth` 설치엔 **FFmpeg**이 필요합니다.
> Windows: `winget install ffmpeg`, macOS: `brew install ffmpeg`.

### 2. 환경변수 설정
```bash
cp .env.example .env
```
`.env` 열고 사용할 키/모드 채우기:
```
GEMINI_API_KEY=AI...          # 필수 (AI 대화)
GROQ_API_KEY=gsk_...          # 선택 (WHISPER_MODE=groq 쓸 때)
OPENAI_API_KEY=sk-...         # 선택 (WHISPER_MODE=api 쓸 때)
WHISPER_MODE=local            # local | api | google | groq
WHISPER_MODEL_SIZE=medium     # tiny | base | small | medium | large
```

### 3. 서버 실행
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 동작 확인
- 헬스체크: <http://localhost:8000/health>
- Swagger UI: <http://localhost:8000/docs>

---

## 📱 Flutter 앱 시작하기

### 1. 의존성 설치
```bash
cd flutter_app
flutter pub get
```

### 2. 서버 주소 확인 (`lib/constants.dart`)
```dart
// 웹 / iOS 시뮬레이터 / 데스크탑
static const String baseUrl = 'http://localhost:8000';
// Android 에뮬레이터
// static const String baseUrl = 'http://10.0.2.2:8000';
// 실제 기기 — PC의 LAN IP로 변경
// static const String baseUrl = 'http://192.168.0.x:8000';
```

### 3. 실행
```bash
flutter run -d chrome           # 웹 브라우저
flutter run -d android          # Android 에뮬/기기
flutter run -d ios              # iOS 시뮬레이터/기기
```

디바이스 목록 확인: `flutter devices`

---

## 🔌 API 엔드포인트

| 경로 | 메서드 | 설명 |
|---|---|---|
| `/api/stt` | POST | 오디오 → 한국어 텍스트 |
| `/api/prosody` | POST | 사용자/원어민 운율 비교 (피치·리듬·강세·MFCC) |
| `/api/prosody/pitch-only` | POST | 피치 곡선만 추출 (시각화용) |
| `/api/chat` | POST | Gemini 시나리오 대화 |
| `/api/scenario` | GET | 시나리오 목록 |
| `/api/scenario/{id}` | GET | 시나리오 상세 |
| `/api/scenario/{id}/opening` | GET | 시나리오 첫 인사 |
| `/api/scenario/{id}/process` | POST | **메인 통합 파이프라인** |

### 메인 파이프라인 `/api/scenario/{id}/process`

Flutter 앱은 이 엔드포인트 하나로 **STT + 운율 + AI 응답** 을 한 번에 받는다.

**요청 (multipart/form-data):**
| 필드 | 타입 | 설명 |
|---|---|---|
| `audio` | File | 아이가 녹음한 wav/mp3/m4a/webm |
| `history` | str | 이전 대화 기록 JSON 문자열 |
| `turn_index` | int | 현재 대화 턴 (레퍼런스 오디오 매칭용) |

**응답 (ProcessResponse):**
```json
{
  "stt": { "text": "배가 아파요", "language": "ko" },
  "prosody": {
    "pitch_contour": [...],
    "ref_pitch_contour": [...],
    "score": 82.5,
    "dtw_distance": 12.3,
    "pitch_score_praat": 80.1,
    "rhythm_score": 74.2,
    "stress_score": 68.9,
    "mfcc_cosine_score": 91.3,
    "composite_score": 79.2
  },
  "chat": {
    "reply": "아이고, 많이 아팠겠네요. 언제부터 아팠어요?",
    "hint": "어제부터 아팠어요."
  },
  "total_score": 82.5
}
```

---

## 🎧 STT 모드 선택

`.env` 의 `WHISPER_MODE` 를 바꾸면 런타임에 STT 엔진 교체.

| 모드 | 설명 | 키 필요 | 인터넷 |
|---|---|---|---|
| `local` | 서버 내 Whisper 모델 직접 실행 | ❌ | ❌ |
| `api` | OpenAI Whisper API (유료) | `OPENAI_API_KEY` | ✅ |
| `groq` | Groq Whisper API (무료, 빠름) | `GROQ_API_KEY` | ✅ |
| `google` | Google Cloud Speech-to-Text | `GOOGLE_CREDENTIALS_PATH` | ✅ |

내부에 `compare_stt_modes()` 함수가 있어 로컬 vs OpenAI API 결과를 동시에 찍어보며 비교 실험 가능.

---

## 🎼 운율 분석 지표

`services/prosody_service.py` 가 한 번의 호출로 네 가지 점수를 모두 반환한다.

| 지표 | 추출 방법 | 비교 방식 |
|---|---|---|
| **피치 (F0)** | `librosa.pyin` (+ Praat 교차검증) | DTW on Euclidean |
| **리듬** | `librosa.onset.onset_detect` → 인접 간격 | DTW on 간격 배열 |
| **강세** | `librosa.feature.rms` (에너지 곡선) | DTW on RMS |
| **음색** | `librosa.feature.mfcc` 평균 벡터 (13차원) | Cosine similarity |

각 점수는 0~100으로 정규화되고, 네 지표의 평균이 `composite_score` 로 반환된다. 추가로 피치 분산 기반의 **러시아어 평탄 억양 감지 피드백** 도 `analyze_with_feedback()` 에서 제공.

---

## 🗣️ 시나리오 시스템

현재 3개 시나리오 제공:

| ID | 제목 | 상황 |
|---|---|---|
| `hospital` | 병원 | 접수 → 증상 → 진료과 안내 |
| `bank` | 은행 | 환영 → 업무 → 환전/계좌 → 마무리 |
| `immigration` | 출입국 | 방문 목적 → 서류 → 체류 안내 |

**대화 방식**: 정해진 대본을 낭독하지 않고, Gemini 가 **시스템 프롬프트에 설정된 캐릭터/규칙 안에서 자유롭게 응답** 한다. 각 프롬프트에는 **[주제 잠금]** 지시가 포함되어 있어, 아이가 시나리오와 무관한 이야기(학교/게임 등)로 이탈하면 부드럽게 되돌린다.

### 원어민 레퍼런스 오디오
운율 채점을 위해 아래 경로에 원어민 녹음을 둔다:
```
data/references/{scenario_id}/{turn_index}.wav
```
예시:
```
data/references/hospital/0.wav   ← "배가 아파요"
data/references/hospital/1.wav   ← "어제부터 아팠어요"
```
파일이 없으면 운율 점수는 생략되고 STT + AI 응답만 반환된다 (러시아어 억양 패턴 피드백은 별도 제공).

---

## 🧪 테스트

```bash
pytest tests/
```

---

## 👥 팀 역할

| 담당 | 역할 | 주요 파일 |
|---|---|---|
| **권오준** | STT / 백엔드 통합 | `main.py`, `config.py`, `services/whisper_service.py`, `routers/stt.py` |
| **Damisola Talabi** | 운율 분석 | `services/prosody_service.py`, `services/scoring_service.py`, `routers/prosody.py` |
| **Batkhuu Bolderdene** | AI 대화 / 유사도 | `services/gemini_service.py`, `routers/chat.py`, `data/scenarios/*.json` |
| **양석원** | 프론트엔드 (코어) | `flutter_app/lib/main.dart`, `screens/`, 마이크 녹음, API 통합 |
| **이태경** | 프론트엔드 (지원) / QA | 시나리오·점수 UI, 파일럿 테스트, 버그 트래킹 |

---

## 📌 알려진 제약

- 현재 구현상 **완전 오프라인 동작 불가** (STT `local` 모드여도 Gemini 대화는 인터넷 필요)
- `WHISPER_MODEL_SIZE=medium` 이상이면 CPU에서 추론이 느릴 수 있음 (한 발화당 2~5초)
- Windows 환경에서 `praat-parselmouth` 설치 실패 시 Praat 교차검증 기능만 자동 비활성화되고 나머지는 정상 동작
