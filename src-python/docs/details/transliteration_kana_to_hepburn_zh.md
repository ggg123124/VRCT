# transliteration_kana_to_hepburn.py - 片假名→黑本式转换

## 概述

将片假名字符串转换为标准黑本式罗马字的模块。支持长音符(macron)、外来语音转换、促音·拨音处理等,全面提供日语罗马字表记所需功能。

## 主要功能

### 标准黑本式转换
- 片假名字符的基本罗马字转换
- 通过长音符(ā ī ū ē ō)表示长音
- 选择性支持连续元音表记

### 特殊音处理
- 促音(ッ)的适当子音重复处理
- 拨音(ン)的m/n使用区分
- 长音符(ー)的前元音延长处理

### 外来语支持
- シェ(she)、チェ(che)等组合
- ヴ音(vu, va, vi, ve, vo)转换
- ファ行(fa, fi, fe, fo)处理

## 主要函数

### katakana_to_hepburn

```python
def katakana_to_hepburn(kata: str, use_macron: bool = True) -> str
```

将片假名字符串转换为黑本式罗马字

#### 参数
- **kata**: 转换对象的片假名字符串
- **use_macron**: 长音符使用标志(True=ā ī ū ē ō, False=aa ii uu ee oo)

#### 返回值
- **str**: 黑本式罗马字字符串(小写)

## 使用方法

### 基本转换

```python
from models.transliteration.transliteration_kana_to_hepburn import katakana_to_hepburn

# 基本片假名转换
result1 = katakana_to_hepburn("カタカナ")
print(result1)  # "katakana"

# 长音的长音符表记
result2 = katakana_to_hepburn("コンピューター", use_macron=True)
print(result2)  # "konpyūtā"

# 长音的连续元音表记
result3 = katakana_to_hepburn("コンピューター", use_macron=False)
print(result3)  # "konpyuutaa"
```

### 特殊音处理

```python
# 促音(ッ)处理
result1 = katakana_to_hepburn("キャッチ")
print(result1)  # "kyatchi"

# 拨音(ン)处理
result2 = katakana_to_hepburn("ホンバン")
print(result2)  # "homban" (n→m转换)

# 外来语特殊音
result3 = katakana_to_hepburn("シェア")
print(result3)  # "shea"

result4 = katakana_to_hepburn("ヴァイオリン")
print(result4)  # "vaiorin"
```

## 转换规则详情

### 基本音对应表

```python
base_mapping = {
    # 清音
    'ア':'a', 'イ':'i', 'ウ':'u', 'エ':'e', 'オ':'o',
    'カ':'ka', 'キ':'ki', 'ク':'ku', 'ケ':'ke', 'コ':'ko',
    'サ':'sa', 'シ':'shi', 'ス':'su', 'セ':'se', 'ソ':'so',
    # ... 等等
}
```

### 拗音组合

```python
digraphs_mapping = {
    ('キ','ャ'):'kya', ('シ','ャ'):'sha', ('チ','ャ'):'cha',
    ('フ','ァ'):'fa', ('シ','ェ'):'she', ('ヴ','ァ'):'va',
    # ... 等等
}
```

### 长音符转换规则

```python
macron_rules = {
    'aa': 'ā', 'ii': 'ī', 'uu': 'ū',
    'ee': 'ē', 'oo': 'ō', 'ou': 'ō'  # 东京型长音
}
```

## 特殊处理算法

### 促音(ッ)处理
- 下一个音的子音部分提取并重复
- マッチャ → ma + tcha → matcha

### 拨音(ン)处理
- n后跟b/p/m时转换为m
- ホンバン → honban → homban

### 长音符(ー)处理
- 前元音延长(后续长音符处理)
- スー → su + - → suu → sū

## 依赖关系

### 必需依赖
- 标准Python库(无外部依赖)

### 相关模块
- `transliteration_transliterator.py`: 主转写类
- `transliteration_context_rules.py`: 文脉依赖规则

## 限制事项·注意点

### 转换精度限制
- 不支持依赖文脉的读音区分
- 不支持专有名词的特殊读音
- 不支持方言·古语的特殊音

### 黑本式范围
- 符合标准黑本式
- 部分外来语音为近似转换
- 拨音的文脉依赖规则简化

## 将来改进点

- 支持更多外来语音
- 文脉依赖读音区分功能
- 性能优化
- 更详细的黑本式变体支持
