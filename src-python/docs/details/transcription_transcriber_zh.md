# transcription_transcriber.py - 语音文字转写引擎

## 概述

将语音数据转换为文字文本的语音识别引擎主类。支持Google Speech Recognition和OpenAI Whisper(faster-whisper)两种引擎,统一管理在线·离线语音识别。通过基于队列的异步处理实现实时语音识别。

## 主要功能

### 语音识别引擎
- Google Speech Recognition(在线)
- OpenAI Whisper(faster-whisper,离线)
- 引擎自动切换功能

### 实时处理
- 从音频队列持续处理数据
- 异步语音识别处理
- 即时通知结果

### 多语言支持
- 同时识别多种语言
- 支持地区特定语言代码
- 自动语言检测

### 音频质量控制
- 音频质量过滤
- 噪声去除功能
- 置信度评分评估

## 类结构

### AudioTranscriber 类
```python
class AudioTranscriber:
    def __init__(self, speaker: bool, source: Any, phrase_timeout: int, max_phrases: int,
                 transcription_engine: str, root: Optional[str] = None,
                 whisper_weight_type: Optional[str] = None, device: str = "cpu",
                 device_index: int = 0, compute_type: str = "auto")
```

语音识别的核心类

#### 初始化参数
- **speaker**: 是扬声器音频还是麦克风音频
- **source**: 音频源
- **phrase_timeout**: 短语超时(秒)
- **max_phrases**: 最大短语数
- **transcription_engine**: 识别引擎("Google"/"Whisper")
- **whisper_weight_type**: Whisper模型类型
- **device**: 计算设备("cpu"/"cuda")
- **device_index**: 设备索引
- **compute_type**: 计算精度类型

## 主要方法

### 语音识别处理

```python
transcribeAudioQueue(audio_queue: Queue, languages: List[str], countries: List[str],
                    avg_logprob: float = -0.8, no_speech_prob: float = 0.6) -> bool
```

从音频队列持续进行语音识别

#### 参数
- **audio_queue**: 音频数据队列
- **languages**: 识别目标语言列表
- **countries**: 地区代码列表  
- **avg_logprob**: Whisper平均对数概率阈值
- **no_speech_prob**: Whisper无音判定阈值

### 结果管理

```python
getTranscript() -> dict
```

获取最新识别结果

```python
updateTranscript(result: dict) -> None
```

更新识别结果并通知

```python
clearTranscriptData() -> None
```

清除识别数据

### 音频数据处理

```python
processMicData() -> AudioData
```

麦克风音频数据的预处理

```python
processSpeakerData() -> AudioData
```

扬声器音频数据的预处理

## 使用方法

### 基本语音识别

```python
from queue import Queue
from models.transcription.transcription_transcriber import AudioTranscriber

# 初始化语音识别
transcriber = AudioTranscriber(
    speaker=False,              # 麦克风音频
    source=mic_source,          # 音频源
    phrase_timeout=3,           # 3秒短语超时
    max_phrases=10,             # 最大10个短语
    transcription_engine="Google",  # Google语音识别
    device="cpu"
)

# 准备音频队列
audio_queue = Queue()

# 设置识别目标语言
languages = ["Japanese", "English"]
countries = ["Japan", "United States"]

# 执行语音识别
def transcription_loop():
    while True:
        success = transcriber.transcribeAudioQueue(
            audio_queue, languages, countries
        )
        if success:
            result = transcriber.getTranscript()
            print(f"识别结果: {result['text']}")
            print(f"语言: {result['language']}")

# 在后台执行
import threading
thread = threading.Thread(target=transcription_loop)
thread.daemon = True
thread.start()
```

### 使用Whisper引擎

```python
# 初始化Whisper语音识别
whisper_transcriber = AudioTranscriber(
    speaker=True,               # 扬声器音频
    source=speaker_source,
    phrase_timeout=5,
    max_phrases=5,
    transcription_engine="Whisper",
    whisper_weight_type="base",     # Whisper模型
    device="cuda",                  # 使用CUDA
    device_index=0,
    compute_type="float16"          # 半精度浮点数
)

# 使用Whisper特定参数进行识别
success = whisper_transcriber.transcribeAudioQueue(
    audio_queue, languages, countries,
    avg_logprob=-0.5,          # 更严格的质量阈值
    no_speech_prob=0.4         # 更敏感的无音检测
)
```

### 回调处理

```python
def on_transcription_result(result):
    """识别结果的回调处理"""
    if result["text"]:
        print(f"识别成功: {result['text']}")
        print(f"语言: {result['language']}")
        print(f"置信度: {result.get('confidence', 'N/A')}")
    else:
        print("语音识别失败")

# 设置结果通知
transcriber.transcript_changed_event.set()  # 事件设置
```

### 带错误处理的使用

```python
def safe_transcription(transcriber, audio_queue, languages, countries):
    """安全的语音识别处理"""
    try:
        success = transcriber.transcribeAudioQueue(
            audio_queue, languages, countries
        )
        
        if success:
            result = transcriber.getTranscript()
            return result
        else:
            return {"text": False, "language": None, "error": "识别失败"}
            
    except Exception as e:
        print(f"语音识别错误: {e}")
        return {"text": False, "language": None, "error": str(e)}
```

## 识别引擎比较

### Google Speech Recognition

#### 优点
- 高识别精度
- 多语言支持
- 实时处理
- 抗噪声能力强

#### 限制
- 必须联网
- API限制
- 隐私担忧
- 延迟

### OpenAI Whisper(faster-whisper)

#### 优点
- 离线运行
- 隐私保护
- 高精度
- 多语言支持

#### 限制
- 首次启动时间长
- 内存使用量大
- 推荐使用CUDA
- 需要模型文件

## 配置参数

### 短语控制
- **phrase_timeout**: 短语间无音时间(秒)
- **max_phrases**: 缓冲区内最大短语数

### Whisper质量设置
- **avg_logprob**: 平均对数概率阈值(-1.0〜0.0)
- **no_speech_prob**: 无音判定阈值(0.0〜1.0)

### 计算设置
- **device**: "cpu"或"cuda"
- **compute_type**: "float32", "float16", "int8"等

## 音频数据格式

### 输入格式
- 采样率: 推荐16kHz
- 位深度: 16bit
- 声道: 推荐单声道
- 格式: WAV、FLAC等

### 处理流程
1. 从音频队列获取数据
2. 音频格式标准化
3. 执行语音识别引擎
4. 结果后处理·过滤
5. 通知最终结果

## 性能优化

### 内存管理
- 设置适当的音频缓冲区大小
- 及早释放不需要的音频数据
- Whisper模型的内存效率化

### 计算优化
- 使用CUDA加速
- 选择适当的计算精度
- 利用批处理

### 延迟削减
- 优化音频缓冲区大小
- 引擎切换的高速化
- 利用缓存功能

## 错误处理

### 网络错误
- 检测Google API连接失败
- 自动切换到Whisper引擎

### 音频质量错误
- 检测·过滤低质量音频
- 监控噪声水平

### 资源错误
- 检测VRAM不足
- 内存不足时的应对

## 依赖关系

### 必需依赖
- `speech_recognition`: Google语音识别
- `faster_whisper`: Whisper语音识别
- `pyaudiowpatch`: 音频输入
- `pydub`: 音频处理

### 可选依赖
- `torch`: CUDA计算
- `utils`: 错误日志功能

## 注意事项

- Google API有使用限制
- Whisper首次启动需要时间
- 使用CUDA时注意VRAM消耗
- 音频质量对识别精度影响很大
- 多语言识别时处理负载增加

## 相关模块

- `transcription_recorder.py`: 音频录制
- `transcription_whisper.py`: Whisper模型管理
- `transcription_languages.py`: 语言代码管理
- `config.py`: 识别配置管理
- `model.py`: 语音识别统一控制
