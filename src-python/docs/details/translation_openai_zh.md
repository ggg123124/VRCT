# translation_openai.py - OpenAI 翻译客户端

## 概述

使用OpenAI API(官方或兼容端点)的通用LLM翻译客户端包装器。提供模型列表获取·认证·模型选择·翻译执行。

## 最近更新 (2025-10-20)

- 使用排除关键词(`whisper`, `embedding`, `image`, `tts`, `audio`, `search`, `transcribe`, `diarize`, `vision`)过滤不适合翻译的模型
- Fine-tune模型(`ft:`)在root以`gpt-`开头时采用
- 集成到从YAML (`prompt/translation_openai.yml`)加载系统提示(`system_prompt`)的配置

### 影响

| 项目 | 内容 |
|------|------|
| 准确性 | 排除不适合模型稳定翻译质量 |
| 可维护性 | 明确过滤逻辑便于重用 |
| 一致性 | 与其他翻译客户端API形状统一 |

## 职责

- 使用OpenAI API Key进行认证确认
- 过滤和排序可用模型
- 验证选择的模型并内部保持
- 生成LangChain `ChatOpenAI`实例
- 通过系统提示执行翻译

## 公开API (方法)

```python
class OpenAIClient:
    def __init__(base_url: str | None = None, root_path: str = None)
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
- `getModelList`: 枚举模型后应用过滤并排序
- `setModel`: 仅接受已获取列表内的模型
- `updateClient`: 用选择的模型重新生成`ChatOpenAI`
- `translate`: 构建系统+用户消息→LLM调用→响应规范化

## 使用示例

```python
client = OpenAIClient()
if client.setAuthKey("OPENAI_API_KEY"):
    models = client.getModelList()
    client.setModel(models[0])
    client.updateClient()
    result = client.translate("こんにちは世界", "Japanese", "English")
    print(result)
```

## 依赖关系

- `openai.OpenAI`: 模型枚举/推理
- `langchain_openai.ChatOpenAI`: LangChain包装器
- `translation_languages.translation_lang`: 支持语言集合
- `translation_utils.loadPromptConfig`: 提示YAML加载

## 注意事项

- `base_url`为None时使用官方端点
- 流式传输禁用(streaming=False)固定
- API Key未设置时`getModelList()`返回空

## 限制事项

- 错误消息详细不全面处理(上层日志记录)
- 翻译结果结构复杂(list/dict)时仅规范化为简单字符串

## 相关文档

- `details/translation_translator.md`
- `details/translation_languages.md`
