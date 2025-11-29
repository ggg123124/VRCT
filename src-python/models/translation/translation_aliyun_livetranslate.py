"""Aliyun Qwen3 LiveTranslate Flash real-time audio translation engine.

This module implements end-to-end audio translation using Aliyun's
LiveTranslate WebSocket API. It bypasses local VAD and STT, directly
translating audio streams from microphone and speaker devices.

Architecture:
- Reuses existing audio capture (SelectedMicEnergyAndAudioRecorder,
  SelectedSpeakerEnergyAndAudioRecorder)
- Reads from mic_audio_queue and speaker_audio_queue
- Converts audio format to 16kHz mono PCM16
- Encodes audio to base64 and sends via WebSocket
- Receives translation results and invokes callbacks
"""

import asyncio
import base64
import json
import queue
import threading
import time
import numpy as np
from typing import Callable, Optional, Dict, Any
from datetime import datetime

try:
    import websockets
except ImportError:
    websockets = None

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
    """Convert audio data to Aliyun LiveTranslate required format (16kHz mono PCM16)."""
    
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
            # Reshape and average channels
            audio_array = audio_array.reshape(-1, 2)
            audio_array = audio_array.mean(axis=1).astype(dtype)
        
        # Resample if needed
        if source_sample_rate != AudioFormatConverter.TARGET_SAMPLE_RATE:
            if scipy_signal is None:
                raise ImportError("scipy is required for audio resampling")
            
            # Calculate number of output samples
            num_samples = int(len(audio_array) * AudioFormatConverter.TARGET_SAMPLE_RATE / source_sample_rate)
            audio_array = scipy_signal.resample(audio_array, num_samples).astype(dtype)
        
        # Convert to bytes
        return audio_array.tobytes()


class AliyunLiveTranslateClient:
    """Base class for Aliyun LiveTranslate WebSocket client."""
    
    # API endpoints
    API_ENDPOINT_CN = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
    API_ENDPOINT_INTL = "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime"
    
    MODEL_NAME = "qwen3-livetranslate-flash-realtime"
    
    def __init__(self, 
                 api_key: str,
                 source_language: str,
                 target_language: str,
                 audio_queue: queue.Queue,
                 result_callback: Callable[[Dict[str, Any]], None],
                 use_international: bool = False,
                 debug_save_audio: bool = False,
                 source_sample_rate: int = 16000):
        """Initialize Aliyun LiveTranslate client.
        
        Args:
            api_key: Aliyun DashScope API key
            source_language: Source language code (e.g., 'en', 'zh', 'ja')
            target_language: Target language code
            audio_queue: Queue containing audio data tuples (bytes, datetime)
            result_callback: Callback function for translation results
            use_international: Use international endpoint if True
            debug_save_audio: Save audio to file for debugging
            source_sample_rate: Source audio sample rate (from microphone device)
        """
        if websockets is None:
            raise ImportError("websockets package is required for Aliyun LiveTranslate")
        
        self.api_key = api_key
        self.source_language = source_language
        self.target_language = target_language
        self.audio_queue = audio_queue
        self.result_callback = result_callback
        self.use_international = use_international
        self.source_sample_rate = source_sample_rate
        
        self.ws = None
        self.running = False
        self.thread = None
        self.loop = None
        
        self._stop_event = threading.Event()
        self._last_audio_time = time.time()
        self._heartbeat_interval = 60  # Send heartbeat every 60 seconds
        
        # Debug: Save audio to file
        self.debug_save_audio = debug_save_audio
        self.debug_audio_file = None
        self.debug_audio_file_original = None
        self.debug_audio_counter = 0
        if self.debug_save_audio:
            try:
                import os
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Save to workspace root, NOT in src-tauri to avoid triggering file watcher
                debug_dir = "debug_audio_output"
                os.makedirs(debug_dir, exist_ok=True)
                debug_filename = f"{debug_dir}/aliyun_audio_{timestamp}_converted_16k.pcm"
                debug_filename_orig = f"{debug_dir}/aliyun_audio_{timestamp}_original_{source_sample_rate}hz.pcm"
                self.debug_audio_file = open(debug_filename, "wb")
                self.debug_audio_file_original = open(debug_filename_orig, "wb")
                printLog(f"[Aliyun LiveTranslate Debug] Source sample rate: {source_sample_rate} Hz")
                printLog(f"[Aliyun LiveTranslate Debug] Saving converted audio to: {debug_filename}")
                printLog(f"[Aliyun LiveTranslate Debug] Saving original audio to: {debug_filename_orig}")
            except Exception as e:
                printLog(f"[Aliyun LiveTranslate Debug] Failed to create debug files: {e}")
                self.debug_save_audio = False
                if self.debug_audio_file:
                    try:
                        self.debug_audio_file.close()
                    except:
                        pass
                    self.debug_audio_file = None
                if self.debug_audio_file_original:
                    try:
                        self.debug_audio_file_original.close()
                    except:
                        pass
                    self.debug_audio_file_original = None
        
    def _get_api_url(self) -> str:
        """Get WebSocket API URL with query parameters."""
        base_url = self.API_ENDPOINT_INTL if self.use_international else self.API_ENDPOINT_CN
        return f"{base_url}?model={self.MODEL_NAME}"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get WebSocket connection headers."""
        return {
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _create_session_update_event(self) -> Dict[str, Any]:
        """Create session.update event for text-only mode."""
        return {
            "event_id": f"event_{int(time.time() * 1000)}",
            "type": "session.update",
            "session": {
                "modalities": ["text"],  # Text-only mode
                "input_audio_format": "pcm16",
                "translation": {
                    "language": self.target_language
                }
            }
        }
    
    def _create_audio_append_event(self, audio_data: bytes) -> Dict[str, Any]:
        """Create input_audio_buffer.append event.
        
        Args:
            audio_data: Raw PCM16 audio bytes
            
        Returns:
            Event dictionary ready to send
        """
        # Base64 encode audio data
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            "event_id": f"event_{int(time.time() * 1000)}",
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }
    
    async def _handle_server_event(self, event: Dict[str, Any]) -> None:
        """Handle server events.
        
        Args:
            event: Parsed event dictionary from server
        """
        event_type = event.get("type", "")
        
        if event_type == "session.created":
            printLog(f"[Aliyun LiveTranslate] Session created")
        elif event_type == "session.updated":
            printLog(f"[Aliyun LiveTranslate] Session updated")
        elif event_type == "response.text.done":
            # Translation result received
            translation_text = event.get("text", "")
            if translation_text:
                # Invoke callback with translation result
                result = {
                    "text": translation_text,
                    "language": self.source_language,
                    "timestamp": datetime.now()
                }
                try:
                    self.result_callback(result)
                except Exception:
                    errorLogging()
        elif event_type == "response.done":
            # Response completed
            usage = event.get("response", {}).get("usage", {})
            printLog(f"[Aliyun LiveTranslate] Response done. Usage: {usage}")
        elif event_type == "error":
            error_info = event.get("error", {})
            printLog(f"[Aliyun LiveTranslate] Error: {error_info}")
    
    async def _websocket_handler(self) -> None:
        """Main WebSocket handler coroutine."""
        url = self._get_api_url()
        headers = self._get_headers()
        
        try:
            async with websockets.connect(url, additional_headers=headers, ping_interval=None) as ws:
                self.ws = ws
                printLog(f"[Aliyun LiveTranslate] WebSocket connected to {url}")
                
                # Send session configuration
                session_update = self._create_session_update_event()
                await ws.send(json.dumps(session_update))
                
                # Create tasks for sending, receiving, and heartbeat
                send_task = asyncio.create_task(self._audio_sender())
                recv_task = asyncio.create_task(self._message_receiver())
                heartbeat_task = asyncio.create_task(self._heartbeat_sender())
                
                # Wait for any task to complete or stop event
                done, pending = await asyncio.wait(
                    [send_task, recv_task, heartbeat_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
        except Exception as e:
            printLog(f"[Aliyun LiveTranslate] WebSocket error: {e}")
            errorLogging()
        finally:
            self.ws = None
            printLog("[Aliyun LiveTranslate] WebSocket disconnected")
    
    async def _audio_sender(self) -> None:
        """Send audio data from queue to WebSocket."""
        while self.running and not self._stop_event.is_set():
            try:
                # Get audio data from queue with timeout
                try:
                    audio_data, timestamp = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    await asyncio.sleep(0.01)
                    continue
                
                # Update last audio time
                self._last_audio_time = time.time()
                
                # Debug: Save original audio data to file
                if self.debug_save_audio and self.debug_audio_file_original:
                    try:
                        self.debug_audio_file_original.write(audio_data)
                        self.debug_audio_file_original.flush()  # Ensure data is written
                        if self.debug_audio_counter == 0:
                            printLog(f"[Aliyun LiveTranslate Debug] First chunk size: {len(audio_data)} bytes")
                    except Exception as e:
                        printLog(f"[Aliyun LiveTranslate Debug] Error writing original audio: {e}")
                
                # Convert audio format to 16kHz mono PCM16 if needed
                converted_audio = audio_data
                if self.source_sample_rate != AudioFormatConverter.TARGET_SAMPLE_RATE:
                    try:
                        printLog(f"[Aliyun LiveTranslate Debug] Converting audio: {self.source_sample_rate}Hz -> 16000Hz, input size: {len(audio_data)} bytes")
                        converted_audio = AudioFormatConverter.convert_audio_data(
                            audio_data=audio_data,
                            source_sample_rate=self.source_sample_rate,
                            source_channels=1,  # Assume mono from mic
                            source_sample_width=2  # 16-bit PCM
                        )
                        printLog(f"[Aliyun LiveTranslate Debug] Conversion complete: output size: {len(converted_audio)} bytes")
                        if self.debug_audio_counter == 0:
                            printLog(f"[Aliyun LiveTranslate Debug] First chunk: {len(audio_data)} bytes ({self.source_sample_rate}Hz) -> {len(converted_audio)} bytes (16000Hz)")
                    except Exception as e:
                        printLog(f"[Aliyun LiveTranslate] Audio conversion error: {e}")
                        errorLogging()
                        converted_audio = audio_data  # Fallback to original
                        printLog(f"[Aliyun LiveTranslate] Using original audio without conversion")
                else:
                    printLog(f"[Aliyun LiveTranslate Debug] No conversion needed, sample rate already 16000Hz")
                
                # Debug: Save converted audio data to file
                if self.debug_save_audio and self.debug_audio_file:
                    try:
                        self.debug_audio_file.write(converted_audio)
                        self.debug_audio_file.flush()  # Ensure data is written
                        self.debug_audio_counter += 1
                        if self.debug_audio_counter % 10 == 0:
                            printLog(f"[Aliyun LiveTranslate Debug] Processed {self.debug_audio_counter} audio chunks")
                    except Exception as e:
                        printLog(f"[Aliyun LiveTranslate Debug] Error writing converted audio: {e}")
                
                # Create and send audio append event
                event = self._create_audio_append_event(converted_audio)
                await self.ws.send(json.dumps(event))
                
            except Exception as e:
                printLog(f"[Aliyun LiveTranslate] Audio sender error: {e}")
                errorLogging()
                break
    
    async def _heartbeat_sender(self) -> None:
        """Send heartbeat to keep connection alive."""
        while self.running and not self._stop_event.is_set():
            try:
                await asyncio.sleep(self._heartbeat_interval)
                
                # Check if we need to send heartbeat (no audio for a while)
                time_since_last_audio = time.time() - self._last_audio_time
                if time_since_last_audio > self._heartbeat_interval:
                    # Send a ping/pong or empty event to keep connection alive
                    try:
                        await self.ws.ping()
                        printLog("[Aliyun LiveTranslate] Heartbeat sent (ping)")
                    except Exception as e:
                        printLog(f"[Aliyun LiveTranslate] Heartbeat error: {e}")
                        break
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                printLog(f"[Aliyun LiveTranslate] Heartbeat sender error: {e}")
                errorLogging()
                break
    
    async def _message_receiver(self) -> None:
        """Receive messages from WebSocket."""
        while self.running and not self._stop_event.is_set():
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=0.1)
                
                # Parse JSON event
                try:
                    event = json.loads(message)
                    await self._handle_server_event(event)
                except json.JSONDecodeError:
                    printLog(f"[Aliyun LiveTranslate] Invalid JSON received: {message}")
                
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed as e:
                printLog(f"[Aliyun LiveTranslate] Connection closed: {e}")
                break
            except Exception as e:
                printLog(f"[Aliyun LiveTranslate] Message receiver error: {e}")
                errorLogging()
                break
    
    def _run_event_loop(self) -> None:
        """Run asyncio event loop in thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._websocket_handler())
        except Exception:
            errorLogging()
        finally:
            self.loop.close()
            self.loop = None
    
    def start(self) -> None:
        """Start the WebSocket client."""
        if self.running:
            printLog("[Aliyun LiveTranslate] Client already running")
            return
        
        self.running = True
        self._stop_event.clear()
        
        # Start background thread
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        
        printLog("[Aliyun LiveTranslate] Client started")
    
    def stop(self) -> None:
        """Stop the WebSocket client."""
        if not self.running:
            return
        
        printLog("[Aliyun LiveTranslate] Stopping client...")
        self.running = False
        self._stop_event.set()
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        
        # Close debug audio files
        if self.debug_audio_file:
            try:
                self.debug_audio_file.flush()
                self.debug_audio_file.close()
                printLog(f"[Aliyun LiveTranslate Debug] Converted audio file closed, total chunks: {self.debug_audio_counter}")
            except Exception as e:
                printLog(f"[Aliyun LiveTranslate Debug] Error closing converted audio file: {e}")
            finally:
                self.debug_audio_file = None
        if self.debug_audio_file_original:
            try:
                self.debug_audio_file_original.flush()
                self.debug_audio_file_original.close()
                printLog(f"[Aliyun LiveTranslate Debug] Original audio file closed")
            except Exception as e:
                printLog(f"[Aliyun LiveTranslate Debug] Error closing original audio file: {e}")
            finally:
                self.debug_audio_file_original = None
        
        printLog("[Aliyun LiveTranslate] Client stopped")


class AliyunMicTranslateClient(AliyunLiveTranslateClient):
    """Aliyun LiveTranslate client for microphone audio (source -> target)."""
    
    def __init__(self,
                 api_key: str,
                 source_language: str,
                 target_language: str,
                 mic_audio_queue: queue.Queue,
                 result_callback: Callable[[Dict[str, Any]], None],
                 use_international: bool = False,
                 debug_save_audio: bool = False,
                 source_sample_rate: int = 16000):
        """Initialize microphone translation client.
        
        Args:
            api_key: Aliyun DashScope API key
            source_language: Source language code (user's language)
            target_language: Target language code (translation target)
            mic_audio_queue: Microphone audio queue
            result_callback: Callback for translation results
            use_international: Use international endpoint if True
            debug_save_audio: Save audio for debugging
            source_sample_rate: Microphone sample rate
        """
        super().__init__(
            api_key=api_key,
            source_language=source_language,
            target_language=target_language,
            audio_queue=mic_audio_queue,
            result_callback=result_callback,
            use_international=use_international,
            debug_save_audio=debug_save_audio,
            source_sample_rate=source_sample_rate
        )


class AliyunSpeakerTranslateClient(AliyunLiveTranslateClient):
    """Aliyun LiveTranslate client for speaker audio (target -> source, reversed)."""
    
    def __init__(self,
                 api_key: str,
                 source_language: str,
                 target_language: str,
                 speaker_audio_queue: queue.Queue,
                 result_callback: Callable[[Dict[str, Any]], None],
                 use_international: bool = False,
                 debug_save_audio: bool = False,
                 source_sample_rate: int = 16000):
        """Initialize speaker translation client.
        
        Args:
            api_key: Aliyun DashScope API key
            source_language: Target language code (reversed, what others speak)
            target_language: Source language code (reversed, translate to user's language)
            speaker_audio_queue: Speaker audio queue
            result_callback: Callback for translation results
            use_international: Use international endpoint if True
            debug_save_audio: Save audio for debugging
            source_sample_rate: Speaker sample rate
        """
        # Note: For speaker, language direction is reversed
        super().__init__(
            api_key=api_key,
            source_language=source_language,  # Actually target language
            target_language=target_language,  # Actually source language
            audio_queue=speaker_audio_queue,
            result_callback=result_callback,
            use_international=use_international,
            debug_save_audio=debug_save_audio,
            source_sample_rate=source_sample_rate
        )
