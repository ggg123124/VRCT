# config.py - 配置管理模块

## 概述

VRCT应用程序的全配置统一管理模块。采用单例模式,为整个应用程序提供统一的配置访问。提供JSON配置文件的读写、配置持久化以及带防抖功能的保存功能。

## 主要功能

### 单例设计
- 应用程序全局唯一配置实例
- 线程安全的配置访问
- 延迟初始化实现轻量级导入

### 配置持久化
- JSON格式配置文件管理
- 带防抖功能的自动保存
- 配置变更的即时反映

### 动态配置管理
- 运行时配置变更支持
- 设备信息动态获取
- 语言和引擎配置自动更新

### 类型安全的配置访问
- 基于属性的访问控制
- 只读和读写配置分离
- 通过装饰器管理序列化

## 类结构

### Config 类
```python
class Config:
    _instance = None              # 单例实例
    _config_data: Dict[str, Any]  # 配置数据
    _timer: Optional[threading.Timer]  # 防抖定时器
    _debounce_time: int = 2       # 防抖时间(秒)
```

## 配置分类

### 只读配置

```python
@property
def VERSION(self) -> str
```
- 应用程序版本

```python  
@property
def PATH_LOCAL(self) -> str
```
- 本地目录路径

```python
@property
def PATH_CONFIG(self) -> str
```
- 配置文件路径

### UI·显示配置

```python
@property
def UI_LANGUAGE(self) -> str
```
- UI显示语言

```python
@property  
def TRANSPARENCY(self) -> int
```
- 窗口透明度(0-100)

```python
@property
def UI_SCALING(self) -> int
```
- UI缩放(50-200%)

```python
@property
def FONT_FAMILY(self) -> str
```
- 使用的字体系列

### 翻译配置

```python
@property
def ENABLE_TRANSLATION(self) -> bool
```
- 翻译功能的启用/禁用

```python
@property
def SELECTED_TRANSLATION_ENGINES(self) -> Dict[str, str]
```
- 已选择的翻译引擎

```python
@property
def SELECTED_YOUR_LANGUAGES(self) -> Dict[str, Dict[str, Any]]
```
- 发送语言配置

```python
@property
def SELECTED_TARGET_LANGUAGES(self) -> Dict[str, Dict[str, Any]]
```
- 接收语言配置

### 语音识别配置

```python
@property
def ENABLE_TRANSCRIPTION_SEND(self) -> bool
```
- 发送语音识别的启用/禁用

```python
@property
def SELECTED_TRANSCRIPTION_ENGINE(self) -> str
```
- 语音识别引擎

```python
@property
def SELECTED_MIC_DEVICE(self) -> str
```
- 已选择的麦克风设备

```python
@property
def MIC_THRESHOLD(self) -> int
```
- 麦克风音量阈值

```python
@property
def MIC_RECORD_TIMEOUT(self) -> int
```
- 麦克风录音超时时间(秒)

### VR配置

```python
@property
def OVERLAY_SMALL_LOG(self) -> bool
```
- 小型日志覆盖层的启用/禁用

```python
@property
def OVERLAY_SMALL_LOG_SETTINGS(self) -> Dict[str, Any]
```
- 小型覆盖层详细配置

```python
@property
def OVERLAY_LARGE_LOG_SETTINGS(self) -> Dict[str, Any]
```
- 大型覆盖层详细配置

### 通信配置

```python
@property
def OSC_IP_ADDRESS(self) -> str
```
- OSC通信IP地址

```python
@property
def OSC_PORT(self) -> int
```
- OSC通信端口

```python
@property
def WEBSOCKET_HOST(self) -> str
```
- WebSocket服务器主机

```python
@property
def WEBSOCKET_PORT(self) -> int
```
- WebSocket服务器端口

### 计算设备配置

```python
@property
def SELECTED_TRANSLATION_COMPUTE_DEVICE(self) -> Dict[str, Any]
```
- 翻译用计算设备

```python
@property
def SELECTED_TRANSCRIPTION_COMPUTE_DEVICE(self) -> Dict[str, Any]
```
- 语音识别用计算设备

## 主要方法

### 配置保存

```python
saveConfig(key: str, value: Any, immediate_save: bool = False) -> None
```
- 配置值保存(带防抖)
- immediate_save=True时立即保存

```python
saveConfigToFile() -> None
```
- 直接保存到配置文件

### 初始化·配置加载

```python
init_config() -> None
```
- 配置初始化
- 设置默认值

```python
load_config() -> None
```
- 从配置文件加载
- 不存在时创建默认配置

## 装饰器功能

### @json_serializable
```python
@json_serializable("setting_name")
@property
def SETTING_NAME(self) -> Any:
```
- 指定配置的JSON序列化对象
- 自动定义保存到config.json的配置

## 使用方法

### 基本用法

```python
from config import config

# 获取配置值
version = config.VERSION
ui_language = config.UI_LANGUAGE
translation_enabled = config.ENABLE_TRANSLATION

# 修改配置值
config.UI_LANGUAGE = "ja"
config.TRANSPARENCY = 80
config.MIC_THRESHOLD = 1500
```

### 复杂配置的修改

```python
# 翻译引擎配置
engines = config.SELECTED_TRANSLATION_ENGINES
engines["1"] = "DeepL"
config.SELECTED_TRANSLATION_ENGINES = engines

# 覆盖层配置修改
overlay_settings = config.OVERLAY_SMALL_LOG_SETTINGS
overlay_settings["x_pos"] = 0.5
overlay_settings["opacity"] = 0.8
config.OVERLAY_SMALL_LOG_SETTINGS = overlay_settings
```

### 立即保存

```python
# 重要配置变更时立即保存
config.saveConfig("ENABLE_TRANSLATION", True, immediate_save=True)
```

## 配置文件格式

配置以JSON格式保存在`config.json`文件中:

```json
{
    "UI_LANGUAGE": "ja",
    "TRANSPARENCY": 85,
    "UI_SCALING": 100,
    "ENABLE_TRANSLATION": true,
    "SELECTED_TRANSLATION_ENGINES": {
        "1": "DeepL",
        "2": "Google",
        "3": "CTranslate2"
    },
    "OVERLAY_SMALL_LOG_SETTINGS": {
        "x_pos": 0.0,
        "y_pos": -0.4,
        "z_pos": 1.0,
        "opacity": 1.0,
        "ui_scaling": 1.0,
        "display_duration": 5,
        "fadeout_duration": 1
    }
}
```

## 默认配置

### UI配置
- UI语言: "en"(英语)
- 透明度: 85%
- UI缩放: 100%
- 字体: "Noto Sans JP"

### 翻译配置
- 翻译功能: 禁用
- 默认引擎: "Google"
- 发送语言: English(US)
- 接收语言: 日语

### 语音识别配置
- 发送语音识别: 禁用
- 接收语音识别: 禁用
- 语音识别引擎: "Google"
- 麦克风阈值: 300

### VR配置
- 小型覆盖层: 禁用
- 大型覆盖层: 禁用
- 覆盖层位置: HMD正前方

### 通信配置
- OSC IP: "127.0.0.1"
- OSC 端口: 9000
- WebSocket 主机: "127.0.0.1"
- WebSocket 端口: 8765

## 依赖关系

### 必需依赖
- `json`: 配置文件序列化
- `threading`: 防抖功能
- `typing`: 类型注解

### 可选依赖
- `device_manager`: 设备信息获取
- `torch`: CUDA计算设备信息
- 各种模型模块: 语言·引擎信息

## 错误处理

- 配置文件读取错误的适当处理
- 无效配置值的验证·校正
- 可选依赖缺失时的降级处理
- 文件写入错误处理

## 性能特性

### 防抖功能
- 配置变更2秒后自动保存
- 连续变更的合并
- 减轻I/O负载

### 延迟初始化
- 重依赖的延迟加载
- 缩短导入时间

### 内存效率
- 配置数据的单例管理
- 防止不必要的复制

## 注意事项

- 配置变更立即反映到内存
- 文件保存通过防抖功能延迟
- 重要配置使用immediate_save=True
- 可选依赖缺失时使用默认值
- 无效配置值会自动校正
- 配置文件损坏时会创建新文件

## 安全考虑事项

- 配置文件的适当权限管理
- 外部输入值验证
- API密钥等机密信息的适当处理
- 防止路径注入攻击

## 最近更新 (2025-10-20)

### LMStudio / Ollama 本地 LLM 配置属性添加

- `LMSTUDIO_URL` / `SELECTABLE_LMSTUDIO_MODEL_LIST` / `SELECTED_LMSTUDIO_MODEL`
- `SELECTABLE_OLLAMA_MODEL_LIST` / `SELECTED_OLLAMA_MODEL`

添加了本地推理引擎连接用URL和动态模型列表获取·选择属性。不需要认证,连接测试后自动更新模型列表。

### 模型选择属性命名统一

将Plamo / Gemini / OpenAI的选择模型从`PLAMO_MODEL` / `GEMINI_MODEL` / `OPENAI_MODEL`统一为`SELECTED_PLAMO_MODEL` / `SELECTED_GEMINI_MODEL` / `SELECTED_OPENAI_MODEL`。配置JSON的保存键也更改为`SELECTED_*`,确保与UI的一致性。

### CTranslate2 语言映射结构变更对应

`translation_lang`内的CTranslate2语言字典嵌套为`translation_lang["CTranslate2"][weight_type]["source"|"target"]`结构。`CTRANSLATE2_WEIGHT_TYPE`属性成为访问的键,因此权重类型变更时需要重新初始化翻译引擎。

### YAML 语言外部定义引入

初始化时调用`loadTranslationLanguages()`,读取`models/translation/languages/languages.yml`并合并到现有映射。失败时使用空字典降级。无需代码修改即可动态添加语言,因此配置初始化的失败日志确认很重要。

### OpenAI 模型列表自动更新

`setOpenAIAuthKey()`成功后获取`SELECTABLE_OPENAI_MODEL_LIST`,未选择时自动选择首个。Gemini / Plamo / LMStudio / Ollama也同样在认证/连接建立时更新列表并补充未选择的模型。

### 字体配置的打包对应

在`overlay_image.py`中添加PyInstaller构建环境(`_internal/fonts/`)检测。开发环境和打包后的字体搜索路径不同,因此`FONT_FAMILY`保持基于文件名的标准不变。

### 依赖关系添加

- `PyYAML`: 语言映射YAML读取
- `google-genai`: Gemini集成
- `grpcio`: OpenAI集成(流式传输等)

### VRAM 错误时的自动降级

翻译启用或翻译执行时检测到VRAM不足,将`ENABLE_TRANSLATION`设为False并强制切换到CTranslate2。配置值会保留,但会向UI通知禁用状态。再次启用请求时尝试重新初始化重模型。

### 测试相关

通过全面的翻译对测试,大量执行`SELECTED_*`模型和语言映射组合。随着配置值变更频率增加,通过2秒防抖抑制文件写入负载。

### 影响总结

| 项目 | 内容 |
|------|------|
| 本地LLM | 通过LMStudio / Ollama的引入扩展离线翻译 |
| 属性统一 | SELECTED_* 命名提高一致性·文档整备性 |
| 语言嵌套化 | CTranslate2权重类型切换处理的重新初始化必要性增加 |
| YAML外部化 | 仅通过配置初始化即可反映语言添加 |
| 模型列表自动更新 | 认证后防止选择错误·改善首次UX |
| 字体搜索 | PyInstaller构建后也能用同一代码运行 |
| 依赖添加 | 对应新功能,环境构建步骤增加 |
| VRAM检测 | 通过安全停止和轻量引擎切换提高稳定性 |
| 测试增强 | 通过大量对验证提高语言/模型配置的可靠性 |
