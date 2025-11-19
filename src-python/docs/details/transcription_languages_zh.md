# transcription_languages.py - 语音识别语言映射

## 概述

提供语音识别引擎支持的语言代码映射表的模块。吸收不同语音识别引擎语言代码规范的差异,提供统一的接口。

## 主要功能

### 语言映射表
- 从显示用语言名转换到各引擎固有的语言代码
- 支持国家·地区特定的语言变体
- 多个语音识别引擎的统一语言管理

### 支持的引擎
- Google Speech Recognition
- OpenAI Whisper(faster-whisper)
- 其他语音识别引擎

## 数据结构

### transcription_lang
```python
transcription_lang: Dict[str, List[Dict[str, str]]]
```

语言及其地区变体的映射

```python
transcription_lang = {
    "English": [
        {"country": "United States", "google_language_code": "en-US"},
        {"country": "United Kingdom", "google_language_code": "en-GB"},
        {"country": "Australia", "google_language_code": "en-AU"}
    ],
    "Japanese": [
        {"country": "Japan", "google_language_code": "ja-JP"}
    ],
    "Korean": [
        {"country": "South Korea", "google_language_code": "ko-KR"}
    ]
}
```

## 使用方法

### 基本语言代码获取

```python
from models.transcription.transcription_languages import transcription_lang

# 获取日语语言代码
japanese_codes = transcription_lang.get("Japanese", [])
if japanese_codes:
    code = japanese_codes[0]["google_language_code"]  # "ja-JP"

# 获取英语地区别语言代码
english_codes = transcription_lang.get("English", [])
for region in english_codes:
    print(f"{region['country']}: {region['google_language_code']}")
```

### 获取可用语言列表

```python
# 支持语言列表
supported_languages = list(transcription_lang.keys())
print(f"支持语言: {supported_languages}")

# 语言和国家组合列表
language_country_pairs = []
for lang, countries in transcription_lang.items():
    for country_data in countries:
        language_country_pairs.append({
            "language": lang,
            "country": country_data["country"],
            "code": country_data["google_language_code"]
        })
```

### 与翻译系统联动

```python
# 确认翻译系统支持的语言
from models.translation.translation_languages import translation_lang

transcription_langs = list(transcription_lang.keys())
translation_langs = []
for engine in translation_lang.keys():
    translation_langs.extend(translation_lang[engine]["source"].keys())

# 语音识别和翻译都支持的语言
supported_langs = list(filter(lambda x: x in transcription_langs, translation_langs))
```

## 主要支持语言

### 西欧语言
- **English**: US, UK, Australia, Canada, India, South Africa
- **Spanish**: Spain, Mexico, Argentina, Colombia
- **French**: France, Canada, Belgium
- **German**: Germany, Austria, Switzerland
- **Italian**: Italy
- **Portuguese**: Brazil, Portugal

### 亚洲语言
- **Japanese**: Japan
- **Korean**: South Korea
- **Chinese**: China (Simplified), Taiwan (Traditional), Hong Kong
- **Thai**: Thailand
- **Vietnamese**: Vietnam

### 其他语言
- **Russian**: Russia
- **Arabic**: Saudi Arabia, UAE, Egypt
- **Hindi**: India
- **Dutch**: Netherlands
- **Swedish**: Sweden
- **Norwegian**: Norway

## 按引擎分类的语言代码格式

### Google Speech Recognition
- RFC 5646准拠的语言标签格式
- 例: "ja-JP", "en-US", "zh-CN"

### OpenAI Whisper
- ISO 639-1语言代码(2字符)
- 例: "ja", "en", "zh"

### 其他引擎
- 对应引擎固有格式
- 通过映射表转换

## 地区支持

### 同一语言的地区别支持
```python
# 英语地区变体
"English": [
    {"country": "United States", "google_language_code": "en-US"},
    {"country": "United Kingdom", "google_language_code": "en-GB"},
    {"country": "Australia", "google_language_code": "en-AU"},
    {"country": "Canada", "google_language_code": "en-CA"},
    {"country": "India", "google_language_code": "en-IN"}
]
```

### 方言·变种支持
```python
# 中文简体字·繁体字支持
"Chinese Simplified": [
    {"country": "China", "google_language_code": "zh-CN"}
],
"Chinese Traditional": [
    {"country": "Taiwan", "google_language_code": "zh-TW"},
    {"country": "Hong Kong", "google_language_code": "zh-HK"}
]
```

## 集成应用

### VRCT中的使用示例

```python
def get_supported_transcription_languages():
    """获取语音识别支持语言"""
    languages = []
    for language, countries in transcription_lang.items():
        for country_data in countries:
            languages.append({
                "language": language,
                "country": country_data["country"],
                "display_name": f"{language} ({country_data['country']})",
                "code": country_data["google_language_code"]
            })
    return languages
```

### 错误处理

```python
def get_language_code(language: str, country: str = None) -> str:
    """安全获取语言代码"""
    try:
        countries = transcription_lang.get(language, [])
        if not countries:
            return "en-US"  # 降级
            
        if country:
            for country_data in countries:
                if country_data["country"] == country:
                    return country_data["google_language_code"]
                    
        # 未指定国家或未找到时返回第一项
        return countries[0]["google_language_code"]
    except (KeyError, IndexError):
        return "en-US"  # 错误时降级
```

## 可扩展性

### 添加新语言
```python
# 添加新语言示例
transcription_lang["Turkish"] = [
    {"country": "Turkey", "google_language_code": "tr-TR"}
]
```

### 支持新引擎
```python
# 添加新引擎代码字段
transcription_lang["English"][0]["azure_language_code"] = "en-US"
transcription_lang["English"][0]["aws_language_code"] = "en-US"
```

## 注意事项

- 语言代码依赖各引擎规范
- 添加新引擎时需要添加对应代码
- 注意地区特定的语音识别精度差异
- 不同引擎支持的语言可能不同

## 相关模块

- `transcription_transcriber.py`: 语音识别引擎本体
- `translation_languages.py`: 翻译引擎语言映射
- `config.py`: 语言设置管理
- `controller.py`: 语言选择UI控制
