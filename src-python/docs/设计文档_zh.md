# 设计文档

## 概述
- 本设计文档描述应用程序的架构、主要组件、并行化模型、错误处理策略、配置保存方针。

## 架构概述
### 层级结构
  - mainloop: 基于 stdin 的命令接收,通过工作线程(多线程)执行。
  - controller: GUI/前端操作与模型的中介。`Controller` 执行业务逻辑。
  - model: 提供实际功能(翻译、转录、覆盖层、OSC、WebSocket、设备管理)的门面式单例。
  - models/*: 按领域分类的实现(Translator, AudioTranscriber, Overlay, WebSocketServer ...)。
  - device_manager: 音频设备检测·监控(Windows 情况下使用 WASAPI/pycaw)。
  - utils: 通用工具(日志、网络检查、compute device 枚举等)。

## 初始化策略
- 重初始化(GPU 模型加载、OpenVR 初始化等)不在导入时进行,而在 `model.init()` 或请求时的 `ensure_initialized()` 中延迟执行。
- `DeviceManager` 在导入时进行轻量级 init,监控线程通过 `startMonitoring()` 开始。

## 并行化·同步模型
- mainloop.Main 有 1 个接收线程(stdin 读取)和 N 个处理工作线程。
- 每个请求放入队列,由 handler() 处理。
- 启用/禁用切换(/set/enable/**, /set/disable/**)通过标准化键分配 Lock 以避免同一资源竞争。
- 模型内部使用 threadFnc(Thread 包装器)实现周期性发送处理和监控处理。
- Audio 录音和转录使用专用 Queue,分离 Producer(Recorder)和 Consumer(AudioTranscriber)。

## 错误处理
- 所有外部调用都用 try/except 保护,通过 `utils.errorLogging()` 将跟踪输出到 error.log。
- JSON 序列化失败时输出回退 JSON 到 stdout,不停止进程。
- VRAM 相关错误通过 model.detectVRAMError() 判断,禁用相应功能(如翻译)并通知用户。

## 配置管理
- `config.py` 持有单一的 Config 单例,变更通过防抖保存到 JSON 文件。
- GUI 的操作由 Controller 接收并更新 Config。

## 日志
- 通过 `utils.setupLogger` 使用轮换文件处理器实现日志(process.log / error.log)。
- 向 stdout 输出结构化日志与前端通信。

## 接口列表(摘录)
- STDIN/STDOUT 协议: mainloop 的 JSON 输入输出(详见 `mainloop.py` 的 mapping)
- OSC: `models.osc.OSCHandler` 管理 OSC 收发和 OSCQuery
- WebSocket: `models.websocket.WebSocketServer` 负责客户端管理和消息广播

## 线程图(要点)
- main_thread: 主线程(stdin 读取,队列投入)
- handler_threads: 从队列取出处理
- device_manager.th_monitoring: 设备监控
- model.mic_print_transcript / speaker_print_transcript: 音频 -> 翻译结果发送循环
- websocket_server_thread: 在独立线程中运行 WebSocket 服务器的 asyncio 循环

## 可扩展性·兼容性设计
- 依赖关系通过 try/except 保护作为可选功能处理(例: 即使没有 faster-whisper 导入也成功)。
- 翻译引擎通过后端名称抽象化,Translator 类提供统一接口。

## 运维考虑
- 提供下载大型模型文件(Whisper, CTranslate2)的机制,向 GUI 报告进度。
- GPU 计算类型通过 utils.getBestComputeType 选择,检测到不当设置时进行回退。
