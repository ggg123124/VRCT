# model.py 设计文档

## 概述

`model.py` 作为 VRCT 应用程序的业务逻辑外观(Facade)，为语音识别、翻译、覆盖层显示、OSC 通信、WebSocket 通信等所有子系统提供统一的接口。采用单例模式实现，通过延迟执行繁重的初始化处理来缩短应用程序的启动时间。

## 架构定位

```
┌─────────────┐
│controller.py│ (Business Logic Control Layer)
└──────┬──────┘
       │ Facade Pattern
┌──────▼──────┐
│  model.py   │ ◄── 此文件
└──────┬──────┘
       │ Aggregation & Delegation
┌──────▼────────────────────────────┐
│ Subsystems                            │
│ - Translator                          │
│ - AudioTranscriber                    │
│ - Overlay / OverlayImage             │
│ - OSCHandler                          │
│ - WebSocketServer                     │
│ - Transliterator                      │
│ - Watchdog                            │
│ - DeviceManager (via device_manager)  │
└───────────────────────────────────────┘
```

## 主要组件

### 1. threadFnc 类

**职责:** 重复执行函数的线程包装器

**特点:**
- 作为守护线程运行
- 提供循环控制（停止、暂停、恢复）功能
- 支持终止时的清理函数

**方法:**

#### `__init__(fnc, end_fnc=None, daemon=True, *args, **kwargs)`

**参数:**
- `fnc`: 重复执行的函数
- `end_fnc`: 线程结束时执行的函数（可选）
- `daemon`: 守护进程标志（默认: True）
- `*args, **kwargs`: 传递给 `fnc` 的参数

#### `stop() -> None`
停止循环并结束线程。

#### `pause() -> None`
暂停循环（停止函数执行）。

#### `resume() -> None`
恢复暂停的循环。

#### `run() -> None`
线程的主循环。在 `self.loop` 为 True 期间，重复调用 `self.fnc()`。

**使用示例:**
```python
def print_message():
    print("Hello")
    sleep(1)

def cleanup():
    print("Thread ended")

th = threadFnc(print_message, end_fnc=cleanup)
th.start()
# ... 运行一段时间 ...
th.stop()
th.join()
```

---

### 2. Model 类

**职责:** 应用程序所有子系统的外观接口

**模式:** 单例模式（通过 `__new__` 控制）

**初始化策略:** 延迟初始化（Lazy Initialization）
- `__new__`: 仅生成实例（轻量级）
- `init()`: 繁重的初始化处理（需要显式调用）
- `ensure_initialized()`: 在需要初始化的方法中自动调用

---

### 3. 初始化方法

#### `__new__(cls) -> Model`

**职责:** 生成单例实例

**处理:**
1. 仅在 `cls._instance` 为 None 时生成新实例
2. 将 `_inited` 标志设置为 False（实际初始化尚未执行）
3. 如果存在现有实例则返回该实例

**重要:** 此方法不执行繁重的初始化（提高 import 时的性能）

#### `init() -> None`

**职责:** 初始化所有子系统

**处理:**
1. **已初始化检查:** 如果 `_inited` 标志为 True 则不执行任何操作
2. **属性初始化:**
   ```python
   self.logger = None
   self.mic_audio_queue = None
   self.mic_mute_status = None
   self.previous_send_message = ""
   self.previous_receive_message = ""
   ```
3. **子系统初始化:**
   - `Translator()`: 翻译引擎
   - `KeywordProcessor()`: 禁用词过滤器
   - `Overlay()`: 覆盖层系统
   - `OverlayImage()`: 覆盖层图像生成
   - `Transliterator()`: 音译（平假名、罗马字转换）
   - `Watchdog()`: 进程监控
   - `OSCHandler()`: OSC 通信
   - `WebSocketServer()`: WebSocket 通信
4. **回调函数初始化:**
   ```python
   self.check_mic_energy_fnc: Callable[[float], None] = lambda v: None
   self.check_speaker_energy_fnc: Callable[[float], None] = lambda v: None
   ```
5. **初始化完成标志:** `_inited = True`

#### `ensure_initialized() -> None`

**职责:** 在未初始化的情况下调用 `init()`

**使用位置:** 所有需要初始化的 public 方法

**错误处理:**
```python
try:
    self.init()
except Exception:
    errorLogging()
```

---

### 4. 翻译功能

#### 模型权重管理

##### `checkTranslatorCTranslate2ModelWeight(weight_type: str) -> bool`
检查指定的模型权重是否存在。

**参数:**
- `weight_type`: "tiny", "small", "medium", "large" 等

**返回值:** 模型存在时返回 True

##### `downloadCTranslate2ModelWeight(weight_type, callback=None, end_callback=None) -> bool`

**职责:** 下载 CTranslate2 模型权重

**参数:**
- `weight_type`: 模型类型
- `callback`: 进度通知回调（接收 `progress: float`）
- `end_callback`: 完成时的回调

**实现:** 委托给 `downloadCTranslate2Weight()` 工具函数

##### `downloadCTranslate2ModelTokenizer(weight_type) -> bool`
下载分词器文件。

#### 翻译模型控制

##### `changeTranslatorCTranslate2Model() -> None`

**职责:** 更改/重新加载翻译模型

**处理:**
```python
self.translator.changeCTranslate2Model(
    path=config.PATH_LOCAL,
    model_type=config.CTRANSLATE2_WEIGHT_TYPE,
    device=config.SELECTED_TRANSLATION_COMPUTE_DEVICE["device"],
    device_index=config.SELECTED_TRANSLATION_COMPUTE_DEVICE["device_index"],
    compute_type=config.SELECTED_TRANSLATION_COMPUTE_TYPE
)
```

**VRAM错误:** 可能抛出 `ValueError("VRAM_OUT_OF_MEMORY")`

##### `isLoadedCTranslate2Model() -> bool`
检查 CTranslate2 模型是否已加载。

##### `isChangedTranslatorParameters() -> bool`
检查翻译参数是否已更改。

##### `setChangedTranslatorParameters(is_changed: bool) -> None`
设置翻译参数更改标志。

#### DeepL 认证

##### `authenticationTranslatorDeepLAuthKey(auth_key: str) -> bool`

**职责:** 验证 DeepL API 密钥

**处理:** 委托给 `translator.authenticationDeepLAuthKey()`

**返回值:** 认证成功时返回 True

#### 翻译执行

##### `getTranslate(translator_name, source_language, target_language, target_country, message) -> Tuple[str, bool]`

**职责:** 翻译消息

**参数:**
- `translator_name`: "CTranslate2", "DeepL", "DeepL_API" 等
- `source_language`: 源语言（"ja", "en" 等）
- `target_language`: 目标语言
- `target_country`: 目标国家（用于方言支持）
- `message`: 要翻译的文本

**返回值:**
- `translation`: 翻译结果（字符串）
- `success_flag`: 成功时返回 True

**错误处理:**
```python
translation = self.translator.translate(...)
if isinstance(translation, str):
    success_flag = True
else:
    # 翻译失败时的重试逻辑
    while True:
        # 故障安全处理
```

##### `getInputTranslate(message, source_language=None) -> Tuple[list, list]`

**职责:** 翻译发送消息（支持多语言）

**处理:**
1. 通过 `config.SELECTED_TRANSLATION_ENGINES[config.SELECTED_TAB_NO]` 获取翻译引擎
2. 通过 `config.SELECTED_TARGET_LANGUAGES` 获取目标语言列表
3. 为每个有效语言调用 `getTranslate()`

**返回值:**
- `translations`: 翻译结果列表
- `success_flags`: 各翻译的成功标志列表

##### `getOutputTranslate(message, source_language=None) -> Tuple[list, list]`

**职责:** 翻译接收消息（单一语言）

**处理:** 与 `getInputTranslate()` 类似，但翻译目标仅为自己的语言（1个）

---

### 5. 语音识别功能

#### Whisper 模型管理

##### `checkTranscriptionWhisperModelWeight(weight_type: str) -> bool`
确认 Whisper 模型权重是否存在。

##### `downloadWhisperModelWeight(weight_type, callback=None, end_callback=None) -> bool`
下载 Whisper 模型权重。

#### 麦克风语音识别

##### `startMicTranscript(fnc: Callable[[dict], None]) -> None`

**职责:** 开始麦克风语音识别

**参数:**
- `fnc`: 接收识别结果的回调函数

**处理流程:**
1. **获取设备:**
   ```python
   mic_host_name = config.SELECTED_MIC_HOST
   mic_device_name = config.SELECTED_MIC_DEVICE
   mic_device_list = device_manager.getMicDevices().get(mic_host_name, [...])
   selected_mic_device = [device for device in mic_device_list if device["name"] == mic_device_name]
   ```
2. **设备验证:**
   - 如果没有设备，调用 `fnc({"text": False, "language": None})` 并结束
3. **创建音频队列:**
   ```python
   self.mic_audio_queue = Queue()
   ```
4. **初始化录音器:**
   ```python
   self.mic_audio_recorder = SelectedMicEnergyAndAudioRecorder(
       device=mic_device,
       energy_threshold=config.MIC_THRESHOLD,
       dynamic_energy_threshold=config.MIC_AUTOMATIC_THRESHOLD,
       phrase_time_limit=config.MIC_RECORD_TIMEOUT,
   )
   self.mic_audio_recorder.recordIntoQueue(self.mic_audio_queue, None)
   ```
5. **初始化转录器:**
   ```python
   self.mic_transcriber = AudioTranscriber(
       speaker=False,
       source=self.mic_audio_recorder.source,
       phrase_timeout=config.MIC_PHRASE_TIMEOUT,
       max_phrases=config.MIC_MAX_PHRASES,
       transcription_engine=config.SELECTED_TRANSCRIPTION_ENGINE,
       root=config.PATH_LOCAL,
       whisper_weight_type=config.WHISPER_WEIGHT_TYPE,
       device=config.SELECTED_TRANSCRIPTION_COMPUTE_DEVICE["device"],
       device_index=config.SELECTED_TRANSCRIPTION_COMPUTE_DEVICE["device_index"],
       compute_type=config.SELECTED_TRANSCRIPTION_COMPUTE_TYPE,
   )
   ```
6. **启动转录线程:**
   ```python
   def sendMicTranscript():
       # 从队列获取音频数据
       # 使用 AudioTranscriber 进行转录
       # 通过 fnc() 发送结果
   
   def endMicTranscript():
       # 清理处理
   
   self.mic_print_transcript = threadFnc(sendMicTranscript, end_fnc=endMicTranscript)
   self.mic_print_transcript.start()
   ```
7. **同步静音状态:**
   ```python
   self.changeMicTranscriptStatus()
   ```

##### `resumeMicTranscript() -> None`

**职责:** 恢复暂停的麦克风语音识别

**处理:**
1. 清空音频队列
2. 恢复录音器: `self.mic_audio_recorder.resume()`

##### `pauseMicTranscript() -> None`

**职责:** 暂停麦克风语音识别

**处理:** `self.mic_audio_recorder.pause()`

##### `changeMicTranscriptStatus() -> None`

**职责:** 根据 VRChat 的麦克风静音状态控制语音识别

**处理:**
```python
if config.VRC_MIC_MUTE_SYNC is True:
    match self.mic_mute_status:
        case True:
            self.pauseMicTranscript()
        case False:
            self.resumeMicTranscript()
        case None:
            self.resumeMicTranscript()  # 状态未知时不暂停
else:
    self.resumeMicTranscript()
```

##### `stopMicTranscript() -> None`

**职责:** 停止麦克风语音识别并释放资源

**处理:**
1. 停止转录线程
2. 恢复录音器（如果暂停中）并停止
3. 销毁实例

**VRAM错误检测:**

##### `detectVRAMError(error: Exception) -> Tuple[bool, Optional[str]]`

**职责:** 检测 VRAM 不足错误

**处理:**
```python
error_str = str(error)
if isinstance(error, ValueError) and len(error.args) > 0 and error.args[0] == "VRAM_OUT_OF_MEMORY":
    return True, error_str
if "CUDA out of memory" in error_str or "CUBLAS_STATUS_ALLOC_FAILED" in error_str:
    return True, error_str
return False, None
```

**使用位置:**
- 执行翻译时
- 开始语音识别时

#### 扬声器语音识别

以下方法与麦克风语音识别具有类似结构:
- `startSpeakerTranscript(fnc)`
- `stopSpeakerTranscript()`

**差异:**
- 使用 `speaker=True` 初始化 AudioTranscriber
- 使用 `SelectedSpeakerEnergyAndAudioRecorder`

#### 能量级别监控

##### `startCheckMicEnergy(fnc: Optional[Callable[[float], None]] = None) -> None`

**职责:** 开始监控麦克风音量级别

**处理:**
1. 设置回调函数: `self.check_mic_energy_fnc = fnc`
2. 获取麦克风设备
3. 初始化能量录音器:
   ```python
   mic_energy_queue = Queue()
   self.mic_energy_recorder = SelectedMicEnergyRecorder(mic_device)
   self.mic_energy_recorder.recordIntoQueue(mic_energy_queue)
   ```
4. 启动能量发送线程:
   ```python
   def sendMicEnergy():
       if not mic_energy_queue.empty():
           energy = mic_energy_queue.get()
           self.check_mic_energy_fnc(energy)
       sleep(0.01)
   
   self.mic_energy_plot_progressbar = threadFnc(sendMicEnergy)
   self.mic_energy_plot_progressbar.start()
   ```

##### `stopCheckMicEnergy() -> None`
停止能量监控并释放资源。

**对应的扬声器方法:**
- `startCheckSpeakerEnergy(fnc)`
- `stopCheckSpeakerEnergy()`

---

### 6. 覆盖层功能

#### 图像生成

##### `createOverlayImageSmallLog(message, your_language, translation, target_language) -> object`

**职责:** 生成小日志窗口的图像

**参数:**
- `message`: 原始消息（可选）
- `your_language`: 源语言（可选）
- `translation`: 翻译结果列表
- `target_language`: 目标语言字典（可选）

**处理:**
```python
target_language_list = []
if isinstance(target_language, dict):
    target_language_list = list(target_language.values())
return self.overlay_image.createOverlayImageSmallLog(
    message, your_language, translation, target_language_list
)
```

##### `createOverlayImageSmallMessage(message: str) -> object`

**职责:** 生成小消息窗口的图像（单一语言）

**处理:**
```python
ui_language = config.UI_LANGUAGE
convert_languages = {
    "en": "Default",
    "jp": "Japanese",
    "ko": "Korean",
    "zh-Hans": "Chinese Simplified",
    "zh-Hant": "Chinese Traditional",
}
language = convert_languages.get(ui_language, "Default")
return self.overlay_image.createOverlayImageSmallLog(message, language)
```

##### `createOverlayImageLargeLog(message_type, message, your_language, translation, target_language=None) -> object`

**职责:** 生成大日志窗口的图像

**参数:**
- `message_type`: "send" 或 "received"

**处理:** 与 `createOverlayImageSmallLog()` 类似

##### `createOverlayImageLargeMessage(message: str) -> object`

**职责:** 生成大消息窗口的图像

**特殊处理:**
```python
overlay_image = OverlayImage(config.PATH_LOCAL)
for _ in range(2):
    # 重复生成2次图像（原因不明，可能是为了修复 bug？）
    overlay_image.createOverlayImageLargeLog("send", message, language)
return overlay_image.createOverlayImageLargeLog("send", message, language)
```

#### 显示控制

##### `clearOverlayImageSmallLog() -> None`
清除小日志窗口。

##### `updateOverlaySmallLog(img: object) -> None`
更新小日志窗口的图像。

##### `updateOverlaySmallLogSettings() -> None`

**职责:** 更新小日志窗口的设置

**处理:** 检测设置更改并反映到覆盖层:
```python
size = "small"
if (self.overlay.settings[size]["x_pos"] != config.OVERLAY_SMALL_LOG_SETTINGS["x_pos"] or
    # ... 其他设置项 ...):
    self.overlay.updateSettings(config.OVERLAY_SMALL_LOG_SETTINGS, size)
```

**设置项:**
- 位置（x_pos, y_pos, z_pos）
- 旋转（x_rotation, y_rotation, z_rotation）
- 追踪器（tracker）
- 显示时长（display_duration）
- 淡出时长（fadeout_duration）
- 不透明度（opacity）
- UI 缩放（ui_scaling）

##### `clearOverlayImageLargeLog() -> None`
清除大日志窗口。

##### `updateOverlayLargeLog(img: object) -> None`
更新大日志窗口的图像。

##### `updateOverlayLargeLogSettings() -> None`
更新大日志窗口的设置（与 `updateOverlaySmallLogSettings()` 类似）。

#### 覆盖层系统控制

##### `startOverlay() -> None`
启动覆盖层系统（初始化 OpenVR）。

##### `shutdownOverlay() -> None`
关闭覆盖层系统（释放资源）。

---

### 7. OSC 通信功能

#### 设置

##### `setOscIpAddress(ip_address: str) -> None`
设置发送到 VRChat 的目标 IP 地址。

##### `setOscPort(port: int) -> None`
设置 OSC 端口号。

#### 消息发送

##### `oscStartSendTyping() -> None`
发送正在输入的通知（VRChat 的聊天框会显示指示器）。

##### `oscStopSendTyping() -> None`
发送输入结束的通知。

##### `oscSendMessage(message: str) -> None`

**职责:** 向 VRChat 发送消息

**参数:**
- `message`: 要发送的文本

**处理:**
```python
self.osc_handler.sendMessage(
    message=message,
    notification=config.NOTIFICATION_VRC_SFX
)
```

#### OSC 接收

##### `setMuteSelfStatus() -> None`
获取 VRChat 当前的麦克风静音状态。

##### `startReceiveOSC() -> None`

**职责:** 开始接收 OSC 参数

**处理:**
```python
def changeHandlerMute(address, osc_arguments):
    if config.ENABLE_TRANSCRIPTION_SEND is True:
        self.mic_mute_status = osc_arguments[0]
        self.changeMicTranscriptStatus()

dict_filter_and_target = {
    self.osc_handler.osc_parameter_muteself: changeHandlerMute,
}
self.osc_handler.setDictFilterAndTarget(dict_filter_and_target)
self.osc_handler.receiveOscParameters()
```

**监控参数:**
- `/avatar/parameters/MuteSelf`: 麦克风静音状态

##### `stopReceiveOSC() -> None`
停止 OSC 接收。

##### `getIsOscQueryEnabled() -> bool`
检查 OSC Query 功能是否启用。

---

### 8. 音译功能

#### 音译系统控制

##### `startTransliteration() -> None`
启动音译系统（生成 `Transliterator` 实例）。

##### `stopTransliteration() -> None`
停止音译系统（销毁实例）。

#### 音译执行

##### `convertMessageToTransliteration(message, hiragana=True, romaji=True) -> list`

**职责:** 将消息转换为平假名和罗马字

**参数:**
- `message`: 要转换的文本
- `hiragana`: 包含平假名
- `romaji`: 包含罗马字

**处理:**
```python
if hiragana is False and romaji is False:
    return []

keys_to_keep = {"orig"}
if hiragana:
    keys_to_keep.add("hira")
if romaji:
    keys_to_keep.add("hepburn")

if self.transliterator is None:
    self.startTransliteration()

data_list = self.transliterator.analyze(message, use_macron=False)
filtered_list = [
    {key: value for key, value in item.items() if key in keys_to_keep}
    for item in data_list
]
return filtered_list
```

**返回值示例:**
```python
[
    {"orig": "こんにちは", "hira": "こんにちは", "hepburn": "konnichiwa"},
    {"orig": "世界", "hira": "せかい", "hepburn": "sekai"}
]
```

---

### 9. 关键词过滤器

#### 过滤器管理

##### `resetKeywordProcessor() -> None`
重置关键词处理器（删除所有关键词）。

##### `addKeywords() -> None`
将禁用词添加到关键词处理器。

**处理:**
```python
for f in config.MIC_WORD_FILTER:
    self.keyword_processor.add_keyword(f)
```

#### 过滤

##### `checkKeywords(message: str) -> bool`
检查消息中是否包含禁用词。

**返回值:** 如果包含禁用词则返回 True

**实现:**
```python
return len(self.keyword_processor.extract_keywords(message)) != 0
```

---

### 10. 重复检测

##### `detectRepeatSendMessage(message: str) -> bool`

**职责:** 检测发送消息的重复

**处理:**
```python
repeat_flag = False
if self.previous_send_message == message:
    repeat_flag = True
self.previous_send_message = message
return repeat_flag
```

##### `detectRepeatReceiveMessage(message: str) -> bool`
检测接收消息的重复（与 `detectRepeatSendMessage()` 类似）。

---

### 11. 设备管理

#### 麦克风设备

##### `getListMicHost() -> list`

**职责:** 获取麦克风主机列表

**返回值:** ["MME", "WASAPI", ...] 等

**处理:**
```python
try:
    dm = device_manager.getMicDevices()
    result = [host for host in dm.keys()]
except Exception:
    errorLogging()
    result = []
return result
```

##### `getMicDefaultDevice() -> str`
获取所选主机的默认麦克风设备名称。

##### `getListMicDevice() -> list`
获取所选主机的麦克风设备列表。

#### 扬声器设备

##### `getListSpeakerDevice() -> list`
获取扬声器设备列表。

**处理:**
```python
try:
    sd = device_manager.getSpeakerDevices()
    result = [device["name"] for device in sd]
except Exception:
    errorLogging()
    result = ["NoDevice"]
return result
```

---

### 12. 语言管理

##### `getListLanguageAndCountry() -> list`

**职责:** 获取同时支持语音识别和翻译的语言/国家列表

**处理:**
1. 从 `transcription_lang` 获取语音识别支持的语言
2. 从 `translation_lang` 获取翻译支持的语言
3. 提取两者都支持的语言
4. 枚举每种语言的国家变体

**返回值示例:**
```python
[
    {"language": "en", "country": "US"},
    {"language": "en", "country": "UK"},
    {"language": "ja", "country": "JP"},
    # ...
]
```

##### `findTranslationEngines(source_lang, target_lang, engines_status) -> list`

**职责:** 搜索支持指定语言对的翻译引擎

**参数:**
- `source_lang`: 源语言字典（可能启用了多种语言）
- `target_lang`: 目标语言字典
- `engines_status`: 各引擎的启用/禁用状态

**处理:**
```python
selectable_engines = [key for key, value in engines_status.items() if value is True]
compatible_engines = []
for engine in list(translation_lang.keys()):
    languages = translation_lang.get(engine, {}).get("source", {})
    source_langs = [e["language"] for e in list(source_lang.values()) if e["enable"] is True]
    target_langs = [e["language"] for e in list(target_lang.values()) if e["enable"] is True]
    language_list = list(languages.keys())

    if all(e in language_list for e in source_langs) and all(e in language_list for e in target_langs):
        if engine in selectable_engines:
            compatible_engines.append(engine)

return compatible_engines
```

---

### 13. 日志记录

##### `startLogger() -> None`

**职责:** 开始文件日志记录

**处理:**
```python
os_makedirs(config.PATH_LOGS, exist_ok=True)
file_name = os_path.join(config.PATH_LOGS, f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
self.logger = setupLogger("log", file_name)
self.logger.disabled = False
```

**日志文件名示例:** `2023-10-13_15-30-45.log`

##### `stopLogger() -> None`
停止文件日志记录。

---

### 14. 软件更新

##### `checkSoftwareUpdated() -> dict`

**职责:** 检查最新版本

**处理:**
```python
update_flag = False
version = ""
try:
    # 从 GitHub API 等获取最新版本信息
    # 使用 packaging.version.parse 进行版本比较
except Exception:
    errorLogging()
return {
    "is_update_available": update_flag,
    "new_version": version,
}
```

##### `updateSoftware() -> None`

**职责:** 执行常规版本更新

**处理:**
1. 下载更新程序（最多重试 5 次）
2. 使用 `Popen()` 启动更新程序
3. 结束当前进程

##### `updateCudaSoftware() -> None`
执行 CUDA 版本更新（使用 `--cuda` 选项启动更新程序）。

---

### 15. Watchdog 功能

##### `startWatchdog() -> None`

**职责:** 启动 Watchdog 监控线程

**处理:**
```python
self.th_watchdog = threadFnc(self.watchdog.start)
self.th_watchdog.daemon = True
self.th_watchdog.start()
```

##### `feedWatchdog() -> None`
向 Watchdog 发送心跳信号（重置超时）。

##### `setWatchdogCallback(callback: Callable) -> None`
设置 Watchdog 超时时的回调函数。

##### `stopWatchdog() -> None`
停止 Watchdog 并等待线程结束。

---

### 16. WebSocket 服务器

#### 服务器控制

##### `startWebSocketServer(host: str, port: int) -> None`

**职责:** 启动 WebSocket 服务器

**处理:**
1. 如果已启动则不执行任何操作
2. 设置 `websocket_server_loop = True`
3. 在单独的线程中运行 asyncio 事件循环:
   ```python
   async def WebSocketServerMain():
       self.websocket_server = WebSocketServer(host, port)
       self.websocket_server_alive = True
       await self.websocket_server.start()
       # 等待循环结束
       self.websocket_server_alive = False
   
   self.th_websocket_server = Thread(target=lambda: asyncio.run(WebSocketServerMain()))
   self.th_websocket_server.daemon = True
   self.th_websocket_server.start()
   ```

##### `stopWebSocketServer() -> None`

**职责:** 停止 WebSocket 服务器

**处理:**
1. 设置 `websocket_server_loop = False`
2. 请求停止服务器
3. 等待线程结束（带超时）

**错误处理:**
```python
try:
    # 服务器停止处理
except Exception:
    errorLogging()
finally:
    self.th_websocket_server = None
    self.websocket_server = None
    self.websocket_server_alive = False
```

##### `checkWebSocketServerAlive() -> bool`
确认 WebSocket 服务器的运行状态。

#### 消息发送

##### `websocketSendMessage(message_dict: dict) -> bool`

**职责:** 向所有连接的客户端广播消息

**参数:**
- `message_dict`: 要发送的字典（将序列化为 JSON）

**处理:**
```python
if not self.websocket_server_alive or not self.websocket_server:
    return False
try:
    self.websocket_server.broadcast(message_dict)
    return True
except Exception:
    errorLogging()
    return False
```

---

## 依赖关系

### 外部库

```python
from subprocess import Popen
from os import makedirs as os_makedirs
from os import path as os_path
from datetime import datetime
from time import sleep
from queue import Queue
from threading import Thread
from requests import get as requests_get
from typing import Callable, Optional, cast
from packaging.version import parse
from flashtext import KeywordProcessor
```

### 内部模块

```python
from device_manager import device_manager
from config import config
from models.translation.translation_translator import Translator
from models.osc.osc import OSCHandler
from models.transcription.transcription_recorder import SelectedMicEnergyAndAudioRecorder, SelectedSpeakerEnergyAndAudioRecorder
from models.transcription.transcription_recorder import SelectedMicEnergyRecorder, SelectedSpeakerEnergyRecorder
from models.transcription.transcription_transcriber import AudioTranscriber
from models.translation.translation_languages import translation_lang
from models.transcription.transcription_languages import transcription_lang
from models.translation.translation_utils import checkCTranslate2Weight, downloadCTranslate2Weight, downloadCTranslate2Tokenizer
from models.transcription.transcription_whisper import checkWhisperWeight, downloadWhisperWeight
from models.transliteration.transliteration_transliterator import Transliterator
from models.overlay.overlay import Overlay
from models.overlay.overlay_image import OverlayImage
from models.watchdog.watchdog import Watchdog
from models.websocket.websocket_server import WebSocketServer
from utils import errorLogging, setupLogger
```

---

## 线程结构

### 主线程
- 应用程序的主循环（由 `mainloop.py` 管理）

### Model 管理的线程

#### 语音识别线程
- `mic_print_transcript`: 麦克风语音识别结果处理
- `speaker_print_transcript`: 扬声器语音识别结果处理

#### 能量监控线程
- `mic_energy_plot_progressbar`: 麦克风音量级别监控
- `speaker_energy_plot_progressbar`: 扬声器音量级别监控

#### 其他线程
- `th_watchdog`: Watchdog 监控
- `th_websocket_server`: WebSocket 服务器（asyncio 事件循环）

### 子系统管理的线程
- `device_manager.th_monitoring`: 设备变更监控
- `mic_audio_recorder.th_record`: 麦克风音频录制
- `speaker_audio_recorder.th_record`: 扬声器音频录制
- `osc_handler.th_receive`: OSC 参数接收

---

## 错误处理

### VRAM不足错误

**检测:**
```python
is_vram_error, error_message = self.detectVRAMError(e)
```

**对应:**
1. 以 `ValueError("VRAM_OUT_OF_MEMORY")` 形式抛出错误
2. 在 Controller 端捕获并禁用功能
3. 通知用户

### 设备访问错误

**检测:**
- 找不到设备: `NoDevice`
- 访问失败时: 向回调传递 `False`

**对应:**
1. 将错误记录到日志
2. 通知 Controller
3. 继续处理（不影响其他功能）

### 网络错误

**检测:**
- 翻译 API 调用失败
- 模型权重下载失败

**对应:**
1. 重试逻辑（翻译情况下）
2. 退回方案（切换到 CTranslate2）
3. 错误通知

---

## 性能优化

### 1. 延迟初始化

将繁重的初始化处理分离到 `init()` 中，直到需要时才执行。

**优点:**
- 缩短应用程序启动时间
- 不消耗未使用功能的资源

### 2. 单例模式

Model 类在整个应用程序中只存在一个实例。

**优点:**
- 减少内存使用
- 状态一致性

### 3. 通过线程进行并行处理

在单独的线程中执行语音识别、能量监控、WebSocket 服务器等阻塞处理。

**优点:**
- 提高 UI 响应性
- 同时执行多个功能

---

## 测试场景

### 1. 初始化测试

**案例:**
- 首次初始化
- 已初始化的情况
- 初始化失败时

**检查项:**
- `_inited` 标志是否正确设置
- 所有子系统是否已初始化
- 错误是否已正确记录

### 2. 语音识别测试

**案例:**
- 没有设备的情况
- 语音识别启动、停止、暂停、恢复
- VRAM错误发生

**检查项:**
- 回调是否正确调用
- 线程是否适当管理
- 错误是否被检测到

### 3. 翻译测试

**案例:**
- 单一语言翻译
- 多语言翻译
- 翻译引擎切换
- API 错误

**检查项:**
- 翻译结果是否正确
- 错误时的退回机制是否工作

### 4. 覆盖层测试

**案例:**
- 图像生成
- 设置更新
- 覆盖层启动、停止

**检查项:**
- 图像是否正确生成
- 设置更改是否反映

---

## 限制

### 1. 单例模式的约束

**问题:** 测试和多实例困难

**影响:**
- 单元测试中难以进行 mock
- 无法支持多个 VRChat 实例

### 2. 全局状态依赖

**问题:** 对 `config` 模块的强依赖

**影响:**
- 降低可测试性
- 配置更改难以追踪

### 3. 错误处理不完整

**问题:** 部分错误被忽略

**影响:**
- 难以调试
- 缺少向用户提供适当的错误通知

### 4. 线程管理复杂性

**问题:** 大量线程及其状态管理

**影响:**
- 死锁风险
- 资源泄漏的可能性

---

## 未来改进建议

### 1. 引入依赖注入（DI）

```python
class Model:
    def __init__(self, config, device_manager, translator, ...):
        self.config = config
        self.device_manager = device_manager
        self.translator = translator
        # ...
```

**优点:**
- 提高可测试性
- 模块间松耦合

### 2. 异步化（asyncio）

```python
async def startMicTranscript(self, callback):
    async for result in self.mic_transcriber.transcribe():
        await callback(result)
```

**优点:**
- 简化线程管理
- 提高性能

### 3. 事件驱动架构

```python
class Model:
    def __init__(self):
        self.event_bus = EventBus()
    
    def on_transcription_result(self, result):
        self.event_bus.emit("transcription_result", result)
```

**优点:**
- 模块间松耦合
- 提高可扩展性

### 4. 统一错误处理

```python
class ModelError(Exception):
    pass

class VRAMError(ModelError):
    pass

class DeviceError(ModelError):
    pass
```

**优点:**
- 错误分类和处理的统一
- 错误信息的追踪

---

## 相关文件

- **controller.py** - 业务逻辑控制层
- **config.py** - 配置管理
- **device_manager.py** - 设备监控、自动选择
- **mainloop.py** - 通信层
- **utils.py** - 日志和工具函数
- **models/** - 子系统实现

---

## 总结

`model.py` 为 VRCT 的所有子系统提供了统一的外观接口，通过简洁的 API 封装了语音识别、翻译、覆盖层、OSC 通信、WebSocket 通信等复杂功能。通过单例模式和延迟初始化实现了资源的高效使用。利用线程并行处理，在同时执行多个功能的同时保持了 UI 的响应性。通过对 VRAM 错误和设备错误的适当处理，提升了用户体验。
