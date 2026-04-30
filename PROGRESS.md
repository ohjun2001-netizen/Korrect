# Korrect 프로젝트 진행 현황

## ✅ 완료된 기능

### 백엔드
- [x] FastAPI 서버 구성 (포트 8080)
- [x] STT 파이프라인 (Whisper local / Groq / OpenAI API / Google)
- [x] 운율 분석 4지표 (피치·리듬·강세·음색 DTW/Cosine 점수)
- [x] Praat 피치 교차검증
- [x] 러시아어 억양 감지 + 피드백 텍스트
- [x] 러시아 억양 MFCC 프로필 (양방향 억양 점수)
- [x] Gemini AI 대화 (gemini-2.5-flash-lite, 3개 시나리오)
- [x] 시나리오 주제 잠금 (병원/은행/출입국 이탈 방지)
- [x] TTS 엔드포인트 (gTTS, 동적 생성)
- [x] 레퍼런스 오디오 서빙 엔드포인트
- [x] CORS 전역 설정
- [x] 전역 예외 핸들러

### 프론트엔드 (Flutter)
- [x] 홈 화면 (시나리오 선택)
- [x] 대화 화면 (STT → AI 응답 → 피치 그래프)
- [x] 피치 그래프 x축 정규화 (사용자/원어민 오버레이)
- [x] 발음 피드백 카드 (파란 박스)
- [x] 점수 세부 바 (억양/리듬/강세/음색 4개)
- [x] 원어민 발음 듣기 버튼 (사용자 발화 TTS 재생)
- [x] 결과 화면 (점수 + 별점 + 세부 바)
- [x] 학습 기록 화면 (세션별 점수 히스토리)
- [x] 웹/모바일 오디오 재생 분기 처리

### 데이터
- [x] 시나리오 JSON (병원/은행/출입국)
- [x] TTS 레퍼런스 오디오 (9개 WAV)
- [x] 러시아 억양 MFCC 프로필 (.npy)

---

## 🔄 진행 중

- [ ] UI/UX 아동 친화적 개선 (담당: 양석원, 이태경)
  - 시나리오 카드 색상 추가
  - 결과 화면 confetti 애니메이션
  - 녹음 버튼 pulse 애니메이션
  - 전체 폰트/버튼 크기 확대

---

## 📋 남은 작업

### 기능
- [ ] 뒤로가기 시 "정말 나갈까요?" 팝업
- [ ] 녹음 최소 시간 체크 (너무 짧으면 안내)
- [ ] 러시아어 병기 (버튼/안내 문구)
- [ ] 시나리오 추가 (학교, 마트 등)

### 안정성
- [ ] Gemini API 유료 전환 or 팀원별 키 분산 (현재 20회/일 제한)
- [ ] 서버 오프라인 시 친절한 안내 메시지 통일

### 발표 준비
- [ ] 앱 아이콘 교체 (현재 기본 Flutter 아이콘)
- [ ] 스플래시 화면
- [ ] 시연 영상 촬영
- [ ] 교수님 디버그 문서 작성 (담당: 권오준)

---

## 👥 팀 역할 및 담당 파일

| 담당 | 역할 | 주요 파일 |
|------|------|-----------|
| **권오준** | STT / 백엔드 통합 / 디버그 문서 | `services/whisper_service.py`, `main.py`, `routers/` |
| **Damisola** | 운율 분석 | `services/prosody_service.py`, `services/scoring_service.py` |
| **Batkhuu** | AI 대화 / 시나리오 | `services/gemini_service.py`, `data/scenarios/*.json` |
| **양석원** | 프론트엔드 코어 | `flutter_app/lib/screens/`, `flutter_app/lib/services/` |
| **이태경** | 프론트엔드 UI/QA | `flutter_app/lib/screens/`, UI 개선 전반 |

---

## 🔑 환경 설정 (팀원 공유용)

```
GEMINI_API_KEY=   # 필수 - Google AI Studio에서 발급
GROQ_API_KEY=     # 권장 - groq.com에서 발급 (무료, 빠름)
WHISPER_MODE=groq # groq 추천 (로컬은 느림)
```

> Gemini 무료 티어: 20회/일 제한 → 테스트 시 아껴서 사용
