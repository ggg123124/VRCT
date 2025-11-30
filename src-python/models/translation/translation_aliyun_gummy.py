"""Aliyun Gummy Chat real-time audio translation engine.

This module implements end-to-end audio translation using Aliyun's
Gummy Chat model with DashScope SDK. It provides sentence-level translation
with fast response times.

Architecture:
- Uses DashScope TranslationRecognizerChat for sentence-level translation
- Automatically detects sentence end (default 700ms silence, configurable)
- Each sentence triggers a new translation session automatically
- Reuses existing audio capture mechanisms
- Converts audio to 16kHz PCM16 format required by Gummy
"""

import queue
import threading
import time
import numpy as np
from typing import Callable, Optional, Dict, Any
from datetime import datetime

try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    import dashscope
    from dashscope.audio.asr import (
        TranslationRecognizerChat,
        TranslationRecognizerCallback,
        TranscriptionResult,
        TranslationResult
    )
except ImportError:
    dashscope = None
    TranslationRecognizerChat = None
    TranslationRecognizerCallback = None
    TranscriptionResult = None
    TranslationResult = None

try:
    from scipy import signal as scipy_signal
except ImportError:
    scipy_signal = None

try:
    from utils import printLog, errorLogging
except ImportError:
    def printLog(data, *args, **kwargs):
        print(data, *args, **kwargs)
    
    def errorLogging():
        import traceback
        traceback.print_exc()


class AudioFormatConverter:
    """Convert audio data to Gummy required format (16kHz mono PCM16)."""
    
    TARGET_SAMPLE_RATE = 16000
    TARGET_CHANNELS = 1
    TARGET_SAMPLE_WIDTH = 2  # 16-bit PCM
    
    @staticmethod
    def convert_audio_data(audio_data: bytes, source_sample_rate: int, 
                          source_channels: int = 1, source_sample_width: int = 2) -> bytes:
        """Convert audio data to target format.
        
        Args:
            audio_data: Raw audio bytes (PCM format)
            source_sample_rate: Source sample rate in Hz
            source_channels: Number of source channels (1=mono, 2=stereo)
            source_sample_width: Sample width in bytes (2=16-bit)
            
        Returns:
            Converted audio bytes in 16kHz mono PCM16 format
        """
        # Convert bytes to numpy array
        dtype = np.int16 if source_sample_width == 2 else np.int32
        audio_array = np.frombuffer(audio_data, dtype=dtype)
        
        # Convert stereo to mono if needed
        if source_channels == 2:
            audio_array = audio_array.reshape(-1, 2)
            audio_array = audio_array.mean(axis=1).astype(dtype)
        
        # Resample if needed
        if source_sample_rate != AudioFormatConverter.TARGET_SAMPLE_RATE:
            if scipy_signal is None:
                raise ImportError("scipy is required for audio resampling")
            
            num_samples = int(len(audio_array) * AudioFormatConverter.TARGET_SAMPLE_RATE / source_sample_rate)
            audio_array = scipy_signal.resample(audio_array, num_samples).astype(dtype)
        
        return audio_array.tobytes()


class GummyChatCallback(TranslationRecognizerCallback):
    """Callback handler for Gummy Chat translation events."""
    
    def __init__(self, target_language: str, result_callback: Callable[[Dict[str, Any]], None]):
        """Initialize callback handler.
        
        Args:
            target_language: Target language code for translation
            result_callback: Callback function to invoke with translation results
        """
        self.target_language = target_language
        self.result_callback = result_callback
        self._current_sentence_id = None
        self._last_original_text = ""  # Cache for last original text
        self._last_translated_text = ""  # Cache for last translation
        self._last_interim_send_time = 0.0  # Timestamp of last interim result sent
        self._interim_send_interval = 0.5  # Send interim results every 0.5 seconds
    
    def on_open(self) -> None:
        """Called when connection opens."""
        printLog("[Gummy Chat] Connection opened")
    
    def on_close(self) -> None:
        """Called when connection closes."""
        printLog("[Gummy Chat] Connection closed")
    
    def on_event(self, request_id, transcription_result: TranscriptionResult, 
                 translation_result: TranslationResult, usage) -> None:
        """Called when translation events arrive.
        
        Args:
            request_id: Request ID
            transcription_result: Transcription (source language recognition) result
            translation_result: Translation result
            usage: Usage information for billing
        """
        try:
            # We need both transcription (original text) and translation
            if transcription_result is None and translation_result is None:
                return
            
            # Get original text from transcription
            original_text = ""
            if transcription_result is not None:
                original_text = transcription_result.text
            
            # Get translation for target language
            translated_text = ""
            is_final = False
            if translation_result is not None:
                translation = translation_result.get_translation(self.target_language)
                if translation is not None:
                    translated_text = translation.text
                    is_final = translation.is_sentence_end
            
            # Log sentence progress
            if transcription_result is not None:
                if transcription_result.sentence_id != self._current_sentence_id:
                    self._current_sentence_id = transcription_result.sentence_id
                    # Reset cache for new sentence
                    self._last_original_text = ""
                    self._last_translated_text = ""
                    self._last_interim_send_time = 0.0
                    printLog(f"[Gummy Chat] New sentence #{transcription_result.sentence_id}")
            
            # Check if content changed (only send if different from last time)
            content_changed = (
                original_text != self._last_original_text or
                translated_text != self._last_translated_text
            )
            
            if not content_changed:
                return  # Skip sending if nothing changed
            
            # Rate limit interim results (non-final): only send every 0.5 seconds
            if not is_final:
                current_time = time.time()
                time_since_last_send = current_time - self._last_interim_send_time
                if time_since_last_send < self._interim_send_interval:
                    return  # Skip sending interim result too soon
                self._last_interim_send_time = current_time
            
            # Update cache
            self._last_original_text = original_text
            self._last_translated_text = translated_text
            
            # Prepare result with both original and translation
            result = {
                "text": original_text,  # Original text in source language
                "language": self.target_language,
                "timestamp": datetime.now(),
                "is_final": is_final,
                "translation": translated_text  # Translated text
            }
            
            # Log translation
            if is_final:
                printLog(f"[Gummy Chat] Original: '{original_text}' -> Translation: '{translated_text}'")
                if usage:
                    printLog(f"[Gummy Chat] Usage: {usage}")
            else:
                printLog(f"[Gummy Chat] Interim - Original: '{original_text}' -> Translation: '{translated_text}'")
            
            # Invoke callback (only when content changed)
            self.result_callback(result)
            
        except Exception as e:
            printLog(f"[Gummy Chat] Callback error: {e}")
            errorLogging()
    
    def on_complete(self) -> None:
        """Called when translation completes."""
        printLog("[Gummy Chat] Translation complete")
    
    def on_error(self, message) -> None:
        """Called on error.
        
        Args:
            message: Error message
        """
        printLog(f"[Gummy Chat] Error: {message}")


class AliyunGummyChatClient:
    """Base class for Aliyun Gummy Chat translation client."""
    
    def __init__(self, 
                 api_key: str,
                 source_language: str,
                 target_language: str,
                 audio_queue: queue.Queue,
                 result_callback: Callable[[Dict[str, Any]], None],
                 source_sample_rate: int = 16000,
                 max_end_silence: int = 700):
        """Initialize Gummy Chat client.
        
        Args:
            api_key: Aliyun DashScope API key
            source_language: Source language code (e.g., 'zh', 'en', 'ja')
            target_language: Target language code
            audio_queue: Queue containing audio data tuples (bytes, datetime)
            result_callback: Callback function for translation results
            source_sample_rate: Source audio sample rate (from microphone device)
            max_end_silence: Max silence duration to end sentence (ms), default 700ms
        """
        if dashscope is None or TranslationRecognizerChat is None:
            raise ImportError("dashscope package is required for Gummy Chat translation")
        
        self.api_key = api_key
        self.source_language = source_language
        self.target_language = target_language
        self.audio_queue = audio_queue
        self.result_callback = result_callback
        self.source_sample_rate = source_sample_rate
        self.max_end_silence = max_end_silence
        
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()
        
        # Set API key
        dashscope.api_key = api_key
        
        printLog(f"[Gummy Chat] Initialized - {source_language} -> {target_language}")
        printLog(f"[Gummy Chat] Max end silence: {max_end_silence}ms")
    
    def _create_translator(self) -> TranslationRecognizerChat:
        """Create a new translator instance for one sentence.
        
        Returns:
            TranslationRecognizerChat instance
        """
        callback = GummyChatCallback(self.target_language, self.result_callback)
        
        translator = TranslationRecognizerChat(
            model="gummy-chat-v1",
            format="pcm",
            sample_rate=16000,  # Gummy requires 16kHz
            source_language=self.source_language,
            transcription_enabled=True,  # Enable to get original text
            translation_enabled=True,
            translation_target_languages=[self.target_language],
            max_end_silence=self.max_end_silence,
            callback=callback
        )
        
        return translator
    
    def _process_audio_loop(self) -> None:
        """Main audio processing loop."""
        printLog("[Gummy Chat] Audio processing started")
        
        # Chunk size: 3200 bytes = 0.1 second at 16kHz, same as official example
        CHUNK_SIZE = 3200
        
        while self.running and not self._stop_event.is_set():
            try:
                # Create new translator for this sentence
                translator = self._create_translator()
                translator.start()
                printLog("[Gummy Chat] Translator started for new sentence")
                
                # Process audio until sentence ends
                sentence_ended = False
                audio_buffer = b""  # Buffer to hold leftover audio
                
                while self.running and not self._stop_event.is_set() and not sentence_ended:
                    try:
                        # Get audio from queue
                        audio_data, timestamp = self.audio_queue.get(timeout=0.1)
                        
                        # Convert audio format if needed
                        converted_audio = audio_data
                        if self.source_sample_rate != AudioFormatConverter.TARGET_SAMPLE_RATE:
                            try:
                                converted_audio = AudioFormatConverter.convert_audio_data(
                                    audio_data=audio_data,
                                    source_sample_rate=self.source_sample_rate,
                                    source_channels=1,
                                    source_sample_width=2
                                )
                            except Exception as e:
                                printLog(f"[Gummy Chat] Audio conversion error: {e}")
                                continue
                        
                        # Add to buffer
                        audio_buffer += converted_audio
                        
                        # Send in small chunks (3200 bytes at a time, like official example)
                        while len(audio_buffer) >= CHUNK_SIZE and not sentence_ended:
                            chunk = audio_buffer[:CHUNK_SIZE]
                            audio_buffer = audio_buffer[CHUNK_SIZE:]
                            
                            # Send audio frame
                            # Returns False when sentence ends (700ms silence detected)
                            can_continue = translator.send_audio_frame(chunk)
                            
                            if not can_continue:
                                printLog("[Gummy Chat] Sentence ended, stopping audio send")
                                sentence_ended = True
                                break
                        
                    except queue.Empty:
                        # If we have buffered audio and no new data, send it
                        if len(audio_buffer) > 0 and not sentence_ended:
                            can_continue = translator.send_audio_frame(audio_buffer)
                            audio_buffer = b""
                            if not can_continue:
                                printLog("[Gummy Chat] Sentence ended (final buffer)")
                                sentence_ended = True
                        continue
                    except Exception as e:
                        printLog(f"[Gummy Chat] Audio send error: {e}")
                        errorLogging()
                        break
                
                # Stop translator (waits for on_complete callback)
                printLog("[Gummy Chat] Stopping translator...")
                translator.stop()
                printLog("[Gummy Chat] Translator stopped, ready for next sentence")
                
                # Small delay before starting next sentence
                time.sleep(0.1)
                
            except Exception as e:
                printLog(f"[Gummy Chat] Translation loop error: {e}")
                errorLogging()
                time.sleep(1.0)  # Wait before retry
        
        printLog("[Gummy Chat] Audio processing stopped")
    
    def start(self) -> None:
        """Start the translation client."""
        if self.running:
            printLog("[Gummy Chat] Client already running")
            return
        
        self.running = True
        self._stop_event.clear()
        
        # Start background thread
        self.thread = threading.Thread(target=self._process_audio_loop, daemon=True)
        self.thread.start()
        
        printLog("[Gummy Chat] Client started")
    
    def stop(self) -> None:
        """Stop the translation client."""
        if not self.running:
            return
        
        printLog("[Gummy Chat] Stopping client...")
        self.running = False
        self._stop_event.set()
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        
        printLog("[Gummy Chat] Client stopped")


class AliyunMicGummyChatClient(AliyunGummyChatClient):
    """Gummy Chat client for microphone audio (source -> target)."""
    
    def __init__(self,
                 api_key: str,
                 source_language: str,
                 target_language: str,
                 mic_audio_queue: queue.Queue,
                 result_callback: Callable[[Dict[str, Any]], None],
                 source_sample_rate: int = 16000,
                 max_end_silence: int = 700):
        """Initialize microphone translation client.
        
        Args:
            api_key: Aliyun DashScope API key
            source_language: Source language code (user's language)
            target_language: Target language code (translation target)
            mic_audio_queue: Microphone audio queue
            result_callback: Callback for translation results
            source_sample_rate: Microphone sample rate
            max_end_silence: Max silence duration to end sentence (ms)
        """
        super().__init__(
            api_key=api_key,
            source_language=source_language,
            target_language=target_language,
            audio_queue=mic_audio_queue,
            result_callback=result_callback,
            source_sample_rate=source_sample_rate,
            max_end_silence=max_end_silence
        )


class AliyunSpeakerGummyChatClient(AliyunGummyChatClient):
    """Gummy Chat client for speaker audio (target -> source, reversed)."""
    
    def __init__(self,
                 api_key: str,
                 source_language: str,
                 target_language: str,
                 speaker_audio_queue: queue.Queue,
                 result_callback: Callable[[Dict[str, Any]], None],
                 source_sample_rate: int = 16000,
                 max_end_silence: int = 700):
        """Initialize speaker translation client.
        
        Args:
            api_key: Aliyun DashScope API key
            source_language: Target language code (reversed, what others speak)
            target_language: Source language code (reversed, translate to user's language)
            speaker_audio_queue: Speaker audio queue
            result_callback: Callback for translation results
            source_sample_rate: Speaker sample rate
            max_end_silence: Max silence duration to end sentence (ms)
        """
        # Note: For speaker, language direction is reversed
        super().__init__(
            api_key=api_key,
            source_language=source_language,  # Actually target language
            target_language=target_language,  # Actually source language
            audio_queue=speaker_audio_queue,
            result_callback=result_callback,
            source_sample_rate=source_sample_rate,
            max_end_silence=max_end_silence
        )


class AliyunMicGummyChatDirectClient:
    """Direct PyAudio-based Gummy Chat client (no queue, lowest latency)."""
    
    def __init__(self,
                 api_key: str,
                 source_language: str,
                 target_language: str,
                 mic_device_index: Optional[int],
                 result_callback: Callable[[Dict[str, Any]], None],
                 max_end_silence: int = 700,
                 max_sentence_duration: int = 25000):
        """Initialize direct microphone translation client.
        
        Args:
            api_key: Aliyun DashScope API key
            source_language: Source language code (user's language)
            target_language: Target language code (translation target)
            mic_device_index: PyAudio device index for microphone
            result_callback: Callback for translation results
            max_end_silence: Max silence duration to end sentence (ms)
            max_sentence_duration: Max duration for a single sentence (ms), prevents TOO_LONG_SPEECH error
        """
        if dashscope is None or TranslationRecognizerChat is None:
            raise ImportError("dashscope package is required for Gummy Chat translation")
        if pyaudio is None:
            raise ImportError("pyaudio package is required for direct audio capture")
        
        self.api_key = api_key
        self.source_language = source_language
        self.target_language = target_language
        self.mic_device_index = mic_device_index
        self.result_callback = result_callback
        self.max_end_silence = max_end_silence
        self.max_sentence_duration = max_sentence_duration  # Prevent TOO_LONG_SPEECH
        
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()
        
        self.mic = None
        self.stream = None
        
        # Set API key
        dashscope.api_key = api_key
        
        printLog(f"[Gummy Direct] Initialized - {source_language} -> {target_language}")
        printLog(f"[Gummy Direct] Max end silence: {max_end_silence}ms, Max sentence duration: {max_sentence_duration}ms")
    
    def _create_translator(self) -> TranslationRecognizerChat:
        """Create a new translator instance for one sentence.
        
        Returns:
            TranslationRecognizerChat instance with custom callback
        """
        # Custom callback that manages PyAudio stream
        callback = GummyDirectCallback(
            target_language=self.target_language,
            result_callback=self.result_callback,
            parent_client=self
        )
        
        translator = TranslationRecognizerChat(
            model="gummy-chat-v1",
            format="pcm",
            sample_rate=16000,  # Gummy requires 16kHz
            source_language=self.source_language,
            transcription_enabled=True,  # Enable to get original text
            translation_enabled=True,
            translation_target_languages=[self.target_language],
            max_end_silence=self.max_end_silence,
            callback=callback
        )
        
        return translator
    
    def _audio_capture_loop(self) -> None:
        """Main audio capture and translation loop (like official example)."""
        printLog("[Gummy Direct] Audio capture started")
        
        while self.running and not self._stop_event.is_set():
            try:
                # Create new translator for each sentence
                translator = self._create_translator()
                translator.start()  # This triggers on_open() which opens mic stream
                printLog("[Gummy Direct] Translator started for new sentence")
                
                # Read and send audio in small chunks (like official example)
                CHUNK_SIZE = 3200  # 0.1 second at 16kHz
                
                # Track sentence start time to prevent TOO_LONG_SPEECH
                sentence_start_time = time.time()
                max_duration_seconds = self.max_sentence_duration / 1000.0
                
                while self.running and not self._stop_event.is_set():
                    if self.stream is None:
                        time.sleep(0.01)
                        continue
                    
                    # Check if sentence exceeded max duration
                    elapsed_time = time.time() - sentence_start_time
                    if elapsed_time > max_duration_seconds:
                        printLog(f"[Gummy Direct] Sentence duration exceeded {max_duration_seconds:.1f}s, auto-restarting to prevent timeout")
                        break
                    
                    try:
                        # Read audio from mic stream
                        audio_data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                        
                        # Send to translator
                        # Returns False when sentence ends (silence detected)
                        can_continue = translator.send_audio_frame(audio_data)
                        
                        if not can_continue:
                            printLog("[Gummy Direct] Sentence ended, stopping")
                            break
                    
                    except Exception as e:
                        printLog(f"[Gummy Direct] Audio read error: {e}")
                        break
                
                # Stop translator (waits for on_complete callback)
                translator.stop()
                printLog("[Gummy Direct] Translator stopped, ready for next sentence")
                
                # Small delay before starting next sentence
                time.sleep(0.1)
            
            except Exception as e:
                printLog(f"[Gummy Direct] Translation loop error: {e}")
                errorLogging()
                time.sleep(1.0)
        
        printLog("[Gummy Direct] Audio capture stopped")
    
    def start(self) -> None:
        """Start the translation client."""
        if self.running:
            printLog("[Gummy Direct] Client already running")
            return
        
        self.running = True
        self._stop_event.clear()
        
        # Start background thread
        self.thread = threading.Thread(target=self._audio_capture_loop, daemon=True)
        self.thread.start()
        
        printLog("[Gummy Direct] Client started")
    
    def stop(self) -> None:
        """Stop the translation client."""
        if not self.running:
            return
        
        printLog("[Gummy Direct] Stopping client...")
        self.running = False
        self._stop_event.set()
        
        # Close PyAudio stream
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
        
        if self.mic:
            try:
                self.mic.terminate()
            except:
                pass
            self.mic = None
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        
        printLog("[Gummy Direct] Client stopped")


class GummyDirectCallback(TranslationRecognizerCallback):
    """Callback handler for direct PyAudio-based Gummy Chat."""
    
    def __init__(self, target_language: str, result_callback: Callable[[Dict[str, Any]], None],
                 parent_client: 'AliyunMicGummyChatDirectClient'):
        """Initialize callback handler.
        
        Args:
            target_language: Target language code for translation
            result_callback: Callback function to invoke with translation results
            parent_client: Reference to parent client for PyAudio management
        """
        self.target_language = target_language
        self.result_callback = result_callback
        self.parent_client = parent_client
        self._current_sentence_id = None
        self._last_original_text = ""  # Cache for last original text
        self._last_translated_text = ""  # Cache for last translation
        self._last_interim_send_time = 0.0  # Timestamp of last interim result sent
        self._interim_send_interval = 0.5  # Send interim results every 0.5 seconds
    
    def on_open(self) -> None:
        """Called when connection opens - initialize PyAudio stream."""
        printLog("[Gummy Direct] Connection opened, starting mic stream")
        try:
            self.parent_client.mic = pyaudio.PyAudio()
            self.parent_client.stream = self.parent_client.mic.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=self.parent_client.mic_device_index,
                frames_per_buffer=3200
            )
            printLog("[Gummy Direct] Mic stream opened successfully")
        except Exception as e:
            printLog(f"[Gummy Direct] Failed to open mic stream: {e}")
            errorLogging()
    
    def on_close(self) -> None:
        """Called when connection closes - close PyAudio stream."""
        printLog("[Gummy Direct] Connection closed")
        if self.parent_client.stream:
            try:
                self.parent_client.stream.stop_stream()
                self.parent_client.stream.close()
            except:
                pass
            self.parent_client.stream = None
        
        if self.parent_client.mic:
            try:
                self.parent_client.mic.terminate()
            except:
                pass
            self.parent_client.mic = None
    
    def on_event(self, request_id, transcription_result: TranscriptionResult, 
                 translation_result: TranslationResult, usage) -> None:
        """Called when translation events arrive.
        
        Args:
            request_id: Request ID
            transcription_result: Transcription result
            translation_result: Translation result
            usage: Usage information
        """
        try:
            # We need both transcription (original text) and translation
            if transcription_result is None and translation_result is None:
                return
            
            # Get original text from transcription
            original_text = ""
            if transcription_result is not None:
                original_text = transcription_result.text
            
            # Get translation for target language
            translated_text = ""
            is_final = False
            if translation_result is not None:
                translation = translation_result.get_translation(self.target_language)
                if translation is not None:
                    translated_text = translation.text
                    is_final = translation.is_sentence_end
            
            # Log sentence progress
            if transcription_result is not None:
                if transcription_result.sentence_id != self._current_sentence_id:
                    self._current_sentence_id = transcription_result.sentence_id
                    # Reset cache for new sentence
                    self._last_original_text = ""
                    self._last_translated_text = ""
                    self._last_interim_send_time = 0.0
                    printLog(f"[Gummy Direct] New sentence #{transcription_result.sentence_id}")
            
            # Check if content changed (only send if different from last time)
            content_changed = (
                original_text != self._last_original_text or
                translated_text != self._last_translated_text
            )
            
            if not content_changed:
                return  # Skip sending if nothing changed
            
            # Rate limit interim results (non-final): only send every 0.5 seconds
            if not is_final:
                current_time = time.time()
                time_since_last_send = current_time - self._last_interim_send_time
                if time_since_last_send < self._interim_send_interval:
                    return  # Skip sending interim result too soon
                self._last_interim_send_time = current_time
            
            # Update cache
            self._last_original_text = original_text
            self._last_translated_text = translated_text
            
            # Prepare result with both original and translation
            result = {
                "text": original_text,  # Original text in source language
                "language": self.target_language,
                "timestamp": datetime.now(),
                "is_final": is_final,
                "translation": translated_text  # Translated text
            }
            
            # Log translation
            if is_final:
                printLog(f"[Gummy Direct] Original: '{original_text}' -> Translation: '{translated_text}'")
                if usage:
                    printLog(f"[Gummy Direct] Usage: {usage}")
            else:
                printLog(f"[Gummy Direct] Interim - Original: '{original_text}' -> Translation: '{translated_text}'")
            
            # Invoke callback (only when content changed)
            self.result_callback(result)
            
        except Exception as e:
            printLog(f"[Gummy Direct] Callback error: {e}")
            errorLogging()
    
    def on_complete(self) -> None:
        """Called when translation completes."""
        printLog("[Gummy Direct] Translation complete")
    
    def on_error(self, message) -> None:
        """Called on error.
        
        Args:
            message: Error message
        """
        printLog(f"[Gummy Direct] Error: {message}")


class AliyunSpeakerGummyChatDirectClient:
    """Direct PyAudioWPatch-based Gummy Chat client for speaker (WASAPI Loopback)."""
    
    def __init__(self,
                 api_key: str,
                 source_language: str,
                 target_language: str,
                 speaker_device_index: Optional[int],
                 result_callback: Callable[[Dict[str, Any]], None],
                 max_end_silence: int = 700,
                 max_sentence_duration: int = 25000,
                 debug_save_audio: bool = False):  # Disable debug by default
        """Initialize direct speaker translation client.
        
        Args:
            api_key: Aliyun DashScope API key
            source_language: Source language code (what others speak in speaker)
            target_language: Target language code (translate to user's language)
            speaker_device_index: PyAudio device index for speaker (WASAPI Loopback)
            result_callback: Callback for translation results
            max_end_silence: Max silence duration to end sentence (ms)
            max_sentence_duration: Max duration for a single sentence (ms), prevents TOO_LONG_SPEECH error
            debug_save_audio: Save audio files for debugging
        """
        if dashscope is None or TranslationRecognizerChat is None:
            raise ImportError("dashscope package is required for Gummy Chat translation")
        if pyaudio is None:
            raise ImportError("pyaudio package is required for direct audio capture")
        
        self.api_key = api_key
        self.source_language = source_language  # What others speak
        self.target_language = target_language  # Translate to user's language
        self.speaker_device_index = speaker_device_index
        self.result_callback = result_callback
        self.max_end_silence = max_end_silence
        self.max_sentence_duration = max_sentence_duration  # Prevent TOO_LONG_SPEECH
        self.debug_save_audio = debug_save_audio
        
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()
        
        self.speaker = None
        self.stream = None
        
        # Audio resampling parameters
        self.native_sample_rate = None  # Device native sample rate
        self.native_channels = None  # Device native channels
        self.target_sample_rate = 16000  # Gummy Chat requires 16kHz
        self.audio_buffer = b""  # Buffer for resampling
        
        # Debug audio saving
        self.debug_audio_dir = r"E:\workspace\python\VRCT\debug_audio_output"
        self.debug_sentence_count = 0
        self.debug_original_audio = []  # Buffer for original audio (48kHz)
        self.debug_resampled_audio = []  # Buffer for resampled audio (16kHz)
        self.debug_logged_conversion = False  # Flag to log conversion info only once
        
        # Create debug directory
        if self.debug_save_audio:
            import os
            os.makedirs(self.debug_audio_dir, exist_ok=True)
            printLog(f"[Gummy Direct Speaker] Debug mode: saving audio to {self.debug_audio_dir}")
        
        # Set API key
        dashscope.api_key = api_key
        
        printLog(f"[Gummy Direct Speaker] Initialized - {source_language} -> {target_language}")
        printLog(f"[Gummy Direct Speaker] Max end silence: {max_end_silence}ms, Max sentence duration: {max_sentence_duration}ms")
    
    def _create_translator(self) -> TranslationRecognizerChat:
        """Create a new translator instance for one sentence.
        
        Returns:
            TranslationRecognizerChat instance with custom callback
        """
        # Custom callback that manages PyAudio stream
        callback = GummySpeakerDirectCallback(
            target_language=self.target_language,
            result_callback=self.result_callback,
            parent_client=self
        )
        
        translator = TranslationRecognizerChat(
            model="gummy-chat-v1",
            format="pcm",
            sample_rate=16000,  # Gummy requires 16kHz
            source_language=self.source_language,
            transcription_enabled=True,  # Enable to get original text
            translation_enabled=True,
            translation_target_languages=[self.target_language],
            max_end_silence=self.max_end_silence,
            callback=callback
        )
        
        return translator
    
    def _stereo_to_mono(self, audio_bytes: bytes, channels: int) -> bytes:
        """Convert stereo/multi-channel audio to mono by averaging channels.
        
        Args:
            audio_bytes: Original audio bytes (int16 PCM)
            channels: Number of channels
        
        Returns:
            Mono audio bytes
        """
        if channels == 1:
            return audio_bytes
        
        # Convert bytes to numpy array
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # Reshape to (samples, channels)
        audio_data = audio_data.reshape(-1, channels)
        
        # Average across channels to get mono
        mono_data = audio_data.mean(axis=1).astype(np.int16)
        
        return mono_data.tobytes()
    
    def _resample_audio(self, audio_bytes: bytes, orig_sr: int, target_sr: int) -> bytes:
        """Resample audio from original sample rate to target sample rate using high-quality method.
        
        Args:
            audio_bytes: Original audio bytes (int16 PCM)
            orig_sr: Original sample rate
            target_sr: Target sample rate
        
        Returns:
            Resampled audio bytes
        """
        if orig_sr == target_sr:
            return audio_bytes
        
        # Convert bytes to numpy array (float32 for better quality)
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
        
        # Calculate target sample count
        num_samples = int(len(audio_data) * target_sr / orig_sr)
        
        # Use scipy's high-quality resampling if available
        try:
            from scipy import signal
            # Use Fourier method for high-quality resampling
            resampled = signal.resample(audio_data, num_samples)
        except ImportError:
            # Fallback to linear interpolation if scipy not available
            indices = np.linspace(0, len(audio_data) - 1, num_samples)
            resampled = np.interp(indices, np.arange(len(audio_data)), audio_data)
        
        # Convert back to int16 bytes with clipping to prevent overflow
        resampled = np.clip(resampled, -32768, 32767)
        return resampled.astype(np.int16).tobytes()
    
    def _save_debug_audio(self) -> None:
        """Save debug audio files (original and resampled) for current sentence."""
        try:
            import wave
            import os
            from datetime import datetime
            
            # Increment sentence counter
            self.debug_sentence_count += 1
            
            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save original audio (48kHz, stereo or mono)
            if len(self.debug_original_audio) > 0:
                channels_str = f"{self.native_channels}ch" if self.native_channels else "mono"
                original_filepath = os.path.join(
                    self.debug_audio_dir,
                    f"sentence_{self.debug_sentence_count:03d}_{timestamp}_original_{self.native_sample_rate}Hz_{channels_str}.wav"
                )
                original_data = b"".join(self.debug_original_audio)
                
                with wave.open(original_filepath, 'wb') as wf:
                    wf.setnchannels(self.native_channels or 1)
                    wf.setsampwidth(2)  # 16-bit (2 bytes)
                    wf.setframerate(self.native_sample_rate or 48000)
                    wf.writeframes(original_data)
                
                printLog(f"[Gummy Direct Speaker] Saved original audio: {original_filepath} ({len(original_data)} bytes)")
            
            # Save resampled audio (16kHz)
            if len(self.debug_resampled_audio) > 0:
                resampled_filepath = os.path.join(
                    self.debug_audio_dir,
                    f"sentence_{self.debug_sentence_count:03d}_{timestamp}_resampled_16kHz.wav"
                )
                resampled_data = b"".join(self.debug_resampled_audio)
                
                with wave.open(resampled_filepath, 'wb') as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(2)  # 16-bit (2 bytes)
                    wf.setframerate(self.target_sample_rate)
                    wf.writeframes(resampled_data)
                
                printLog(f"[Gummy Direct Speaker] Saved resampled audio: {resampled_filepath} ({len(resampled_data)} bytes)")
            
            # Calculate duration info
            original_duration = len(b"".join(self.debug_original_audio)) / 2 / (self.native_sample_rate or 48000)
            resampled_duration = len(b"".join(self.debug_resampled_audio)) / 2 / self.target_sample_rate
            printLog(f"[Gummy Direct Speaker] Audio duration - Original: {original_duration:.2f}s, Resampled: {resampled_duration:.2f}s")
            
        except Exception as e:
            printLog(f"[Gummy Direct Speaker] Failed to save debug audio: {e}")
            errorLogging()
    
    def _audio_capture_loop(self) -> None:
        """Main audio capture and translation loop using PyAudio stream callbacks."""
        printLog("[Gummy Direct Speaker] Audio capture started")
        
        while self.running and not self._stop_event.is_set():
            try:
                # Reset debug buffers for new sentence
                if self.debug_save_audio:
                    self.debug_original_audio = []
                    self.debug_resampled_audio = []
                
                # Create new translator for each sentence
                translator = self._create_translator()
                translator.start()  # This triggers on_open() which opens speaker stream
                printLog("[Gummy Direct Speaker] Translator started for new sentence")
                
                # Read and send audio in small chunks
                CHUNK_SIZE = 3200  # 0.1 second at 16kHz (after resampling)
                
                # Track sentence start time to prevent TOO_LONG_SPEECH
                sentence_start_time = time.time()
                max_duration_seconds = self.max_sentence_duration / 1000.0
                
                while self.running and not self._stop_event.is_set():
                    if self.stream is None:
                        time.sleep(0.01)
                        continue
                    
                    # Check if sentence exceeded max duration
                    elapsed_time = time.time() - sentence_start_time
                    if elapsed_time > max_duration_seconds:
                        printLog(f"[Gummy Direct Speaker] Sentence duration exceeded {max_duration_seconds:.1f}s, auto-restarting to prevent timeout")
                        break
                    
                    try:
                        # Calculate native chunk size based on sample rate ratio
                        if self.native_sample_rate and self.native_sample_rate != self.target_sample_rate:
                            native_chunk_size = int(CHUNK_SIZE * self.native_sample_rate / self.target_sample_rate)
                        else:
                            native_chunk_size = CHUNK_SIZE
                        
                        # Adjust for stereo (need to read more frames for stereo)
                        if self.native_channels and self.native_channels > 1:
                            native_chunk_size = native_chunk_size * self.native_channels
                        
                        # Read audio from speaker stream (original, native sample rate and channels)
                        original_audio = self.stream.read(native_chunk_size // (self.native_channels or 1), exception_on_overflow=False)
                        
                        # Save original audio for debugging
                        if self.debug_save_audio:
                            self.debug_original_audio.append(original_audio)
                        
                        # Step 1: Convert stereo to mono (if needed)
                        if self.native_channels and self.native_channels > 1:
                            mono_audio = self._stereo_to_mono(original_audio, self.native_channels)
                            if not self.debug_logged_conversion:
                                printLog(f"[Gummy Direct Speaker] Converting {self.native_channels} channels to mono")
                                self.debug_logged_conversion = True
                        else:
                            mono_audio = original_audio
                        
                        # Step 2: Resample to 16kHz (if needed)
                        if self.native_sample_rate and self.native_sample_rate != self.target_sample_rate:
                            resampled_audio = self._resample_audio(mono_audio, self.native_sample_rate, self.target_sample_rate)
                        else:
                            resampled_audio = mono_audio
                        
                        # Save resampled audio for debugging
                        if self.debug_save_audio:
                            self.debug_resampled_audio.append(resampled_audio)
                        
                        # Send to translator
                        # Returns False when sentence ends (silence detected)
                        can_continue = translator.send_audio_frame(resampled_audio)
                        
                        if not can_continue:
                            printLog("[Gummy Direct Speaker] Sentence ended, stopping")
                            break
                    
                    except Exception as e:
                        printLog(f"[Gummy Direct Speaker] Audio read error: {e}")
                        errorLogging()
                        break
                
                # Stop translator (waits for on_complete callback)
                translator.stop()
                printLog("[Gummy Direct Speaker] Translator stopped, ready for next sentence")
                
                # Save debug audio files for this sentence
                if self.debug_save_audio and len(self.debug_resampled_audio) > 0:
                    self._save_debug_audio()
                
                # Small delay before starting next sentence
                time.sleep(0.1)
            
            except Exception as e:
                printLog(f"[Gummy Direct Speaker] Translation loop error: {e}")
                errorLogging()
                time.sleep(1.0)
        
        printLog("[Gummy Direct Speaker] Audio capture stopped")
    
    def start(self) -> None:
        """Start the translation client."""
        if self.running:
            printLog("[Gummy Direct Speaker] Client already running")
            return
        
        self.running = True
        self._stop_event.clear()
        
        # Start background thread
        self.thread = threading.Thread(target=self._audio_capture_loop, daemon=True)
        self.thread.start()
        
        printLog("[Gummy Direct Speaker] Client started")
    
    def stop(self) -> None:
        """Stop the translation client."""
        if not self.running:
            return
        
        printLog("[Gummy Direct Speaker] Stopping client...")
        self.running = False
        self._stop_event.set()
        
        # Close PyAudio stream
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
        
        if self.speaker:
            try:
                self.speaker.terminate()
            except:
                pass
            self.speaker = None
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        
        printLog("[Gummy Direct Speaker] Client stopped")


class GummySpeakerDirectCallback(TranslationRecognizerCallback):
    """Callback handler for direct PyAudio-based speaker Gummy Chat."""
    
    def __init__(self, target_language: str, result_callback: Callable[[Dict[str, Any]], None],
                 parent_client: 'AliyunSpeakerGummyChatDirectClient'):
        """Initialize callback handler.
        
        Args:
            target_language: Target language code for translation
            result_callback: Callback function to invoke with translation results
            parent_client: Reference to parent client for PyAudio management
        """
        self.target_language = target_language
        self.result_callback = result_callback
        self.parent_client = parent_client
        self._current_sentence_id = None
        self._last_original_text = ""  # Cache for last original text
        self._last_translated_text = ""  # Cache for last translation
        self._last_interim_send_time = 0.0  # Timestamp of last interim result sent
        self._interim_send_interval = 2  # Send interim results every 0.5 seconds
    
    def on_open(self) -> None:
        """Called when connection opens - initialize PyAudio stream with native sample rate."""
        printLog("[Gummy Direct Speaker] Connection opened, starting speaker stream")
        try:
            import pyaudiowpatch as pyaudio
            
            self.parent_client.speaker = pyaudio.PyAudio()
            
            # Get device info to determine native sample rate
            device_info = self.parent_client.speaker.get_device_info_by_index(
                self.parent_client.speaker_device_index
            )
            
            # Use device's native sample rate and channels (CRITICAL: don't force conversion)
            native_sample_rate = int(device_info.get('defaultSampleRate', 48000))
            native_channels = int(device_info.get('maxInputChannels', 2))
            
            # Store native parameters for processing later
            self.parent_client.native_sample_rate = native_sample_rate
            self.parent_client.native_channels = native_channels
            
            # Calculate chunk size for native sample rate (proportional to 3200 samples @ 16kHz)
            # 3200 samples @ 16kHz = 0.2 seconds
            frames_per_buffer = int(native_sample_rate * 0.2)  # 0.2s buffer
            
            printLog(f"[Gummy Direct Speaker] Device info:")
            printLog(f"  - Native sample rate: {native_sample_rate} Hz")
            printLog(f"  - Native channels: {native_channels}")
            printLog(f"  - Frames per buffer: {frames_per_buffer}")
            printLog(f"  - Will convert to: {self.parent_client.target_sample_rate} Hz, Mono")
            
            # Open stream at NATIVE parameters (let device use its natural format)
            self.parent_client.stream = self.parent_client.speaker.open(
                format=pyaudio.paInt16,
                channels=native_channels,  # CRITICAL: Use native channels, not forced mono!
                rate=native_sample_rate,
                input=True,
                input_device_index=self.parent_client.speaker_device_index,
                frames_per_buffer=frames_per_buffer
            )
            printLog("[Gummy Direct Speaker] Speaker stream opened successfully")
        except Exception as e:
            printLog(f"[Gummy Direct Speaker] Failed to open speaker stream: {e}")
            errorLogging()
    
    def on_close(self) -> None:
        """Called when connection closes - close PyAudio stream."""
        printLog("[Gummy Direct Speaker] Connection closed")
        if self.parent_client.stream:
            try:
                self.parent_client.stream.stop_stream()
                self.parent_client.stream.close()
            except:
                pass
            self.parent_client.stream = None
        
        if self.parent_client.speaker:
            try:
                self.parent_client.speaker.terminate()
            except:
                pass
            self.parent_client.speaker = None
    
    def on_event(self, request_id, transcription_result: TranscriptionResult, 
                 translation_result: TranslationResult, usage) -> None:
        """Called when translation events arrive.
        
        Args:
            request_id: Request ID
            transcription_result: Transcription result
            translation_result: Translation result
            usage: Usage information
        """
        try:
            # We need both transcription (original text) and translation
            if transcription_result is None and translation_result is None:
                return
            
            # Get original text from transcription
            original_text = ""
            if transcription_result is not None:
                original_text = transcription_result.text
            
            # Get translation for target language
            translated_text = ""
            is_final = False
            if translation_result is not None:
                translation = translation_result.get_translation(self.target_language)
                if translation is not None:
                    translated_text = translation.text
                    is_final = translation.is_sentence_end
            
            # Log sentence progress
            if transcription_result is not None:
                if transcription_result.sentence_id != self._current_sentence_id:
                    self._current_sentence_id = transcription_result.sentence_id
                    # Reset cache for new sentence
                    self._last_original_text = ""
                    self._last_translated_text = ""
                    self._last_interim_send_time = 0.0
                    printLog(f"[Gummy Direct Speaker] New sentence #{transcription_result.sentence_id}")
            
            # Check if content changed (only send if different from last time)
            content_changed = (
                original_text != self._last_original_text or
                translated_text != self._last_translated_text
            )
            
            if not content_changed:
                return  # Skip sending if nothing changed
            
            # Rate limit interim results (non-final): only send every 0.5 seconds
            if not is_final:
                current_time = time.time()
                time_since_last_send = current_time - self._last_interim_send_time
                if time_since_last_send < self._interim_send_interval:
                    return  # Skip sending interim result too soon
                self._last_interim_send_time = current_time
            
            # Update cache
            self._last_original_text = original_text
            self._last_translated_text = translated_text
            
            # Prepare result with both original and translation
            result = {
                "text": original_text,  # Original text in source language
                "language": self.target_language,
                "timestamp": datetime.now(),
                "is_final": is_final,
                "translation": translated_text  # Translated text
            }
            
            # Log translation
            if is_final:
                printLog(f"[Gummy Direct Speaker] Original: '{original_text}' -> Translation: '{translated_text}'")
                if usage:
                    printLog(f"[Gummy Direct Speaker] Usage: {usage}")
            else:
                printLog(f"[Gummy Direct Speaker] Interim - Original: '{original_text}' -> Translation: '{translated_text}'")
            
            # Invoke callback (only when content changed)
            self.result_callback(result)
            
        except Exception as e:
            printLog(f"[Gummy Direct Speaker] Callback error: {e}")
            errorLogging()
    
    def on_complete(self) -> None:
        """Called when translation completes."""
        printLog("[Gummy Direct Speaker] Translation complete")
    
    def on_error(self, message) -> None:
        """Called on error.
        
        Args:
            message: Error message
        """
        printLog(f"[Gummy Direct Speaker] Error: {message}")
