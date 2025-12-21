"""Markdown output formatting for meeting transcriptions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from whisper_stt.diarization import SpeakerSegment


def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_meeting_transcript(
    segments: list[SpeakerSegment],
    title: str,
    duration_seconds: Optional[float] = None,
    source_file: Optional[str] = None,
) -> str:
    lines = [f"# {title}", ""]

    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

    if duration_seconds:
        lines.append(f"**Duration:** {format_timestamp(duration_seconds)}")

    if source_file:
        lines.append(f"**Source:** {source_file}")

    unique_speakers = sorted(set(seg.speaker for seg in segments))
    speaker_map = {
        old: f"Speaker {i + 1}"
        for i, old in enumerate(unique_speakers)
        if old != "Unknown"
    }
    speaker_map["Unknown"] = "Unknown Speaker"

    lines.append(f"**Speakers:** {len(unique_speakers)} detected")
    lines.extend(["", "---", ""])

    current_speaker = None
    for seg in segments:
        speaker = speaker_map.get(seg.speaker, seg.speaker)
        timestamp = format_timestamp(seg.start)

        if speaker != current_speaker:
            if current_speaker is not None:
                lines.append("")
            lines.append(f"[{timestamp}] **{speaker}:**")
            current_speaker = speaker

        lines.append(seg.text)

    lines.append("")
    return "\n".join(lines)


def save_transcript(
    content: str,
    output_path: Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def generate_output_path(
    source_file: Path,
    title: str,
    output_dir: Optional[Path] = None,
) -> Path:
    if output_dir is None:
        output_dir = source_file.parent

    safe_title = "".join(
        c if c.isalnum() or c in " -_" else "_"
        for c in title
    ).strip().replace(" ", "_")

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{safe_title}_{date_str}.md"

    return output_dir / filename
