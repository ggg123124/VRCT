# translation_utils.py - CTranslate2模型管理实用工具

## 概述

进行CTranslate2本地机器翻译模型的自动下载、解压、管理的实用模块。支持多种模型大小(small/large)和平台(CPU/CUDA),提供模型文件完整性检查和自动修复功能。

## 主要功能

### 模型自动管理
- CTranslate2模型自动下载
- ZIP格式模型的解压·配置
- 模型文件完整性验证
- 损坏模型的自动重新获取

### 多平台支持
- CPU版·CUDA版双支持
- 多模型大小管理
- 平台专用优化

## 常量·设置

### 模型定义

```python
# CTranslate2权重文件信息
ctranslate2_weights = {
    "small": {
        "url": "m2m100_418m.zip",
        "directory_name": "m2m100_418m",
        "tokenizer": "facebook/m2m100_418M"
    },
    "large": {
        "url": "m2m100_12b.zip", 
        "directory_name": "m2m100_12b",
        "tokenizer": "facebook/m2m100_1.2b"
    }
}
```

### 配置参数
- **BASE_WEIGHTS_URL**: 模型分发基础URL
- **LOCAL_WEIGHTS_DIR**: 本地保存目录
- **CHUNK_SIZE**: 下载时的块大小

## 主要功能

### 模型下载

```python
def downloadCTranslate2Model(model_type: str, device: str = "cpu") -> bool:
    """CTranslate2模型自动下载"""
```

下载指定模型类型和设备的模型

#### 参数
- **model_type**: 模型大小("small"/"large")
- **device**: 计算设备("cpu"/"cuda")

#### 返回值
- **bool**: 下载成功与否

### 模型存在确认

```python
def checkCTranslate2ModelExists(model_type: str, device: str = "cpu") -> bool:
    """模型文件存在确认"""
```

检查指定模型是否存在于本地

### 模型完整性验证

```python
def validateCTranslate2Model(model_type: str, device: str = "cpu") -> bool:
    """模型文件完整性验证"""  
```

确认已下载模型的完整性

## 模型规格

### small模型(m2m100_418m)

- **大小**: ~400MB
- **参数**: 418M
- **语言**: 100种语言
- **内存**: CPU ~1GB RAM, CUDA ~500MB VRAM
- **性能**: 速度快,质量良好

### large模型(m2m100_12b)

- **大小**: ~4.8GB
- **参数**: 1.2B
- **语言**: 100种语言
- **内存**: CPU ~6GB RAM, CUDA ~3GB VRAM
- **性能**: 速度中等,质量高

## 文件结构

### 目录布局
```
weights/
└── ctranslate2/
    ├── m2m100_418m/          # small模型(CPU版)
    ├── m2m100_418m_cuda/     # small模型(CUDA版)
    ├── m2m100_12b/           # large模型(CPU版)
    └── m2m100_12b_cuda/      # large模型(CUDA版)
```

### 必需文件
- `model.bin`: 转换后的模型权重
- `vocabulary.txt`: 词汇文件
- `config.json`: 模型配置文件
- `shared_vocabulary.txt`: 共享词汇文件

## 错误处理

### 网络错误
- 连接超时
- 下载中断
- 服务器错误

### 文件系统错误
- 容量不足
- 权限错误
- 文件损坏

## 依赖关系

### 必需依赖
- `requests`: HTTP下载
- `zipfile`: 存档解压
- `os`: 文件系统操作
- `pathlib`: 路径操作

## 注意事项

- 首次下载需要时间(取决于模型大小)
- 确保足够的存储容量
- 网络环境影响下载速度
- CUDA版需要对应的GPU环境
- 推荐备份模型文件

## 相关模块

- `translation_translator.py`: 模型使用类
- `translation_languages.py`: 语言代码管理
- `config.py`: 配置管理
- `utils.py`: 通用实用工具
