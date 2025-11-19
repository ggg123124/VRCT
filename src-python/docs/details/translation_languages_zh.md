# translation_languages.py - 翻译语言映射

## 概述

提供翻译引擎支持的语言代码映射表的模块。吸收不同翻译引擎(DeepL、Google、Bing、Papago等)语言代码规范的差异,提供统一的翻译语言管理。

## 主要功能

### 多引擎支持

- DeepL(免费版·API版)
- Google Translate
- Microsoft Translator(Bing)
- Papago Translator
- 其他Web翻译服务

### 语言代码统一管理

- 各引擎特有的语言代码格式统一化
- 源语言(source)和目标语言(target)的分离管理
- 地区特定语言变体支持

## 数据结构

### translation_lang

```python
translation_lang: Dict[str, Dict[str, Dict[str, str]]] = {
    "引擎名": {
        "source": {"语言名": "语言代码", ...},
        "target": {"语言名": "语言代码", ...}
    }
}
```

### DeepL翻译引擎(免费版)

```python
translation_lang["DeepL"] = {
    "source": {
        "Arabic": "ar", "Bulgarian": "bg", "Czech": "cs", "Danish": "da",
        "German": "de", "Greek": "el", "English": "en", "Spanish": "es",
        "Estonian": "et", "Finnish": "fi", "French": "fr", "Irish": "ga",
        "Croatian": "hr", "Hungarian": "hu", "Indonesian": "id", 
        "Icelandic": "is", "Italian": "it", "Japanese": "ja",
        "Korean": "ko", "Lithuanian": "lt", "Latvian": "lv",
        "Maltese": "mt", "Bokmal": "nb", "Dutch": "nl",
        "Norwegian": "no", "Polish": "pl", "Portuguese": "pt",
        "Romanian": "ro", "Russian": "ru", "Slovak": "sk",
        "Slovenian": "sl", "Swedish": "sv", "Turkish": "tr",
        "Ukrainian": "uk", "Chinese Simplified": "zh",
        "Chinese Traditional": "zh"
    },
    "target": {/* 相同映射 */}
}
```

### DeepL API(付费版概要)

```python
translation_lang["DeepL_API"] = {
    "source": {/* 基本与DeepL相同 */},
    "target": {
        "Japanese": "ja",
        "English American": "en-US",    # 地区差异
        "English British": "en-GB",
        "Portuguese Brazilian": "pt-BR", # 巴西葡萄牙语
        "Portuguese European": "pt-PT",  # 欧洲葡萄牙语
        "Chinese Simplified": "zh",
        "Chinese Traditional": "zh"
        /* 其他语言 */
    }
}
```

## 主要支持语言

### 西欧语言

- **English**: 英语(美国·英国变体)
- **German**: 德语
- **French**: 法语
- **Spanish**: 西班牙语
- **Italian**: 意大利语
- **Portuguese**: 葡萄牙语(巴西·欧洲)
- **Dutch**: 荷兰语
- **Swedish**: 瑞典语
- **Norwegian**: 挪威语

### 东欧·斯拉夫语言

- **Russian**: 俄语
- **Polish**: 波兰语
- **Czech**: 捷克语
- **Slovak**: 斯洛伐克语
- **Ukrainian**: 乌克兰语
- **Bulgarian**: 保加利亚语
- **Croatian**: 克罗地亚语
- **Slovenian**: 斯洛文尼亚语

### 亚洲语言

- **Japanese**: 日语
- **Korean**: 韩语
- **Chinese Simplified**: 简体中文
- **Chinese Traditional**: 繁体中文
- **Indonesian**: 印度尼西亚语

### 其他语言

- **Arabic**: 阿拉伯语
- **Turkish**: 土耳其语
- **Finnish**: 芬兰语
- **Estonian**: 爱沙尼亚语
- **Latvian**: 拉脱维亚语
- **Lithuanian**: 立陶宛语
- **Maltese**: 马耳他语
- **Irish**: 爱尔兰语

## 使用方法

### 基本语言代码获取

```python
from models.translation.translation_languages import translation_lang

# DeepL日语到英语翻译
deepl_source = translation_lang["DeepL"]["source"]["Japanese"]  # "ja"
deepl_target = translation_lang["DeepL"]["target"]["English"]   # "en"

# DeepL API地区特定英语指定
deepl_api_target = translation_lang["DeepL_API"]["target"]["English American"]  # "en-US"
```

### 确认支持的语言

```python
def get_supported_languages(engine_name):
    """获取指定引擎的支持语言列表"""
    if engine_name in translation_lang:
        engine_data = translation_lang[engine_name]
        source_langs = list(engine_data["source"].keys())
        target_langs = list(engine_data["target"].keys()) 
        return {
            "source": source_langs,
            "target": target_langs,
            "common": list(set(source_langs) & set(target_langs))
        }
    return None

# 使用示例
deepl_langs = get_supported_languages("DeepL")
print(f"DeepL支持语言数: {len(deepl_langs['common'])}")
```

### 语言代码转换

```python
def convert_language_code(language_name, from_engine, to_engine, direction="source"):
    """引擎间语言代码转换"""
    try:
        # 从源引擎确认语言名
        from_codes = translation_lang[from_engine][direction]
        to_codes = translation_lang[to_engine][direction]
        
        if language_name in from_codes and language_name in to_codes:
            return to_codes[language_name]
        return None
    except KeyError:
        return None

# 使用示例:从DeepL到Google Translate的转换
google_code = convert_language_code("Japanese", "DeepL", "Google", "target")
```

### 翻译系统中的集成使用

```python
class TranslationLanguageManager:
    """翻译语言管理类"""
    
    @staticmethod
    def get_language_code(engine, language, direction="target"):
        """安全的语言代码获取"""
        try:
            return translation_lang[engine][direction][language]
        except KeyError:
            return None
    
    @staticmethod
    def is_language_supported(engine, language, direction="target"):
        """语言支持确认"""
        try:
            return language in translation_lang[engine][direction]
        except KeyError:
            return False
    
    @staticmethod
    def get_compatible_engines(source_lang, target_lang):
        """支持两种语言的引擎列表"""
        compatible = []
        for engine in translation_lang:
            source_supported = TranslationLanguageManager.is_language_supported(
                engine, source_lang, "source"
            )
            target_supported = TranslationLanguageManager.is_language_supported(
                engine, target_lang, "target"
            )
            if source_supported and target_supported:
                compatible.append(engine)
        return compatible

# 使用示例
manager = TranslationLanguageManager()

# 支持日语→英语的引擎
engines = manager.get_compatible_engines("Japanese", "English")
print(f"支持的引擎: {engines}")

# 特定引擎的语言代码获取
ja_code = manager.get_language_code("DeepL", "Japanese", "source")
en_code = manager.get_language_code("DeepL", "English", "target")
```

## 引擎特点

### DeepL(免费版)

- **优势**: 高精度、自然翻译
- **限制**: 月使用量限制、API限制
- **支持**: 26种语言

### DeepL API(付费版)

- **优势**: DeepL的高精度、地区语言支持
- **限制**: 按量计费
- **支持**: 地区特定语言变体

### Google Translate

- **优势**: 多语言支持、快速
- **限制**: API限制、精度参差不齐
- **支持**: 100+语言

### Microsoft Translator

- **优势**: 实时翻译、语音支持
- **限制**: 需要API密钥
- **支持**: 70+语言

## 地区变体支持

### 英语的地区差异

```python
# DeepL API的英语变体
"English American": "en-US",    # 美式英语
"English British": "en-GB",     # 英式英语
```

### 葡萄牙语的地区差异

```python
# 巴西葡萄牙语和欧洲葡萄牙语
"Portuguese Brazilian": "pt-BR",
"Portuguese European": "pt-PT",
```

### 中文的字体系统差异

```python
# 简繁体区分
"Chinese Simplified": "zh",     # 简体(中国大陆)
"Chinese Traditional": "zh",    # 繁体(台湾·香港)
```

## 可扩展性

### 新引擎添加

```python
# 新翻译引擎添加示例
translation_lang["NewEngine"] = {
    "source": {
        "Japanese": "jp",
        "English": "en",
        "Korean": "kr"
    },
    "target": {
        "Japanese": "jp",
        "English": "en",
        "Korean": "kr"
    }
}
```

### 新语言添加

```python
# 向现有引擎添加新语言
translation_lang["DeepL"]["source"]["Hindi"] = "hi"
translation_lang["DeepL"]["target"]["Hindi"] = "hi"
```

## 错误处理

### 安全的语言代码获取

```python
def safe_get_language_code(engine, language, direction="target", fallback="en"):
    """带回退功能的语言代码获取"""
    try:
        return translation_lang[engine][direction][language]
    except KeyError:
        # 返回回退语言
        try:
            return translation_lang[engine][direction].get("English", fallback)
        except KeyError:
            return fallback
```

### 语言支持验证

```python
def validate_translation_pair(engine, source_lang, target_lang):
    """翻译对有效性验证"""
    try:
        engine_data = translation_lang[engine]
        source_supported = source_lang in engine_data["source"]
        target_supported = target_lang in engine_data["target"]
        
        return {
            "valid": source_supported and target_supported,
            "source_supported": source_supported,
            "target_supported": target_supported
        }
    except KeyError:
        return {
            "valid": False,
            "source_supported": False,
            "target_supported": False,
            "error": f"Unknown engine: {engine}"
        }
```

## 注意事项

- 引擎的语言代码格式各不相同
- 地区变体的支持情况因引擎而异
- 添加新语言时需确认所有引擎的支持情况
- API限制和计费方式因引擎而异
- 某些语言对的翻译精度可能有差异

## 相关模块

- `translation_translator.py`: 翻译引擎本体
- `translation_utils.py`: 翻译实用工具
- `transcription_languages.py`: 语音识别语言映射
- `config.py`: 翻译语言设置管理
- `controller.py`: 语言选择UI控制

## 最近更新 (2025-10-20)

### CTranslate2 语言结构变更

传统: 权重类型作为顶层键(`translation_lang["m2m100_418M-ct2-int8"]`).

现在: `translation_lang["CTranslate2"][weight_type]["source"|"target"]`的嵌套结构。`model.findTranslationEngines` / `translation_translator`中`engine == "CTranslate2"`时使用`CTRANSLATE2_WEIGHT_TYPE`访问内部字典。

### 外部 YAML 语言映射引入

添加`models/translation/languages/languages.yml`,在`config.init_config()`中调用`loadTranslationLanguages(path=config.PATH_LOCAL)`合并/覆盖到现有`translation_lang`。读取失败时返回空字典作为回退。(添加PyYAML)

### LMStudio / Ollama 翻译模型支持准备

作为新的本地LLM连接添加LMStudio / Ollama。现阶段定义了模型列表·选择用的端点和属性(`SELECTABLE_LMSTUDIO_MODEL_LIST`、`SELECTED_LMSTUDIO_MODEL`、`SELECTABLE_OLLAMA_MODEL_LIST`、`SELECTED_OLLAMA_MODEL`)。语言映射计划通过YAML扩展集成(未实现部分未集成到翻译本体的`translate()`)。

### 模型选择属性名称统一

将Plamo / Gemini / OpenAI的选择模型属性从`PLAMO_MODEL` / `GEMINI_MODEL` / `OPENAI_MODEL`统一为`SELECTED_PLAMO_MODEL` / `SELECTED_GEMINI_MODEL` / `SELECTED_OPENAI_MODEL`。保存键也更新为`SELECTED_*`。

### 影响

| 项目 | 内容 |
|------|------|
| CTranslate2 | 嵌套化需要修改语言引用代码 |
| YAML | 无需代码编辑即可动态添加语言 |
| LLM连接 | 计划通过YAML扩展语言映射(未实现) |
| 属性 | 统一为SELECTED_*提高UI/设置一致性 |
