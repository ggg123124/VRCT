# transcription_recorder.py - 音频录制接口

## 概述

录制作为语音识别系统输入的音频数据的录音器类群。支持麦克风和扬声器输出,与能量级别监控功能一起将音频数据发送到队列。使用pyaudiowpatch库与Windows音频系统集成。

## 主要功能

### 音频录制功能
- 从麦克风录制音频
- 录制扬声器输出(回环)
- 实时音频数据队列

### 能量监控
- 监控音频能量级别
- 动态阈值调整
- 静音检测

### 设备支持
- 支持多个音频设备
- 设备特定配置管理
- 自动设备选择

## 类结构

### BaseRecorder 类
```python
class BaseRecorder:
    def __init__(self, source: Any, energy_threshold: int, dynamic_energy_threshold: bool, record_timeout: int)
```

基础录音器类 - 提供共同功能

### SelectedMicRecorder 类
```python
class SelectedMicRecorder(BaseRecorder):
    def __init__(self, device: dict, energy_threshold: int, dynamic_energy_threshold: bool, record_timeout: int)
```

从选定的麦克风设备录音

### SelectedSpeakerRecorder 类
```python
class SelectedSpeakerRecorder(BaseRecorder):
    def __init__(self, device: dict, energy_threshold: int, dynamic_energy_threshold: bool, record_timeout: int)
```

从选定的扬声器设备录音(回环)

### 能量监控类群

#### BaseEnergyRecorder 类
```python
class BaseEnergyRecorder:
    def __init__(self, source: Any)
```

能量级别监控的基类

#### SelectedMicEnergyRecorder 类
```python
class SelectedMicEnergyRecorder(BaseEnergyRecorder):
    def __init__(self, device: dict)
```

麦克风能量级别监控

#### SelectedSpeakerEnergyRecorder 类
```python
class SelectedSpeakerEnergyRecorder(BaseEnergyRecorder):
    def __init__(self, device: dict)
```

扬声器能量级别监控

### 集成录音类群

#### BaseEnergyAndAudioRecorder 类
```python
class BaseEnergyAndAudioRecorder:
    def __init__(self, source: Any, energy_threshold: int, dynamic_energy_threshold: bool,
                 phrase_time_limit: int, phrase_timeout: int, record_timeout: int)
```

集成音频录制和能量监控

#### SelectedMicEnergyAndAudioRecorder 类
```python
class SelectedMicEnergyAndAudioRecorder(BaseEnergyAndAudioRecorder):
    def __init__(self, device: dict, energy_threshold: int, dynamic_energy_threshold: bool,
                 phrase_time_limit: int, phrase_timeout: int = 1, record_timeout: int = 5)
```

集成麦克风音频录制和能量监控

#### SelectedSpeakerEnergyAndAudioRecorder 类
```python
class SelectedSpeakerEnergyAndAudioRecorder(BaseEnergyAndAudioRecorder):
    def __init__(self, device: dict, energy_threshold: int, dynamic_energy_threshold: bool,
                 phrase_time_limit: int, phrase_timeout: int = 1, record_timeout: int = 5)
```

集成扬声器音频录制和能量监控

## 主要方法

### 录音控制

```python
adjustForNoise() -> None
```
- 根据环境噪音调整阈值
- 录音开始前的校准

```python
recordIntoQueue(audio_queue: Queue) -> None
```
- 持续将音频数据加入队列
- 在后台线程执行

```python
pause() -> None
resume() -> None
stop() -> None
```
- 录音的暂停·恢复·停止控制

### 能量监控

```python
recordIntoQueue(energy_queue: Queue) -> None
```
- 将能量级别加入队列
- 提供实时监控数据

## 使用方法

### 基本麦克风录音

```python
from queue import Queue
from models.transcription.transcription_recorder import SelectedMicRecorder

# 设备配置
mic_device = {
    "name": "麦克风 (USB Audio Device)",
    "index": 0,
    "channels": 1,
    "sample_rate": 16000
}

# 录音设置
energy_threshold = 300
dynamic_threshold = True
record_timeout = 5

# 录音器初始化
recorder = SelectedMicRecorder(
    device=mic_device,
    energy_threshold=energy_threshold,
    dynamic_energy_threshold=dynamic_threshold,
    record_timeout=record_timeout
)

# 创建音频队列
audio_queue = Queue()

# 开始录音
recorder.adjustForNoise()  # 噪音调整
recorder.recordIntoQueue(audio_queue)

# 获取音频数据
while True:
    if not audio_queue.empty():
        audio_data = audio_queue.get()
        print(f"接收音频数据: {len(audio_data)} bytes")
```

### 扬声器录音(回环)

```python
from models.transcription.transcription_recorder import SelectedSpeakerRecorder

# 扬声器设备配置
speaker_device = {
    "name": "扬声器 (USB Audio Device)",
    "index": 1,
    "channels": 2,
    "sample_rate": 44100
}

# 扬声器录音器
recorder = SelectedSpeakerRecorder(
    device=speaker_device,
    energy_threshold=500,
    dynamic_energy_threshold=False,
    record_timeout=3
)

audio_queue = Queue()
recorder.recordIntoQueue(audio_queue)
```

### 能量监控

```python
from models.transcription.transcription_recorder import SelectedMicEnergyRecorder

# 仅能量监控
energy_recorder = SelectedMicEnergyRecorder(mic_device)
energy_queue = Queue()

energy_recorder.recordIntoQueue(energy_queue)

# 获取能量级别
while True:
    if not energy_queue.empty():
        energy_level = energy_queue.get()
        print(f"能量级别: {energy_level}")
```

### 集成录音(音频+能量)

```python
from models.transcription.transcription_recorder import SelectedMicEnergyAndAudioRecorder

# 集成录音器
integrated_recorder = SelectedMicEnergyAndAudioRecorder(
    device=mic_device,
    energy_threshold=300,
    dynamic_energy_threshold=True,
    phrase_time_limit=5,     # 短语限制时间
    phrase_timeout=1,        # 短语超时
    record_timeout=5         # 录音超时
)

audio_queue = Queue()
energy_queue = Queue()

# 同时输出到两个队列
integrated_recorder.recordIntoQueue(audio_queue, energy_queue)
```

## 配置参数

### 阈值设置
- **energy_threshold**: 音频检测的能量阈值
- **dynamic_energy_threshold**: 动态阈值调整的启用/禁用

### 超时设置
- **record_timeout**: 录音持续时间上限
- **phrase_timeout**: 短语间的静音允许时间
- **phrase_time_limit**: 单个短语的最大长度

### 设备设置
- **name**: 设备名称
- **index**: 设备索引
- **channels**: 通道数(1=单声道, 2=立体声)
- **sample_rate**: 采样率(Hz)

## 设备支持

### 麦克风设备
- USB麦克风
- 内置麦克风
- 蓝牙麦克风
- 虚拟麦克风设备

### 扬声器设备(回环)
- USB扬声器/耳机
- 内置扬声器
- 蓝牙扬声器
- 虚拟音频设备

## 错误处理

### 设备错误
- 设备连接失败检测
- 提供适当错误消息

### 音频格式错误
- 不支持格式的检测
- 自动格式转换

### 内存错误
- 防止队列溢出
- 优化内存使用

## 性能特性

### 延迟
- 低延迟录音(~10ms)
- 实时处理优化

### 吞吐量
- 支持连续录音
- 支持高采样率

### 内存使用
- 高效缓冲区管理
- 队列大小优化

## 依赖关系

### 必需依赖
- `speech_recognition`: 语音识别库
- `pyaudiowpatch`: Windows音频系统集成
- `queue`: 数据队列

### 可选依赖
- `datetime`: 时间戳功能

## 注意事项

- Windows专用(pyaudiowpatch限制)
- 需要适当的音频设备驱动程序
- 互斥控制导致的同时设备访问限制
- 使用高采样率时CPU使用率上升

## 相关模块

- `transcription_transcriber.py`: 语音识别引擎
- `device_manager.py`: 设备管理
- `config.py`: 录音设置管理
- `model.py`: 录音控制集成
