"""
Google TTS로 원어민 레퍼런스 오디오 생성
출력: data/references/{scenario_id}/{turn_index}.wav (16kHz mono)
"""
import io
from pathlib import Path
from gtts import gTTS
from pydub import AudioSegment

SENTENCES = {
    "hospital": [
        "배가 아파요.",
        "어제부터 아팠어요.",
        "네, 열이 있어요.",
        "제 이름은 민준이에요.",
    ],
    "bank": [
        "돈을 바꾸고 싶어요.",
        "한국 돈으로 바꿔 주세요.",
        "만 원어치 바꿔 주세요.",
    ],
    "immigration": [
        "비자를 연장하고 싶어요.",
        "네, 여권 가져왔어요.",
        "일 년 더 있고 싶어요.",
    ],
}

OUTPUT_DIR = Path("data/references")

def main():
    for scenario_id, sentences in SENTENCES.items():
        out_dir = OUTPUT_DIR / scenario_id
        out_dir.mkdir(parents=True, exist_ok=True)

        for turn_index, text in enumerate(sentences):
            out_path = out_dir / f"{turn_index}.wav"

            # gTTS로 MP3 생성 (메모리)
            tts = gTTS(text=text, lang="ko")
            mp3_buf = io.BytesIO()
            tts.write_to_fp(mp3_buf)
            mp3_buf.seek(0)

            # MP3 → WAV 16kHz mono 변환
            audio = AudioSegment.from_mp3(mp3_buf)
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(out_path, format="wav")

            print(f"[생성] {out_path} — {text}")

    print("\n완료!")

if __name__ == "__main__":
    main()
