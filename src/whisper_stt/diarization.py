"""Speaker diarization using pyannote.audio."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import torch

logger = logging.getLogger(__name__)


@dataclass
class SpeakerSegment:
    speaker: str
    start: float
    end: float
    text: str = ""


class Diarizer:
    """Speaker diarization using pyannote.audio pipeline."""

    HUGGINGFACE_TOKEN_ENV = "HF_TOKEN"

    def __init__(
        self,
        device: Optional[str] = None,
        hf_token: Optional[str] = None,
    ) -> None:
        self._pipeline = None

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self._hf_token = hf_token or self._get_hf_token()

    def _get_hf_token(self) -> Optional[str]:
        import os
        token = os.environ.get(self.HUGGINGFACE_TOKEN_ENV)
        if not token:
            logger.warning(
                f"HuggingFace token not found. Set {self.HUGGINGFACE_TOKEN_ENV} env var. "
                "Get token at: https://huggingface.co/settings/tokens"
            )
        return token

    @property
    def pipeline(self):
        if self._pipeline is None:
            self._pipeline = self._load_pipeline()
        return self._pipeline

    def _load_pipeline(self):
        try:
            from pyannote.audio import Pipeline
        except ImportError:
            raise ImportError(
                "pyannote.audio required. Install with: pip install pyannote.audio"
            )

        logger.info("Loading speaker diarization pipeline...")

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=self._hf_token,
        )

        if self.device == "cuda" and torch.cuda.is_available():
            pipeline = pipeline.to(torch.device("cuda"))

        logger.info("Diarization pipeline loaded.")
        return pipeline

    def diarize(
        self,
        audio_path: Union[str, Path],
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
    ) -> list[SpeakerSegment]:
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Diarizing: {audio_path.name}")

        kwargs = {}
        if num_speakers is not None:
            kwargs["num_speakers"] = num_speakers
        if min_speakers is not None:
            kwargs["min_speakers"] = min_speakers
        if max_speakers is not None:
            kwargs["max_speakers"] = max_speakers

        diarization = self.pipeline(str(audio_path), **kwargs)

        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append(SpeakerSegment(
                speaker=speaker,
                start=turn.start,
                end=turn.end,
            ))

        segments.sort(key=lambda s: s.start)
        logger.info(f"Found {len(set(s.speaker for s in segments))} speakers, {len(segments)} segments")
        return segments

    def merge_with_transcription(
        self,
        segments: list[SpeakerSegment],
        transcription_segments: list[dict],
    ) -> list[SpeakerSegment]:
        """Merge diarization segments with Whisper transcription segments."""
        result = []

        for trans_seg in transcription_segments:
            trans_start = trans_seg["start"]
            trans_end = trans_seg["end"]
            trans_text = trans_seg["text"].strip()

            best_speaker = "Unknown"
            best_overlap = 0.0

            for diar_seg in segments:
                overlap_start = max(trans_start, diar_seg.start)
                overlap_end = min(trans_end, diar_seg.end)
                overlap = max(0, overlap_end - overlap_start)

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = diar_seg.speaker

            result.append(SpeakerSegment(
                speaker=best_speaker,
                start=trans_start,
                end=trans_end,
                text=trans_text,
            ))

        return result

    def unload(self) -> None:
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
            if self.device == "cuda":
                torch.cuda.empty_cache()
