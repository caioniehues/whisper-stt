"""Whisper transcription engine wrapper optimized for ROCm."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Iterator, Optional, Union

import numpy as np
import torch
import whisper

logger = logging.getLogger(__name__)


class Transcriber:
    """OpenAI Whisper wrapper optimized for AMD ROCm.

    Uses large-v3 model by default for best accuracy on RX 7800XT.
    Falls back to medium if VRAM is insufficient.

    Args:
        model_name: Whisper model to use. Defaults to "large-v3".
        device: Device to run inference on. Defaults to "cuda" (ROCm).
        language: Target language for transcription. Defaults to "en".
        
    Example:
        >>> transcriber = Transcriber()
        >>> text = transcriber.transcribe("audio.mp3")
        >>> print(text)
    """
    
    SUPPORTED_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3", "turbo"]
    FALLBACK_MODEL = "medium"
    
    def __init__(
        self,
        model_name: str = "large-v3",
        device: Optional[str] = None,
        language: str = "en",
    ) -> None:
        self.model_name = model_name
        self.language = language
        self._model: Optional[whisper.Whisper] = None
        
        # Auto-detect device
        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
            else:
                self.device = "cpu"
                logger.warning("CUDA/ROCm not available, falling back to CPU")
        else:
            self.device = device
            
    @property
    def model(self) -> whisper.Whisper:
        """Lazy-load the Whisper model."""
        if self._model is None:
            self._model = self._load_model()
        return self._model
    
    def _load_model(self) -> whisper.Whisper:
        """Load Whisper model with VRAM fallback logic."""
        try:
            logger.info(f"Loading Whisper model '{self.model_name}' on {self.device}...")
            model = whisper.load_model(self.model_name, device=self.device)
            logger.info(f"Model loaded successfully")
            return model
        except torch.cuda.OutOfMemoryError:
            logger.warning(
                f"Insufficient VRAM for '{self.model_name}', "
                f"falling back to '{self.FALLBACK_MODEL}'"
            )
            torch.cuda.empty_cache()
            return whisper.load_model(self.FALLBACK_MODEL, device=self.device)
    
    def transcribe(
        self,
        audio: Union[str, Path, np.ndarray],
        *,
        task: str = "transcribe",
        verbose: bool = False,
        word_timestamps: bool = False,
        **kwargs,
    ) -> dict:
        """Transcribe audio to text.
        
        Args:
            audio: Path to audio file or numpy array of audio data.
            task: "transcribe" or "translate" (to English).
            verbose: Print progress during transcription.
            word_timestamps: Include word-level timestamps.
            **kwargs: Additional arguments passed to whisper.transcribe().
            
        Returns:
            Dictionary with 'text', 'segments', and 'language' keys.
        """
        if isinstance(audio, (str, Path)):
            audio = str(audio)
            
        result = self.model.transcribe(
            audio,
            language=self.language,
            task=task,
            verbose=verbose,
            word_timestamps=word_timestamps,
            **kwargs,
        )
        
        return result
    
    def transcribe_stream(
        self,
        audio_chunks: Iterator[np.ndarray],
        *,
        chunk_duration: float = 5.0,
        on_partial: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Transcribe streaming audio chunks.
        
        Args:
            audio_chunks: Iterator yielding numpy arrays of audio data.
            chunk_duration: Duration of each chunk in seconds.
            on_partial: Callback for partial transcription results.
            
        Returns:
            Complete transcription text.
        """
        full_text_parts = []
        buffer = np.array([], dtype=np.float32)
        sample_rate = 16000  # Whisper expects 16kHz
        chunk_samples = int(chunk_duration * sample_rate)
        
        for chunk in audio_chunks:
            buffer = np.concatenate([buffer, chunk])
            
            if len(buffer) >= chunk_samples:
                # Transcribe the buffer
                result = self.transcribe(buffer)
                text = result["text"].strip()
                
                if text:
                    full_text_parts.append(text)
                    if on_partial:
                        on_partial(text)
                
                # Keep a small overlap for context
                overlap_samples = int(0.5 * sample_rate)
                buffer = buffer[-overlap_samples:]
        
        # Process remaining audio
        if len(buffer) > sample_rate:  # At least 1 second
            result = self.transcribe(buffer)
            text = result["text"].strip()
            if text:
                full_text_parts.append(text)
                if on_partial:
                    on_partial(text)
        
        return " ".join(full_text_parts)
    
    def get_vram_usage(self) -> Optional[float]:
        """Get current GPU VRAM usage in GB."""
        if self.device == "cuda" and torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 ** 3)
        return None
    
    def unload(self) -> None:
        """Unload the model and free VRAM."""
        if self._model is not None:
            del self._model
            self._model = None
            if self.device == "cuda":
                torch.cuda.empty_cache()
            logger.info("Model unloaded")
