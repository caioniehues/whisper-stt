"""CLI entry point for whisper-stt."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_realtime(args: argparse.Namespace) -> int:
    from whisper_stt.realtime import run_realtime

    print("Starting real-time transcription...")
    print("Press F13 to toggle recording. Ctrl+C to exit.")
    print("-" * 40)

    run_realtime(
        model_name=args.model,
        language=args.language,
    )
    return 0


def cmd_transcribe(args: argparse.Namespace) -> int:
    from whisper_stt.meeting import MeetingTranscriber

    files = []
    for pattern in args.files:
        path = Path(pattern)
        if path.is_file():
            files.append(path)
        else:
            files.extend(Path(".").glob(pattern))

    if not files:
        print("No audio files found.", file=sys.stderr)
        return 1

    print(f"Found {len(files)} file(s) to process.")

    transcriber = MeetingTranscriber(
        model_name=args.model,
        language=args.language,
    )

    output_dir = Path(args.output) if args.output else None

    def on_progress(msg: str, progress: float) -> None:
        bar_width = 30
        filled = int(bar_width * progress)
        bar = "=" * filled + "-" * (bar_width - filled)
        print(f"\r[{bar}] {progress * 100:.0f}% {msg}", end="", flush=True)
        if progress >= 1.0:
            print()

    for audio_file in files:
        print(f"\nProcessing: {audio_file.name}")

        try:
            result = transcriber.transcribe(
                audio_file,
                output_dir=output_dir,
                num_speakers=args.speakers,
                on_progress=on_progress,
            )
            print(f"  Title: {result.title}")
            print(f"  Speakers: {result.num_speakers}")
            print(f"  Duration: {result.duration:.1f}s")
            print(f"  Output: {result.output_path}")

        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)

    transcriber.unload()
    return 0


def cmd_gui(args: argparse.Namespace) -> int:
    from whisper_stt.gui import run_gui
    return run_gui(
        model_name=args.model,
        language=args.language,
    )


def cmd_daemon(args: argparse.Namespace) -> int:
    from whisper_stt.service.daemon import run_daemon
    return run_daemon(
        model_name=args.model,
        language=args.language,
    )


def cmd_tray(args: argparse.Namespace) -> int:
    from whisper_stt.tray import run_tray
    return run_tray(
        model_name=args.model,
        language=args.language,
    )


def cmd_status(args: argparse.Namespace) -> int:
    from whisper_stt.service.daemon import DaemonManager
    
    manager = DaemonManager()
    status = manager.read_status()
    is_running = manager.is_running()
    
    if not is_running:
        print("Service: stopped")
        return 1
    
    recording = status.get("recording", False)
    model = status.get("model", "unknown")
    pid = status.get("pid", "unknown")
    
    print(f"Service: running (PID {pid})")
    print(f"Model: {model}")
    print(f"Recording: {'yes' if recording else 'no'}")
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    from whisper_stt.service.daemon import DaemonManager
    
    manager = DaemonManager()
    if manager.stop_daemon():
        print("Service stopped.")
        return 0
    else:
        print("Service not running.")
        return 1


def cmd_toggle(args: argparse.Namespace) -> int:
    from whisper_stt.service.daemon import DaemonManager
    
    manager = DaemonManager()
    if manager.is_running():
        return cmd_stop(args)
    else:
        return cmd_daemon(args)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stt",
        description="Real-time speech-to-text for AMD ROCm on Wayland",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "-m", "--model",
        default="large-v3",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3", "turbo"],
        help="Whisper model to use (default: large-v3)",
    )
    parser.add_argument(
        "-l", "--language",
        default="en",
        help="Language code (default: en)",
    )

    subparsers = parser.add_subparsers(dest="command")

    realtime_parser = subparsers.add_parser(
        "realtime",
        aliases=["rt"],
        help="Real-time push-to-talk mode (F13 toggle)",
    )
    realtime_parser.set_defaults(func=cmd_realtime)

    transcribe_parser = subparsers.add_parser(
        "transcribe",
        aliases=["t", "file"],
        help="Transcribe audio file(s) with speaker diarization",
    )
    transcribe_parser.add_argument(
        "files",
        nargs="+",
        help="Audio file(s) or glob pattern",
    )
    transcribe_parser.add_argument(
        "-o", "--output",
        help="Output directory for transcripts",
    )
    transcribe_parser.add_argument(
        "-s", "--speakers",
        type=int,
        help="Number of speakers (auto-detect if not specified)",
    )
    transcribe_parser.set_defaults(func=cmd_transcribe)

    gui_parser = subparsers.add_parser(
        "gui",
        help="Open Meeting Mode GUI",
    )
    gui_parser.set_defaults(func=cmd_gui)

    daemon_parser = subparsers.add_parser(
        "daemon",
        help="Run as background daemon",
    )
    daemon_parser.set_defaults(func=cmd_daemon)

    tray_parser = subparsers.add_parser(
        "tray",
        help="Run with system tray icon",
    )
    tray_parser.set_defaults(func=cmd_tray)

    status_parser = subparsers.add_parser(
        "status",
        help="Show daemon status",
    )
    status_parser.set_defaults(func=cmd_status)

    stop_parser = subparsers.add_parser(
        "stop",
        help="Stop running daemon",
    )
    stop_parser.set_defaults(func=cmd_stop)

    toggle_parser = subparsers.add_parser(
        "toggle",
        help="Toggle daemon on/off",
    )
    toggle_parser.set_defaults(func=cmd_toggle)

    args = parser.parse_args(argv)
    setup_logging(args.verbose)

    if args.command is None:
        return cmd_realtime(args)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
