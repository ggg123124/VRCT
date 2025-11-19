# 规格说明书

## 概述

- 项目名称: VRCT (VR Chat Translator)
- 目的: 实时转录麦克风输入和扬声器输出并进行翻译,通过 VR 覆盖层或 OSC/WebSocket 发送到外部的后端逻辑。
- 语言: Python

## 目标用户

- 希望在 VR 环境中使用实时翻译·转录的终端用户
- 与前端(GUI)或 VR 客户端(OSC)协作的应用程序开发者

## 主要功能(功能需求)

### 1. 音频采集·转录
   - 从麦克风(发送)和扬声器(接收)获取音频,使用本地 Whisper(faster-whisper)或外部服务转换为文本。
   - 监控音频能量(音量),基于阈值进行检测。

### 2. 翻译
   - 支持多个后端: DeepL / DeepL API / 各种云翻译 / 本地 CTranslate2 模型。
   - 批量翻译到多个输出语言,翻译引擎回退(如 CTranslate2)。
   - 翻译模型的下载和管理功能。

### 3. 显示·通知
   - 为 OpenVR 覆盖层(small/large)生成和更新图像。
   - 通过 OSC 向 VR 发送消息(typing/通知等)。
   - 通过 WebSocket 服务器向外部客户端进行 JSON 广播。

### 4. 输入输出接口
   - 基于 stdin 行的 JSON 命令接收(mainloop 实现)。
   - 向 stdout 输出结构化的 JSON 响应(printResponse/printLog)。

### 5. 配置·持久化
   - 使用基于 JSON 的配置文件(通过 `config.py` 读写和防抖保存)。

### 6. 日志和监控
   - 使用轮换管理进程日志(process.log)和错误日志(error.log)。
   - Watchdog 机制定期进行存活检查·回调。

## 非功能需求

- 平台: 主要针对 Windows(音频部分使用 WASAPI)。考虑跨平台的导入安全性。
- 可用性: 即使在没有外部依赖(PyAudio, CUDA, ctranslate2 等)的环境中也能安全导入,功能降级后运行。
- 性能: 使用本地模型时利用 GPU 确保计算性能。实现 compute type 选择逻辑。
- 安全性: 外部 API 密钥(如 DeepL)在配置中处理,代码中避免明文保存(保存到配置文件)。

## 运行流程

- 启动: 运行接受 stdin 命令的 mainloop。必要的初始化采用延迟执行(lazy init)。
- 模型重量下载: CTranslate2/Whisper 权重下载到 `weights/` 目录,通过校验和等确认完整性。
- 故障时: 异常通过 utils.errorLogging() 将跟踪输出到 error.log。重要功能有回退实现。

## 接口(摘录)

- stdin(JSON): {"endpoint": "/set/..." | "/get/..." | "/run/...", "data": <base64(JSON)|any>}
- stdout(JSON): printResponse/printLog 输出标准化响应(status, endpoint, result 等)。

## 依赖关系(包括可选)

- 必需(实现时假设): requests, packaging, flashtext, pillow, pyaudiowpatch, speech_recognition
- 本地推荐: faster-whisper, ctranslate2, torch(使用 GPU 时)
- Windows 特定(音频回环): pycaw, comtypes

参考: 作为实现上的安全设计,可选导入用 try/except 保护,即使缺少依赖也不会在导入时崩溃。

## 最近更新 (2025-10-20 translate_api 分支)

本章仅记录对现有规格的差异。基于代码库的事实更新点。

### 翻译引擎/模型管理的扩展

- OpenAI / Plamo / Gemini 的选择模型属性从 `PLAMO_MODEL` / `GEMINI_MODEL` / `OPENAI_MODEL` 重命名为 `SELECTED_PLAMO_MODEL` / `SELECTED_GEMINI_MODEL` / `SELECTED_OPENAI_MODEL`(旧名称从保存对象迁移)。
- 新本地 LLM 连接: LMStudio (`LMSTUDIO_URL`, `SELECTABLE_LMSTUDIO_MODEL_LIST`, `SELECTED_LMSTUDIO_MODEL`)。
- 新本地 LLM 连接: Ollama (`SELECTABLE_OLLAMA_MODEL_LIST`, `SELECTED_OLLAMA_MODEL`)。
- 设置 OpenAI 认证密钥时自动获取模型列表(`SELECTABLE_OPENAI_MODEL_LIST`),未选择时回退到第一个候选。统一方法名 `OpenAi` → `OpenAI`。

### 端点添加/更改

在 `mainloop.py` 的 `mapping` / `run_mapping` 中添加以下内容:

- `/get/data/selectable_lmstudio_model_list`, `/get/data/selected_lmstudio_model`, `/set/data/selected_lmstudio_model`, `/get/data/lmstudio_url`, `/set/data/lmstudio_url`
- `/get/data/ollama_connection`, `/get/data/selectable_ollama_model_list`, `/get/data/selected_ollama_model`, `/set/data/selected_ollama_model`
- OpenAI 系: `getOpenAIAuthKey`, `setOpenAIAuthKey`, `delOpenAIAuthKey`, `getOpenAIModelList`, `getOpenAIModel`, `setOpenAIModel` 名称统一。

### 翻译语言定义的结构变更

- CTranslate2 的语言定义从顶层直接键(例: `m2m100_418M-ct2-int8`)重组为 `translation_lang['CTranslate2'][weight_type]` 的嵌套结构。使用端的兼容逻辑(`model.findTranslationEngines`)修改为通过 weight_type 引用。
- 新增 YAML 语言映射文件 `models/translation/languages/languages.yml`。在 `config.init_config()` 中调用 `loadTranslationLanguages()` 集成(失败时回退到空字典)。

### 提示文件整理

- 从 `translation_gemini.yml`, `translation_lmstudio.yml` 中删除 `supported_languages` 块,在 `system_prompt` 中简化。

### 资源/PyInstaller

- 在 PyInstaller spec (`backend.spec`, `backend_cuda.spec`) 的 `datas` 中添加 `./src-python/models/translation/prompt` 和 `./src-python/models/translation/languages`。
- 字体位置从 `fonts/` 直接下移动到 `src-python/models/overlay/fonts/`,在 `overlay_image.py` 中添加构建时(`_internal/fonts`)和开发时的动态搜索逻辑。

### 依赖包添加

- 在 `requirements.txt` / `requirements_cuda.txt` 中添加 `PyYAML==6.0.2`(YAML 读取), `google-genai==1.45.0`, `grpcio==1.67.1`。

### 认证处理微调

- Plamo / Gemini 认证方法中传递 `root_path=config.PATH_LOCAL` 以统一本地引用。
- OpenAI 模型设置方法名称从 `setTranslatorOpenAiModel` 更改为 `setTranslatorOpenAIModel`。

### 测试扩展

- 在 `backend_test.py` 中添加全语言对翻译覆盖测试 `test_translate_all_language_pairs()`。结果保存为 `translation_test_results.json`。

### 内部工具修正

- `downloadCTranslate2Tokenizer()` 正确创建 `tokenizer_path` 并使用 `transformers.AutoTokenizer.from_pretrained(tokenizer, cache_dir=tokenizer_path)`。

### 影响范围汇总

| 区分 | 影响内容 |
|------|----------|
| 配置 | 新属性/现有名称更改(`SELECTED_*`, `LMSTUDIO_URL`) |
| 端点 | LMStudio / Ollama / OpenAI 名称统一添加 |
| 翻译语言 | CTranslate2 嵌套结构/引入 YAML 映射 |
| 资源 | PyInstaller datas 添加/字体路径迁移 |
| 依赖 | 添加 PyYAML / google-genai / grpcio |
| 认证 | OpenAI/Plamo/Gemini 认证后模型列表更新 & 添加 root_path 参数 |
| 测试 | 添加全语言对覆盖测试 |
| 工具 | Tokenizer 下载处理修正 |

### 许可证影响

添加的依赖不会强制更改现有 LICENSE 的记载范围,不需要更新许可证文本(在当前 OSS 许可证允许范围内)。
