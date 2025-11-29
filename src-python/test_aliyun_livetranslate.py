"""Aliyun Qwen3 LiveTranslate Flash Test Client
Test Aliyun LiveTranslate translation via stdin/stdout communication with backend.
Based on test_client.py structure.

Usage:
1. Ensure Aliyun API key is configured
2. Run: python test_aliyun_livetranslate.py
3. Select test mode from prompts
"""
import os
import subprocess
import json
import base64
import sys
import time
import threading
from typing import Optional, Dict, Any

# Use default API key directly
print("="*60)
print("  VRCT Aliyun LiveTranslate Test Client")
print("="*60)
print()
api_key = "sk-946b7996fce440e7a9c56ef5a8faed19"
print(f"Using API key: {api_key}")
print()

class Color:
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class TestClient:
    def __init__(self, aliyun_api_key: str):
        """Start backend process and establish stdin/stdout communication"""
        print(f"{Color.CYAN}Starting backend process...{Color.RESET}")
        self.process = subprocess.Popen(
            [sys.executable, 'mainloop.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd='.'
        )
        self._watchdog_stop_event = threading.Event()
        self._watchdog_thread: Optional[threading.Thread] = None
        
        # Wait for initialization
        print(f"{Color.CYAN}Waiting for backend initialization...{Color.RESET}")
        self._wait_for_initialization()
        print(f"{Color.GREEN}Backend started successfully{Color.RESET}\n")
        
        # Configure API key
        print(f"{Color.CYAN}Configuring Aliyun API key...{Color.RESET}")
        self._configure_api_key(aliyun_api_key)
        
        # Start watchdog
        self._start_watchdog()

    def _wait_for_initialization(self, timeout: Optional[float] = None):
        """Wait for backend initialization complete (/run/initialization_complete)"""
        import os
        env_timeout = os.getenv("VRCT_INIT_TIMEOUT")
        if timeout is None:
            try:
                timeout = float(env_timeout) if env_timeout else None
            except ValueError:
                timeout = None

        start_time = time.time()
        last_progress_endpoint = None
        last_progress_time_log = 0.0

        while True:
            # Check if process terminated
            if self.process.poll() is not None:
                # Print stderr output for debugging
                stderr_output = self.process.stderr.read()
                if stderr_output:
                    print(f"{Color.RED}[Backend Error Output]{Color.RESET}")
                    print(stderr_output)
                raise RuntimeError("Backend process terminated during initialization")

            # soft timeout warning
            if timeout is not None and (time.time() - start_time) > timeout:
                print(f"{Color.YELLOW}[WARN]{Color.RESET} Initialization exceeded {timeout:.1f} seconds. Download may take longer time, continue waiting...")
                timeout = None

            # Progress log every 30 seconds
            now = time.time()
            if now - last_progress_time_log >= 30:
                elapsed = now - start_time
                ep_info = last_progress_endpoint or "(no response)"
                print(f"{Color.CYAN}[Progress]{Color.RESET} Initialization time: {elapsed:.1f}s / Last endpoint: {ep_info}")
                last_progress_time_log = now

            line = self.process.stdout.readline()
            if not line:
                continue

            stripped = line.strip()
            if not stripped:
                continue

            # Try parse JSON
            try:
                response = json.loads(stripped)
                endpoint = response.get("endpoint", "")
                status = response.get("status", 0)
                last_progress_endpoint = endpoint or last_progress_endpoint
                if status == 348:
                    print(f"{Color.CYAN}  [Init Log]{Color.RESET} Status: {status} endpoint:{endpoint or '(none)'}")
                else:
                    print(f"{Color.CYAN}  [Initializing]{Color.RESET} {endpoint} (Status: {status})")
                if endpoint == "/run/initialization_complete" and status == 200:
                    total_elapsed = time.time() - start_time
                    print(f"{Color.GREEN}  [Init Complete]{Color.RESET} Time: {total_elapsed:.1f}s")
                    return
            except json.JSONDecodeError:
                print(f"{Color.CYAN}  [Backend]{Color.RESET} {stripped}")
                continue

    def _configure_api_key(self, api_key: str):
        """Configure Aliyun API key via endpoint"""
        try:
            resp = self.send_request("/set/data/aliyun_auth_key", api_key, timeout=10.0, silent=True)
            if resp.get("status") == 200:
                print(f"{Color.GREEN}API key configured successfully{Color.RESET}\n")
            else:
                print(f"{Color.YELLOW}API key configuration returned status: {resp.get('status')}{Color.RESET}")
                print(f"Result: {resp.get('result')}\n")
        except Exception as e:
            print(f"{Color.RED}Failed to configure API key: {e}{Color.RESET}\n")

    def send_request(self, endpoint: str, data: Optional[Any] = None, timeout: float = 30.0, silent: bool = False) -> Dict[str, Any]:
        """Send request to endpoint and receive response"""
        try:
            if self.process.poll() is not None:
                print(f"{Color.RED}[ERROR]{Color.RESET} Backend process terminated")
                return {"status": 500, "endpoint": endpoint, "result": "Backend process is not running"}
            
            # Build request
            request = {"endpoint": endpoint}
            
            if data is not None:
                json_data = json.dumps(data, ensure_ascii=False)
                encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
                request["data"] = encoded_data
            
            # Send request
            request_json = json.dumps(request, ensure_ascii=False)
            if not silent:
                print(f"{Color.BLUE}[Send]{Color.RESET} {endpoint}")
                if data is not None:
                    print(f"  Data: {data}")
                print("  Waiting for response...", flush=True)
            
            try:
                self.process.stdin.write(request_json + '\n')
                self.process.stdin.flush()
            except (OSError, BrokenPipeError) as e:
                print(f"{Color.RED}[ERROR]{Color.RESET} Communication failed with backend: {e}")
                # Print stderr output for debugging
                stderr_output = self.process.stderr.read()
                if stderr_output:
                    print(f"{Color.RED}[Backend Error Output]{Color.RESET}")
                    print(stderr_output)
                return {"status": 500, "endpoint": endpoint, "result": f"Communication error: {e}"}
            
            # Wait for response from corresponding endpoint
            start_time = time.time()
            while True:
                if time.time() - start_time > timeout:
                    print(f"{Color.RED}[TIMEOUT]{Color.RESET} Response timeout ({timeout}s)")
                    return {"status": 504, "endpoint": endpoint, "result": f"Timeout after {timeout} seconds"}
                
                response_line = self.process.stdout.readline()
                
                if not response_line:
                    if self.process.poll() is not None:
                        return {"status": 500, "endpoint": endpoint, "result": "Backend process terminated"}
                    continue
                
                try:
                    response = json.loads(response_line.strip())
                except json.JSONDecodeError:
                    print(f"{Color.CYAN}[Backend Output]{Color.RESET} {response_line.strip()}")
                    continue
                
                response_endpoint = response.get("endpoint", "")
                if response_endpoint == endpoint:
                    status = response.get("status", 500)
                    result = response.get("result", None)
                    
                    if not silent:
                        if status == 200:
                            print(f"{Color.GREEN}[Receive]{Color.RESET} Status: {status}")
                        elif status == 400:
                            print(f"{Color.YELLOW}[Receive]{Color.RESET} Status: {status}")
                        elif status == 348:
                            print(f"{Color.CYAN}[LOG]{Color.RESET} Status: {status} (endpoint={response_endpoint})")
                        else:
                            print(f"{Color.RED}[Receive]{Color.RESET} Status: {status}")
                    
                    if not silent:
                        if status == 348:
                            print("  Log content:")
                            full_str = json.dumps(response, ensure_ascii=False, indent=2)
                            for line in full_str.split('\n'):
                                print(f"    {line}")
                            print()
                        else:
                            print(f"  Endpoint: {response_endpoint}")
                            print("  Result:")
                            if isinstance(result, (dict, list)):
                                result_str = json.dumps(result, ensure_ascii=False, indent=2)
                                for line in result_str.split('\n'):
                                    print(f"    {line}")
                            else:
                                print(f"    {result}")
                            print()
                    
                    return response
                else:
                    if not silent and response_endpoint:
                        print(f"{Color.YELLOW}[Other Endpoint Response]{Color.RESET} {response_endpoint}")
                    continue
            
        except Exception as e:
            print(f"{Color.RED}[ERROR]{Color.RESET} Error occurred: {e}")
            import traceback
            traceback.print_exc()
            return {"status": 500, "endpoint": endpoint, "result": f"Error: {e}"}

    def _start_watchdog(self):
        """Start watchdog thread (send /run/feed_watchdog every 30 seconds)"""
        def _watchdog_loop():
            print(f"{Color.CYAN}[Watchdog]{Color.RESET} Started (30s interval)")
            while not self._watchdog_stop_event.is_set():
                if self._watchdog_stop_event.wait(timeout=30):
                    break
                if self.process.poll() is None:
                    try:
                        request = {"endpoint": "/run/feed_watchdog"}
                        request_json = json.dumps(request, ensure_ascii=False)
                        self.process.stdin.write(request_json + '\n')
                        self.process.stdin.flush()
                    except Exception as e:
                        print(f"{Color.YELLOW}[Watchdog]{Color.RESET} Send error: {e}")
                        break
            print(f"{Color.CYAN}[Watchdog]{Color.RESET} Stopped")
        
        self._watchdog_thread = threading.Thread(target=_watchdog_loop, daemon=True)
        self._watchdog_thread.start()

    def cleanup(self):
        """Terminate backend process"""
        print(f"\n{Color.CYAN}Terminating backend process...{Color.RESET}")
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            self._watchdog_stop_event.set()
            self._watchdog_thread.join(timeout=2)
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
        print(f"{Color.GREEN}Terminated{Color.RESET}")

def run_aliyun_tests(client: TestClient):
    """Execute Aliyun translation related tests"""
    print(f"{Color.BOLD}=== Aliyun LiveTranslate Translation Test ==={Color.RESET}\n")
    
    # Test 1: Set API key first (required for engine to appear in available list)
    print(f"{Color.BOLD}Test 1: Set Aliyun API key{Color.RESET}")
    # Note: Using test API key here, replace with valid key for actual use
    test_api_key = "sk-946b7996fce440e7a9c56ef5a8faed19"
    resp = client.send_request("/set/data/aliyun_auth_key", test_api_key)
    if resp.get("status") == 200:
        print(f"{Color.GREEN}✓ API key set successfully{Color.RESET}\n")
    else:
        print(f"{Color.YELLOW}! API key set status: {resp.get('status')}{Color.RESET}")
        print(f"{Color.YELLOW}! Response: {resp}{Color.RESET}\n")
    
    # Test 2: Get available languages first
    print(f"{Color.BOLD}Test 2: Get available languages{Color.RESET}")
    resp = client.send_request("/get/data/selectable_language_list")
    languages = resp.get("result", [])
    print(f"Available languages: {len(languages)}")
    if languages:
        # Print first few languages to see the format
        print(f"First 3 languages: {json.dumps(languages[:3], ensure_ascii=False, indent=2)}")
    print(f"{Color.GREEN}✓ Language list retrieved{Color.RESET}\n")
    
    # Test 3: Set source and target languages to supported pair (Japanese -> English)
    print(f"{Color.BOLD}Test 3: Set source and target languages (Japanese -> English){Color.RESET}")
    # Find Japanese and English in language list
    japanese_lang = None
    english_lang = None
    for lang in languages:
        if lang.get('language') == 'Japanese':
            japanese_lang = lang
        elif lang.get('language') == 'English':
            english_lang = lang
    
    if japanese_lang and english_lang:
        # Set source language (Japanese)
        your_languages_config = {
            "1": {"1": {**japanese_lang, "enable": True}},
            "2": {"1": {**japanese_lang, "enable": True}},
            "3": {"1": {**japanese_lang, "enable": True}}
        }
        resp = client.send_request("/set/data/selected_your_languages", your_languages_config)
        print(f"Source language (Japanese) set: {resp.get('status')}")
        
        # Set target language (English)
        target_languages_config = {
            "1": {"1": {**english_lang, "enable": True}},
            "2": {"1": {**english_lang, "enable": True}},
            "3": {"1": {**english_lang, "enable": True}}
        }
        resp = client.send_request("/set/data/selected_target_languages", target_languages_config)
        print(f"Target language (English) set: {resp.get('status')}")
        print(f"{Color.GREEN}✓ Language configuration complete{Color.RESET}\n")
    else:
        print(f"{Color.YELLOW}! Could not find Japanese or English in language list{Color.RESET}\n")
    
    # Test 4: Get available translation engines (should now include Aliyun after language setup)
    print(f"{Color.BOLD}Test 4: Get available translation engines{Color.RESET}")
    resp = client.send_request("/get/data/selectable_translation_engines")
    engines = resp.get("result", [])
    print(f"Available engines: {engines}")
    
    if "Aliyun_LiveTranslate" not in engines:
        print(f"{Color.RED}Error: Aliyun translation engine not in list{Color.RESET}")
        print(f"{Color.YELLOW}Hint: Make sure API key was set correctly and languages are supported{Color.RESET}")
        return False
    print(f"{Color.GREEN}✓ Aliyun translation engine registered{Color.RESET}\n")
    
    # Test 5: Set translation engine to Aliyun
    print(f"{Color.BOLD}Test 5: Set translation engine to Aliyun LiveTranslate{Color.RESET}")
    translation_engines_config = {
        "1": "Aliyun_LiveTranslate",
        "2": "Aliyun_LiveTranslate",
        "3": "Aliyun_LiveTranslate"
    }
    resp = client.send_request("/set/data/selected_translation_engines", translation_engines_config)
    if resp.get("status") == 200:
        print(f"{Color.GREEN}✓ Translation engine set{Color.RESET}\n")
    else:
        print(f"{Color.YELLOW}! Translation engine set status: {resp.get('status')}{Color.RESET}\n")
    
    # Test 6: Enable translation
    print(f"{Color.BOLD}Test 6: Enable translation{Color.RESET}")
    resp = client.send_request("/set/enable/translation")
    if resp.get("status") == 200:
        print(f"{Color.GREEN}✓ Translation enabled{Color.RESET}\n")
    else:
        print(f"{Color.YELLOW}! Translation enable status: {resp.get('status')}{Color.RESET}\n")
    
    # Test 7: Wait for translation results
    print(f"{Color.BOLD}Test 7: Running test{Color.RESET}")
    print(f"{Color.CYAN}Translation enabled, please speak into microphone or play audio...{Color.RESET}")
    print(f"{Color.CYAN}Test will run for 30 seconds, observe console output for translation results...{Color.RESET}")
    
    # Monitor for 30 seconds to check for translation results
    for i in range(30):
        time.sleep(1)
        if i % 5 == 0:
            print(f"{Color.CYAN}[{i}/30s]{Color.RESET} Running...")
    
    # Test 8: Disable translation
    print(f"\n{Color.BOLD}Test 8: Disable translation{Color.RESET}")
    resp = client.send_request("/set/disable/translation")
    if resp.get("status") == 200:
        print(f"{Color.GREEN}✓ Translation disabled{Color.RESET}\n")
    else:
        print(f"{Color.YELLOW}! Translation disable status: {resp.get('status')}{Color.RESET}\n")
    
    print(f"{Color.BOLD}=== Aliyun translation test complete ==={Color.RESET}\n")
    print(f"{Color.GREEN}Hint: If you see translation results during test, integration succeeded!{Color.RESET}")
    print(f"{Color.YELLOW}Note: Ensure valid API key and network connection{Color.RESET}")
    return True

def run_interactive_mode(client: TestClient):
    """Interactive mode test"""
    print(f"{Color.BOLD}=== Interactive Mode ==={Color.RESET}")
    print("Enter endpoint and data to test")
    print("Enter 'quit' or 'exit' to quit\n")
    
    while True:
        try:
            endpoint = input(f"{Color.CYAN}Enter endpoint (e.g. /get/data/version): {Color.RESET}").strip()
            
            if endpoint.lower() in ['quit', 'exit', 'q']:
                break
            
            if not endpoint:
                print(f"{Color.YELLOW}Please enter endpoint{Color.RESET}\n")
                continue
            
            data_input = input(f"{Color.CYAN}Enter data (JSON format, press Enter if none): {Color.RESET}").strip()
            
            data = None
            if data_input:
                try:
                    data = json.loads(data_input)
                except json.JSONDecodeError:
                    print(f"{Color.YELLOW}JSON parse failed, sending as string{Color.RESET}")
                    data = data_input
            
            client.send_request(endpoint, data)
            
        except KeyboardInterrupt:
            print(f"\n{Color.YELLOW}Interrupted{Color.RESET}")
            break
        except Exception as e:
            print(f"{Color.RED}Error: {e}{Color.RESET}\n")

def main():
    """Main function"""
    client = None
    try:
        # Initialize test client
        client = TestClient(api_key)
        
        # Select test mode
        print("Select test mode:")
        print("1. Run Aliyun translation automated test")
        print("2. Interactive mode (manual endpoint test)")
        try:
            mode = input(f"{Color.CYAN}Select (1-2): {Color.RESET}").strip()
        except EOFError:
            mode = "1"
            print("1 (auto-selected)")
        
        print()
        
        if mode == "1":
            run_aliyun_tests(client)
        elif mode == "2":
            run_interactive_mode(client)
        else:
            print(f"{Color.YELLOW}Invalid selection, starting interactive mode{Color.RESET}\n")
            run_interactive_mode(client)
        
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}Test interrupted by user{Color.RESET}")
    except Exception as e:
        print(f"{Color.RED}Error occurred: {e}{Color.RESET}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            client.cleanup()

if __name__ == "__main__":
    main()