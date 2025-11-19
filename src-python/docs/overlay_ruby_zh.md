# 小型日志 Ruby 显示功能 (Ruby Overlay for Small Log)

## 概要
小型日志 (Small Log Overlay) 包含日语原文时,可以在原文消息上方显示 2 段 ruby 注音,上段为罗马字(hepburn),下段为平假名(hira)。现阶段不为翻译行添加 ruby 注音。

## 启用条件
- 原文 `message` 存在且非空字符串。
- 在 `model.createOverlayImageSmallLog` 内自动调用 `convertMessageToTransliteration(..., hiragana=True, romaji=True)` 生成 token。
- 生成的 token 中包含 `hepburn` 或 `hira`。

## 大型日志 (Large Log) 扩展

大型日志也支持 token 单位的 ruby 绘制。`createOverlayImageLargeLog` / `createTextboxLargeLog` 系列 API 添加了以下参数,可实现相同的 ruby 输出。

- transliteration_tokens: Optional[List[dict]] — 原文用 token(orig/hira/hepburn)
- translation_transliteration_tokens: Optional[List[List[dict]] | List[dict]] — 每个翻译的 token 数组,或首个翻译用的扁平 List[dict]
- ruby_font_scale: float — Ruby 字体倍率(相对于原文字体大小的比例)
- ruby_line_spacing: int — Ruby 行间距像素

对应行为:

- 仅存在原文且该原文有 token 时,为原文添加 token 单位的 ruby。

- 同时存在原文和翻译时,原则上抑制原文 ruby,为翻译侧添加 ruby(翻译侧有 token 时)。

- `translation_transliteration_tokens` 接受两种输入格式:

	- List[List[dict]] — 每个翻译行的 tokens 数组(推荐)

	- List[dict] — 扁平 tokens 数组(应用于第一个翻译行)

后备方案:

- 当 token 单位布局横向溢出或存在换行时,自动回退到现有的块级 ruby(在 1 行块中显示 romaji 上 / hira 下)。

注意事项:

- 为保持现有显示逻辑的兼容性,参数可省略(None/[])。
- 传递扁平 `translation_transliteration_tokens` 时仅应用于第一个翻译。若要为多个翻译分别传递 ruby,请使用 List[List[dict]] 格式。

## 配置键 (`config.OVERLAY_SMALL_LOG_SETTINGS`)
| 键 | 类型 | 初始值 | 说明 |
| ---- | --- | ------ | ---- |
| ruby_font_scale | float | 0.5 | Ruby 字符大小倍率 (原文字体大小 * 倍率)。安全范围 0.05〜3.0 |
| ruby_line_spacing | int | 4 | 罗马字行与平假名行的垂直间距 (px)。0〜200 |

## 布局规格

1. Ruby 块 (romaji 上 / hiragana 下) 居中绘制。

2. 下方垂直连接传统正文文本框。

3. 字体族与正文相同 (对应语言的 NotoSans 系)。

4. 不存在 ruby 时仅显示传统样式。

## 后备方案

- Ruby 生成过程中发生异常时记录日志,仅显示正文无 ruby。

- Token 为空时(两者均为 False)使用传统显示。

## 示例

以下是使用 `createOverlayImageLargeLog` 仅为翻译侧传递 ruby 的示例(传递扁平 tokens 和分别传递每个翻译的 tokens):

```python
# 传递扁平 tokens 应用于第一个翻译
overlay.createOverlayImageLargeLog("receive", "こんにちは、世界!", "Japanese", ["Hello, World!"], ["English"], transliteration_tokens=[], translation_transliteration_tokens=[
	{"orig": "こんにちは", "hira": "こんにちは", "hepburn": "konnichiha"},
	{"orig": "世界", "hira": "せかい", "hepburn": "sekai"},
])

# 为每个翻译分别给定 tokens(推荐)
overlay.createOverlayImageLargeLog("receive", "こんにちは、世界!", "Japanese", ["Hello, World!"], ["English"], transliteration_tokens=[], translation_transliteration_tokens=[
	[
		{"orig": "Hello", "hira": "", "hepburn": "Hello"},
		{"orig": "World", "hira": "", "hepburn": "World"},
	]
])
```

## 未来扩展候选
- 为翻译行添加 ruby 的选项。
- Token 单位的宽度居中和换行。
- 高级宽度测量 (改进可变宽度字体支持)。

## 简易测试
执行 `src-python/overlay_ruby_test.py` 将生成 `overlay_small_ruby_test.png`,可确认纵向顺序和位置。

```bash
# PowerShell (激活虚拟环境后)
python src-python/overlay_ruby_test.py
```

## 注意
UI 缩放仅更改 OpenVR 端的显示大小,不直接更改图像内部字体大小。Ruby 可见性低时请调整 `ruby_font_scale`。
