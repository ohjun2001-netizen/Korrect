def compute_total_score(prosody_score: float | None, text_match_score: float | None) -> float:
    """
    종합 점수 계산 (0~100).
    - prosody_score: 운율 유사도 점수 (없으면 None)
    - text_match_score: 발음 정확도 점수 (없으면 None)
    """
    scores = []

    if prosody_score is not None:
        scores.append(("prosody", prosody_score, 0.6))  # 운율 60% 비중

    if text_match_score is not None:
        scores.append(("text", text_match_score, 0.4))  # 발음 정확도 40% 비중

    if not scores:
        return 0.0

    # 가중 평균
    total_weight = sum(w for _, _, w in scores)
    weighted_sum = sum(score * w for _, score, w in scores)

    return round(weighted_sum / total_weight, 1)


def compute_text_match_score(recognized: str, expected: str) -> float:
    """
    인식된 텍스트와 기대 텍스트의 유사도를 0~100으로 반환.
    간단한 문자 단위 일치율 계산.
    """
    if not expected:
        return 100.0

    recognized = recognized.strip()
    expected = expected.strip()

    if recognized == expected:
        return 100.0

    # 공통 문자 비율 (간단 구현 — 필요 시 Levenshtein으로 교체 가능)
    common = sum(1 for c in recognized if c in expected)
    score = (common / max(len(recognized), len(expected))) * 100.0

    return round(min(score, 100.0), 1)
