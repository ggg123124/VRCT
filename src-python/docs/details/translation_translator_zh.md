# translation_translator.py - 翻译引擎集成类

## 概述

集成管理多个翻译引擎的高级翻译接口。统一处理DeepL、Google、Bing、Papago、CTranslate2等多种翻译服务,提供错误自动回退功能和认证管理。

## 主要功能

### 多引擎集成
- DeepL(免费版·API版)
- Google Translate(Web爬取)
- Microsoft Translator(Bing)
- Papago Translator
- CTranslate2(本地翻译)

### 统一接口
- 隐藏引擎依赖的单一翻译方法
- 自动错误处理·回退
- 认证信息统一管理

### 离线翻译支持
- 通过CTranslate2完全离线翻译
- 支持多种模型大小(small/large)
- CUDA加速支持

## 类结构

### Translator 类
```python
class Translator:
    def __init__(self) -> None:
        self.deepl_client: Optional[DeepLClient] = None
        self.ctranslate2_translator: Any = None
        self.ctranslate2_tokenizer: Any = None
        self.is_loaded_ctranslate2_model: bool = False
        self.is_changed_translator_parameters: bool = False
        self.is_enable_translators: bool = ENABLE_TRANSLATORS
```

翻译功能的核心类

#### 属性
- **deepl_client**: DeepL API客户端
- **ctranslate2_translator**: 本地翻译模型
- **ctranslate2_tokenizer**: CTranslate2分词器
- **is_loaded_ctranslate2_model**: 本地模型加载状态
- **is_enable_translators**: Web翻译服务可用标志

## 主要方法

### 翻译执行

```python
translate(translator_name: str, source_language: str, target_language: str, 
          target_country: str, message: str) -> Any
```

统一翻译接口

#### 参数
- **translator_name**: 翻译引擎名("DeepL", "Google", "CTranslate2"等)
- **source_language**: 源语言
- **target_language**: 目标语言
- **target_country**: 目标国家·地区
- **message**: 翻译对象文本

#### 返回值
- **str**: 翻译结果(成功时)
- **False**: 翻译失败时

### DeepL认证管理

```python
authenticationDeepLAuthKey(authkey: str) -> bool
```

DeepL API密钥的认证和设置

#### 参数
- **authkey**: DeepL API密钥

#### 返回值
- **bool**: 认证成功与否

### CTranslate2管理

```python
changeCTranslate2Model(path: str, model_type: str, device: str = "cpu",
                      device_index: int = 0, compute_type: str = "auto") -> None
```

加载·更改本地翻译模型

#### 参数
- **path**: 模型文件基础路径
- **model_type**: 模型大小("small"/"large")
- **device**: 计算设备("cpu"/"cuda")
- **device_index**: 设备索引
- **compute_type**: 计算精度类型

### 状态管理

```python
isLoadedCTranslate2Model() -> bool
```

确认CTranslate2模型加载状态

```python
isChangedTranslatorParameters() -> bool
setChangedTranslatorParameters(is_changed: bool) -> None
```

管理翻译设置更改标志

## 使用方法

### 基本翻译

```python
from models.translation.translation_translator import Translator

# 初始化翻译器
translator = Translator()

# 使用Google翻译
result = translator.translate(
    translator_name="Google",
    source_language="Japanese",
    target_language="English", 
    target_country="United States",
    message="你好,世界!"
)

if result != False:
    print(f"翻译结果: {result}")  # "Hello, world!"
else:
    print("翻译失败")
```

### 使用DeepL API

```python
# 设置DeepL API密钥
api_key = "your-deepl-api-key"
auth_success = translator.authenticationDeepLAuthKey(api_key)

if auth_success:
    print("DeepL API认证成功")
    
    # 使用DeepL API翻译
    result = translator.translate(
        translator_name="DeepL_API",
        source_language="English",
        target_language="Japanese",
        target_country="Japan", 
        message="Hello, world!"
    )
    print(f"DeepL翻译: {result}")
else:
    print("DeepL API认证失败")
```

### 使用本地翻译(CTranslate2)

```python
# 加载本地模型
translator.changeCTranslate2Model(
    path=".",                    # 应用程序根目录
    model_type="small",          # 使用small模型
    device="cuda",               # 使用GPU
    device_index=0,
    compute_type="float16"       # 半精度加速
)

# 确认模型加载
if translator.isLoadedCTranslate2Model():
    print("CTranslate2模型加载完成")
    
    # 执行本地翻译
    result = translator.translate(
        translator_name="CTranslate2",
        source_language="Japanese",
        target_language="English",
        target_country="United States",
        message="机器翻译测试"
    )
    print(f"本地翻译: {result}")
else:
    print("CTranslate2模型加载失败")
```

### 带错误处理的翻译

```python
def safe_translate(translator, message, source_lang="Japanese", target_lang="English"):
    """安全的翻译处理"""
    # 翻译引擎优先级
    engines = ["DeepL_API", "DeepL", "Google", "CTranslate2"]
    
    for engine in engines:
        try:
            result = translator.translate(
                translator_name=engine,
                source_language=source_lang,
                target_language=target_lang,
                target_country="United States",
                message=message
            )
            
            if result != False:
                print(f"{engine}翻译成功: {result}")
                return result
            else:
                print(f"{engine}翻译失败,尝试下一个引擎")
                
        except Exception as e:
            print(f"{engine}错误: {e}")
            continue
    
    print("所有翻译引擎均失败")
    return None

# 使用示例
result = safe_translate(translator, "你好")
```

### 翻译设置管理

```python
# 确认设置更改标志
if translator.isChangedTranslatorParameters():
    print("翻译设置已更改")
    
    # 应用设置更改(例:重新加载模型)
    translator.changeCTranslate2Model(".", "small", "cpu")
    
    # 重置标志
    translator.setChangedTranslatorParameters(False)
```

## 翻译引擎比较

### DeepL API(付费)
- **精度**: 最高水平
- **速度**: 快速
- **限制**: API使用费、月限制
- **支持**: 26种语言、地区差异

### DeepL(免费)
- **精度**: 高质量
- **速度**: 中等
- **限制**: 月使用量限制、字数限制
- **支持**: 26种语言

### Google Translate
- **精度**: 良好
- **速度**: 快速
- **限制**: 访问频率限制
- **支持**: 100+语言

### CTranslate2(本地)
- **精度**: 中~高(取决于模型)
- **速度**: 快速(使用GPU时)
- **限制**: 无(离线)
- **支持**: 主要语言对

### 其他(Bing, Papago等)
- **精度**: 中等
- **速度**: 中等
- **限制**: 服务依赖
- **支持**: 服务特定

## CTranslate2详细信息

### 支持的模型
```python
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

### 性能特性

#### small 模型
- **大小**: ~400MB
- **内存**: ~1GB RAM
- **VRAM**: ~500MB(使用CUDA时)
- **速度**: 快速
- **精度**: 良好

#### large 模型
- **大小**: ~4.8GB
- **内存**: ~6GB RAM  
- **VRAM**: ~3GB(使用CUDA时)
- **速度**: 中等
- **精度**: 高质量

### 计算类型设置
```python
# 使用CPU时
compute_type = "int8"          # 注重速度

# 使用CUDA时
compute_type = "float16"       # 注重平衡
compute_type = "int8_float16"  # 注重内存效率
```

## 错误处理

### 网络错误
- 连接超时
- API限制超出
- 服务临时停止

### 认证错误
- 无效的API密钥
- 账户已过期
- 使用量上限

### 模型错误
- 文件损坏
- VRAM不足
- 不支持的语言对

### 应对措施
```python
def robust_translation(translator, message, source_lang, target_lang):
    """健壮的翻译处理"""
    # 首先尝试在线翻译
    online_engines = ["DeepL_API", "DeepL", "Google"]
    
    for engine in online_engines:
        try:
            result = translator.translate(engine, source_lang, target_lang, "", message)
            if result != False:
                return result
        except Exception as e:
            print(f"{engine}错误: {e}")
            continue
    
    # 在线翻译全部失败时回退到本地翻译
    try:
        if not translator.isLoadedCTranslate2Model():
            translator.changeCTranslate2Model(".", "small", "cpu")
            
        result = translator.translate("CTranslate2", source_lang, target_lang, "", message)
        if result != False:
            return result
    except Exception as e:
        print(f"本地翻译错误: {e}")
    
    return "翻译失败"
```

## 依赖关系

### 必需依赖
- `translation_languages`: 语言代码管理
- `translation_utils`: CTranslate2实用工具
- `utils`: 错误日志、计算设备管理

### 可选依赖
- `deepl`: DeepL API库
- `translators`: Web翻译服务库
- `ctranslate2`: 本地翻译引擎
- `transformers`: 分词器

## 配置要求

### 环境变量
- `DEEPL_AUTH_KEY`: DeepL API密钥(可选)

### 文件配置
```
root/
└── weights/
    └── ctranslate2/
        ├── m2m100_418m/     # small模型
        └── m2m100_12b/      # large模型
```

## 注意事项

- Web翻译服务注意使用限制
- CTranslate2首次加载需要时间
- 使用GPU时注意VRAM消耗
- 需要妥善管理API认证信息
- 长文翻译时推荐分割处理

## 相关模块

- `translation_languages.py`: 语言代码映射
- `translation_utils.py`: CTranslate2实用工具
- `config.py`: 翻译设置管理
- `model.py`: 翻译功能集成
- `controller.py`: 翻译控制接口

## 最近更新 (2025-10-20)

### 新增本地 LLM 引擎

添加LMStudio / Ollama作为翻译引擎。连接确认后获取模型列表(`SELECTABLE_LMSTUDIO_MODEL_LIST` / `SELECTABLE_OLLAMA_MODEL_LIST`),未选择时自动选择首个模型(`SELECTED_LMSTUDIO_MODEL` / `SELECTED_OLLAMA_MODEL`)。目前与CTranslate2类似假定本地运行,翻译函数侧为将来集成(温度等参数)保持抽象化。

### 模型选择属性名称统一

将Plamo / Gemini / OpenAI的选择模型属性更改为`SELECTED_*`格式。旧名称(`PLAMO_MODEL` / `GEMINI_MODEL` / `OPENAI_MODEL`)停止使用。自动认证后的模型列表更新逻辑中未选择时补充首个。

### OpenAI / Gemini / Plamo 认证后模型列表自动更新

Auth设置方法完成时重新获取`SELECTABLE_*_MODEL_LIST`,不足时推送到UI。OpenAI在设置密钥后立即反映最新模型列表以加速。Gemini / Plamo也通过调用`updateTranslator*Client()`重新生成客户端。

### CTranslate2 语言嵌套化支持

结构更改为`translation_lang["CTranslate2"][weight_type]["source"|"target"]`。通过`CTRANSLATE2_WEIGHT_TYPE`引用权重类型的语言集合。Translator内在`translator_name == "CTranslate2"`分支中引用weight_type进行语言判定的实现变更。

### YAML 语言映射引入

读取外部文件`languages.yml`动态扩展翻译引擎的支持语言。添加新语言只需编辑YAML(无需重新部署代码)。读取失败时返回空字典作为回退保留现有硬编码。

### VRAM 错误检测和回退

DeepL / Plamo / Gemini / OpenAI执行时检测VRAM不足自动切换到CTranslate2并停止翻译(`ENABLE_TRANSLATION=False`)。用户通知后再次启用时尝试重新初始化。为提高稳定性在日志中记录VRAM错误详情。

### 分词器路径修正

修正CTranslate2分词器下载处理中保存目录创建和路径使用顺序不一致问题。降低首次启动失败率。

### 全语言对综合测试引入

在`backend_test.py`中添加`test_translate_all_language_pairs()`。列举多引擎·全语言对执行生成`translation_test_results.json`。用于早期检测失败对和验证YAML添加语言。

### 影响

| 项目 | 内容 |
|------|------|
| 本地LLM | 扩充离线翻译候选(LMStudio/Ollama) |
| 属性统一 | SELECTED_*命名提高一致性和可维护性 |
| CTranslate2结构 | 可针对每个权重类型引用最优语言集合 |
| YAML外部化 | 语言添加/删除仅需编辑配置文件 |
| VRAM检测 | 错误时自动停止+切换轻量引擎提高稳定性 |
| Tokenizer修正 | 减少首次设置失败 |
| 综合测试 | 全面保证语言组合质量 |
