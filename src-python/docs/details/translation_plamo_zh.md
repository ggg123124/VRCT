# translation_plamo.py - Plamo 翻译客户端

## 概述

使用Preferred Networks提供的Plamo API的翻译向LLM客户端包装器。通过统一接口提供模型列表获取·认证·模型选择·翻译执行。

## 最近更新 (2025-10-20)

- 新增: Plamo客户端集成
- 从YAML (`prompt/translation_plamo.yml`)加载提示配置(系统提示`system_prompt`)
- 获取模型列表后排序以确保可重现性

### 影响

| 项目 | 内容 |
|------|------|
| 可扩展性 | 支持日本API扩大选择 |
| 可维护性 | 与其他LLM客户端相同结构易于维护 |
| 一致性 | 方法命名/职责统一化 |

## 职责

- API Key认证确认
- 枚举可用模型并排序
- 模型选择的验证
- 生成LangChain `ChatOpenAI`实例
- 通过系统提示执行翻译

## 公开API (方法)

```python
class PlamoClient:
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
- `getModelList`: 已认证状态下枚举模型→排序
- `setModel`: 仅接受枚举列表内模型
- `updateClient`: 重构`ChatOpenAI`
- `translate`: 用系统+用户消息推理并规范化响应

## 使用示例

```python
client = PlamoClient()
if client.setAuthKey("PLAMO_API_KEY"):
    models = client.getModelList()
    if models:
        client.setModel(models[0])
        client.updateClient()
        result = client.translate("こんにちは世界", "Japanese", "English")
        print(result)
```

## 依赖关系

- `openai.OpenAI`: Plamo兼容API调用
- `langchain_openai.ChatOpenAI`: LangChain包装器
- `translation_languages.translation_lang`: 支持语言集合
- `translation_utils.loadPromptConfig`: 提示YAML加载

## 注意事项

- BASE_URL固定: `https://api.platform.preferredai.jp/v1`
- API Key未设置时无法获取模型列表
- 流式传输禁用(streaming=False)

## 限制事项

- 详细错误不全面处理(上层日志/降级)
- 翻译结果结构复杂时仅规范化为简单字符串

## 相关文档

- `details/translation_translator.md`
- `details/translation_languages.md`
