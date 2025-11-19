# 详细设计文档

此文档记载主要类·函数的详细信息、数据结构、异常情况、线程行为。

## 目录
- Model
- Controller
- Main (mainloop)
- DeviceManager
- Utils
- 模型权重下载和完整性

## Model
- 单例: `model = Model()`
- 延迟初始化: 具备 `init()` 和 `ensure_initialized()`,init 构建重资源(Overlay, Translator, Watchdog, OSC handler 等)。
- 主要职责
  - 翻译/转录相关的启动停止包装器
  - Overlay/OSChandler/WebSocket 的操作
  - 关键词检测(flashtext)和重复检测
  - VRAM 错误检测和回退
- 重要属性(摘录)
  - `translator` : Translator 实例
  - `overlay` / `overlay_image` : Overlay 系
  - `mic_*`, `speaker_*` : 录音、转录器、energy recorder
  - `watchdog` : Watchdog
  - `osc_handler`, `websocket_server`
- 线程控制
  - 使用 threadFnc 运行周期性处理。可以 stop/pause/resume。

## Controller
- 接收 GUI 请求,操作 Model 并将结果返回给 run() 回调。
- 实现各种配置更改(/set/ 和 /get/ 端点)。
- 具有翻译/转录/覆盖层协作逻辑,进行消息格式化(messageFormatter)和 OSC 发送。
- 下载工作在独立线程中进行,通过 run_mapping 通知进度。

## Main (mainloop.Main)
- 通过 readline() 从 stdin 接收并解析 JSON,将 endpoint 和 data 投入队列。
- worker_count 个 handler 线程从 queue 取出并执行 `_call_handler`。
- endpoint 锁标准化: `/set/enable/...` 和 `/set/disable/...` 共享相同的标准化键 `/lock/set/...` 进行互斥控制。
- 标准化错误响应和重试逻辑(status==423 重新入队)。

## DeviceManager
- 单例。初始化轻量,通过 `init()` 设置内部结构,通过 `update()` 获取实际设备。
- Windows 环境使用 COM 事件(pycaw/MMNotificationClient)检测,或通过 PyAudio 轮询构建设备列表。
- 回调设计: 检测到更改时调用 Controller 的回调促进 UI 更新。

## Utils
- `validateDictStructure(data, structure)` : JSON 结构验证。
- `getComputeDeviceList()` / `getBestComputeType()` : 枚举 CPU/CUDA,返回推荐的 compute_type。
- `setupLogger()` / `printLog()` / `printResponse()` / `errorLogging()` : 日志、标准输出格式化、错误记录。
- 网络/套接字/IP 地址检查工具。

## 模型权重下载
- `models.translation.translation_utils` 和 `models.transcription.transcription_whisper` 中有下载/检查函数,验证校验和和文件存在。
- GUI 的请求由 Controller 在异步线程中执行,进度回调通过 run_mapping 传递到前端。

## 边缘情况/异常处理
- 外部 API 的速率限制或认证错误向调用方返回 400 系响应,必要时进行回退实现(切换到 CTranslate2)。
- 执行大型模型时的 VRAM 错误会被检测,禁用相应功能并通知用户。
- 音频设备不存在时返回 NoDevice,由 UI 端处理。

## 测试观点
- 消息接收/发送的端到端: stdin -> handler -> Controller -> Model -> printResponse 流程。
- 设备行为: DeviceManager.update() 能否获取设备列表(通过 PyAudio)。
- 模型下载: 下载成功·失败,校验和验证。
- 日志/错误: errorLogging() 的异常跟踪是否记录到 error.log。
