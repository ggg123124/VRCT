# translation_lmstudio.py - LMStudio 本地 LLM 翻译客户端

## 概述

利用LMStudio兼容OpenAI API的本地LLM翻译客户端包装器。通过统一接口提供模型列表获取·模型选择·翻译处理。

## 最近更新 (2025-10-20)

- 新增: 将本地LLM (LMStudio)集成到翻译引擎组
- 通过`getModelList()`从当前运行实例获取可用模型
- `setModel()`成功时调用`updateClient()`重构LangChain `ChatOpenAI`
- 从YAML (`prompt/translation_lmstudio.yml`)加载系统提示(`system_prompt`)和支持语言

### 影响

| 项目 | 内容 |
|------|------|
| 可扩展性 | 可利用无需网络的本地推理 |
| 一致性 | 与其他API客户端(OpenAI/Plamo/Gemini/Ollama)相同方法构成 |
| 可维护性 | 将翻译逻辑集中到通用格式 |

## 职责

- 确认到LMStudio端点的连通性(认证替代)
- 收集可用模型列表并排序
- 验证选择的模型并内部保持
- 生成LangChain包装器实例
- 通过系统提示执行带指示的翻译

## 公开API (方法)

```python
class LMStudioClient:
    def __init__(base_url: str | None = None, root_path: str = None)
    def getBaseURL() -> str | None
    def setBaseURL(base_url: str | None) -> bool
    def getModelList() -> list[str]
    def getModel() -> str | None
    def setModel(model: str) -> bool
    def updateClient() -> None
    def translate(text: str, input_lang: str, output_lang: str) -> str
```

### 方法详细

- `setBaseURL`: 仅在连通性确认(_authentication_check)成功时内部更新
- `getModelList`: 用`OpenAI`客户端枚举`/models`并提取id
- `setModel`: 仅接受`getModelList`内的模型名
- `updateClient`: 用最新模型重新生成`ChatOpenAI`实例
- `translate`: 用系统/用户消息向LLM查询并规范化字符串响应

## 使用示例

```python
client = LMStudioClient(base_url="http://localhost:1234/v1")
models = client.getModelList()
if models:
    client.setModel(models[0])
    client.updateClient()
    translated = client.translate("こんにちは世界", "Japanese", "English")
    print(translated)
```

## 依赖关系

- `openai.OpenAI`: LMStudio OpenAI兼容API调用
- `langchain_openai.ChatOpenAI`: LangChain抽象化
- `translation_languages.translation_lang`: 支持语言集合
- `translation_utils.loadPromptConfig`: 提示YAML加载

## 注意事项

- `api_key`使用固定字符串"lmstudio"(LMStudio侧不需要)
- 模型列表获取依赖端点兼容性(旧版本可能不支持)
- 调用`updateClient()`前无法使用`translate()`

## 限制事项

- 不支持流式传输(streaming=False)
- 错误处理不全面,详细原因需在上层处理

## 相关文档

- `details/translation_translator.md`
- `details/translation_languages.md`
