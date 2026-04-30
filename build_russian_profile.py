"""
러시아 억양 MFCC 프로필 빌드
필터링된 러시아어 모국어 화자 WAV 파일들에서 MFCC 평균 벡터를 추출해 저장
출력: data/russian_accent_profile.npy
"""
import numpy as np
import librosa
from pathlib import Path

WAV_DIR = Path(r"E:\russian_speakers")
OUTPUT_PATH = Path("data/russian_accent_profile.npy")
N_MFCC = 13


def main():
    wav_files = list(WAV_DIR.rglob("*.wav"))
    print(f"총 {len(wav_files)}개 파일 처리 중...")

    vectors = []
    errors = 0

    for i, wav_path in enumerate(wav_files):
        try:
            y, sr = librosa.load(wav_path, sr=16000, mono=True)
            if len(y) < sr * 0.3:  # 0.3초 미만 스킵
                continue
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
            vectors.append(mfcc.mean(axis=1))
        except Exception:
            errors += 1

        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{len(wav_files)} 처리 완료...")

    profile = np.mean(vectors, axis=0)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUTPUT_PATH, profile)

    print(f"\n완료: {len(vectors)}개 사용, {errors}개 오류")
    print(f"프로필 저장: {OUTPUT_PATH}")
    print(f"벡터 shape: {profile.shape}")


if __name__ == "__main__":
    main()
