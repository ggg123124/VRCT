"""
前端模拟测试客户端
通过 stdin/stdout 与后端通信，测试各个端点。

使用方法:
1. 启动后端: python mainloop.py
2. 在另一个终端运行此脚本: python test_client_zh.py
3. 指定端点和数据执行测试
"""
import os
import subprocess
import json
import base64
import sys
import time
import threading
from typing import Optional, Dict, Any

if os.path.exists("config.json"):
    os.remove("config.json")

class Color:
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class TestClient:
    def __init__(self):
        """启动后端进程并建立 stdin/stdout 通信"""
        print(f"{Color.CYAN}正在启动后端进程...{Color.RESET}")
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
        
        # 等待初始化完成
        print(f"{Color.CYAN}等待后端初始化...{Color.RESET}")
        self._wait_for_initialization()
        print(f"{Color.GREEN}后端启动完成{Color.RESET}\n")
        
        # 初始化完成后启动看门狗
        self._start_watchdog()

    def _wait_for_initialization(self, timeout: Optional[float] = None):
        """等待后端初始化完成 (/run/initialization_complete)。

        旧规范: 60秒后抛出 TimeoutError。
        新规范:
          - timeout 为 None 时无限期等待。
          - 如果设置了 'VRCT_INIT_TIMEOUT' 环境变量，则作为软超时值使用。
          - 软超时到达时不抛出错误，而是显示警告并继续等待。
          - 进度: 每30秒显示一次经过时间和最后接收到的端点。
          - 只有当后端进程终止时才抛出异常。
        """
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
            # 检测进程是否终止
            if self.process.poll() is not None:
                raise RuntimeError("后端进程在初始化期间终止")

            # 软超时警告显示
            if timeout is not None and (time.time() - start_time) > timeout:
                # 只显示一次警告并解除超时（之后继续等待）
                print(f"{Color.YELLOW}[警告]{Color.RESET} 初始化超过 {timeout:.1f} 秒。可能正在下载文件，时间较长。继续等待中。可通过环境变量 VRCT_INIT_TIMEOUT 调整。")
                timeout = None  # 解除

            # 每30秒显示进度日志
            now = time.time()
            if now - last_progress_time_log >= 30:
                elapsed = now - start_time
                ep_info = last_progress_endpoint or "(未接收)"
                print(f"{Color.CYAN}[进度]{Color.RESET} 初始化已耗时 {elapsed:.1f} 秒 / 最后端点: {ep_info}")
                last_progress_time_log = now

            line = self.process.stdout.readline()
            if not line:
                # 没有数据但进程仍在运行 -> 继续
                continue

            stripped = line.strip()
            if not stripped:
                continue

            # 尝试解析 JSON
            try:
                response = json.loads(stripped)
                endpoint = response.get("endpoint", "")
                status = response.get("status", 0)
                last_progress_endpoint = endpoint or last_progress_endpoint
                if status == 348:
                    # 348 视为日志: 展开所有字段
                    print(f"{Color.CYAN}  [初始化日志]{Color.RESET} 状态: {status} 端点:{endpoint or '(无)'}")
                    expanded = json.dumps(response, ensure_ascii=False, indent=2)
                    for line in expanded.split('\n'):
                        print(f"    {line}")
                else:
                    print(f"{Color.CYAN}  [初始化中]{Color.RESET} {endpoint} (状态: {status})")
                if endpoint == "/run/initialization_complete" and status == 200:
                    total_elapsed = time.time() - start_time
                    print(f"{Color.GREEN}  [初始化完成]{Color.RESET} 耗时 {total_elapsed:.1f} 秒")
                    return
            except json.JSONDecodeError:
                # 作为日志行处理
                print(f"{Color.CYAN}  [后端]{Color.RESET} {stripped}")
                continue

    def send_request(self, endpoint: str, data: Optional[Any] = None, timeout: float = 30.0, silent: bool = False) -> Dict[str, Any]:
        """
        向端点发送请求并获取响应
        等待直到收到对应端点的响应
        
        参数:
            endpoint: 测试的端点 (例如: "/get/data/version")
            data: 发送的数据 (None, dict, str, int, float, bool, list等)
            timeout: 超时时间(秒)
        
        返回:
            响应字典 {"status": int, "endpoint": str, "result": Any}
        """
        try:
            # 检查进程是否存活
            if self.process.poll() is not None:
                print(f"{Color.RED}[错误]{Color.RESET} 后端进程已终止")
                return {"status": 500, "endpoint": endpoint, "result": "后端进程未运行"}
            
            # 构建请求
            request = {"endpoint": endpoint}
            
            if data is not None:
                # 将数据转换为 JSON 字符串并进行 Base64 编码
                json_data = json.dumps(data, ensure_ascii=False)
                encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
                request["data"] = encoded_data
            
            # 发送请求
            request_json = json.dumps(request, ensure_ascii=False)
            if not silent:
                print(f"{Color.BLUE}[发送]{Color.RESET} {endpoint}")
                if data is not None:
                    print(f"  数据: {data}")
                print("  等待响应中...", flush=True)
            
            try:
                self.process.stdin.write(request_json + '\n')
                self.process.stdin.flush()
            except (OSError, BrokenPipeError) as e:
                print(f"{Color.RED}[错误]{Color.RESET} 与后端进程通信失败: {e}")
                # 检查 stderr 内容
                stderr_output = self.process.stderr.read()
                if stderr_output:
                    print(f"{Color.RED}[后端错误]{Color.RESET}")
                    print(stderr_output)
                return {"status": 500, "endpoint": endpoint, "result": f"通信错误: {e}"}
            
            # 等待直到收到对应端点的响应
            start_time = time.time()
            while True:
                # 超时检查
                if time.time() - start_time > timeout:
                    print(f"{Color.RED}[超时]{Color.RESET} 响应超时 ({timeout}秒)")
                    return {"status": 504, "endpoint": endpoint, "result": f"超时 {timeout} 秒"}
                
                # 接收响应
                response_line = self.process.stdout.readline()
                
                if not response_line:
                    # 进程可能已终止
                    if self.process.poll() is not None:
                        return {"status": 500, "endpoint": endpoint, "result": "后端进程已终止"}
                    continue
                
                # 解析为 JSON
                try:
                    response = json.loads(response_line.strip())
                except json.JSONDecodeError:
                    # 显示非 JSON 行，如日志输出
                    print(f"{Color.CYAN}[后端输出]{Color.RESET} {response_line.strip()}")
                    continue
                
                # 检查响应的端点是否匹配
                response_endpoint = response.get("endpoint", "")
                if response_endpoint == endpoint:
                    # 收到对应的响应
                    status = response.get("status", 500)
                    result = response.get("result", None)
                    
                    # 根据状态码用不同颜色显示
                    if not silent:
                        if status == 200:
                            print(f"{Color.GREEN}[接收]{Color.RESET} 状态: {status}")
                        elif status == 400:
                            print(f"{Color.YELLOW}[接收]{Color.RESET} 状态: {status}")
                        elif status == 348:
                            # 348 = 日志: 展开内容
                            print(f"{Color.CYAN}[日志]{Color.RESET} 状态: {status} (端点={response_endpoint})")
                        else:
                            print(f"{Color.RED}[接收]{Color.RESET} 状态: {status}")
                    
                    # 格式化显示结果
                    if not silent:
                        # 348 的情况优先显示完整内容作为日志
                        if status == 348:
                            print("  日志条目完整内容:")
                            full_str = json.dumps(response, ensure_ascii=False, indent=2)
                            for line in full_str.split('\n'):
                                print(f"    {line}")
                            print()
                        else:
                            print(f"  端点: {response_endpoint}")
                            print("  结果:")
                            if isinstance(result, (dict, list)):
                                # dict/list 使用缩进显示
                                result_str = json.dumps(result, ensure_ascii=False, indent=2)
                                for line in result_str.split('\n'):
                                    print(f"    {line}")
                            else:
                                print(f"    {result}")
                            
                            # 也显示完整响应
                            print("  完整响应:")
                            response_str = json.dumps(response, ensure_ascii=False, indent=2)
                            for line in response_str.split('\n'):
                                print(f"    {line}")
                            print()
                    
                    return response
                else:
                    # 其他端点的响应或日志消息
                    if not silent:
                        if response_endpoint:
                            print(f"{Color.YELLOW}[其他端点响应]{Color.RESET} {response_endpoint}")
                        else:
                            # 没有 endpoint 键，视为日志消息
                            print(f"{Color.CYAN}[后端日志]{Color.RESET}")
                        print(f"  {json.dumps(response, ensure_ascii=False)}")
                    continue
            
        except json.JSONDecodeError as e:
            print(f"{Color.RED}[错误]{Color.RESET} JSON 解码错误: {e}")
            return {"status": 500, "endpoint": endpoint, "result": f"JSON 解码错误: {e}"}
        except (BrokenPipeError, OSError) as e:
            print(f"{Color.RED}[错误]{Color.RESET} 进程通信错误: {e}")
            # 检查进程状态
            if self.process.poll() is not None:
                print(f"{Color.RED}[错误]{Color.RESET} 后端进程已终止")
                # 显示 stderr 内容
                try:
                    stderr_output = self.process.stderr.read()
                    if stderr_output:
                        print(f"{Color.RED}[后端错误输出]{Color.RESET}")
                        print(stderr_output)
                except Exception:
                    pass
            return {"status": 500, "endpoint": endpoint, "result": f"进程通信错误: {e}"}
        except Exception as e:
            print(f"{Color.RED}[错误]{Color.RESET} 未预期的错误: {e}")
            import traceback
            traceback.print_exc()
            return {"status": 500, "endpoint": endpoint, "result": f"错误: {e}"}

    def _start_watchdog(self):
        """启动看门狗线程 (每30秒发送 /run/feed_watchdog)"""
        def _watchdog_loop():
            print(f"{Color.CYAN}[看门狗]{Color.RESET} 已启动 (30秒间隔)")
            while not self._watchdog_stop_event.is_set():
                if self._watchdog_stop_event.wait(timeout=30):
                    break
                if self.process.poll() is None:
                    try:
                        request = {"endpoint": "/run/feed_watchdog"}
                        request_json = json.dumps(request, ensure_ascii=False)
                        self.process.stdin.write(request_json + '\n')
                        self.process.stdin.flush()
                        # 不接收响应（后台发送）
                    except Exception as e:
                        print(f"{Color.YELLOW}[看门狗]{Color.RESET} 发送错误: {e}")
                        break
            print(f"{Color.CYAN}[看门狗]{Color.RESET} 已终止")
        
        self._watchdog_thread = threading.Thread(target=_watchdog_loop, daemon=True)
        self._watchdog_thread.start()

    def cleanup(self):
        """终止后端进程"""
        print(f"\n{Color.CYAN}正在终止后端进程...{Color.RESET}")
        # 停止看门狗
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            self._watchdog_stop_event.set()
            self._watchdog_thread.join(timeout=2)
        # 终止进程
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
        print(f"{Color.GREEN}终止完成{Color.RESET}")

def run_example_tests(client: TestClient):
    """执行示例测试"""
    print(f"{Color.BOLD}=== 示例测试开始 ==={Color.RESET}\n")
    
    # 1. 获取版本信息
    print(f"{Color.BOLD}测试 1: 获取版本信息{Color.RESET}")
    client.send_request("/get/data/version")
    
    # 2. 设置透明度
    print(f"{Color.BOLD}测试 2: 设置透明度{Color.RESET}")
    client.send_request("/set/data/transparency", 75)
    
    # 3. 设置 UI 语言
    print(f"{Color.BOLD}测试 3: 设置 UI 语言{Color.RESET}")
    client.send_request("/set/data/ui_language", "ja")
    
    # 4. 启用翻译功能
    print(f"{Color.BOLD}测试 4: 启用翻译功能{Color.RESET}")
    client.send_request("/set/enable/translation")
    
    # 5. 禁用翻译功能
    print(f"{Color.BOLD}测试 5: 禁用翻译功能{Color.RESET}")
    client.send_request("/set/disable/translation")
    
    # 6. 无效端点
    print(f"{Color.BOLD}测试 6: 无效端点{Color.RESET}")
    client.send_request("/invalid/endpoint")
    
    print(f"{Color.BOLD}=== 示例测试结束 ==={Color.RESET}\n")

class AutomatedEndpointTester:
    """从 backend_test.py 移植到 stdin/stdout 通信的自动测试类

    参数:
        client: TestClient 实例
        silent: True 时抑制详细日志
        export_path: 将测试结果写入 JSON 的路径 (None 则不写入)
        export_csv: True 时同时写入 CSV
    """
    def __init__(self, client: TestClient, silent: bool = False, export_path: Optional[str] = None, export_csv: bool = False):
        self.client = client
        self.silent = silent
        self.export_path = export_path
        self.export_csv = export_csv
        # 缓存 config 类的值
        self.cache: Dict[str, Any] = {}
        # 端点分类 (暂时硬编码，因为没有动态获取手段)
        self.validity_endpoints = [
            "/set/enable/translation",
            "/set/disable/translation",
            "/set/enable/transcription_send",
            "/set/disable/transcription_send",
            "/set/enable/transcription_receive",
            "/set/disable/transcription_receive",
            "/set/enable/websocket_server",
            "/set/disable/websocket_server",
            "/set/enable/convert_message_to_romaji",
            "/set/disable/convert_message_to_romaji",
            "/set/enable/convert_message_to_hiragana",
            "/set/disable/convert_message_to_hiragana",
        ]
        self.set_data_endpoints = [
            "/set/data/selected_tab_no",
            "/set/data/selected_translation_engines",
            "/set/data/selected_your_languages",
            "/set/data/selected_target_languages",
            "/set/data/selected_transcription_engine",
            "/set/data/transparency",
            "/set/data/ui_scaling",
            "/set/data/textbox_ui_scaling",
            "/set/data/message_box_ratio",
            "/set/data/send_message_button_type",
            "/set/data/font_family",
            "/set/data/ui_language",
            "/set/data/main_window_geometry",
            "/set/data/selected_translation_compute_device",
            "/set/data/selected_transcription_compute_device",
            "/set/data/selected_ctranslate2_weight_type",
            "/set/data/selected_plamo_model",
            "/set/data/plamo_auth_key",
            "/set/data/selected_gemini_model",
            "/set/data/gemini_auth_key",
            "/set/data/selected_openai_model",
            "/set/data/openai_auth_key",
            "/set/data/selected_lmstudio_model",
            "/set/data/lmstudio_url",
            "/set/data/selected_ollama_model",
            "/set/data/deepl_auth_key",
            "/set/data/selected_mic_host",
            "/set/data/selected_mic_device",
            "/set/data/mic_threshold",
            "/set/data/mic_record_timeout",
            "/set/data/mic_phrase_timeout",
            "/set/data/mic_max_phrases",
            "/set/data/hotkeys",
            "/set/data/plugins_status",
            "/set/data/mic_avg_logprob",
            "/set/data/mic_no_speech_prob",
            "/set/data/mic_word_filter",
            "/set/data/selected_speaker_device",
            "/set/data/speaker_threshold",
            "/set/data/speaker_record_timeout",
            "/set/data/speaker_phrase_timeout",
            "/set/data/speaker_max_phrases",
            "/set/data/speaker_avg_logprob",
            "/set/data/speaker_no_speech_prob",
            "/set/data/selected_whisper_weight_type",
            "/set/data/overlay_small_log_settings",
            "/set/data/overlay_large_log_settings",
            "/set/data/send_message_format_parts",
            "/set/data/received_message_format_parts",
            "/set/data/websocket_host",
            "/set/data/websocket_port",
            "/set/data/osc_ip_address",
            "/set/data/osc_port",
            "/set/data/selected_translation_compute_type",
            "/set/data/selected_transcription_compute_type",
        ]
        self.run_endpoints = [
            "/run/send_message_box",
            "/run/typing_message_box",
            "/run/stop_typing_message_box",
            "/run/send_text_overlay",
            "/run/swap_your_language_and_target_language",
            "/run/update_software",
            "/run/update_cuda_software",
            "/run/download_ctranslate2_weight",
            "/run/download_whisper_weight",
            "/run/open_filepath_logs",
            "/run/open_filepath_config_file",
            "/run/feed_watchdog",
            "/run/lmstudio_connection",
            "/run/ollama_connection",
        ]
        self.delete_data_endpoints = [
            "/delete/data/deepl_auth_key",
        ]
        self.results: Dict[str, Dict[str, Any]] = {}

    # ---------------------------------- 工具方法 ----------------------------------
    def _record(self, endpoint: str, status: Optional[int], result: Any, expected_status: list[int]):
        self.results[endpoint] = {
            "status": status,
            "result": result,
            "expected_status": expected_status,
            "success": status in expected_status if status is not None else False
        }

    def _get(self, endpoint: str) -> Any:
        """获取 /get/data/* 的结果并缓存"""
        resp = self.client.send_request(endpoint, silent=self.silent)
        if resp.get("status") == 200:
            self.cache[endpoint.split("/")[-1]] = resp.get("result")
            return resp.get("result")
        return None

    # ---------------------------------- 数据生成器 ----------------------------------
    def _gen_set_data(self, endpoint: str):
        expected = [200]
        data = None
        # 基本沿用 backend_test.py 的逻辑
        if endpoint == "/set/data/selected_tab_no":
            data = sys.modules.get('__random_tab_choices', None) or None  # 未来动态扩展的占位符
            data = data or "1"
        elif endpoint == "/set/data/selected_translation_engines":
            engines = self._get("/get/data/selectable_translation_engines") or []
            data = {i: (engines and (engines[0] if len(engines) else None)) for i in ["1","2","3"]}
        elif endpoint == "/set/data/selected_your_languages":
            lang_list = self._get("/get/data/selectable_language_list") or []
            if lang_list:
                choice = lang_list[0]
                data = {i: {"1": {**choice, "enable": True}} for i in ["1","2","3"]}
        elif endpoint == "/set/data/selected_target_languages":
            lang_list = self._get("/get/data/selectable_language_list") or []
            if lang_list:
                base = lang_list[0]
                data = {i: {j: {**base, "enable": (j=="1")} for j in ["1","2","3"]} for i in ["1","2","3"]}
        elif endpoint == "/set/data/selected_transcription_engine":
            engines = self._get("/get/data/selectable_transcription_engines") or []
            data = engines[0] if engines else None
        elif endpoint == "/set/data/transparency":
            import random
            data = random.randint(0,100)
        elif endpoint == "/set/data/ui_scaling" or endpoint == "/set/data/textbox_ui_scaling":
            import random
            data = random.randint(50,200)
        elif endpoint == "/set/data/message_box_ratio":
            import random
            data = round(random.uniform(0.1,0.9),2)
        elif endpoint == "/set/data/send_message_button_type":
            import random
            data = random.choice(["show","hide","show_and_disable_enter_key"])
        elif endpoint == "/set/data/font_family":
            import random
            data = random.choice(["Arial","Verdana","Times New Roman"]) 
        elif endpoint == "/set/data/ui_language":
            import random
            data = random.choice(["en","ja","ko","zh-Hant","zh-Hans"]) 
        elif endpoint == "/set/data/main_window_geometry":
            import random
            data = {
                "x_pos": random.randint(0,1920),
                "y_pos": random.randint(0,1080),
                "width": random.randint(800,1920),
                "height": random.randint(600,1080)
            }
        elif endpoint == "/set/data/selected_translation_compute_device":
            lst = self._get("/get/data/selectable_translation_compute_device_list") or []
            import random
            data = random.choice(lst) if lst else None
        elif endpoint == "/set/data/selected_transcription_compute_device":
            lst = self._get("/get/data/selectable_transcription_compute_device_list") or []
            import random
            data = random.choice(lst) if lst else None
        elif endpoint == "/set/data/selected_ctranslate2_weight_type":
            dct = self._get("/get/data/selectable_ctranslate2_weight_type_dict") or {}
            keys = list(dct.keys())
            import random
            data = random.choice(keys) if keys else None
        elif endpoint == "/set/data/selected_plamo_model":
            lst = self._get("/get/data/selectable_plamo_model_list") or []
            import random
            data = random.choice(lst) if lst else None
            expected = [200,400]
        elif endpoint == "/set/data/plamo_auth_key":
            data = "PLAMO_DUMMY_KEY"
            expected = [200,400]
        elif endpoint == "/set/data/selected_gemini_model":
            lst = self._get("/get/data/selectable_gemini_model_list") or []
            import random
            data = random.choice(lst) if lst else None
            expected = [200,400]
        elif endpoint == "/set/data/gemini_auth_key":
            data = "GEMINI_DUMMY_KEY"
            expected = [200,400]
        elif endpoint == "/set/data/selected_openai_model":
            lst = self._get("/get/data/selectable_openai_model_list") or []
            import random
            data = random.choice(lst) if lst else None
            expected = [200,400]
        elif endpoint == "/set/data/openai_auth_key":
            data = "OPENAI_DUMMY_KEY"
            expected = [200,400]
        elif endpoint == "/set/data/selected_lmstudio_model":
            lst = self._get("/get/data/selectable_lmstudio_model_list") or []
            import random
            data = random.choice(lst) if lst else None
            expected = [200,400]
        elif endpoint == "/set/data/lmstudio_url":
            import random
            data = random.choice(["http://localhost:1234/v1","http://127.0.0.1:1234/v1","http://invalid_host:9999/v1"])
            expected=[200,400]
        elif endpoint == "/set/data/selected_ollama_model":
            lst = self._get("/get/data/selectable_ollama_model_list") or []
            import random
            data = random.choice(lst) if lst else None
            expected = [200,400]
        elif endpoint == "/set/data/deepl_auth_key":
            data = "DEEPL_DUMMY_KEY"
            expected=[200,400]
        elif endpoint == "/set/data/selected_mic_host":
            lst = self._get("/get/data/selectable_mic_host_list") or []
            import random
            data = random.choice(lst) if lst else None
        elif endpoint == "/set/data/selected_mic_device":
            lst = self._get("/get/data/selectable_mic_device_list") or []
            import random
            data = random.choice(lst) if lst else None
        elif endpoint == "/set/data/mic_threshold":
            import random
            val = random.randint(-1000,3000)
            data = val
            expected=[200] if 0 <= val <= 2000 else [400]
        elif endpoint == "/set/data/mic_record_timeout":
            import random
            val = random.randint(-1,10)
            phrase = self._get("/get/data/mic_phrase_timeout")
            data = val
            expected=[200] if (phrase is not None and 0 <= val <= phrase) else [400]
        elif endpoint == "/set/data/mic_phrase_timeout":
            import random
            val = random.randint(-1,10)
            record = self._get("/get/data/mic_record_timeout")
            data = val
            expected=[200] if (record is not None and record <= val) else [400]
        elif endpoint == "/set/data/mic_max_phrases":
            import random
            val = random.randint(-1,10)
            data = val
            expected=[200] if val >= 0 else [400]
        elif endpoint == "/set/data/hotkeys":
            data = {'toggle_vrct_visibility': None,'toggle_translation': None,'toggle_transcription_send': None,'toggle_transcription_receive': None}
        elif endpoint == "/set/data/plugins_status":
            plugins = self._get("/get/data/plugins") or []
            import random
            data = {p: random.choice([True,False]) for p in plugins}
        elif endpoint == "/set/data/mic_avg_logprob":
            import random
            data = random.uniform(-5,0)
        elif endpoint == "/set/data/mic_no_speech_prob":
            import random
            data = random.uniform(0,1)
        elif endpoint == "/set/data/mic_word_filter":
            import random
            data = random.choice([["test_0_0","test_0_1","test_0_2",None],["test_1_0","test_1_1",None],["test_2_0",None],[None]])
        elif endpoint == "/set/data/selected_speaker_device":
            lst = self._get("/get/data/selectable_speaker_device_list") or []
            import random
            data = random.choice(lst) if lst else None
        elif endpoint == "/set/data/speaker_threshold":
            import random
            val = random.randint(-1000,5000)
            data = val
            expected=[200] if 0 <= val <= 4000 else [400]
        elif endpoint == "/set/data/speaker_record_timeout":
            import random
            val = random.randint(-1,10)
            phrase = self._get("/get/data/speaker_phrase_timeout")
            data = val
            expected=[200] if (phrase is not None and 0 <= val <= phrase) else [400]
        elif endpoint == "/set/data/speaker_phrase_timeout":
            import random
            val = random.randint(-1,10)
            record = self._get("/get/data/speaker_record_timeout")
            data = val
            expected=[200] if (record is not None and record <= val) else [400]
        elif endpoint == "/set/data/speaker_max_phrases":
            import random
            val = random.randint(-1,10)
            data = val
            expected=[200] if val >= 0 else [400]
        elif endpoint == "/set/data/speaker_avg_logprob":
            import random
            data = random.uniform(-5,0)
        elif endpoint == "/set/data/speaker_no_speech_prob":
            import random
            data = random.uniform(0,1)
        elif endpoint == "/set/data/selected_whisper_weight_type":
            dct = self._get("/get/data/selectable_whisper_weight_type_dict") or {}
            import random
            keys=[k for k,v in dct.items() if v]
            data = random.choice(keys) if keys else None
        elif endpoint == "/set/data/overlay_small_log_settings" or endpoint == "/set/data/overlay_large_log_settings":
            import random
            data = {
                "x_pos": random.random(),
                "y_pos": random.random(),
                "z_pos": random.random(),
                "x_rotation": random.random(),
                "y_rotation": random.random(),
                "z_rotation": random.random(),
                "display_duration": random.randint(0,100),
                "fadeout_duration": random.randint(0,100),
                "opacity": random.random(),
                "ui_scaling": random.random(),
                "tracker": random.choice(["HMD","LeftHand","RightHand"])
            }
        elif endpoint == "/set/data/send_message_format_parts":
            fmt = self._get("/get/data/send_message_format_parts")
            data = fmt
        elif endpoint == "/set/data/received_message_format_parts":
            fmt = self._get("/get/data/received_message_format_parts")
            data = fmt
        elif endpoint == "/set/data/websocket_host":
            import random
            val = random.choice(["127.0.0.1","aaaaadwafasdsd","0210.1564.845.0"])
            data = val
            expected = [200,400] if val=="127.0.0.1" else [400]
        elif endpoint == "/set/data/websocket_port":
            import random
            data = random.randint(1024,65535)
            expected=[200,400]
        elif endpoint == "/set/data/osc_ip_address":
            import random
            val = random.choice(["127.0.0.1","aaaaadwafasdsd","0210.1564.845.0"])
            data = val
            expected = [200] if val=="127.0.0.1" else [400]
        elif endpoint == "/set/data/osc_port":
            import random
            data = random.randint(1024,65535)
        elif endpoint == "/set/data/selected_translation_compute_type":
            device = self.cache.get("selected_translation_compute_device") or self._get("/get/data/selected_translation_compute_device")
            if device and isinstance(device, dict):
                import random
                data = random.choice(device.get("compute_types", [])) if device.get("compute_types") else None
        elif endpoint == "/set/data/selected_transcription_compute_type":
            device = self.cache.get("selected_transcription_compute_device") or self._get("/get/data/selected_transcription_compute_device")
            if device and isinstance(device, dict):
                import random
                data = random.choice(device.get("compute_types", [])) if device.get("compute_types") else None
        return data, expected

    def _gen_run_data(self, endpoint: str):
        expected = [200]
        data = None
        import random
        if endpoint == "/run/send_message_box":
            choices=[{"data":{"id":"000001","message":"测试"},"status":[200]},
                     {"data":{"id":"000002","message":"Hello World!"},"status":[200]},
                     {"data":{"id":"000003","message":"你好，世界！"},"status":[200]},
                     {"data":{"id":"000004","message":"안녕하세요 세계!"},"status":[200]},
                     {"data":{"id":"000005","message":"こんにちは 世界！"},"status":[200]}]
            choice = random.choice(choices)
            data = choice["data"]
            expected = choice["status"]
        elif endpoint in ["/run/typing_message_box","/run/stop_typing_message_box","/run/send_text_overlay","/run/swap_your_language_and_target_language"]:
            data = "测试覆盖层" if endpoint == "/run/send_text_overlay" else None
        elif endpoint in ["/run/update_software","/run/update_cuda_software","/run/download_ctranslate2_weight","/run/download_whisper_weight","/run/open_filepath_logs","/run/open_filepath_config_file","/run/feed_watchdog"]:
            expected=[401]
        elif endpoint in ["/run/lmstudio_connection","/run/ollama_connection"]:
            expected=[200,400]
        return data, expected

    # ---------------------------------- 测试 ----------------------------------
    def test_validity_single(self, endpoint: str):
        expected=[200]
        if endpoint == "/set/enable/websocket_server":
            expected=[200,400]
        resp = self.client.send_request(endpoint)
        status = resp.get("status")
        result = resp.get("result")
        self._record(endpoint, status, result, expected)
        ok = status in expected
        tag = f"{Color.GREEN}通过{Color.RESET}" if ok else f"{Color.RED}失败{Color.RESET}"
        print(f"[有效性测试] {endpoint} -> {tag} ({status})")
        return ok

    def test_set_data_single(self, endpoint: str):
        data, expected = self._gen_set_data(endpoint)
        if expected == [404]:
            self._record(endpoint, None, None, expected)
            print(f"[数据设置] {endpoint} -> {Color.RED}未知{Color.RESET}")
            return False
        # data 为 None 但 expected 包含 400 时也发送测试
        if data is None and 400 not in expected:
            self._record(endpoint, None, None, expected)
            print(f"[数据设置] {endpoint} -> {Color.YELLOW}跳过(无数据){Color.RESET}")
            return True
        resp = self.client.send_request(endpoint, data, silent=self.silent)
        status = resp.get("status")
        result = resp.get("result")
        self._record(endpoint, status, result, expected)
        ok = status in expected
        tag = f"{Color.GREEN}通过{Color.RESET}" if ok else f"{Color.RED}失败{Color.RESET}"
        print(f"[数据设置] {endpoint} -> {tag} ({status}) 数据={data}")
        return ok

    def test_run_single(self, endpoint: str):
        data, expected = self._gen_run_data(endpoint)
        if expected == [401]:
            self._record(endpoint, None, None, expected)
            print(f"[执行] {endpoint} -> {Color.YELLOW}跳过(401){Color.RESET}")
            return True
        resp = self.client.send_request(endpoint, data, silent=self.silent)
        status = resp.get("status")
        result = resp.get("result")
        self._record(endpoint, status, result, expected)
        ok = status in expected
        tag = f"{Color.GREEN}通过{Color.RESET}" if ok else f"{Color.RED}失败{Color.RESET}"
        print(f"[执行] {endpoint} -> {tag} ({status})")
        return ok

    def test_delete_single(self, endpoint: str):
        expected=[200]
        resp = self.client.send_request(endpoint, silent=self.silent)
        status = resp.get("status")
        result = resp.get("result")
        self._record(endpoint, status, result, expected)
        ok = status in expected
        tag = f"{Color.GREEN}通过{Color.RESET}" if ok else f"{Color.RED}失败{Color.RESET}"
        print(f"[删除] {endpoint} -> {tag} ({status})")
        return ok

    def run_all(self):
        print(f"{Color.BOLD}=== 启用/禁用端点测试 ==={Color.RESET}")
        for ep in self.validity_endpoints:
            self.test_validity_single(ep)
        print(f"{Color.BOLD}=== 数据设置端点测试 ==={Color.RESET}")
        for ep in self.set_data_endpoints:
            self.test_set_data_single(ep)
        print(f"{Color.BOLD}=== 执行端点测试 ==={Color.RESET}")
        for ep in self.run_endpoints:
            self.test_run_single(ep)
        print(f"{Color.BOLD}=== 删除端点测试 ==={Color.RESET}")
        for ep in self.delete_data_endpoints:
            self.test_delete_single(ep)

    def run_random(self, iterations: int = 500):
        import random
        print(f"{Color.BOLD}=== 随机访问测试(迭代={iterations}) ==={Color.RESET}")
        groups = ["validity","set","run","delete"]
        for i in range(iterations):
            g = random.choice(groups)
            if g == "validity":
                ep = random.choice(self.validity_endpoints)
                self.test_validity_single(ep)
            elif g == "set":
                ep = random.choice(self.set_data_endpoints)
                self.test_set_data_single(ep)
            elif g == "run":
                ep = random.choice(self.run_endpoints)
                self.test_run_single(ep)
            else:
                ep = random.choice(self.delete_data_endpoints)
                self.test_delete_single(ep)
        # 最后关闭所有 disable 系
        for ep in self.validity_endpoints:
            if ep.startswith("/set/disable/"):
                self.client.send_request(ep, silent=True)

    def run_specific_random(self, iterations: int = 200):
        import random
        print(f"{Color.BOLD}=== 特定(osc/websocket)随机测试(迭代={iterations}) ==={Color.RESET}")
        set_specific = ["/set/data/osc_ip_address","/set/data/osc_port","/set/data/websocket_host","/set/data/websocket_port"]
        for i in range(iterations):
            ep = random.choice(set_specific)
            self.test_set_data_single(ep)

    def summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r["success"])
        skipped = sum(1 for r in self.results.values() if r["expected_status"] == [401])
        failed = total - passed - skipped
        print(f"\n{Color.BOLD}==== 测试总结 ==== {Color.RESET}")
        print(f"总数: {total} / 成功: {passed} / 失败: {failed} / 跳过(401): {skipped}")
        if failed:
            print(f"{Color.RED}失败详情:{Color.RESET}")
            for ep, r in self.results.items():
                if not r["success"] and r["expected_status"] != [401]:
                    print(f"- {ep} 状态={r['status']} 预期={r['expected_status']} 结果={r['result']}")
        print(f"{Color.BOLD}======================={Color.RESET}\n")
        # 按交互选项导出
        if self.export_path:
            try:
                self.export_results(self.export_path)
                print(f"{Color.GREEN}[导出]{Color.RESET} 已写入 JSON: {self.export_path}")
                if self.export_csv:
                    csv_path = self._derive_csv_path(self.export_path)
                    self.export_results_csv(csv_path)
                    print(f"{Color.GREEN}[导出]{Color.RESET} 已写入 CSV: {csv_path}")
            except Exception as e:
                print(f"{Color.RED}[导出错误]{Color.RESET} {e}")

    def _derive_csv_path(self, json_path: str) -> str:
        base, ext = os.path.splitext(json_path)
        return base + '.csv'

    def export_results(self, filename: str):
        """将结果写入 JSON 文件"""
        payload = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total": len(self.results),
            "results": self.results,
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def export_results_csv(self, filename: str):
        """将结果写入 CSV (简易)"""
        import csv
        with open(filename, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["端点", "状态", "预期", "成功"])
            for ep, r in self.results.items():
                w.writerow([ep, r.get("status"), ",".join(map(str, r.get("expected_status", []))), r.get("success")])

def run_interactive_mode(client: TestClient):
    """对话模式执行测试"""
    print(f"{Color.BOLD}=== 对话模式 ==={Color.RESET}")
    print("指定端点和数据来执行测试。")
    print("输入 'quit' 或 'exit' 退出。\n")
    
    while True:
        try:
            # 输入端点
            endpoint = input(f"{Color.CYAN}输入端点 (例如: /get/data/version): {Color.RESET}").strip()
            
            if endpoint.lower() in ['quit', 'exit', 'q']:
                break
            
            if not endpoint:
                print(f"{Color.YELLOW}请输入端点{Color.RESET}\n")
                continue
            
            # 输入数据
            data_input = input(f"{Color.CYAN}输入数据 (JSON格式, 无则按回车): {Color.RESET}").strip()
            
            data = None
            if data_input:
                try:
                    data = json.loads(data_input)
                except json.JSONDecodeError:
                    print(f"{Color.YELLOW}无法解析为 JSON。将作为字符串发送{Color.RESET}")
                    data = data_input
            
            # 发送请求
            client.send_request(endpoint, data)
            
        except KeyboardInterrupt:
            print(f"\n{Color.YELLOW}已中断{Color.RESET}")
            break
        except Exception as e:
            print(f"{Color.RED}错误: {e}{Color.RESET}\n")

def main():
    """主程序"""
    print(f"{Color.BOLD}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}  VRCT 后端测试客户端{Color.RESET}")
    print(f"{Color.BOLD}{'='*60}{Color.RESET}\n")
    
    client = None
    try:
        # 初始化测试客户端
        client = TestClient()
        
        # 选择模式
        print("请选择模式:")
        print("1. 运行示例测试")
        print("2. 对话模式")
        print("3. 自动测试(全部)")
        print("4. 随机访问测试")
        print("5. 特定(osc/websocket)随机测试")
        mode = input(f"{Color.CYAN}选择 (1-5): {Color.RESET}").strip()

        # 附加选项
        silent_choice = input(f"{Color.CYAN}抑制详细日志? (y/N): {Color.RESET}").strip().lower()
        silent = silent_choice == 'y'
        export_choice = input(f"{Color.CYAN}导出结果为 JSON? (y/N): {Color.RESET}").strip().lower()
        export_path = None
        export_csv = False
        if export_choice == 'y':
            default_name = f"test_results_{int(time.time())}.json"
            path_in = input(f"{Color.CYAN}输出文件名[{default_name}]: {Color.RESET}").strip()
            export_path = path_in or default_name
            csv_choice = input(f"{Color.CYAN}同时导出 CSV? (y/N): {Color.RESET}").strip().lower()
            export_csv = csv_choice == 'y'
        
        print()
        
        if mode == "1":
            run_example_tests(client)
        elif mode == "2":
            run_interactive_mode(client)
        elif mode == "3":
            tester = AutomatedEndpointTester(client, silent=silent, export_path=export_path, export_csv=export_csv)
            tester.run_all()
            tester.summary()
        elif mode == "4":
            tester = AutomatedEndpointTester(client, silent=silent, export_path=export_path, export_csv=export_csv)
            tester.run_random()
            tester.summary()
        elif mode == "5":
            tester = AutomatedEndpointTester(client, silent=silent, export_path=export_path, export_csv=export_csv)
            tester.run_specific_random()
            tester.summary()
        else:
            print(f"{Color.YELLOW}无效的选择。启动对话模式。{Color.RESET}\n")
            run_interactive_mode(client)
        
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}用户中断{Color.RESET}")
    except Exception as e:
        print(f"{Color.RED}发生错误: {e}{Color.RESET}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            client.cleanup()

if __name__ == "__main__":
    main()
