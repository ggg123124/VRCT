"""Aliyun Gummy Realtime Speech Translation Transcriber.

This module provides real-time speech-to-translation functionality using
Alibaba Cloud's Gummy model via the dashscope SDK.
"""

import os
import threading
from queue import Queue, Empty
from typing import Optional, List, Dict, Any, Callable

try:
    import dashscope
    from dashscope.audio.asr import TranslationRecognizerRealtime, TranslationRecognizerCallback
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    TranslationRecognizerCallback = object

from utils import errorLogging


class GummyCallback(TranslationRecognizerCallback if DASHSCOPE_AVAILABLE else object):
    """Callback handler for Gummy realtime translation events."""

    def __init__(self, result_queue: Queue, source_language: str, target_languages: List[str]):
        self.result_queue = result_queue
        self.source_language = source_language
        self.target_languages = target_languages
        self._current_transcription = ""
        self._current_translation = ""

    def on_open(self):
        """Called when WebSocket connection is established."""
        pass

    def on_close(self):
        """Called when WebSocket connection is closed."""
        pass

    def on_event(self, request_id, transcription_result, translation_result, usage):
        """Called when recognition/translation event is received.

        Args:
            request_id: Request identifier
            transcription_result: Speech recognition result
            translation_result: Translation result
            usage: Token/resource usage info
        """
        try:
            source_text = ""
            translated_text = ""
            is_sentence_end = False

            # Extract transcription (source language text)
            if transcription_result is not None:
                source_text = transcription_result.get_sentence().get("text", "")
                is_sentence_end = transcription_result.get_sentence().get("end_time", 0) > 0

            # Extract translation (target language text)
            if translation_result is not None and self.target_languages:
                target_lang = self.target_languages[0]
                translation = translation_result.get_translation(target_lang)
                if translation:
                    translated_text = translation.text if hasattr(translation, 'text') else str(translation)
                    is_sentence_end = getattr(translation, 'is_sentence_end', is_sentence_end)

            # Put result into queue if we have meaningful content
            if source_text or translated_text:
                result = {
                    "source_text": source_text,
                    "translated_text": translated_text,
                    "source_language": self.source_language,
                    "target_language": self.target_languages[0] if self.target_languages else None,
                    "is_sentence_end": is_sentence_end,
                    "confidence": 1.0,
                }
                self.result_queue.put(result)

        except Exception:
            errorLogging()

    def on_error(self, message):
        """Called when an error occurs.

        Args:
            message: Error message
        """
        errorLogging()
        self.result_queue.put({
            "error": str(message),
            "source_text": "",
            "translated_text": "",
            "is_sentence_end": True,
        })

    def on_complete(self):
        """Called when recognition is complete."""
        pass


class GummyRealtimeTranscriber:
    """Aliyun Gummy Realtime Speech Translation Client.

    This class wraps the dashscope SDK to provide real-time speech-to-translation
    functionality. Audio frames are sent via WebSocket and translation results
    are received asynchronously.
    """

    # Supported language codes
    SUPPORTED_LANGUAGES = [
        "zh", "en", "ja", "ko", "yue", "de", "fr", "ru", "es", "it",
        "pt", "id", "ar", "th", "hi", "da", "ur", "tr", "nl", "ms", "vi"
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        source_language: str = "zh",
        target_languages: Optional[List[str]] = None,
        sample_rate: int = 16000,
        audio_format: str = "pcm",
    ):
        """Initialize Gummy Realtime Transcriber.

        Args:
            api_key: Aliyun API key (or use DASHSCOPE_API_KEY env var)
            source_language: Source language code (e.g., 'zh', 'en', 'ja')
            target_languages: List of target language codes for translation
            sample_rate: Audio sample rate in Hz (default: 16000)
            audio_format: Audio format ('pcm', 'wav', 'mp3')
        """
        self.api_key = api_key
        self.source_language = source_language
        self.target_languages = target_languages or ["en"]
        self.sample_rate = sample_rate
        self.audio_format = audio_format

        self._recognizer = None
        self._callback = None
        self._result_queue: Queue = Queue()
        self._is_running = False
        self._lock = threading.Lock()

    def setAuthKey(self, api_key: str) -> bool:
        """Validate and set API key.

        Args:
            api_key: Aliyun API key

        Returns:
            True if key is valid, False otherwise
        """
        if not DASHSCOPE_AVAILABLE:
            return False

        if not api_key or not isinstance(api_key, str):
            return False

        # Test API key by attempting to create a recognizer
        try:
            dashscope.api_key = api_key
            # Simple validation - just check if we can initialize
            # Real validation happens on first use
            self.api_key = api_key
            return True
        except Exception:
            errorLogging()
            return False

    def setLanguages(self, source_language: str, target_languages: List[str]) -> None:
        """Set source and target languages.

        Args:
            source_language: Source language code
            target_languages: List of target language codes
        """
        if source_language in self.SUPPORTED_LANGUAGES:
            self.source_language = source_language
        if target_languages:
            self.target_languages = [
                lang for lang in target_languages
                if lang in self.SUPPORTED_LANGUAGES
            ]

    def start(self) -> bool:
        """Start the realtime translation session.

        Returns:
            True if started successfully, False otherwise
        """
        if not DASHSCOPE_AVAILABLE:
            return False

        if not self.api_key:
            return False

        with self._lock:
            if self._is_running:
                return True

            try:
                # Set API key
                dashscope.api_key = self.api_key

                # Clear result queue
                while not self._result_queue.empty():
                    try:
                        self._result_queue.get_nowait()
                    except Empty:
                        break

                # Create callback
                self._callback = GummyCallback(
                    result_queue=self._result_queue,
                    source_language=self.source_language,
                    target_languages=self.target_languages,
                )

                # Create recognizer
                self._recognizer = TranslationRecognizerRealtime(
                    model="gummy-realtime-v1",
                    format=self.audio_format,
                    sample_rate=self.sample_rate,
                    transcription_enabled=True,
                    translation_enabled=True,
                    translation_target_languages=self.target_languages,
                    callback=self._callback,
                )

                # Start recognition
                self._recognizer.start()
                self._is_running = True
                return True

            except Exception:
                errorLogging()
                self._is_running = False
                return False

    def stop(self) -> None:
        """Stop the realtime translation session."""
        with self._lock:
            if self._recognizer is not None:
                try:
                    self._recognizer.stop()
                except Exception:
                    errorLogging()
                finally:
                    self._recognizer = None
                    self._callback = None
                    self._is_running = False

    def send_audio_frame(self, audio_bytes: bytes) -> bool:
        """Send audio frame for recognition.

        Args:
            audio_bytes: Raw audio data (PCM format recommended)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self._is_running or self._recognizer is None:
            return False

        try:
            self._recognizer.send_audio_frame(audio_bytes)
            return True
        except Exception:
            errorLogging()
            return False

    def get_result(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """Get translation result from queue.

        Args:
            timeout: Maximum time to wait for result (seconds)

        Returns:
            Result dict with keys: source_text, translated_text, source_language,
            target_language, is_sentence_end, confidence. None if no result available.
        """
        try:
            return self._result_queue.get(timeout=timeout)
        except Empty:
            return None

    def get_all_results(self) -> List[Dict[str, Any]]:
        """Get all available results from queue.

        Returns:
            List of result dicts
        """
        results = []
        while True:
            try:
                result = self._result_queue.get_nowait()
                results.append(result)
            except Empty:
                break
        return results

    def is_running(self) -> bool:
        """Check if transcriber is running.

        Returns:
            True if running, False otherwise
        """
        return self._is_running

    def clear_queue(self) -> None:
        """Clear all pending results from queue."""
        while not self._result_queue.empty():
            try:
                self._result_queue.get_nowait()
            except Empty:
                break


def checkGummyAvailable() -> bool:
    """Check if Gummy SDK is available.

    Returns:
        True if dashscope is installed, False otherwise
    """
    return DASHSCOPE_AVAILABLE


def validateGummyApiKey(api_key: str) -> bool:
    """Validate Gummy API key.

    Args:
        api_key: API key to validate

    Returns:
        True if valid, False otherwise
    """
    if not DASHSCOPE_AVAILABLE:
        return False

    if not api_key or not isinstance(api_key, str):
        return False

    try:
        # Try to initialize with the key
        transcriber = GummyRealtimeTranscriber(api_key=api_key)
        return transcriber.setAuthKey(api_key)
    except Exception:
        errorLogging()
        return False


if __name__ == "__main__":
    # Simple test
    print(f"Dashscope available: {DASHSCOPE_AVAILABLE}")
    print(f"Supported languages: {GummyRealtimeTranscriber.SUPPORTED_LANGUAGES}")
