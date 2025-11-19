# controller.py 设计文档

## 概述

`controller.py` 是 VRCT 应用程序的业务逻辑层,负责前端(UI)和后端(Model)之间的控制流程。作为语音识别、翻译、OSC 通信、覆盖层显示等 VRCT 所有功能的协调者,提供各种配置的获取·更新、设备管理、错误处理。

## 架构位置

```
┌─────────────┐
│ Frontend    │ (Tauri/React)
│ (UI Layer)  │
└──────┬──────┘
       │ JSON-RPC (stdin/stdout)
┌──────▼──────┐
│ mainloop.py │ (通信层)
└──────┬──────┘
       │ 函数调用
┌──────▼──────┐
│controller.py│ ◄── 本文件
└──────┬──────┘
       │ 门面模式
┌──────▼──────┐
│  model.py   │ (业务逻辑门面)
└──────┬──────┘
       │
┌──────▼──────┐
│ Subsystems  │ (transcription, translation, osc, overlay, etc.)
└─────────────┘
```

## 主要组件

### 1. Controller 类

#### 构造函数 `__init__()`

**职责:** 初始化 Controller 实例并设置依赖关系

**初始化处理:**
1. **映射字典的初始化:**
   - `init_mapping`: 初始化时执行的端点组
   - `run_mapping`: 前端通知用端点
2. **回调函数设置:**
   - `run`: 向前端发送通知的函数(默认为 no-op)
3. **Model 初始化:**
   - 调用 `model.init()` 准备子系统
   - 失败时用 `errorLogging()` 记录日志并继续
4. **设备访问状态:**
   - `device_access_status`: 设备排他访问控制标志

**类型提示:**
```python
self.init_mapping: dict
self.run_mapping: dict
self.run: Callable[[int, str, Any], None]
self.device_access_status: bool
```

#### 设置方法

##### `setInitMapping(init_mapping: dict) -> None`
设置初始化时执行的端点映射。由 `mainloop.py` 调用。

##### `setRunMapping(run_mapping: dict) -> None`
设置前端通知用的端点映射。

##### `setRun(run: Callable[[int, str, Any], None]) -> None`
设置前端通知函数。传入 `mainloop.py` 的 `printResponse()` 包装器。

#### 辅助方法

##### `_is_overlay_available() -> bool`
安全检查覆盖层功能是否可用。避免 Model 未初始化时的 `AttributeError`。

**实现:**
```python
try:
    overlay = getattr(model, "overlay", None)
    return overlay is not None and getattr(overlay, "initialized", False)
except Exception:
    errorLogging()
    return False
```

---

### 2. 通知方法(响应函数)

向前端通知状态变化的方法组。都通过 `self.run()` 将 JSON 发送到 stdout。

#### 网络相关

##### `connectedNetwork() -> None`
通知检测到网络连接。

##### `disconnectedNetwork() -> None`
通知检测到网络断开。

#### AI 模型相关

##### `enableAiModels() -> None`
通知 AI 模型(CTranslate2/Whisper)可用。

##### `disableAiModels() -> None`
通知 AI 模型不可用(下载失败等)。

#### 设备管理相关

##### `updateMicHostList() -> None`
更新麦克风主机列表(MME/WASAPI 等)。

##### `updateMicDeviceList() -> None`
更新麦克风设备列表。

##### `updateSpeakerDeviceList() -> None`
更新扬声器设备列表。

##### `updateSelectedMicDevice(host: str, device: str) -> None`
通知选中的麦克风设备。用于自动设备选择。

##### `updateSelectedSpeakerDevice(device: str) -> None`
通知选中的扬声器设备。

#### 能量级别通知

##### `progressBarMicEnergy(energy: Union[bool, int]) -> None`
通知麦克风音量级别。`False` 时发送设备错误。

##### `progressBarSpeakerEnergy(energy: Union[bool, int]) -> None`
通知扬声器音量级别。

#### 配置同步

##### `updateConfigSettings() -> None`
初始化完成时向前端发送所有配置值。执行 `init_mapping` 的所有端点。

---

### 3. 设备控制方法

#### 重启系

##### `restartAccessMicDevices() -> None`
重启麦克风访问。根据以下条件启动各功能:
- `config.ENABLE_TRANSCRIPTION_SEND` 为 True: 开始语音识别
- `config.ENABLE_CHECK_ENERGY_SEND` 为 True: 开始音量监控

##### `restartAccessSpeakerDevices() -> None`
重启扬声器访问。

#### 停止系

##### `stopAccessMicDevices() -> None`
停止麦克风相关功能。

##### `stopAccessSpeakerDevices() -> None`
停止扬声器相关功能。

**使用场景:**
- 设备变更时
- 自动设备选择导致设备切换时
- 应用程序关闭时

---

### 4. 消息处理方法

#### `micMessage(result: dict) -> None`

**职责:** 处理和分发麦克风语音识别结果

**处理流程:**
1. **结果验证:**
   - 获取 `result["text"]` 和 `result["language"]`
   - `False` 时通知设备错误并结束
2. **过滤:**
   - `model.checkKeywords()`: 禁止词检查
   - `model.detectRepeatSendMessage()`: 重复消息检查
3. **翻译处理:**
   - `config.ENABLE_TRANSLATION` 为 True 时:
     - 用 `model.getInputTranslate()` 执行翻译
     - 翻译引擎错误时切换到 CTranslate2
     - VRAM 不足错误时禁用翻译功能
4. **音译处理:**
   - `config.CONVERT_MESSAGE_TO_HIRAGANA/ROMAJI` 为 True 时:
     - 用 `model.convertMessageToTransliteration()` 转换
5. **分发处理:**
   - **VRChat OSC:** `config.SEND_MESSAGE_TO_VRC` 为 True 时
     - 用 `messageFormatter()` 格式化
     - 用 `model.oscSendMessage()` 发送
   - **UI 通知:** 用 `self.run()` 向 transcription_mic 端点通知
   - **覆盖层:** `config.OVERLAY_LARGE_LOG` 为 True 时
     - 用 `model.createOverlayImageLargeLog()` 生成图像
     - 用 `model.updateOverlayLargeLog()` 更新显示
   - **WebSocket:** 服务器运行中时
     - 用 `model.websocketSendMessage()` 广播
   - **日志文件:** `config.LOGGER_FEATURE` 为 True 时

**VRAM 错误处理:**
```python
try:
    translation, success = model.getInputTranslate(message, source_language=language)
except Exception as e:
    is_vram_error, error_message = model.detectVRAMError(e)
    if is_vram_error:
        # 禁用翻译功能
        self.setDisableTranslation()
        self.run(400, self.run_mapping["error_translation_mic_vram_overflow"], {...})
        return
```

#### `speakerMessage(result: dict) -> None`

**职责:** 处理和分发扬声器语音识别结果

**处理流程:** 与 `micMessage()` 类似,但有以下差异:
- **覆盖层:**
  - Small Log: 接收消息用的小日志窗口
  - Large Log: 显示发送和接收的日志窗口
- **OSC 发送:** 依赖 `config.SEND_RECEIVED_MESSAGE_TO_VRC` 设置
- **翻译:** 使用 `model.getOutputTranslate()`(接收消息用)

#### `chatMessage(data: dict) -> dict`

**职责:** 处理来自 UI 聊天框的消息

**参数:**
- `data["id"]`: 消息 ID(用于 UI 响应映射)
- `data["message"]`: 发送消息

**特殊处理:**
- **排除词处理:**
  - `config.USE_EXCLUDE_WORDS` 为 True 时
  - `replaceExclamationsWithRandom()`: 将 `![word]` 替换为临时令牌
  - 翻译后用 `restoreText()` 恢复
  - 从最终消息中删除 `![...]`
- **同步响应:** 
  - 与其他消息处理不同,返回 `dict` 结果
  - UI 需要等待翻译结果

**响应格式:**
```python
{
    "status": 200,
    "result": {
        "id": "msg-123",
        "original": {
            "message": "Hello",
            "transliteration": ["he", "ro"]
        },
        "translations": [
            {
                "message": "こんにちは",
                "transliteration": ["ko", "n", "ni", "chi", "wa"]
            }
        ]
    }
}
```

---

### 5. 消息格式

#### `messageFormatter(format_type: str, translation: list, message: str) -> str`

**职责:** 格式化 OSC 发送用消息

**参数:**
- `format_type`: "SEND" 或 "RECEIVED"
- `translation`: 翻译结果列表
- `message`: 原始消息

**处理逻辑:**
1. 获取格式设置:
   - `config.SEND_MESSAGE_FORMAT_PARTS` 或 `config.RECEIVED_MESSAGE_FORMAT_PARTS`
2. 构建各部分:
   - `message_part`: prefix + message + suffix
   - `translation_part`: prefix + separator.join(translation) + suffix
3. 组合:
   - 两者都存在: 根据 `translation_first` 设置决定顺序
   - 仅翻译: translation_part
   - 仅消息: message_part

**配置示例:**
```python
config.SEND_MESSAGE_FORMAT_PARTS = {
    "message": {"prefix": "[", "suffix": "] "},
    "translation": {"prefix": "", "suffix": "", "separator": " / "},
    "translation_first": False,
    "separator": ""
}
# 输出示例: [Hello] こんにちは / 你好
```

---

### 6. 排除词处理

#### `replaceExclamationsWithRandom(text: str) -> Tuple[str, dict]`

**职责:** 保护不需要翻译的单词

**处理:**
1. 检测 `![word]` 模式
2. 将每个匹配替换为 `$<十六进制编号>`(从 4096 开始的序号)
3. 返回替换映射字典

**用途:** 保护专有名词和不需要翻译的单词

#### `restoreText(escaped_text: str, escape_dict: dict) -> str`

**职责:** 在翻译后的文本中恢复原始单词

**处理:** 用正则表达式检测 `$<十六进制编号>` 并替换为原始单词(忽略大小写)

#### `removeExclamations(text: str) -> str`

**职责:** 从最终消息中删除 `![...]` 标记

**处理:** 将 `![word]` 替换为 `word`

---

### 7. 配置获取·更新方法(GET/SET)

Controller 定义了约 200 个配置项的 getter/setter。以下是代表性模式。

#### 模式1: 简单配置值

```python
@staticmethod
def getTransparency(*args, **kwargs) -> dict:
    return {"status": 200, "result": config.TRANSPARENCY}

@staticmethod
def setTransparency(data, *args, **kwargs) -> dict:
    config.TRANSPARENCY = int(data)
    return {"status": 200, "result": config.TRANSPARENCY}
```

#### 模式2: 启用/禁用切换

```python
@staticmethod
def getOverlaySmallLog(*args, **kwargs) -> dict:
    return {"status": 200, "result": config.OVERLAY_SMALL_LOG}

@staticmethod
def setEnableOverlaySmallLog(*args, **kwargs) -> dict:
    if config.OVERLAY_SMALL_LOG is False:
        if config.OVERLAY_LARGE_LOG is False:
            model.startOverlay()  # 副作用: 启动覆盖层系统
        config.OVERLAY_SMALL_LOG = True
    return {"status": 200, "result": config.OVERLAY_SMALL_LOG}

@staticmethod
def setDisableOverlaySmallLog(*args, **kwargs) -> dict:
    if config.OVERLAY_SMALL_LOG is True:
        model.clearOverlayImageSmallLog()
        if config.OVERLAY_LARGE_LOG is False:
            model.shutdownOverlay()  # 副作用: 停止覆盖层系统
        config.OVERLAY_SMALL_LOG = False
    return {"status": 200, "result": config.OVERLAY_SMALL_LOG}
```

#### 模式3: 带验证的配置

```python
@staticmethod
def setMicThreshold(data, *args, **kwargs) -> dict:
    try:
        data = int(data)
        if 0 <= data <= config.MAX_MIC_THRESHOLD:
            config.MIC_THRESHOLD = data
            status = 200
        else:
            raise ValueError()
    except Exception:
        response = {
            "status": 400,
            "result": {
                "message": "Mic energy threshold value is out of range",
                "data": config.MIC_THRESHOLD
            }
        }
    else:
        response = {"status": status, "result": config.MIC_THRESHOLD}
    return response
```

#### 模式4: 有依赖关系的配置

```python
def setSelectedTranslationComputeDevice(self, device: str, *args, **kwargs) -> dict:
    config.SELECTED_TRANSLATION_COMPUTE_DEVICE = device
    config.SELECTED_TRANSLATION_COMPUTE_TYPE = "auto"
    # 自动更新依赖配置
    self.run(200, self.run_mapping["selected_translation_compute_type"], 
             config.SELECTED_TRANSLATION_COMPUTE_TYPE)
    # 设置模型重新加载标志
    model.setChangedTranslatorParameters(True)
    return {"status": 200, "result": config.SELECTED_TRANSLATION_COMPUTE_DEVICE}
```

---

### 8. 翻译功能控制

#### `setEnableTranslation(*args, **kwargs) -> dict`

**职责:** 启用翻译功能并加载模型

**处理流程:**
1. 已启用时不做任何处理
2. 模型未加载或参数变更时:
   - 用 `model.changeTranslatorCTranslate2Model()` 加载模型
   - VRAM 不足错误时:
     - 恢复默认设置
     - 发送错误通知
     - 禁用翻译
3. 设置 `config.ENABLE_TRANSLATION = True`

**错误处理:**
```python
try:
    model.changeTranslatorCTranslate2Model()
except Exception as e:
    is_vram_error, error_message = model.detectVRAMError(e)
    if is_vram_error:
        self.run(400, self.run_mapping["error_translation_enable_vram_overflow"], {...})
        self.setDisableTranslation()
```

#### `setDisableTranslation(*args, **kwargs) -> dict`

**职责:** 禁用翻译功能(释放内存)

#### `changeToCTranslate2Process() -> None`

**职责:** 外部翻译 API 错误时切换到 CTranslate2

**处理:**
1. 禁用当前翻译引擎
2. 切换到 CTranslate2
3. 通知前端

---

### 9. 语音识别控制

#### 线程管理方法

##### `startTranscriptionSendMessage() -> None`
开始麦克风语音识别。进行设备访问的排他控制。

**排他控制:**
```python
while self.device_access_status is False:
    sleep(1)  # 其他处理正在使用设备时等待
self.device_access_status = False  # 获取锁
try:
    model.startMicTranscript(self.micMessage)
finally:
    self.device_access_status = True  # 释放锁
```

**VRAM 错误处理:**
- 用 `model.detectVRAMError()` 检测错误
- 停止语音识别
- 通知前端

##### `stopTranscriptionSendMessage() -> None`
停止麦克风语音识别。

##### `startThreadingTranscriptionSendMessage() -> None`
在独立线程中开始语音识别。

##### `stopThreadingTranscriptionSendMessage() -> None`
在独立线程中停止语音识别并等待完成(`join()`)。

**对应的扬声器用方法:**
- `startTranscriptionReceiveMessage()`
- `stopTranscriptionReceiveMessage()`
- `startThreadingTranscriptionReceiveMessage()`
- `stopThreadingTranscriptionReceiveMessage()`

---

### 10. 能量监控

#### `startCheckMicEnergy() -> None`
开始麦克风音量级别监控。将 `progressBarMicEnergy()` 作为回调传递。

#### `stopCheckMicEnergy() -> None`
停止麦克风音量级别监控。

#### `startThreadingCheckMicEnergy() -> None`
在独立线程中开始能量监控。

#### `stopThreadingCheckMicEnergy() -> None`
在独立线程中停止能量监控并等待完成。

**对应的扬声器用方法:**
- `startCheckSpeakerEnergy()`
- `stopCheckSpeakerEnergy()`
- `startThreadingCheckSpeakerEnergy()`
- `stopThreadingCheckSpeakerEnergy()`

---

### 11. 模型权重管理

#### DownloadCTranslate2 类

**职责:** CTranslate2 模型下载进度管理

**方法:**
- `progressBar(progress: float)`: 向前端通知进度率
- `downloaded()`: 下载完成时的处理
  - 确认模型存在
  - 添加到可选模型列表
  - 通知前端

#### DownloadWhisper 类

**职责:** Whisper 模型下载进度管理(与 CTranslate2 结构相同)

#### `downloadCtranslate2Weight(data: str, asynchronous: bool = True, *args, **kwargs) -> dict`

**职责:** 开始 CTranslate2 模型下载

**参数:**
- `data`: 模型类型("tiny", "small", "medium" 等)
- `asynchronous`: 启用异步下载

**处理:**
1. 创建 `DownloadCTranslate2` 实例
2. `asynchronous` 为 True 时:
   - 用 `startThreadingDownloadCtranslate2Weight()` 在独立线程执行
3. `asynchronous` 为 False 时:
   - 用 `model.downloadCTranslate2ModelWeight()` 同步执行(初始化时使用)
4. 下载分词器

#### `downloadWhisperWeight(data: str, asynchronous: bool = True, *args, **kwargs) -> dict`

**职责:** 开始 Whisper 模型下载(与 CTranslate2 结构相同)

---

### 12. 自动设备选择

#### `applyAutoMicSelect() -> None`

**职责:** 应用麦克风自动选择功能

**处理:**
1. 设置回调:
   - `device_manager.setCallbackProcessBeforeUpdateMicDevices(self.stopAccessMicDevices)`
   - `device_manager.setCallbackDefaultMicDevice(self.updateSelectedMicDevice)`
   - `device_manager.setCallbackProcessAfterUpdateMicDevices(self.restartAccessMicDevices)`
2. 强制执行设备更新: `device_manager.forceUpdateAndSetMicDevices()`
3. 开始监控: `device_manager.startMonitoring()`

**运行流程:**
```
检测到设备变更
  ↓
stopAccessMicDevices() ← 停止正在使用设备的处理
  ↓
updateSelectedMicDevice() ← 选择新的默认设备
  ↓
restartAccessMicDevices() ← 用新设备重新开始处理
```

#### `setEnableAutoMicSelect(*args, **kwargs) -> dict`
启用自动麦克风选择。

#### `setDisableAutoMicSelect(*args, **kwargs) -> dict`
禁用自动麦克风选择。只有两个自动选择都禁用时才停止监控。

**对应的扬声器用方法:**
- `applyAutoSpeakerSelect()`
- `setEnableAutoSpeakerSelect()`
- `setDisableAutoSpeakerSelect()`

---

### 13. 语言·翻译引擎管理

#### `updateTranslationEngineAndEngineList() -> None`

**职责:** 根据选择的语言更新可用翻译引擎

**处理:**
1. 获取当前标签的选择引擎
2. 用 `getTranslationEngines()` 获取可用引擎列表
3. 选中的引擎不可用时回退到 CTranslate2
4. **特殊情况:** 输入语言和输出语言相同时:
   - 仅 CTranslate2 可用(仅音译)
5. 通知前端

#### `getTranslationEngines(*args, **kwargs) -> dict`

**职责:** 返回当前语言设置可用的翻译引擎

**逻辑:**
1. 用 `model.findTranslationEngines()` 搜索支持语言对的引擎
2. 输入语言和输出语言相同时:
   - CTranslate2 有效时 ["CTranslate2"]
   - 否则 []

#### `setSelectedYourLanguages(select: dict, *args, **kwargs) -> dict`
设置输入语言并调用 `updateTranslationEngineAndEngineList()`。

#### `setSelectedTargetLanguages(select: dict, *args, **kwargs) -> dict`
设置输出语言并调用 `updateTranslationEngineAndEngineList()`。

#### `swapYourLanguageAndTargetLanguage(*args, **kwargs) -> dict`

**职责:** 交换输入语言和输出语言

**处理:**
1. 获取当前标签的输入语言和输出语言(第一个)
2. 相互交换
3. 调用 `setSelectedYourLanguages()` 和 `setSelectedTargetLanguages()`
4. 返回两个结果

---

### 14. 语音识别引擎管理

#### `updateTranscriptionEngine() -> None`

**职责:** 根据 Whisper 模型可用性更新语音识别引擎

**处理:**
1. 确认当前选择的 Whisper 模型是否存在
2. 获取可用引擎列表
3. 当前引擎不可用时:
   - Whisper ⇔ Google 切换
   - 两者都不可用时回退到 Whisper

#### `updateDownloadedWhisperModelWeight() -> None`

**职责:** 更新已下载 Whisper 模型列表

**处理:**
对所有模型类型用 `model.checkTranscriptionWhisperModelWeight()` 确认存在。

---

### 15. OSC 通信控制

#### `setOscIpAddress(data, *args, **kwargs) -> dict`

**职责:** 设置 VRChat 发送目标 IP 地址

**处理:**
1. 用 `isValidIpAddress()` 验证
2. 用 `model.setOscIpAddress()` 应用设置
3. 根据 OSC Query 状态重新初始化:
   - 有效时: 调用 `enableOscQuery()`
   - 无效时: 调用 `disableOscQuery()`
   - 麦克风静音同步启用时禁用并通知

**错误处理:**
- IP 地址无效: status 400
- 设置应用失败: 恢复原 IP 并返回 status 400

#### `setOscPort(data, *args, **kwargs) -> dict`
设置 OSC 端口号。

#### `enableOscQuery() -> None`
向前端通知 OSC Query 功能已启用。

#### `disableOscQuery(mute_sync_info: bool = False) -> None`
通知 OSC Query 功能已禁用。也发送禁用的功能列表。

---

### 16. DeepL API 认证

#### `setDeeplAuthKey(data, *args, **kwargs) -> dict`

**职责:** 设置 DeepL API 密钥并执行认证

**处理:**
1. 密钥长度验证(36 或 39 字符)
2. 用 `model.authenticationTranslatorDeepLAuthKey()` 认证
3. 认证成功时:
   - 保存到 `config.AUTH_KEYS["DeepL_API"]`
   - 设置 `config.SELECTABLE_TRANSLATION_ENGINE_STATUS["DeepL_API"]` 为 True
   - 调用 `updateTranslationEngineAndEngineList()`
4. 认证失败时: 返回 status 400

#### `delDeeplAuthKey(*args, **kwargs) -> dict`

**职责:** 删除 DeepL API 密钥

**处理:**
1. 设置 `config.AUTH_KEYS["DeepL_API"]` 为 None
2. 设置 `config.SELECTABLE_TRANSLATION_ENGINE_STATUS["DeepL_API"]` 为 False
3. 调用 `updateTranslationEngineAndEngineList()`

---

### 17. WebSocket 服务器控制

#### `setWebSocketHost(data, *args, **kwargs) -> dict`

**职责:** 更改 WebSocket 服务器主机地址

**处理:**
1. 用 `isValidIpAddress()` 验证
2. 服务器停止时:
   - 仅更改设置
3. 服务器运行时:
   - 确认新主机是否可用(`isAvailableWebSocketServer()`)
   - 停止服务器 → 重启
   - 不可用时返回 status 400

#### `setWebSocketPort(data, *args, **kwargs) -> dict`
更改 WebSocket 服务器端口号(逻辑与 `setWebSocketHost()` 相同)。

#### `setEnableWebSocketServer(*args, **kwargs) -> dict`

**职责:** 启动 WebSocket 服务器

**处理:**
1. 已运行时不做处理
2. 确认主机和端口是否可用
3. 用 `model.startWebSocketServer()` 启动
4. 不可用时返回 status 400

#### `setDisableWebSocketServer(*args, **kwargs) -> dict`
停止 WebSocket 服务器。

---

### 18. VRChat 麦克风静音同步

#### `setEnableVrcMicMuteSync(*args, **kwargs) -> dict`

**职责:** 启用 VRChat 麦克风静音状态与语音识别的联动

**前提条件:** OSC Query 已启用

**处理:**
1. OSC Query 无效时返回 status 400
2. `model.setMuteSelfStatus()`: 获取当前静音状态
3. `model.changeMicTranscriptStatus()`: 根据静音状态控制语音识别
4. `config.VRC_MIC_MUTE_SYNC = True`

#### `setDisableVrcMicMuteSync(*args, **kwargs) -> dict`
禁用麦克风静音同步并调用 `model.changeMicTranscriptStatus()`。

---

### 19. Watchdog 管理

Watchdog 是 UI 与后端间的通信监控功能。UI 没有定期 "feed" 信号时强制结束后端。

#### `startWatchdog(*args, **kwargs) -> dict`
启动 Watchdog。

#### `feedWatchdog(*args, **kwargs) -> dict`
向 Watchdog 发送心跳信号(UI 定期调用)。

#### `setWatchdogCallback(callback) -> dict`
设置 Watchdog 超时时调用的回调函数。传入 `mainloop.stop()`。

#### `stopWatchdog(*args, **kwargs) -> dict`
停止 Watchdog。

---

### 20. 软件更新

#### `checkSoftwareUpdated() -> dict`

**职责:** 确认最新版本

**处理:**
1. 用 `model.checkSoftwareUpdated()` 获取版本信息
2. 通知前端(`software_update_info` 端点)
3. 返回结果

**版本信息格式:**
```python
{
    "current_version": "1.2.3",
    "latest_version": "1.2.4",
    "update_available": True,
    "download_url": "https://..."
}
```

#### `updateSoftware(*args, **kwargs) -> dict`

**职责:** 执行普通版更新

**处理:**
1. 在独立线程中启动 `model.updateSoftware()`(避免阻塞)
2. 立即返回 status 200

#### `updateCudaSoftware(*args, **kwargs) -> dict`

**职责:** 执行 CUDA 版更新

**处理:** 与 `updateSoftware()` 相同但调用 `model.updateCudaSoftware()`。

---

### 21. 初始化处理

#### `init(*args, **kwargs) -> None`

**职责:** 应用程序的完整初始化

**处理流程:**

**1. 清除日志**
```python
removeLog()
printLog("Start Initialization")
```

**2. 网络连接确认**
```python
connected_network = isConnectedNetwork()
if connected_network:
    self.connectedNetwork()
else:
    self.disconnectedNetwork()
```

**3. 模型权重下载(进度 1/4)**
```python
self.initializationProgress(1)
if connected_network:
    # CTranslate2 和 Whisper 并行下载
    th_download_ctranslate2 = Thread(target=self.downloadCtranslate2Weight, args=(weight_type, False))
    th_download_whisper = Thread(target=self.downloadWhisperWeight, args=(weight_type, False))
    th_download_ctranslate2.start()
    th_download_whisper.start()
    th_download_ctranslate2.join()
    th_download_whisper.join()
```

**4. AI 模型状态确认**
```python
if (model.checkTranslatorCTranslate2ModelWeight(...) is False or
    model.checkTranscriptionWhisperModelWeight(...) is False):
    self.disableAiModels()
else:
    self.enableAiModels()
```

**5. 翻译·语音识别引擎初始化(进度 2/4)**
```python
self.initializationProgress(2)
# 翻译引擎
for engine in config.SELECTABLE_TRANSLATION_ENGINE_LIST:
    match engine:
        case "CTranslate2":
            # 模型权重存在确认
        case "DeepL_API":
            # API 密钥认证
        case _:
            # 需要网络连接的引擎

# 语音识别引擎
for engine in config.SELECTABLE_TRANSCRIPTION_ENGINE_LIST:
    # 类似逻辑
```

**6. 引擎和音译设置(进度 3/4)**
```python
self.updateDownloadedCTranslate2ModelWeight()
self.updateTranslationEngineAndEngineList()
self.updateDownloadedWhisperModelWeight()
self.updateTranscriptionEngine()

if config.CONVERT_MESSAGE_TO_ROMAJI or config.CONVERT_MESSAGE_TO_HIRAGANA:
    model.startTransliteration()
```

**7. 外围功能初始化(进度 4/4)**
```python
self.initializationProgress(4)
model.addKeywords()  # 词语过滤器
self.checkSoftwareUpdated()  # 版本检查
if config.LOGGER_FEATURE:
    model.startLogger()  # 日志记录
model.startReceiveOSC()  # OSC 接收

# OSC Query
osc_query_enabled = model.getIsOscQueryEnabled()
if osc_query_enabled:
    self.enableOscQuery()
    if config.VRC_MIC_MUTE_SYNC:
        self.setEnableVrcMicMuteSync()
else:
    # 禁用麦克风静音同步
    self.disableOscQuery(...)
```

**8. 设备管理初始化**
```python
device_manager.setCallbackHostList(self.updateMicHostList)
device_manager.setCallbackMicDeviceList(self.updateMicDeviceList)
device_manager.setCallbackSpeakerDeviceList(self.updateSpeakerDeviceList)

if config.AUTO_MIC_SELECT:
    self.applyAutoMicSelect()
if config.AUTO_SPEAKER_SELECT:
    self.applyAutoSpeakerSelect()
```

**9. 覆盖层和 WebSocket 启动**
```python
if config.OVERLAY_SMALL_LOG or config.OVERLAY_LARGE_LOG:
    model.startOverlay()

if config.WEBSOCKET_SERVER:
    if isAvailableWebSocketServer(...):
        model.startWebSocketServer(...)
```

**10. 配置同步和完成**
```python
self.updateConfigSettings()  # 向前端发送所有配置
printLog("End Initialization")
self.startWatchdog()  # 开始监控
```

---

## 错误处理策略

### 1. VRAM 不足错误

**检测位置:**
- 翻译执行时(`micMessage()`, `speakerMessage()`, `chatMessage()`)
- 翻译功能启用时(`setEnableTranslation()`)
- 语音识别开始时(`startTranscriptionSendMessage()`, `startTranscriptionReceiveMessage()`)

**处理:**
1. 用 `model.detectVRAMError(e)` 检测 VRAM 错误
2. 禁用相应功能
3. 向前端发送错误通知
4. 记录到日志文件

**自动恢复:**
- 翻译功能: 禁用后继续
- 语音识别: 停止后继续

### 2. 设备访问错误

**检测位置:**
- 访问麦克风·扬声器时

**处理:**
1. `energy` 为 `False` 时
2. 向 `error_device` 端点发送错误通知
3. 继续处理(其他功能不受影响)

### 3. 网络错误

**检测位置:**
- 调用翻译 API 时
- 下载模型权重时

**处理:**
1. 外部 API 错误: 用 `changeToCTranslate2Process()` 切换到 CTranslate2
2. 下载错误: 发送错误通知,禁用 AI 功能

### 4. 配置验证错误

**处理:**
- 返回 status 400 和错误消息
- 在 `data` 字段中包含当前有效配置值

**示例:**
```python
{
    "status": 400,
    "result": {
        "message": "Mic energy threshold value is out of range",
        "data": 1000  # 当前有效值
    }
}
```

---

## 线程安全性

### 排他控制

#### 设备访问控制

**问题:** 多个功能同时访问设备会冲突

**解决方案:** 通过 `device_access_status` 标志进行排他控制
```python
while self.device_access_status is False:
    sleep(1)  # 等待
self.device_access_status = False  # 获取锁
try:
    # 设备访问处理
finally:
    self.device_access_status = True  # 释放锁
```

**使用位置:**
- `startTranscriptionSendMessage()`
- `startTranscriptionReceiveMessage()`
- `startCheckMicEnergy()`
- `startCheckSpeakerEnergy()`

### 守护线程

**所有工作线程都是 `daemon = True`:**
- 主线程结束时自动结束
- 根据需要执行显式 join(停止处理等)

**示例:**
```python
th_startTranscriptionSendMessage = Thread(target=self.startTranscriptionSendMessage)
th_startTranscriptionSendMessage.daemon = True
th_startTranscriptionSendMessage.start()
```

---

## 性能考虑

### 1. 异步下载

**初始化时:** 同步下载(`asynchronous=False`)
- 阻塞 UI 确保完成下载

**用户操作时:** 异步下载(`asynchronous=True`)
- 在独立线程中执行,用进度条通知

### 2. 并行初始化

CTranslate2 和 Whisper 并行下载:
```python
th_download_ctranslate2.start()
th_download_whisper.start()
th_download_ctranslate2.join()
th_download_whisper.join()
```

### 3. 模型延迟加载

翻译模型在调用 `setEnableTranslation()` 之前不加载。

---

## 依赖关系

### 外部模块

```python
from typing import Callable, Any, List, Optional
from time import sleep
from subprocess import Popen
from threading import Thread
import re
```

### 内部模块

```python
from device_manager import device_manager
from config import config
from model import model
from utils import removeLog, printLog, errorLogging, isConnectedNetwork, isValidIpAddress, isAvailableWebSocketServer
```

---

## 配置项分类

### UI 相关(约 20 项)
- 透明度、缩放、字体、语言、窗口位置等

### 语音识别相关(约 30 项)
- 设备选择、阈值、超时、过滤器等

### 翻译相关(约 25 项)
- 引擎选择、语言对、模型类型、计算设备等

### OSC 通信相关(约 15 项)
- IP 地址、端口、消息格式、发送设置等

### 覆盖层相关(约 10 项)
- 显示设置、位置、大小、透明度等

### 其他(约 20 项)
- WebSocket、日志、热键、插件等

**合计:** 约 120 个配置项(getter/setter 约 240 个方法)

---

## 限制

### 1. 全局状态依赖

所有配置作为 `config` 模块的全局变量管理。
- **优点:** 简单访问
- **缺点:** 可测试性降低,并行执行时竞争风险

### 2. 同步响应限制

大多数方法同步返回响应,重处理(模型加载等)可能阻塞 UI。

**对策:** 重处理在独立线程中执行,完成通知通过 `self.run()` 发送

### 3. 错误恢复限制

部分错误(VRAM 不足等)自动恢复,但配置文件损坏或模型文件损坏等需要手动处理。

---

## 测试场景

### 1. 初始化测试

**情况:**
- 有·无网络连接
- 有·无模型权重
- 非法配置值

**确认项目:**
- 所有引擎状态是否正确设置
- 错误是否记录到日志
- 是否向前端发送正确初始配置

### 2. 语音识别测试

**情况:**
- 设备切换中进行语音识别
- VRAM 不足错误发生
- 重复消息过滤

**确认项目:**
- 排他控制是否正确运行
- 错误发生时是否适当恢复

### 3. 翻译测试

**情况:**
- 多个翻译引擎切换
- API 限制错误
- 排除词处理

**确认项目:**
- 引擎切换是否正确运行
- 排除词是否正确恢复

### 4. 配置变更测试

**情况:**
- 设置无效值
- 有依赖关系的配置变更
- 启用/禁用切换

**确认项目:**
- 验证是否正确运行
- 依赖配置是否自动更新

---

## 未来扩展性

### 1. 推进异步化

迁移到 `asyncio` 完全消除 UI 阻塞。

### 2. 依赖注入

用 DI 容器管理 `config` 和 `model`,提高可测试性。

### 3. 事件驱动架构

配置变更时触发事件,各子系统独立响应。

### 4. 错误恢复强化

- 自动重试机制
- 自动应用回退配置
- 错误发生时部分功能继续

---

## 相关文件

- **mainloop.py** - 通信层,请求路由
- **model.py** - 业务逻辑门面
- **config.py** - 配置管理
- **device_manager.py** - 设备监控·自动选择
- **utils.py** - 日志和工具函数

---

## 编码规范

- **PEP 8 样式指南**
- **类型提示:** 使用 `typing` 模块
- **Docstring:** Google 风格(部分未实现)
- **静态方法:** 不持有状态的方法使用 `@staticmethod`
- **错误处理:** 彻底防御性编程

---

## 总结

`controller.py` 是 VRCT 核心业务逻辑控制层,管理约 120 个配置项和约 200 个端点。作为前端和后端的桥梁,控制配置获取·更新、功能启用·禁用、错误处理、设备管理等应用程序整体运行。通过排他控制和线程管理,即使在多个功能同时运行的环境中也保持稳定性。通过 VRAM 不足错误和外部 API 错误的自动恢复功能,实现了用户体验的提升。
