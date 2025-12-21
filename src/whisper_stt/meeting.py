"""Meeting transcription with speaker diarization."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Union

from whisper_stt.transcriber import Transcriber
from whisper_stt.diarization import Diarizer, SpeakerSegment
from whisper_stt.markdown import format_meeting_transcript, save_transcript, generate_output_path
from whisper_stt.title_generator import generate_title_from_segments

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    title: str
    segments: list[SpeakerSegment]
    markdown: str
    output_path: Optional[Path]
    duration: float
    num_speakers: int


class MeetingTranscriber:
    """Transcribe audio files with speaker diarization."""

    def __init__(
        self,
        model_name: str = "large-v3",
        language: str = "en",
        hf_token: Optional[str] = None,
    ) -> None:
        self.model_name = model_name
        self.language = language
        self.hf_token = hf_token

        self._transcriber: Optional[Transcriber] = None
        self._diarizer: Optional[Diarizer] = None

    @property
    def transcriber(self) -> Transcriber:
        if self._transcriber is None:
            self._transcriber = Transcriber(
                model_name=self.model_name,
                language=self.language,
            )
        return self._transcriber

    @property
    def diarizer(self) -> Diarizer:
        if self._diarizer is None:
            self._diarizer = Diarizer(hf_token=self.hf_token)
        return self._diarizer

    def transcribe(
        self,
        audio_path: Union[str, Path],
        output_dir: Optional[Path] = None,
        num_speakers: Optional[int] = None,
        on_progress: Optional[Callable[[str, float], None]] = None,
    ) -> TranscriptionResult:
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Processing: {audio_path.name}")

        if on_progress:
            on_progress("Loading models...", 0.0)

        if on_progress:
            on_progress("Transcribing audio...", 0.1)

        transcription = self.transcriber.transcribe(
            audio_path,
            word_timestamps=True,
            beam_size=10,
            best_of=10,
        )

        if on_progress:
            on_progress("Identifying speakers...", 0.5)

        diarization_segments = self.diarizer.diarize(
            audio_path,
            num_speakers=num_speakers,
        )

        if on_progress:
            on_progress("Merging results...", 0.8)

        merged_segments = self.diarizer.merge_with_transcription(
            diarization_segments,
            transcription["segments"],
        )

        if on_progress:
            on_progress("Generating output...", 0.9)

        title = generate_title_from_segments(merged_segments)

        duration = 0.0
        if merged_segments:
            duration = max(seg.end for seg in merged_segments)

        num_speakers = len(set(seg.speaker for seg in merged_segments))

        markdown = format_meeting_transcript(
            segments=merged_segments,
            title=title,
            duration_seconds=duration,
            source_file=audio_path.name,
        )

        output_path = generate_output_path(
            source_file=audio_path,
            title=title,
            output_dir=output_dir,
        )
        save_transcript(markdown, output_path)

        if on_progress:
            on_progress("Complete!", 1.0)

        logger.info(f"Transcript saved: {output_path}")

        return TranscriptionResult(
            title=title,
            segments=merged_segments,
            markdown=markdown,
            output_path=output_path,
            duration=duration,
            num_speakers=num_speakers,
        )

    def transcribe_batch(
        self,
        audio_files: list[Path],
        output_dir: Optional[Path] = None,
        on_file_complete: Optional[Callable[[Path, TranscriptionResult], None]] = None,
    ) -> list[TranscriptionResult]:
        results = []

        for i, audio_path in enumerate(audio_files):
            logger.info(f"Processing {i + 1}/{len(audio_files)}: {audio_path.name}")

            try:
                result = self.transcribe(audio_path, output_dir=output_dir)
                results.append(result)

                if on_file_complete:
                    on_file_complete(audio_path, result)

            except Exception as e:
                logger.error(f"Failed to process {audio_path}: {e}")

        return results

    def unload(self) -> None:
        if self._transcriber:
            self._transcriber.unload()
        if self._diarizer:
            self._diarizer.unload()
