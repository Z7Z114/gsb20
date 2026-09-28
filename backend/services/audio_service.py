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


audio_processor = AudioProcessor()
