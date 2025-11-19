# model.py - VRCT核心模型类

## 概述

定义VRCT应用程序核心Model类的模块。集成管理语音识别、翻译、VR覆盖层、OSC通信、WebSocket服务器等主要功能,控制整个系统的运行。

## 最近更新 (2025-10-20)

### VRAM错误检测和降级

- 添加`detectVRAMError()`识别CUDA内存相关消息/自定义异常`VRAM_OUT_OF_MEMORY`
- 翻译/语音识别执行中检测到VRAM错误时,支持Controller侧禁用翻译功能并降级到CTranslate2的运用
- 标准化向UI通知的错误详细字符串提取

### CTranslate2语言映射嵌套对应

- `getListLanguageAndCountry()` / `findTranslationEngines()`更新为参考`translation_lang['CTranslate2'][CTRANSLATE2_WEIGHT_TYPE]['source']`的嵌套结构
- 权重类型切换时对应语言集合动态变化并触发引擎重新判定

### 本地LLM翻译引擎集成

- 添加LMStudio / Ollama用客户端初始化·模型列表获取方法: `authenticationTranslatorLMStudio()`, `getTranslatorLMStudioModelList()`, `setTranslatorLMStudioModel()`, `updateTranslatorLMStudioClient()`等
- Ollama也以相同接口统一 (`getTranslatorOllamaModelList`, `setTranslatorOllamaModel`, `updateTranslatorOllamaClient`)
- 与Plamo / Gemini / OpenAI相同格式实现模型选择逻辑,简化从Controller的调用

### 分词器·资源获取稳定化

- 在`downloadCTranslate2ModelTokenizer()`中明确化CTranslate2分词器下载处理,避免PyInstaller路径周围的不一致
- 字体路径搜索委托给OverlayImage侧 (`OverlayImage(config.PATH_LOCAL)`),Model仅保持生成和更新调用

### 翻译失败时的故障安全重试

- `getTranslate()`内翻译失败(非字符串)时重试循环CTranslate2返回稳定结果
- 返回成功判定标志,便于上层检测引擎限制错误/降级

### 关键词过滤器重新初始化改进

- `resetKeywordProcessor()`重新生成实例,通过`addKeywords()`立即反映配置变更后的过滤器更新

### WebSocket服务器管理强化

- 通过`asyncio.run`包装线程稳定化异步服务器启动
- 添加循环标志`websocket_server_loop`和状态标志`websocket_server_alive`,标准化安全停止处理和存活确认

### 影响

| 项目 | 内容 |
|------|------|
| 稳定性 | 通过VRAM检测和故障安全重试避免异常终止 |
| 可扩展性 | 通过本地LLM集成对应无需网络环境 |
| 灵活性 | 根据CTranslate2权重类型动态切换语言集合 |
| 可维护性 | 分词器/字体获取职责分离提高可读性 |
| 可观测性 | 错误详细标准化便于UI/日志诊断 |

## 主要功能

### 单例模式

- 保证应用程序全局唯一Model实例
- 通过延迟初始化实现轻量导入

### 语音识别功能

- 麦克风音频实时文字转录
- 扬声器输出语音识别
- 能量级别监控
- 支持多语言

### 翻译功能

- 支持多个翻译引擎(DeepL、Google、CTranslate2等)
- 语言自动检测
- 批量翻译处理

### VR覆盖层

- OpenVR集成
- 小型·大型日志覆盖层
- 动态位置·透明度控制

### OSC通信

- 与VRChat的OSC通信
- 打字状态同步
- 静音状态监控

### WebSocket服务器

- 与外部应用程序通信
- 实时消息分发

## 类结构

### threadFnc 类

```python
class threadFnc(Thread):
    def __init__(self, fnc, end_fnc=None, daemon: bool = True, *args, **kwargs)
```

- 重复执行函数的线程包装器
- 暂停·恢复功能
- 错误保护功能

### Model 类

```python
class Model:
    def __new__(cls)  # 单例模式
    def init(self)    # 重初始化处理
    def ensure_initialized(self)  # 延迟初始化
```

## 主要方法

### 初始化·管理

```python
init() -> None
```

- 所有组件初始化
- 重处理需明确调用

```python
ensure_initialized() -> None
```

- 需要时自动初始化
- 安全延迟初始化

### 翻译功能方法

```python
getInputTranslate(message, source_language=None) -> Tuple[List[str], List[bool]]
```

- 输入消息多语言翻译
- 同时返回成功标志

```python
getOutputTranslate(message, source_language=None) -> Tuple[List[str], List[bool]]
```

- 输出消息翻译(反向)

```python
authenticationTranslatorDeepLAuthKey(auth_key) -> bool
```

- DeepL API密钥认证

### 语音识别功能方法

```python
startMicTranscript(fnc: Callable) -> None
```

- 启动麦克风语音识别
- 通过回调函数通知结果

```python
startSpeakerTranscript(fnc: Callable) -> None
```

- 启动扬声器语音识别

```python
pauseMicTranscript() -> None
resumeMicTranscript() -> None
```

- 语音识别暂停·恢复

```python
startCheckMicEnergy(fnc: Callable) -> None
startCheckSpeakerEnergy(fnc: Callable) -> None
```

- 监控音频能量级别

### VR覆盖层功能

```python
createOverlayImageSmallLog(message, your_language, translation, target_language) -> Image
```

- 生成小型日志覆盖层图像

```python
createOverlayImageLargeLog(message_type, message, your_language, translation, target_language) -> Image
```

- 生成大型日志覆盖层图像

```python
updateOverlaySmallLogSettings() -> None
updateOverlayLargeLogSettings() -> None
```

- 更新覆盖层配置

### OSC通信功能

```python
oscSendMessage(message: str) -> None
```

- 向VRChat发送消息

```python
oscStartSendTyping() -> None
oscStopSendTyping() -> None
```

- 通知打字状态

```python
setMuteSelfStatus() -> None
```

- 获取VRChat静音状态

### WebSocket功能

```python
startWebSocketServer(host: str, port: int) -> None
```

- 启动WebSocket服务器

```python
websocketSendMessage(message_dict: dict) -> bool
```

- 向所有客户端发送消息

```python
checkWebSocketServerAlive() -> bool
```

- 确认服务器运行状态

### 文件下载功能

```python
downloadCTranslate2ModelWeight(weight_type, callback=None, end_callback=None)
```

- 翻译模型下载

```python
downloadWhisperModelWeight(weight_type, callback=None, end_callback=None)
```

- 语音识别模型下载

### 看门狗功能

```python
startWatchdog() -> None
feedWatchdog() -> None
setWatchdogCallback(callback: Callable) -> None
```

- 系统监控和超时处理

## 使用方法

### 基本用法

```python
from model import model

# 明确初始化(推荐)
model.init()

# 或自动初始化
model.ensure_initialized()

# 使用翻译功能
translations, success_flags = model.getInputTranslate("Hello World")

# 启动语音识别
def on_transcript_result(result):
    print(f"识别结果: {result}")

model.startMicTranscript(on_transcript_result)
```

### VR覆盖层使用

```python
# 启动覆盖层
model.startOverlay()

# 创建和更新图像
img = model.createOverlayImageSmallLog(
    message="Hello",
    your_language="English",
    translation=["こんにちは"],
    target_language={"1": {"language": "Japanese", "enable": True}}
)
model.updateOverlaySmallLog(img)
```

### WebSocket服务器使用

```python
# 启动服务器
model.startWebSocketServer("127.0.0.1", 8765)

# 发送消息
message = {"type": "translation", "text": "Hello", "translation": "こんにちは"}
success = model.websocketSendMessage(message)
```

## 依赖关系

### 必需模块

- `controller`: 应用程序控制
- `config`: 配置管理
- `device_manager`: 设备管理

### 音频·翻译相关

- `models.transcription.*`: 语音识别
- `models.translation.*`: 翻译功能
- `models.transliteration.*`: 音译转换

### VR·通信相关

- `models.overlay.*`: VR覆盖层
- `models.osc.*`: OSC通信
- `models.websocket.*`: WebSocket通信

### 工具

- `models.watchdog.*`: 监控功能
- `utils`: 通用工具
- `flashtext`: 关键词过滤

## 配置依赖关系

许多功能依赖config模块配置:

- 语音识别配置(阈值、超时等)
- 翻译配置(引擎选择、语言配置等)
- VR配置(覆盖层位置、透明度等)
- OSC配置(IP地址、端口等)

## 错误处理

- 适当处理初始化错误
- VRAM不足错误的检测和对应
- 网络错误恢复功能
- 保证线程安全

## 注意事项

- 因重初始化处理,推荐明确初始化
- 需要OpenVR环境(使用VR覆盖层时)
- 推荐CUDA环境(高速语音识别·翻译)
- WebSocket服务器异步运行
- 需要音频设备访问权限

## 性能考虑事项

- 通过延迟初始化优化内存使用
- 通过线程池并行处理
- 防止模型重复加载
- 通过队列异步处理
