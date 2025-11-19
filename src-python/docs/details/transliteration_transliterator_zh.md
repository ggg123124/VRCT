# transliteration_transliterator.py - 综合音写·转写系统

## 概述

利用SudachiPy的日语罗马字转写系统主类。集成形态素分析、汉字·送假名分离、文脉依赖规则应用、黑本式转换,提供高精度日语罗马字化。

## 主要功能

### 统合转写系统
- 通过SudachiPy进行高精度形态素分析
- 汉字·送假名自动分离处理
- 应用文脉依赖读音变更规则

### 多层转换处理
- 片假名读音获取·分配
- 平假名自动转换
- 黑本式罗马字生成

### 并行处理支持
- 线程安全的分词器利用
- 通过锁机制实现安全并行执行
- 高负载环境下稳定运行

## 类结构

### Transliterator 类
```python
class Transliterator:
    def __init__(self) -> None:
        self.tokenizer_obj: tokenizer.Tokenizer
        self.mode: tokenizer.Tokenizer.SplitMode
        self._tokenizer_lock: threading.Lock
```

日语转写处理的核心类

## 主要方法

### analyze

```python
def analyze(self, text: str, use_macron: bool = False) -> List[Dict[str, Any]]
```

分析文本生成转写信息

#### 参数
- **text**: 分析对象的日语文本
- **use_macron**: 长音符使用标志

#### 返回值
- **List[Dict[str, Any]]**: 分词转写信息列表

#### 输出字典结构
```python
{
    "orig": str,      # 原始字符·字符串
    "kana": str,      # 片假名读音
    "hira": str,      # 平假名读音  
    "hepburn": str    # 黑本式罗马字
}
```

### split_kanji_okurigana (静态方法)

```python
@staticmethod
def split_kanji_okurigana(surface: str, reading_kana: str, use_macron: bool = True) -> List[Dict[str, str]]
```

将单词的表层形式和读音分割为汉字·送假名块

## 使用方法

### 基本转写处理

```python
from models.transliteration.transliteration_transliterator import Transliterator

# 初始化转写系统
transliterator = Transliterator()

# 基本文章转写
text = "向こうへ行く"
results = transliterator.analyze(text)

for token in results:
    print(f"{token['orig']} -> {token['kana']} -> {token['hira']} -> {token['hepburn']}")
```

### 长音符使用的长音处理

```python
# 使用长音符的长音表记
text = "東京に行く"
results_macron = transliterator.analyze(text, use_macron=True)
results_normal = transliterator.analyze(text, use_macron=False)

# 输出:
# 长音符: 東京 -> tōkyō
# 无长音符: 東京 -> toukyou
```

### 文脉依赖规则效果确认

```python
# 依赖文脉的读音变更示例("何"的读音区分)
test_cases = [
    "何が好き？",      # 何 -> ナニ
    "何度も挑戦",      # 何 -> ナン
]

for text in test_cases:
    results = transliterator.analyze(text)
    for token in results:
        if token['orig'] == '何':
            print(f"「何」读音: {token['kana']} -> {token['hepburn']}")
```

## 内部处理流程

### 分析处理管道

1. **SudachiPy形态素分析**
2. **各分词处理**
3. **符号·空白特殊处理**
4. **单一字符处理**
5. **多字符汉字·送假名分离**
6. **文脉依赖规则应用**
7. **规则应用后重新计算**

### 汉字·送假名分离算法

1. **表层形式块分割** - 按汉字/非汉字分块
2. **读音分配** - 按块字符数比例分配
3. **余量读音分配** - 汉字块优先
4. **最终读音分配** - 生成各块转写信息

## 并行处理·线程安全

### 锁机制

```python
# 线程安全使用示例
processor = ThreadSafeUsage()
texts = ["東京に行く", "大阪で食事"]
results = processor.process_texts_concurrently(texts)
```

## 错误处理

### 异常处理

```python
def safe_analyze(text):
    """安全分析处理"""
    try:
        results = transliterator.analyze(text)
        return results, None
    except RuntimeError as e:
        if "Already borrowed" in str(e):
            return None, "RETRY_NEEDED"
        return None, "RUNTIME_ERROR"
```

## 依赖关系

### 必需依赖
- `sudachipy`: 形态素分析引擎
- `threading`: 并行控制
- `typing`: 类型提示

### 内部模块依赖
- `transliteration_kana_to_hepburn`: 黑本式转换
- `transliteration_context_rules`: 文脉依赖规则

## 注意事项·限制

### 处理精度限制
- 依赖形态素分析结果
- 未知词·专有名词读音推测
- 依文脉可能分割不准确

### 性能限制
- 首次执行时词典加载时间
- 大量文本处理时的内存使用
- 并行访问时的锁等待

## 相关模块

- `transliteration_kana_to_hepburn.py`: 黑本式转换处理
- `transliteration_context_rules.py`: 文脉依赖规则应用
- `config.py`: 系统设置管理
- `utils.py`: 实用函数

## 将来改进点

- 自定义读音词典支持
- 更高精度文脉分析
- 与其他语言音写系统集成
- 实时处理优化
