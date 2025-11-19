# transcription_whisper.py - Whisper模型管理

## 概述

管理OpenAI Whisper(faster-whisper)模型的下载、验证、加载的实用模块。支持多种模型大小,提供从Hugging Face Hub自动下载功能和文件完整性检查功能。

## 主要功能

### 模型管理
- 支持多种Whisper模型大小
- 从Hugging Face Hub自动下载
- 模型文件完整性验证

### 下载功能
- 带进度显示的下载
- 支持续传
- 错误处理

### 模型加载
- 高效的模型初始化
- CUDA支持
- 计算类型优化

## 支持的模型

### 可用模型
```python
_MODELS = {
    "tiny": "Systran/faster-whisper-tiny",           # ~39MB
    "base": "Systran/faster-whisper-base",           # ~74MB  
    "small": "Systran/faster-whisper-small",         # ~244MB
    "medium": "Systran/faster-whisper-medium",       # ~769MB
    "large-v1": "Systran/faster-whisper-large-v1",  # ~1.5GB
    "large-v2": "Systran/faster-whisper-large-v2",  # ~1.5GB
    "large-v3": "Systran/faster-whisper-large-v3",  # ~1.5GB
    "large-v3-turbo-int8": "Zoont/faster-whisper-large-v3-turbo-int8-ct2",  # ~794MB
    "large-v3-turbo": "deepdml/faster-whisper-large-v3-turbo-ct2"           # ~1.58GB
}
```

### 模型特性比较

#### tiny
- **大小**: ~39MB
- **精度**: 低
- **速度**: 最快
- **用途**: 实时处理、资源受限环境

#### base  
- **大小**: ~74MB
- **精度**: 中等
- **速度**: 快
- **用途**: 一般用途、注重平衡

#### small
- **大小**: ~244MB  
- **精度**: 良好
- **速度**: 中等
- **用途**: 注重质量、移动环境

#### medium
- **大小**: ~769MB
- **精度**: 高
- **速度**: 较慢
- **用途**: 高质量识别、桌面环境

#### large系列
- **大小**: ~1.5GB
- **精度**: 最高
- **速度**: 慢
- **用途**: 最高质量、服务器环境

## 主要函数

### 文件下载

```python
downloadFile(url: str, path: str, func: Optional[Callable[[float], None]] = None) -> None
```

流式下载文件

#### 参数
- **url**: 下载URL
- **path**: 保存路径
- **func**: 进度回调函数

### 模型验证

```python
checkWhisperWeight(root: str, weight_type: str) -> bool
```

确认Whisper模型的可用性

#### 参数
- **root**: 应用程序根路径
- **weight_type**: 模型类型("tiny", "base"等)

#### 返回值
- **bool**: 模型是否可用

### 模型下载

```python
downloadWhisperWeight(root: str, weight_type: str, 
                     callback: Optional[Callable[[float], None]] = None,
                     end_callback: Optional[Callable[[], None]] = None) -> None
```

下载Whisper模型

#### 参数
- **root**: 应用程序根路径
- **weight_type**: 要下载的模型类型
- **callback**: 进度回调
- **end_callback**: 完成回调

### 模型加载

```python
getWhisperModel(root: str, weight_type: str, device: str = "cpu",
                device_index: int = 0, compute_type: str = "auto") -> WhisperModel
```

初始化Whisper模型

#### 参数
- **root**: 应用程序根路径
- **weight_type**: 要使用的模型类型
- **device**: 计算设备("cpu"/"cuda")
- **device_index**: 设备索引
- **compute_type**: 计算精度类型

#### 返回值
- **WhisperModel**: 初始化的Whisper模型实例

## 使用方法

### 模型确认和下载

```python
from models.transcription.transcription_whisper import checkWhisperWeight, downloadWhisperWeight

root_path = "."
model_type = "base"

# 确认模型可用性
if not checkWhisperWeight(root_path, model_type):
    print(f"未找到{model_type}模型。开始下载...")
    
    # 进度回调
    def progress_callback(progress):
        print(f"下载进度: {progress:.1%}")
    
    # 完成回调  
    def completion_callback():
        print("下载完成!")
    
    # 下载模型
    downloadWhisperWeight(
        root=root_path,
        weight_type=model_type,
        callback=progress_callback,
        end_callback=completion_callback
    )
else:
    print(f"{model_type}模型可用")
```

### 模型加载和使用

```python
from models.transcription.transcription_whisper import getWhisperModel

# 在CPU上加载模型
model = getWhisperModel(
    root=".",
    weight_type="base", 
    device="cpu"
)

# 在CUDA上加载模型(使用GPU)
gpu_model = getWhisperModel(
    root=".",
    weight_type="small",
    device="cuda",
    device_index=0,
    compute_type="float16"  # 半精度加速
)

# 执行语音识别
audio_file = "audio.wav"
segments, info = model.transcribe(audio_file, language="ja")

for segment in segments:
    print(f"{segment.start:.1f}s - {segment.end:.1f}s: {segment.text}")
```

### 带错误处理的使用

```python
def safe_model_loading(root, weight_type, device="cpu"):
    """安全的模型加载"""
    try:
        # 确认模型存在
        if not checkWhisperWeight(root, weight_type):
            print(f"正在下载模型 {weight_type}...")
            downloadWhisperWeight(root, weight_type)
        
        # 加载模型
        model = getWhisperModel(root, weight_type, device)
        return model
        
    except Exception as e:
        print(f"模型加载错误: {e}")
        # 回退: 尝试更小的模型
        if weight_type != "tiny":
            return safe_model_loading(root, "tiny", device)
        return None
```

### 带进度显示的下载

```python
import sys

def download_with_progress(root, weight_type):
    """带进度显示的下载"""
    def show_progress(progress):
        bar_length = 40
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        sys.stdout.write(f'\r[{bar}] {progress:.1%}')
        sys.stdout.flush()
    
    def download_complete():
        print("\n下载完成!")
    
    print(f"正在下载Whisper {weight_type}模型...")
    downloadWhisperWeight(root, weight_type, show_progress, download_complete)
```

## 目录结构

### 模型文件布局
```
root/
└── weights/
    └── whisper/
        ├── tiny/
        │   ├── config.json
        │   ├── preprocessor_config.json  
        │   ├── model.bin
        │   ├── tokenizer.json
        │   └── vocabulary.txt
        ├── base/
        └── small/
```

### 必需文件
```python
_FILENAMES = [
    "config.json",           # 模型配置
    "preprocessor_config.json",  # 预处理配置
    "model.bin",            # 模型权重
    "tokenizer.json",       # 分词器
    "vocabulary.txt",       # 词汇文件
    "vocabulary.json"       # 词汇文件(JSON格式)
]
```

## 性能考虑事项

### 内存使用量
- **tiny**: ~100MB RAM
- **base**: ~200MB RAM
- **small**: ~500MB RAM  
- **medium**: ~1.5GB RAM
- **large**: ~3GB RAM

### VRAM使用量(使用CUDA时)
- **tiny**: ~200MB VRAM
- **base**: ~300MB VRAM
- **small**: ~600MB VRAM
- **medium**: ~1.8GB VRAM
- **large**: ~3.5GB VRAM

### 处理速度(参考)
- **tiny**: 可实时处理
- **base**: 1x-2x 实时
- **small**: 0.5x-1x 实时
- **medium**: 0.2x-0.5x 实时
- **large**: 0.1x-0.3x 实时

## 计算类型设置

### 可用计算类型
- **float32**: 最高精度,慢
- **float16**: 高精度,中速(推荐CUDA)
- **int8**: 中精度,快
- **int8_float16**: 混合精度,平衡

### 推荐设置
```python
# 使用CPU时
compute_type = "int8"  # 注重速度

# 使用CUDA时(RTX及以上)
compute_type = "float16"  # 精度和速度平衡

# 使用CUDA时(VRAM受限)
compute_type = "int8_float16"  # 注重内存效率
```

## 错误处理

### 下载错误
- 网络连接失败
- 磁盘空间不足
- 权限不足

### 模型加载错误  
- VRAM不足
- 模型文件损坏
- 设备不支持

### 应对措施
```python
def robust_model_loading(root, preferred_type="base"):
    """健壮的模型加载"""
    model_priority = ["tiny", "base", "small", "medium"]
    
    # 优先模型放在前面
    if preferred_type in model_priority:
        model_priority.remove(preferred_type)
        model_priority.insert(0, preferred_type)
    
    for model_type in model_priority:
        try:
            if checkWhisperWeight(root, model_type):
                return getWhisperModel(root, model_type)
        except Exception as e:
            print(f"{model_type}模型加载失败: {e}")
            continue
    
    raise RuntimeError("没有可用的Whisper模型")
```

## 依赖关系

### 必需依赖
- `faster_whisper`: Whisper引擎
- `requests`: 文件下载
- `utils`: 实用功能

### 可选依赖
- `torch`: CUDA计算(使用GPU时)

## 注意事项

- 首次加载模型时下载需要时间
- 模型越大精度越高,但消耗更多内存和VRAM
- 使用CUDA时需要适当的GPU驱动
- 模型文件完整性检查很重要
- 下载时间因网络环境而异

## 相关模块

- `transcription_transcriber.py`: Whisper语音识别引擎
- `config.py`: Whisper模型配置管理
- `utils.py`: 计算设备管理
- `model.py`: Whisper统一控制
