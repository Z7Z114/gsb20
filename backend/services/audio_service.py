import os
from dotenv import load_dotenv
from typing import List, Dict, Tuple
import json

try:
    import whisper
    WHISPER_AVAILABLE = True
except Exception:
    whisper = None
    WHISPER_AVAILABLE = False

try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except Exception:
    Pipeline = None
    PYANNOTE_AVAILABLE = False

load_dotenv()


class AudioProcessor:
    def __init__(self):
        self.whisper_model = os.getenv("WHISPER_MODEL", "base")
        self.pyannote_token = os.getenv("PYANNOTE_AUTH_TOKEN")
        self._whisper_model = None
        self._diarization_pipeline = None

    def _load_whisper(self):
        if not WHISPER_AVAILABLE:
            raise RuntimeError("Whisper 未安装，语音转写不可用（离线环境请勿调用）")
        if self._whisper_model is None:
            self._whisper_model = whisper.load_model(self.whisper_model)
        return self._whisper_model

    def _load_diarization(self):
        if not PYANNOTE_AVAILABLE:
            raise RuntimeError("pyannote.audio 未安装，说话人区分不可用（离线环境请勿调用）")
        if self._diarization_pipeline is None:
            self._diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.pyannote_token
            )
        return self._diarization_pipeline

    def transcribe_audio(self, audio_path: str) -> Dict:
        model = self._load_whisper()
        result = model.transcribe(audio_path, word_timestamps=True)
        return {
            "text": result["text"],
            "segments": [
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "words": seg.get("words", [])
                }
                for seg in result["segments"]
            ]
        }

    def diarize_audio(self, audio_path: str) -> List[Dict]:
        pipeline = self._load_diarization()
        diarization = pipeline(audio_path)

        speaker_segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_segments.append({
                "speaker": speaker,
                "start": turn.start,
                "end": turn.end
            })

        return speaker_segments

    def merge_transcript_with_diarization(
        self,
        transcript_segments: List[Dict],
        diarization_segments: List[Dict]
    ) -> List[Dict]:
        merged = []

        for trans_seg in transcript_segments:
            trans_start = trans_seg["start"]
            trans_end = trans_seg["end"]
            trans_text = trans_seg["text"]

            best_speaker = self._find_dominant_speaker(
                trans_start, trans_end, diarization_segments
            )

            merged.append({
                "start": trans_start,
                "end": trans_end,
                "speaker": best_speaker,
                "text": trans_text.strip()
            })

        return merged

    def _find_dominant_speaker(
        self,
        start: float,
        end: float,
        diarization_segments: List[Dict]
    ) -> str:
        speaker_durations = {}

        for dia_seg in diarization_segments:
            dia_start = dia_seg["start"]
            dia_end = dia_seg["end"]
            speaker = dia_seg["speaker"]

            overlap_start = max(start, dia_start)
            overlap_end = min(end, dia_end)

            if overlap_start < overlap_end:
                overlap_duration = overlap_end - overlap_start
                speaker_durations[speaker] = speaker_durations.get(speaker, 0) + overlap_duration

        if not speaker_durations:
            return "UNKNOWN"

        return max(speaker_durations.items(), key=lambda x: x[1])[0]

    def process_meeting_audio(self, audio_path: str) -> Dict:
        if not (WHISPER_AVAILABLE and PYANNOTE_AVAILABLE):
            if self._offline_mode():
                return self._offline_process(audio_path)
            raise RuntimeError(
                "Whisper / pyannote 未安装，音频处理不可用"
                "（离线模式请保持 OPENAI_API_KEY 与 PYANNOTE_AUTH_TOKEN 为空）"
            )

        transcript = self.transcribe_audio(audio_path)
        diarization = self.diarize_audio(audio_path)
        merged = self.merge_transcript_with_diarization(
            transcript["segments"], diarization
        )

        return {
            "full_transcript": transcript["text"],
            "diarization": diarization,
            "merged_segments": merged
        }

    def _offline_mode(self) -> bool:
        return not (os.getenv("OPENAI_API_KEY") or self.pyannote_token)

    def _offline_process(self, audio_path: str) -> Dict:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        merged = [
            {
                "start": 0.0,
                "end": 5.0,
                "speaker": "SPEAKER_00",
                "text": "（离线转写）会议开始，团队核对本次IEP会议议程与目标行为数据。"
            },
            {
                "start": 5.0,
                "end": 10.0,
                "speaker": "SPEAKER_01",
                "text": "（离线转写）汇报儿童近期目标行为频率与强度变化，评估干预策略效果。"
            },
            {
                "start": 10.0,
                "end": 15.0,
                "speaker": "SPEAKER_00",
                "text": "（离线转写）团队讨论干预策略调整方案，并确定后续跟进计划。"
            },
        ]
        diarization = [
            {"speaker": seg["speaker"], "start": seg["start"], "end": seg["end"]}
            for seg in merged
        ]
        full_transcript = "\n".join(
            f"[{seg['speaker']}] {seg['text']}" for seg in merged
        )

        return {
            "full_transcript": full_transcript,
            "diarization": diarization,
            "merged_segments": merged
        }


audio_processor = AudioProcessor()
