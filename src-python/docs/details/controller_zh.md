# controller.py - VRCT控制器模块

## 概述

VRCT应用程序的业务逻辑控制器类。位于UI层和模型层之间,负责将用户输入转换为适当的处理并将结果返回给UI。统一进行所有功能控制、配置管理和状态管理。

## 最近更新 (2025-10-20)

### 新增本地LLM翻译引擎集成

- 添加LMStudio / Ollama连接确认端点: `/run/lmstudio_connection`, `/run/ollama_connection`
- LMStudio URL配置: `/get|set/data/lmstudio_url`
- 模型列表获取和选择: `/get/data/*_model_list`, `/get|set/data/*_model` (lmstudio / ollama / plamo / gemini / openai)
- 认证·连接成功时通过run通知`selectable_*_model_list` / `selected_*_model` (例如: `/run/selectable_lmstudio_model_list`, `/run/selected_lmstudio_model`)

### 模型列表自动更新流程

- Plamo / Gemini / OpenAI认证后动态获取最新模型列表,未选择时自动设置为首个模型
- LMStudio / Ollama在连接成功时将本地枚举的模型立即反映到选择候选

### VRAM错误检测和自动降级

- 检测翻译处理中的`CUDA out of memory` / `CUBLAS_STATUS_ALLOC_FAILED`等,通过`/run/error_translation_*_vram_overflow`通知
- 自动禁用翻译功能并降级到CTranslate2,再次启用尝试时也会检测VRAM错误并安全解除

### CTranslate2 权重 / Whisper 权重管理

- 下载进度/完成/错误用run端点: `download_progress_ctranslate2_weight`, `downloaded_ctranslate2_weight`, `error_ctranslate2_weight` / Whisper也类似
- 完成时反映`SELECTABLE_CTRANSLATE2_WEIGHT_TYPE_DICT` / `SELECTABLE_WHISPER_WEIGHT_TYPE_DICT`的值更新

### 命名·结构整理

- 翻译引擎选择使用按标签页区分的`SELECTED_TRANSLATION_ENGINES[tab_no]`
- 语言选择结构: 基于`SELECTED_YOUR_LANGUAGES[tab_no]`, `SELECTED_TARGET_LANGUAGES[tab_no]`的嵌套进行引擎适配性判定
- CTranslate2的语言映射对应按权重类型(`CTRANSLATE2_WEIGHT_TYPE`)嵌套的结构

### 语言映射外部化

- `getListLanguageAndCountry()`集成从YAML加载的`translation_lang` / `transcription_lang`,仅提取兼容语言

### API密钥验证的严格化

- Plamo API: 密钥长度判定从"==72"改为">=72",允许72字符以上
- Gemini API: 最小密钥长度从20提高到39
- OpenAI API: 严格要求"sk-"前缀且长度164字符以上,错误消息统一为"无效"

### 翻译模型选择时的应用确保

- OpenAI / Plamo / Gemini / LMStudio / Ollama在模型设置后必定调用`setTranslatorXModel()`和`updateTranslatorXClient()`确保客户端状态反映
- 默认模型自动选择时也立即执行模型应用

### 设备自动选择改进

- 麦克风/扬声器自动选择功能在更新前后设置适当的停止/重启回调链(包括energy检查重启)

### 影响

| 项目 | 内容 |
|------|------|
| 翻译灵活性 | 通过本地LLM (LMStudio/Ollama)实现无需网络的运行 |
| 恢复性 | VRAM错误时自动降级防止异常终止 |
| 可扩展性 | 模型列表自动更新,添加新模型时无需手动更改 |
| 一致性 | 统一的SELECTED_/SELECTABLE_命名和按标签页管理简化UI联动 |
| 可读性 | 外部YAML语言定义减少代码侧硬编码 |

## 主要功能

### 功能控制

- 翻译功能的启用·禁用
- 语音识别功能控制
- VR覆盖层管理
- WebSocket服务器控制

### 配置管理

- 应用程序配置的获取·更新
- 设备配置管理
- 语言·引擎配置控制

### 状态管理

- 系统状态监控
- 错误状态管理
- 初始化过程控制

### 通信控制

- OSC通信管理
- WebSocket通信控制
- 外部应用程序联动

## 类结构

### Controller 类

```python
class Controller:
    def __init__(self) -> None
```

核心控制器类

### 内部辅助类

#### DownloadCTranslate2 类

```python
class DownloadCTranslate2:
    def progressBar(self, progress) -> None
    def downloaded(self) -> None
```

- 翻译模型下载进度管理

#### DownloadWhisper 类

```python
class DownloadWhisper:
    def progressBar(self, progress) -> None
    def downloaded(self) -> None
```

- 语音识别模型下载进度管理

## 主要方法

### 初始化·配置

```python
init() -> None
```

- 控制器初始化
- 各组件启动
- 应用初始配置

```python
setInitMapping(init_mapping: dict) -> None
setRunMapping(run_mapping: dict) -> None
setRun(run: Callable) -> None
```

- 端点·回调配置

### 翻译功能控制

```python
setEnableTranslation(data) -> dict
setDisableTranslation(data) -> dict
```

- 翻译功能的启用·禁用

```python
setSelectedTranslationEngines(data) -> dict
getSelectedTranslationEngines(data) -> dict
```

- 翻译引擎的选择·获取

```python
setSelectedYourLanguages(data) -> dict
setSelectedTargetLanguages(data) -> dict
```

- 发送·接收语言配置

```python
sendMessageBox(data) -> dict
```

- 消息翻译·发送处理

### 语音识别功能控制

```python
setEnableTranscriptionSend(data) -> dict
setEnableTranscriptionReceive(data) -> dict
```

- 语音识别功能启用

```python
setSelectedTranscriptionEngine(data) -> dict
getSelectedTranscriptionEngine(data) -> dict
```

- 语音识别引擎选择·获取

```python
setSelectedMicDevice(data) -> dict
setSelectedSpeakerDevice(data) -> dict
```

- 音频设备选择

```python
setMicThreshold(data) -> dict
setSpeakerThreshold(data) -> dict
```

- 音量阈值设置

### VR覆盖层控制

```python
setEnableOverlaySmallLog(data) -> dict
setEnableOverlayLargeLog(data) -> dict
```

- VR覆盖层启用

```python
setOverlaySmallLogSettings(data) -> dict
setOverlayLargeLogSettings(data) -> dict
```

- 覆盖层配置更新

### WebSocket控制

```python
setEnableWebSocketServer(data) -> dict
setDisableWebSocketServer(data) -> dict
```

- WebSocket服务器控制

```python
setWebSocketHost(data) -> dict
setWebSocketPort(data) -> dict
```

- WebSocket连接配置

### 系统管理

```python
updateSoftware(data) -> dict
updateCudaSoftware(data) -> dict
```

- 软件更新

```python
downloadCtranslate2Weight(data) -> dict
downloadWhisperWeight(data) -> dict
```

- AI模型下载

```python
feedWatchdog(data) -> dict
```

- 看门狗存活信号发送

## 使用方法

### 基本用法

```python
from controller import Controller

# 控制器初始化
controller = Controller()
controller.init()

# 启用翻译功能
result = controller.setEnableTranslation(None)
print(f"翻译功能: {result}")

# 发送消息
message_data = {"id": "123", "message": "Hello World"}
result = controller.sendMessageBox(message_data)
```

### 端点配置

```python
# 映射配置
mapping = {
    "/set/enable/translation": controller.setEnableTranslation,
    "/get/data/version": controller.getVersion,
}

# 执行函数配置
def run_callback(status, endpoint, result):
    print(f"Status: {status}, Endpoint: {endpoint}, Result: {result}")

controller.setRun(run_callback)
```

### 语音识别配置

```python
# 选择麦克风设备
host_data = "DirectSound"
result = controller.setSelectedMicHost(host_data)

device_data = "麦克风 (USB Audio Device)"
result = controller.setSelectedMicDevice(device_data)

# 启动语音识别
result = controller.setEnableTranscriptionSend(None)
```

## 响应格式

所有方法返回统一的响应格式:

```python
{
    "status": int,    # HTTP状态码(200, 400, 500等)
    "result": any     # 处理结果(成功时)或错误消息(失败时)
}
```

### 成功响应示例

```python
{
    "status": 200,
    "result": "翻译功能已启用"
}
```

### 错误响应示例

```python
{
    "status": 400,
    "result": "Invalid device selection"
}
```

## 详细状态管理

### 系统状态

- 各功能的启用·禁用状态
- 设备连接状态
- 网络连接状态

### 错误状态

- 设备错误
- 翻译引擎错误
- VRAM溢出错误

### 初始化状态

- 分阶段初始化过程
- 依赖关系解决状态

## 事件处理

### 语音识别事件

```python
micMessage(result: dict) -> None
```

- 麦克风语音识别结果处理
- 翻译·过滤·发送

```python
speakerMessage(result: dict) -> None
```

- 扬声器语音识别结果处理

### 下载事件

- 进度通知
- 完成通知
- 错误通知

### 设备变更事件

- 麦克风·扬声器选择变更
- 计算设备变更

## 依赖关系

### 直接依赖

- `config`: 配置管理
- `model`: 核心模型功能
- `device_manager`: 设备管理
- `utils`: 工具功能

### 间接依赖

- 各种模型模块(翻译、语音识别等)
- VR覆盖层模块
- 通信模块

## 错误处理

### VRAM不足错误

- 自动切换到CTranslate2
- 向用户适当通知

### 设备错误

- 设备连接状态监控
- 自动恢复功能

### 网络错误

- 连接状态定期确认
- 切换到离线功能

### 配置错误

- 配置值有效性检查
- 恢复到默认值

## 性能考虑事项

### 延迟初始化

- 在需要时初始化功能
- 优化内存使用

### 异步处理

- 后台执行重处理
- 维护UI响应性

### 缓存功能

- 配置值缓存
- 翻译结果缓存

## 注意事项

- 所有方法都是异常安全的
- 配置变更立即反映到config
- 重处理在单独线程执行
- VR功能仅在适当环境下工作
- 网络功能在离线时受限

## 安全考虑事项

- 外部输入的适当验证
- API密钥的安全管理
- 文件访问限制
- 网络通信加密(适用情况下)
