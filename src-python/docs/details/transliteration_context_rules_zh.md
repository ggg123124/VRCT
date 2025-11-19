# transliteration_context_rules.py - 文脉转写规则引擎

## 概述

对分词结果应用文脉依赖转写规则的紧凑规则引擎。基于相邻分词信息动态修正读音(假名),实现更自然准确的转写。

## 主要功能

### 文脉依赖转写
- 利用相邻分词信息修正读音
- 基于优先级的规则应用顺序
- 支持正则表达式·完全匹配

### 规则引擎
- 内嵌规则定义(无需外部JSON文件)
- 支持前后相邻分词检查
- 通过原地修改实现高效处理

### 动态读音变更
- 根据文脉改写假名读音
- 自动清除平假名·黑本式
- 触发调用端重新计算

## 规则定义结构

### DEFAULT_RULES

```python
DEFAULT_RULES = {
    "rules": [
        {
            "name": "nan_next_tdna",           # 规则名
            "target": "何",                    # 目标字符
            "match_mode": "equals",            # 匹配模式
            "direction": "next",               # 检查方向
            "kana_set": ["タ", "チ", "ツ"...], # 条件字符集
            "on_true": {"kana": "ナン"},       # 条件为真时的动作
            "on_false": {"kana": "ナニ"}       # 条件为假时的动作
        }
    ]
}
```

## 主要函数

### apply_context_rules

```python
def apply_context_rules(results: List[Dict[str, Any]], use_macron: bool = False) -> List[Dict[str, Any]]
```

对分词列表应用文脉规则

#### 参数
- **results**: 由`Transliterator.split_kanji_okurigana`生成的分词字典列表
- **use_macron**: 兼容性参数(规则处理中未使用)

#### 返回值
- **List[Dict[str, Any]]**: 修正后的分词列表(也进行原地修改)

## 使用方法

### 基本文脉规则应用

```python
from models.transliteration.transliteration_context_rules import apply_context_rules

# 分词结果(示例)
results = [
    {"orig": "何", "kana": "ナニ", "hira": "なに", "hepburn": "nani"},
    {"orig": "度", "kana": "ド", "hira": "ど", "hepburn": "do"}
]

# 应用文脉规则
modified_results = apply_context_rules(results)

# "何度"时,"何"会被改为"ナン"
```

## 处理逻辑

### 处理流程

1. **规则准备** - 按优先级降序排序,预编译正则表达式
2. **分词扫描** - 对各分词依次应用规则
3. **匹配判定** - `equals`完全匹配或`regex`正则匹配
4. **相邻分词检查** - 基于`direction`特定相邻分词
5. **条件评估** - 检查相邻分词`kana`首字符与`kana_set`匹配
6. **动作执行** - 根据条件选择`on_true`/`on_false`,改写`kana`并清除`hira`/`hepburn`

## 具体规则示例

### "何"的读音区分规则

```python
{
    "name": "nan_next_tdna",
    "target": "何",
    "direction": "next",
    "kana_set": ["タ", "チ", "ツ", "テ", "ト", "ダ", "ヂ", "ヅ", "デ", "ド", "ナ", "ニ", "ヌ", "ネ", "ノ"],
    "on_true": {"kana": "ナン"},
    "on_false": {"kana": "ナニ"}
}
```

- "何度" → "何"读作"ナン"
- "何回" → "何"读作"ナニ"

## 依赖关系

### 必需依赖
- `typing`: 类型提示
- `re`: 正则表达式处理

### 相关模块
- `transliteration_transliterator.py`: 主转写类
- `transliteration_kana_to_hepburn.py`: 假名→黑本式转换

## 注意事项

- 规则应用后`hira`和`hepburn`变为空字符串,需要调用端重新计算
- 当前规则专用于日语
- 规则应用顺序依赖优先级,需适当设置
