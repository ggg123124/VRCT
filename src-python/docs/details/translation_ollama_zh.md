# translation_ollama.py - Ollama 本地 LLM 翻译客户端

## 概述

将Ollama服务器上运行的本地LLM作为翻译引擎的客户端包装器。通过统一模式提供模型列表获取·模型选择·翻译执行。

## 最近更新 (2025-10-20)

- 新增: 将Ollama集成到翻译引擎组
- 使用`/api/ping`进行连通性确认的简易认证
- 从`/api/tags`提取可用模型列表·排序
- 从YAML (`prompt/translation_ollama.yml`)加载系统提示(`system_prompt`)和支持语言

### 影响

| 项目 | 内容 |
|------|------|
| 可扩展性 | 可利用LAN内本地推理 |
| 可移植性 | 适应GPU/CPU任意配置的Ollama环境 |
| 一致性 | 与其他翻译客户端(OpenAI/Gemini/Plamo/LMStudio)统一API |

## 职责

- 确认到Ollama实例的连接
- 获取模型列表(标签枚举)并排序
- 验证选择的模型并内部保持
- 生成LangChain `ChatOllama`实例
- 组合系统提示和用户输入执行翻译

## 公开API (方法)

```python
class OllamaClient:
    def __init__(root_path: str = None)
    def authenticationCheck() -> bool
    def getModelList() -> list[str]
    def getModel() -> str | None
    def setModel(model: str) -> bool
    def updateClient() -> None
    def translate(text: str, input_lang: str, output_lang: str) -> str
```

### 方法详细

- `authenticationCheck`: 通过`/api/ping`是否返回200判断可用性
- `getModelList`: 仅在认证成功时从`/api/tags`结果提取name
- `setModel`: 仅在已获取模型列表中存在时设置
- `updateClient`: 用最新模型重新生成`ChatOllama`
- `translate`: 向LLM发送system/user消息并规范化合并结果

## 使用示例

```python
client = OllamaClient()
if client.authenticationCheck():
    models = client.getModelList()
    if models:
        client.setModel(models[0])
        client.updateClient()
        translated = client.translate("こんにちは世界", "Japanese", "English")
        print(translated)
```

## 依赖关系

- `requests`: Ping/标签API调用
- `langchain_ollama.ChatOllama`: LangChain LLM包装器
- `translation_languages.translation_lang`: 支持语言集合
- `translation_utils.loadPromptConfig`: 提示YAML加载

## 注意事项

- 服务器默认URL: `http://localhost:11434`
- 模型列表获取依赖运行中的本地服务器状态
- 调用`updateClient()`前无法使用`translate()`

## 限制事项

- 不支持流式传输(streaming=False)
- 错误详细不全面处理(上层降级)

## 相关文档

- `details/translation_translator.md`
- `details/translation_languages.md`
