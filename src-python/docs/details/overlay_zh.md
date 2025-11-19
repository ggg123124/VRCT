# overlay - VR覆盖层集成系统

## 概述

面向VRChat的OpenVR覆盖层系统。提供在VR空间内显示翻译结果和字幕的功能,集成管理HMD·控制器跟踪、淡入淡出效果、多语言字体支持。

## 主要组件

### overlay.py - 主覆盖层管理
- OpenVR覆盖层的生成·配置·控制
- HMD·左手·右手跟踪设置
- 淡入淡出效果

### overlay_image.py - 图像生成·绘制
- 多语言文本图像生成
- 消息日志·历史显示
- 字体·布局管理

### overlay_utils.py - 数学变换工具
- 3D坐标变换矩阵计算
- 欧拉角·旋转矩阵转换
- 齐次坐标系变换

## 类结构

### Overlay 类 (overlay.py)

```python
class Overlay:
    def __init__(self, settings_dict: Dict[str, Dict[str, Any]]) -> None:
        self.system: Optional[Any] = None          # OpenVR系统
        self.overlay: Optional[Any] = None         # 覆盖层接口
        self.handle: Dict[str, Any] = {}           # 按尺寸分类的句柄
        self.settings: Dict[str, Dict[str, Any]]   # 按尺寸分类的设置
        self.lastUpdate: Dict[str, float] = {}     # 最后更新时间
        self.fadeRatio: Dict[str, float] = {}      # 淡入淡出比率
```

VR覆盖层综合管理类

#### 主要功能
- OpenVR初始化·管理
- 同时管理多个尺寸覆盖层
- 实时淡入淡出效果处理
- SteamVR连接状态监控

### OverlayImage 类 (overlay_image.py)

```python
class OverlayImage:
    LANGUAGES = {
        "Default": "NotoSansJP-Regular.ttf",
        "Japanese": "NotoSansJP-Regular.ttf",
        "Korean": "NotoSansKR-Regular.ttf",
        "Chinese Simplified": "NotoSansSC-Regular.ttf",
        "Chinese Traditional": "NotoSansTC-Regular.ttf"
    }
    
    def __init__(self, root_path: Optional[str] = None) -> None:
        self.message_log: List[dict] = []
        self.root_path: str
```

文本图像生成·多语言字体管理类

#### 主要功能
- 多语言字体自动选择
- 消息历史管理
- 动态图像生成·合成
- UI元素尺寸计算

## 主要方法

### Overlay 类

#### 初始化·控制

```python
def startOverlay(self) -> None
```

启动覆盖层系统

```python
def shutdownOverlay(self) -> None
```

终止覆盖层系统·释放资源

```python
def reStartOverlay(self) -> None
```

重启覆盖层系统

#### 显示控制

```python
def showOverlay(self, image: Image, size: str) -> None
```

在覆盖层显示图像

#### 参数
- **image**: 要显示的PIL图像
- **size**: 覆盖层尺寸标识符

```python
def setOpacity(self, opacity: float, size: str) -> None
```

设置覆盖层透明度

#### 参数
- **opacity**: 透明度(0.0-1.0)
- **size**: 目标尺寸

```python
def setTrackedDeviceRelative(self, tracker: str, size: str) -> None
```

将覆盖层放置到跟踪设备

#### 参数
- **tracker**: 跟踪设备("HMD", "LeftHand", "RightHand")
- **size**: 覆盖层尺寸

### OverlayImage 类

#### 图像生成

```python
def createOverlayImage(self, message: str, language: str, ui_size: dict,
                      ui_settings: dict, message_log_settings: dict) -> Image
```

生成覆盖层用图像

#### 参数
- **message**: 显示消息
- **language**: 语言设置
- **ui_size**: UI尺寸设置
- **ui_settings**: UI显示设置
- **message_log_settings**: 日志显示设置

#### 返回值
- **Image**: 生成的PIL图像

#### 历史管理

```python
def addMessageLog(self, message: str, timestamp: datetime) -> None
```

向消息日志添加新内容

#### 参数
- **message**: 要添加的消息
- **timestamp**: 时间戳

```python
def clearMessageLog(self) -> None
```

清除消息日志

## 使用方法

### 基本覆盖层显示

```python
from models.overlay.overlay import Overlay
from models.overlay.overlay_image import OverlayImage
from PIL import Image

# 覆盖层设置
settings = {
    "small": {
        "width": 0.3,
        "height": 0.1,
        "x_pos": 0.0,
        "y_pos": -0.2,
        "z_pos": 1.0,
        "opacity": 0.8,
        "display_duration": 3.0,
        "fadeout_duration": 1.0
    },
    "large": {
        "width": 0.5,
        "height": 0.2,
        "x_pos": 0.0,
        "y_pos": -0.3,
        "z_pos": 1.2,
        "opacity": 0.9,
        "display_duration": 5.0,
        "fadeout_duration": 1.5
    }
}

# 覆盖层系统初始化
overlay_system = Overlay(settings)
overlay_image = OverlayImage()

# 启动系统
overlay_system.startOverlay()

# 翻译结果显示
translation_text = "Hello, world! / 你好,世界!"

# 图像生成设置
ui_size = OverlayImage.getUiSizeSmallLog()
ui_settings = {
    "font_size": 20,
    "text_color": (255, 255, 255, 255),
    "background_color": (0, 0, 0, 180)
}
message_log_settings = {
    "enabled": True,
    "max_lines": 5
}

# 图像生成·显示
overlay_img = overlay_image.createOverlayImage(
    message=translation_text,
    language="Japanese",
    ui_size=ui_size,
    ui_settings=ui_settings,
    message_log_settings=message_log_settings
)

# 在覆盖层显示
overlay_system.showOverlay(overlay_img, "small")

# 终止系统
import time
time.sleep(10)
overlay_system.shutdownOverlay()
```

### HMD·控制器跟踪设置

```python
# 固定显示到HMD
overlay_system.setTrackedDeviceRelative("HMD", "large")

# 跟随左手控制器
overlay_system.setTrackedDeviceRelative("LeftHand", "small")

# 跟随右手控制器
overlay_system.setTrackedDeviceRelative("RightHand", "small")

# 位置·旋转微调(设置变更)
overlay_system.settings["small"]["x_pos"] = 0.1
overlay_system.settings["small"]["y_pos"] = -0.1
overlay_system.settings["small"]["z_pos"] = 0.8
overlay_system.settings["small"]["x_rotation"] = -30.0
overlay_system.settings["small"]["y_rotation"] = 15.0

# 应用设置
overlay_system.setTrackedDeviceRelative("LeftHand", "small")
```

## 依赖关系·系统要求

### 必需依赖
- `openvr`: OpenVR Python绑定
- `numpy`: 数值计算·矩阵运算
- `PIL (Pillow)`: 图像处理·生成
- `psutil`: 进程监控

### 系统要求
```python
system_requirements = {
    "steamvr": "必需SteamVR环境",
    "openvr_runtime": "OpenVR Runtime",
    "vr_headset": "支持的VR头显(Oculus, Vive, Index等)",
    "graphics": "VR支持的GPU",
    "python": "Python 3.7以上"
}

performance_requirements = {
    "cpu": "VR处理所需的充足CPU性能",
    "memory": "额外内存使用量 ~100-500MB",
    "disk_space": "字体文件所需容量 ~50MB"
}
```

### 可选依赖
- `utils.errorLogging`: 错误日志功能(有降级处理)

## 注意事项·限制

### VR环境限制
- SteamVR未启动时无法运行
- VR头显未连接时有限制
- 依赖OpenVR驱动程序兼容性

### 性能限制
- 实时绘制处理导致CPU·GPU负载
- 字体渲染导致内存使用增加
- 高分辨率VR显示器的绘制负载

## 相关模块

- `config.py`: 覆盖层配置管理
- `controller.py`: 覆盖层控制接口
- `model.py`: 覆盖层功能集成
- `utils.py`: 错误日志·工具

## 最近更新 (2025-10-20)

### 字体搜索规范强化

在`overlay_image.py`中添加了PyInstaller构建后的`_internal/fonts/`目录检测逻辑。按以下优先顺序搜索字体目录:

1. `root_path/_internal/fonts/` (PyInstaller打包环境)
2. `src-python/models/overlay/fonts/` (开发环境相对路径)
3. `models/overlay/fonts/` (直接执行时)

未找到时通过`FileNotFoundError`早期通知。这样可在分发二进制文件和开发环境中维持相同代码路径。

### 影响

| 项目 | 内容 |
|------|------|
| PyInstaller对应 | 防止打包后字体加载失败 |
| 可移植性 | 通过代码内条件分支吸收环境差异 |
| 错误检测 | 字体未配置时通过早期异常防止不正确绘制 |

## 未来改进点

- 支持更丰富的UI元素
- 动画·特效功能
- 自定义字体·主题系统
- 性能监控·自动优化
- 考虑支持其他VR平台
