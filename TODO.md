# Korrect 남은 작업

데모데이까지 처리할 작업 목록. 우선순위별로 정리.

---

## 🔴 필수 (데모 전 반드시)

### 1. 의존성 재설치
```bash
pip install -r requirements.txt
```
새로 추가한 `praat-parselmouth` 설치 확인. 실패해도 나머지는 정상 동작 (Praat 교차검증만 비활성).

### 2. 실제 오디오로 prosody 4지표 테스트
사용자/레퍼런스 wav 파일 하나씩 넣고 `/api/prosody` 호출.
- `pitch_score`, `rhythm_score`, `stress_score`, `mfcc_cosine_score`, `composite_score` 값 확인
- NaN · 0점 · 100점 극단값 튀면 임계값 튜닝 필요 (→ 8번 연결)

### 3. 원어민 레퍼런스 오디오 녹음
경로: `data/references/{scenario_id}/{turn_index}.wav`
- 최소 `hospital/0.wav` ~ `hospital/3.wav` 까지
- bank, immigration 도 순차 확보
- **파일 없으면 운율 점수 자체가 안 찍힘**

### 4. Flutter UI에 새 prosody 점수 표시
백엔드는 이제 다음 필드를 내려보냄:
- `rhythm_score`, `stress_score`, `mfcc_cosine_score`, `composite_score`

현재 UI에는 안 보임. 결정 필요:
- [ ] composite 하나만 큰 점수로 표시
- [ ] 4개 막대그래프로 세분화 표시
- [ ] 둘 다

---

## 🟡 권장

### 5. Groq API 키 발급 + 연결 테스트
1. <https://console.groq.com/keys> 에서 키 발급
2. `.env` 에 `GROQ_API_KEY=gsk_...` 추가
3. `WHISPER_MODE=groq` 로 변경
4. `/api/stt` 호출해서 정상 응답 확인

로컬 Whisper `medium` 이 느리면 Groq 로 전환해서 데모 응답 속도 개선.

### 6. 데모데이 호스팅 방식 결정
| 옵션 | 장점 | 단점 |
|---|---|---|
| A. 노트북 현장 구동 | 세팅 간단 | 학교 WiFi 방화벽/포트 차단 리스크 |
| B. ngrok 터널링 | 무료, 설치 빠름 | 집 데스크탑/네트워크 의존 |
| C. Render/Railway 무료 배포 | 가장 안정적 | 초기 배포 시간 필요 |

추천: **Groq + Render 조합** (서버 가벼워져서 무료 티어에도 올라감)

### 7. 주제 잠금 실전 테스트
3개 시나리오별로 일부러 엉뚱한 발화 던져보기:
- 병원: "어제 축구했어요" / "유튜브 봤어요"
- 은행: "치킨 먹고 싶어요"
- 출입국: "놀이터 가고 싶어요"

→ Gemini가 부드럽게 시나리오로 되돌리는지 확인. 안 되면 `services/gemini_service.py` 의 시스템 프롬프트 강화.

---

## 🟢 여유 있으면

### 8. prosody 점수 임계값 튜닝
`services/prosody_service.py` 의 정규화 상수들:
```python
DTW_PITCH_MAX = 150.0    # Hz
DTW_RHYTHM_MAX = 0.5     # seconds
DTW_STRESS_MAX = 0.1     # RMS amplitude
```
실제 아동 발화 vs 원어민 발화로 테스트 후 점수 분포 정상화.

### 9. 시나리오 확장 (선택)
- 병원 → 접수 + 의사 진료 2단계 분리
- 새 시나리오: 학교 / 식당 / 마트 등

### 10. 데모 리허설 + 백업
- [ ] 전체 플로우 시연 순서 연습
- [ ] 실시간 실패 대비 백업 영상 녹화
- [ ] 충전기 / 멀티탭 / 폰 핫스팟 준비
- [ ] 마이크 권한 미리 허용된 데모 기기 확보

---

## ✅ 완료된 작업 (참고)

- Prosody 4지표(피치·리듬·강세·MFCC) + Praat 교차검증 코드 추가
- Gemini 시스템 프롬프트 3종에 주제 잠금 지시 반영
- Groq STT 모드 추가 (`whisper_service.py` + `config.py`)
- 스키마 확장 (`ProsodyResponse` 에 새 필드 5개)
- README 전면 재작성 + `.env.example` 갱신
