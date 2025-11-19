# config.py 文档

## 概述
`config.py` 是管理应用程序所有配置的单例类 `Config` 模块。负责配置值的读取、保存、验证,并通过防抖功能实现到 JSON 文件的持久化。

## 主要功能
- 通过单例模式统一管理配置
- 从 JSON 文件 (`config.json`) 读取配置并自动保存
- 通过防抖功能优化写入(默认 2 秒)
- 明确分离只读属性和读写属性
- 可选模块的安全导入(安全处理环境依赖)
- 属性 setter 中的类型检查和验证
- 使用 `@json_serializable` 装饰器管理需持久化的属性

## 架构

### 设计模式
- **单例模式**: 通过 `__new__` 方法保证单一实例
- **属性模式**: 通过 getter/setter 实现类型安全的访问控制

### 配置分类
1. **只读配置** (Read Only)
   - 应用程序版本、路径、URL、常量等
   - 仅提供属性(无 setter)

2. **运行时配置** (Read Write)
   - 功能启用/禁用标志
   - 运行时状态管理
   - 不保存到 JSON 的临时配置

3. **持久化配置** (Save Json Data)
   - 用户设置、设备选择、UI 设置等
   - 使用 `@json_serializable` 装饰器标记
   - 通过 `saveConfig()` 自动保存

## 使用方法

### 基本用法

```python
from config import config

# 获取配置值(只读)
version = config.VERSION
app_path = config.PATH_LOCAL

# 获取配置值(读写)
current_tab = config.SELECTED_TAB_NO
mic_threshold = config.MIC_THRESHOLD

# 修改配置值(自动保存)
config.SELECTED_TAB_NO = "2"
config.MIC_THRESHOLD = 500
config.TRANSPARENCY = 80

# 立即保存的情况
config.MAIN_WINDOW_GEOMETRY = {"x_pos": 100, "y_pos": 200, "width": 900, "height": 700}
# MESSAGE_BOX_RATIO 和 MAIN_WINDOW_GEOMETRY 会通过 immediate_save=True 立即保存
```

### 防抖保存机制

```python
# 普通配置修改: 2 秒后保存
config.UI_LANGUAGE = "ja"
config.FONT_FAMILY = "Arial"  # 前一个计时器被取消,重新开始 2 秒计时

# 需要立即保存的配置: 无防抖
config.MESSAGE_BOX_RATIO = 15  # 立即写入文件
```

## 运行环境·依赖关系

### 必需依赖
- Python 3.10 以上(使用 match-case 语法)
- `torch`: 用于判断 CUDA 可用性
- `threading`: 用于防抖计时器

### 可选依赖(带安全机制)
以下模块导入失败也能正常运行:
- `device_manager`: 设备管理(麦克风/扬声器)
- `models.translation.translation_languages`: 翻译语言列表
- `models.translation.translation_utils`: CTranslate2 权重列表
- `models.transcription.transcription_languages`: 语音识别语言列表
- `models.transcription.transcription_whisper`: Whisper 模型列表

### 项目内依赖
- `utils`: 错误日志、字典结构验证、计算设备列表获取

## 文件结构

### 主要类: `Config`

#### 类属性
```python
_instance: Config | None  # 单例实例
_config_data: Dict[str, Any]  # JSON 保存数据
_timer: Optional[threading.Timer]  # 防抖计时器
_debounce_time: int = 2  # 防抖时间(秒)
```

#### 主要方法

**初始化·保存**
- `__new__(cls)`: 生成单例实例·初始化
- `init_config()`: 设置默认值
- `load_config()`: 从 JSON 文件读取配置
- `saveConfig(key, value, immediate_save=False)`: 保存配置(带防抖)
- `saveConfigToFile()`: 立即写入 JSON 文件

**装饰器**
- `@json_serializable(var_name)`: 标记需持久化的属性

### 配置属性列表

#### 只读配置(23 项)

| 属性名 | 类型 | 说明 | 默认值 |
|------------|----|----|------------|
| `VERSION` | str | 应用程序版本 | "3.3.0" |
| `PATH_LOCAL` | str | 应用程序本地路径 | 运行时确定 |
| `PATH_CONFIG` | str | 配置文件路径 | `{PATH_LOCAL}/config.json` |
| `PATH_LOGS` | str | 日志目录路径 | `{PATH_LOCAL}/logs` |
| `GITHUB_URL` | str | GitHub API URL | 仓库 URL |
| `UPDATER_URL` | str | 更新程序 API 的 URL | 更新程序 URL |
| `BOOTH_URL` | str | Booth 销售页面 URL | Booth URL |
| `DOCUMENTS_URL` | str | 文档 URL | Notion URL |
| `DEEPL_AUTH_KEY_PAGE_URL` | str | DeepL 认证密钥获取页面 | DeepL URL |
| `MAX_MIC_THRESHOLD` | int | 麦克风阈值最大值 | 2000 |
| `MAX_SPEAKER_THRESHOLD` | int | 扬声器阈值最大值 | 4000 |
| `WATCHDOG_TIMEOUT` | int | Watchdog 超时时间(秒) | 60 |
| `WATCHDOG_INTERVAL` | int | Watchdog 检查间隔(秒) | 20 |
| `SELECTABLE_TAB_NO_LIST` | List[str] | 可选标签页号 | ["1", "2", "3"] |
| `SELECTED_TAB_TARGET_LANGUAGES_NO_LIST` | List[str] | 目标语言标签页号 | ["1", "2", "3"] |
| `SELECTABLE_CTRANSLATE2_WEIGHT_TYPE_LIST` | List[str] | CTranslate2 权重类型列表 | 动态获取 |
| `SELECTABLE_WHISPER_WEIGHT_TYPE_LIST` | List[str] | Whisper 权重类型列表 | 动态获取 |
| `SELECTABLE_TRANSLATION_ENGINE_LIST` | List[str] | 翻译引擎列表 | 动态获取 |
| `SELECTABLE_TRANSCRIPTION_ENGINE_LIST` | List[str] | 语音识别引擎列表 | 动态获取 |
| `SELECTABLE_UI_LANGUAGE_LIST` | List[str] | UI 语言列表 | ["en", "ja", "ko", "zh-Hant", "zh-Hans"] |
| `COMPUTE_MODE` | str | 计算模式 | "cuda" or "cpu" |
| `SELECTABLE_COMPUTE_DEVICE_LIST` | List[Dict] | 可选计算设备列表 | 动态获取 |
| `SEND_MESSAGE_BUTTON_TYPE_LIST` | List[str] | 发送按钮类型列表 | ["show", "hide", "show_and_disable_enter_key"] |

#### 运行时配置(10 项)

| 属性名 | 类型 | 说明 | 默认值 | JSON 保存 |
|------------|----|----|-----------|---------|
| `ENABLE_TRANSLATION` | bool | 翻译功能启用标志 | False | 否 |
| `ENABLE_TRANSCRIPTION_SEND` | bool | 发送语音识别启用标志 | False | 否 |
| `ENABLE_TRANSCRIPTION_RECEIVE` | bool | 接收语音识别启用标志 | False | 否 |
| `ENABLE_FOREGROUND` | bool | 前台启用标志 | False | 否 |
| `ENABLE_CHECK_ENERGY_SEND` | bool | 发送能量检查启用 | False | 否 |
| `ENABLE_CHECK_ENERGY_RECEIVE` | bool | 接收能量检查启用 | False | 否 |
| `SELECTABLE_CTRANSLATE2_WEIGHT_TYPE_DICT` | Dict[str, bool] | CTranslate2 权重状态字典 | {} | 否 |
| `SELECTABLE_WHISPER_WEIGHT_TYPE_DICT` | Dict[str, bool] | Whisper 权重状态字典 | {} | 否 |
| `SELECTABLE_TRANSLATION_ENGINE_STATUS` | Dict[str, bool] | 翻译引擎状态字典 | {} | 否 |
| `SELECTABLE_TRANSCRIPTION_ENGINE_STATUS` | Dict[str, bool] | 语音识别引擎状态字典 | {} | 否 |

#### 持久化配置(60 项以上)

**主窗口设置**
- `SELECTED_TAB_NO`: 当前选中的标签页号
- `SELECTED_TRANSLATION_ENGINES`: 每个标签页的翻译引擎选择
- `SELECTED_YOUR_LANGUAGES`: 每个标签页的输入语言设置
- `SELECTED_TARGET_LANGUAGES`: 每个标签页的目标语言设置
- `SELECTED_TRANSCRIPTION_ENGINE`: 语音识别引擎
- `CONVERT_MESSAGE_TO_ROMAJI`: 罗马字转换启用标志
- `CONVERT_MESSAGE_TO_HIRAGANA`: 平假名转换启用标志
- `MAIN_WINDOW_SIDEBAR_COMPACT_MODE`: 侧边栏紧凑模式
- `SEND_MESSAGE_FORMAT_PARTS`: 发送消息格式
- `RECEIVED_MESSAGE_FORMAT_PARTS`: 接收消息格式

**UI 窗口设置**
- `TRANSPARENCY`: 窗口透明度(0-100)
- `UI_SCALING`: UI 缩放(%)
- `TEXTBOX_UI_SCALING`: 文本框缩放(%)
- `MESSAGE_BOX_RATIO`: 消息框比例(立即保存)
- `SEND_MESSAGE_BUTTON_TYPE`: 发送按钮类型
- `SHOW_RESEND_BUTTON`: 重新发送按钮显示标志
- `FONT_FAMILY`: 字体系列
- `UI_LANGUAGE`: UI 语言
- `MAIN_WINDOW_GEOMETRY`: 窗口位置·大小(立即保存)

**麦克风设置**
- `AUTO_MIC_SELECT`: 自动麦克风选择
- `SELECTED_MIC_HOST`: 已选麦克风主机
- `SELECTED_MIC_DEVICE`: 已选麦克风设备
- `MIC_THRESHOLD`: 麦克风阈值
- `MIC_AUTOMATIC_THRESHOLD`: 自动阈值调整
- `MIC_RECORD_TIMEOUT`: 录音超时时间(秒)
- `MIC_PHRASE_TIMEOUT`: 短语超时时间(秒)
- `MIC_MAX_PHRASES`: 最大短语数
- `MIC_WORD_FILTER`: 词语过滤器列表
- `MIC_AVG_LOGPROB`: 平均对数概率阈值
- `MIC_NO_SPEECH_PROB`: 无语音概率阈值

**扬声器设置**
- `AUTO_SPEAKER_SELECT`: 自动扬声器选择
- `SELECTED_SPEAKER_DEVICE`: 已选扬声器设备
- `SPEAKER_THRESHOLD`: 扬声器阈值
- `SPEAKER_AUTOMATIC_THRESHOLD`: 自动阈值调整
- `SPEAKER_RECORD_TIMEOUT`: 录音超时时间(秒)
- `SPEAKER_PHRASE_TIMEOUT`: 短语超时时间(秒)
- `SPEAKER_MAX_PHRASES`: 最大短语数
- `SPEAKER_AVG_LOGPROB`: 平均对数概率阈值
- `SPEAKER_NO_SPEECH_PROB`: 无语音概率阈值

**模型设置**
- `SELECTED_TRANSLATION_COMPUTE_DEVICE`: 翻译计算设备
- `SELECTED_TRANSCRIPTION_COMPUTE_DEVICE`: 语音识别计算设备
- `CTRANSLATE2_WEIGHT_TYPE`: CTranslate2 权重类型
- `SELECTED_TRANSLATION_COMPUTE_TYPE`: 翻译计算类型
- `WHISPER_WEIGHT_TYPE`: Whisper 权重类型
- `SELECTED_TRANSCRIPTION_COMPUTE_TYPE`: 语音识别计算类型

**通信设置**
- `OSC_IP_ADDRESS`: OSC IP 地址(默认: "127.0.0.1")
- `OSC_PORT`: OSC 端口(默认: 9000)
- `AUTH_KEYS`: 认证密钥字典(DeepL API 等)
- `WEBSOCKET_HOST`: WebSocket 主机
- `WEBSOCKET_PORT`: WebSocket 端口
- `WEBSOCKET_SERVER`: WebSocket 服务器启用标志(非持久化)

**覆盖层设置**
- `OVERLAY_SMALL_LOG`: 小日志覆盖层启用
- `OVERLAY_SMALL_LOG_SETTINGS`: 小日志覆盖层设置(位置、旋转、显示时间等)
- `OVERLAY_LARGE_LOG`: 大日志覆盖层启用
- `OVERLAY_LARGE_LOG_SETTINGS`: 大日志覆盖层设置
- `OVERLAY_SHOW_ONLY_TRANSLATED_MESSAGES`: 仅显示翻译消息

**其他设置**
- `HOTKEYS`: 热键设置字典(立即保存)
- `PLUGINS_STATUS`: 插件状态列表(立即保存)
- `USE_EXCLUDE_WORDS`: 使用排除词功能标志
- `AUTO_CLEAR_MESSAGE_BOX`: 自动清除消息框
- `SEND_ONLY_TRANSLATED_MESSAGES`: 仅发送翻译消息
- `SEND_MESSAGE_TO_VRC`: 向 VRChat 发送消息
- `SEND_RECEIVED_MESSAGE_TO_VRC`: 将接收的消息发送到 VRChat
- `LOGGER_FEATURE`: 日志记录功能启用
- `VRC_MIC_MUTE_SYNC`: VRChat 麦克风静音同步
- `NOTIFICATION_VRC_SFX`: VRChat 通知音效

## 内部实现细节

### 防抖保存的实现

```python
def saveConfig(self, key: str, value: Any, immediate_save: bool = False) -> None:
    self._config_data[key] = value

    # 取消现有计时器
    if isinstance(self._timer, threading.Timer) and self._timer.is_alive():
        self._timer.cancel()

    if immediate_save:
        self.saveConfigToFile()
    else:
        # 设置 2 秒后保存的计时器
        self._timer = threading.Timer(self._debounce_time, self.saveConfigToFile)
        self._timer.daemon = True
        self._timer.start()
```

### 属性验证示例

```python
@SELECTED_TAB_NO.setter
def SELECTED_TAB_NO(self, value):
    if isinstance(value, str):
        if value in self.SELECTABLE_TAB_NO_LIST:
            self._SELECTED_TAB_NO = value
            self.saveConfig(inspect.currentframe().f_code.co_name, value)
```

每个 setter 都实现以下模式:
1. 类型检查 (`isinstance`)
2. 值的范围·有效性检查
3. 赋值给内部变量
4. 调用 `saveConfig`(如果是持久化对象)

### 消息格式结构

```python
{
    "message": {
        "prefix": "",  # 消息前缀字符串
        "suffix": ""   # 消息后缀字符串
    },
    "separator": "\n",  # 消息和翻译的分隔符
    "translation": {
        "prefix": "",      # 翻译前缀字符串
        "separator": "\n", # 多个翻译的分隔符
        "suffix": ""       # 翻译后缀字符串
    },
    "translation_first": False  # 是否先显示翻译
}
```

### 覆盖层设置结构

```python
{
    "x_pos": 0.0,          # X 坐标
    "y_pos": 0.0,          # Y 坐标
    "z_pos": 0.0,          # Z 坐标
    "x_rotation": 0.0,     # X 轴旋转
    "y_rotation": 0.0,     # Y 轴旋转
    "z_rotation": 0.0,     # Z 轴旋转
    "display_duration": 5, # 显示时间(秒)
    "fadeout_duration": 2, # 淡出时间(秒)
    "opacity": 1.0,        # 不透明度(0.0-1.0)
    "ui_scaling": 1.0,     # UI 缩放
    "tracker": "HMD"       # 追踪器 ("HMD", "LeftHand", "RightHand")
}
```

## 错误处理

### 安全导入
```python
try:
    from device_manager import device_manager
except Exception:
    device_manager = None  # 回退值
```

所有外部模块导入都用 try-except 包装,导入失败时 `Config` 类仍能正常运行。

### 初始化错误
```python
def __new__(cls):
    if cls._instance is None:
        cls._instance = super(Config, cls).__new__(cls)
        try:
            cls._instance.init_config()
        except Exception:
            errorLogging()  # 将错误记录到日志
        try:
            cls._instance.load_config()
        except Exception:
            errorLogging()
    return cls._instance
```

初始化和加载处理分别独立进行错误处理。

### 配置加载时的错误
```python
for key, value in self._config_data.items():
    try:
        setattr(self, key, value)
    except Exception:
        errorLogging()  # 即使个别配置读取失败也继续
```

从 JSON 读取的配置中,即使有非法值也会继续读取其他配置。

## 性能考虑

1. **防抖保存**: 频繁配置修改时减少 I/O
2. **延迟初始化**: 可选模块仅在需要时加载
3. **单例**: 防止配置对象复制
4. **守护线程**: 计时器线程在主线程结束时自动结束

## 安全考虑

1. **认证密钥**: 存储在 `AUTH_KEYS` 中的外部 API 密钥以明文保存在 JSON 中
2. **路径验证**: IP 地址通过 `isValidIpAddress` 进行验证
3. **类型安全**: 所有 setter 都执行类型检查

## 测试建议

### 单元测试
```python
def test_config_singleton():
    config1 = Config()
    config2 = Config()
    assert config1 is config2

def test_debounce_save():
    config.UI_LANGUAGE = "ja"
    time.sleep(1)
    config.UI_LANGUAGE = "en"
    # 2 秒内的修改只保存一次
    time.sleep(2.5)
    # 这里保存完成
```

### 验证测试
```python
def test_invalid_tab_no():
    config.SELECTED_TAB_NO = "invalid"  # 被忽略
    assert config.SELECTED_TAB_NO != "invalid"
```

### 可选依赖测试
```python
def test_missing_device_manager():
    # 即使 device_manager 为 None 也能运行
    assert config.SELECTABLE_COMPUTE_DEVICE_LIST is not None
```

## 迁移

### 配置文件版本升级
`load_config()` 会忽略不存在的键,使用 `init_config()` 的默认值。新版本添加键时:

1. 现有键从 JSON 读取
2. 新键使用 `init_config()` 的默认值
3. 下次保存时所有键都会写入 JSON

## 限制

1. **多进程**: 单例是按进程的。多进程环境中每个进程都有独立实例
2. **线程安全**: 属性访问本身不是线程安全的(仅保存计时器是线程对应的)
3. **循环引用**: 注意 `device_manager` 和 `config` 之间的循环引用
4. **JSON 限制**: 只能保存可序列化为 JSON 的类型

## 许可证
参阅项目根目录中的 `LICENSE` 文件

## 相关文档
- `controller.md`: Controller 类的配置使用方法
- `mainloop.md`: 主循环中的配置引用
- `仕様書.md`: 整体规格
- `設計書.md`: 系统设计

## 更改历史

### v3.3.0
- 当前版本
- 添加 WebSocket 服务器配置
- 扩展覆盖层设置
