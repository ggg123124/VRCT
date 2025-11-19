# translation_gemini.py - Gemini 翻译客户端

## 概述

用于翻译用途的Google Gemini / Gemma系列模型客户端包装器。通过统一接口提供模型列表获取·认证·模型选择·翻译执行。

## 最近更新 (2025-10-20)

- 新增: Gemini客户端集成
- 通过排除关键词(`audio`, `image`, `veo`, `tts`, `robotics`, `computer-use`)过滤非文本导向模型
- 仅采用支持`generateContent`的模型
- 从YAML (`prompt/translation_gemini.yml`)加载系统提示(`system_prompt`)

### 影响

| 项目 | 内容 |
|------|------|
| 准确性 | 排除非文本专业模型稳定翻译质量 |
| 可维护性 | 明确过滤逻辑便于重用 |
| 一致性 | 与其他LLM客户端API形状统一 |

## 职责

- API Key认证确认
- Gemini/Gemma系列模型枚举和过滤
- 模型选择验证并内部保持
- 生成LangChain `ChatGoogleGenerativeAI`实例
- 通过系统提示执行翻译

## 公开API (方法)

```python
class GeminiClient:
    def __init__(root_path: str = None)
    def getModelList() -> list[str]
    def getAuthKey() -> str | None
    def setAuthKey(api_key: str) -> bool
    def getModel() -> str | None
    def setModel(model: str) -> bool
    def updateClient() -> None
    def translate(text: str, input_lang: str, output_lang: str) -> str
```

### 方法详细

- `setAuthKey`: 仅在`_authentication_check`成功时内部保存
- `getModelList`: 应用过滤后排序
- `setModel`: 仅接受已获取模型列表内的
- `updateClient`: 重构`ChatGoogleGenerativeAI`
- `translate`: 构建系统+用户消息→调用→响应规范化

## 使用示例

```python
client = GeminiClient()
if client.setAuthKey("GEMINI_API_KEY"):
    models = client.getModelList()
    if models:
        client.setModel(models[0])
        client.updateClient()
        result = client.translate("こんにちは世界", "Japanese", "English")
        print(result)
```

## 依赖关系

- `google.genai`: 模型枚举/认证
- `langchain_google_genai.ChatGoogleGenerativeAI`: LangChain包装器
- `translation_languages.translation_lang`: 支持语言集合
- `translation_utils.loadPromptConfig`: 提示YAML加载

## 注意事项

- 非文本导向模型(图像/音频/机器人等)被排除
- 流式传输禁用(streaming=False)
- 必需API Key(未设置时getModelList不可用)

## 限制事项

- 不全面处理详细错误(上层日志记录/降级)
- 复杂响应结构仅规范化为简单字符串

## 相关文档

- `details/translation_translator.md`
- `details/translation_languages.md`
