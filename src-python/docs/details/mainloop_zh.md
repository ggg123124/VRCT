# mainloop.py - VRCT主循环模块

## 概述

管理VRCT应用程序主事件循环的模块。处理来自标准输入的JSON请求,调用适当的控制器方法并返回响应,担当应用程序的核心角色。

## 最近更新 (2025-10-20)

### 新增端点和run_mapping扩展

- 添加VRAM相关错误通知端点: `/run/error_translation_chat_vram_overflow`等5种(翻译/语音识别发送接收分别)
- 本地LLM (LMStudio/Ollama)模型列表通知: `/run/selectable_lmstudio_model_list`, `/run/selectable_ollama_model_list`和选择模型`/run/selected_*_model`
- 与传统的Plamo/Gemini/OpenAI模型获取通知格式统一
- LMStudio/Ollama连接确认端点: 将`/get/data/lmstudio_connection`, `/get/data/ollama_connection`移动到`/run/lmstudio_connection`, `/run/ollama_connection`统一异步通知
- 添加字符转换端点: `/set/data/convert_message_to_romaji`, `/set/data/convert_message_to_hiragana`, `/set/enable/convert_message_to_romaji`, `/set/enable/convert_message_to_hiragana`, `/set/disable/convert_message_to_romaji`, `/set/disable/convert_message_to_hiragana`控制音译功能

### 端点锁定键规范化

- 将`/set/enable/*` `/set/disable/*`的冲突规范化为`/lock/set/<name>`,强化互斥控制
- 锁定获取失败时重新投入队列,通过轻量重试防止死锁

### 并行工作者处理的稳定化

- 处理器处理后短暂`sleep(0.2)`,缓解大量高速连续请求时的线程饥饿
- 423 (Locked)状态时采用固定短期重试而非指数重试,提高响应时间可预测性

### VRAM错误降级联动

- Controller检测VRAM并关闭翻译/降级到CTranslate2后,通过run_mapping向UI反映状态
- 处理器即使错误时也继续线程,以500响应返回`Internal error`并输出日志

### 模型列表动态更新通知

- 认证·连接成功后通过run逐次通知目标模型列表/选择模型 (Plamo/Gemini/OpenAI/LMStudio/Ollama)

### 影响

| 项目 | 内容 |
|------|------|
| 稳定性 | 通过互斥控制和重新队列投入避免冲突时的崩溃 |
| 可观测性 | VRAM/下载进度/模型更新事件通过run立即通知 |
| 可扩展性 | 伴随新增本地LLM引擎添加,统一通用模型通知格式 |
| 响应可预测性 | 固定重试策略使等待时间易读 |
| 降级 | VRAM错误时自动翻译停止和切换到CTranslate2联动 |

## 主要功能

### 请求处理系统

- 接收来自标准输入的JSON格式请求
- 基于端点的路由
- 支持异步·并行处理

### 端点管理

- 类REST端点结构
- 按功能分类端点
- 通过互斥控制实现线程安全

### 初始化系统

- 应用程序配置初始化
- 解决组件间依赖关系
- 分阶段功能启用

## 类结构

### Main 类

```python
class Main:
    def __init__(self, controller_instance: Controller, mapping_data: dict, worker_count: int = 3)
```

- 主循环控制
- 工作线程池管理
- 端点互斥控制

## 端点分类

### 功能控制类

```text
/set/enable/*   - 各功能启用
/set/disable/*  - 各功能禁用
```

### 数据操作类

```text
/get/data/*     - 配置数据获取
/set/data/*     - 配置数据更新
/delete/data/*  - 数据删除
```

### 执行类

```text
/run/*          - 各种处理执行
```

## 主要端点

### 翻译功能

- `/set/enable/translation`: 启用翻译功能
- `/set/disable/translation`: 禁用翻译功能
- `/set/data/selected_translation_engines`: 翻译引擎选择
- `/run/send_message_box`: 消息发送

### 语音识别功能

- `/set/enable/transcription_send`: 启用发送语音识别
- `/set/enable/transcription_receive`: 启用接收语音识别
- `/set/data/selected_transcription_engine`: 语音识别引擎选择

### VR功能

- `/set/data/overlay_small_log_settings`: 小型覆盖层配置
- `/set/data/overlay_large_log_settings`: 大型覆盖层配置

### WebSocket功能

- `/set/enable/websocket_server`: 启用WebSocket服务器
- `/set/data/websocket_host`: 服务器主机配置
- `/set/data/websocket_port`: 服务器端口配置

### 系统管理

- `/run/update_software`: 软件更新
- `/run/download_ctranslate2_weight`: 翻译模型下载
- `/run/download_whisper_weight`: 语音识别模型下载

## 主要方法

### 请求处理

```python
receiver() -> None
```

- 接收来自标准输入的JSON请求
- 适当处理解析错误

```python
handleRequest(endpoint: str, data: Any = None) -> tuple
```

- 执行端点处理
- 返回状态码和结果

```python
handler() -> None
```

- 工作线程主处理
- 从队列获取·处理请求

### 线程管理

```python
startReceiver() -> None
```

- 启动接收器线程

```python
startHandler() -> None
```

- 启动处理器线程池

```python
start() -> None
```

- 启动所有线程

```python
stop(wait: float = 2.0) -> None
```

- 安全停止所有线程

## 使用方法

### 基本用法

```python
from mainloop import main_instance

# 启动主循环
main_instance.start()

# 设置看门狗回调
main_instance.controller.setWatchdogCallback(main_instance.stop)

# 控制器初始化
main_instance.controller.init()
```

### 直接请求处理

```python
# 直接调用端点
result, status = main_instance.handleRequest("/get/data/version", None)
print(f"版本: {result}")

# 启用翻译功能
result, status = main_instance.handleRequest("/set/enable/translation", None)
```

### 来自标准输入的处理

```json
{
    "endpoint": "/run/send_message_box",
    "data": "eyJpZCI6ICIxMjMiLCAibWVzc2FnZSI6ICJIZWxsbyBXb3JsZCJ9"
}
```

## 请求格式

### 输入格式

```json
{
    "endpoint": "string",     // 必需:处理目标端点
    "data": "string|null"     // 可选:Base64编码数据
}
```

### 输出格式

```json
{
    "status": 200,           // HTTP状态码
    "endpoint": "string",    // 已处理的端点
    "result": "any"         // 处理结果
}
```

## 状态码

- `200`: 成功
- `400`: 无效请求
- `404`: 端点不存在
- `423`: 锁定中(功能已禁用)
- `500`: 内部错误

## 互斥控制

### 锁定功能

- enable/disable对共享相同的锁定键
- 防止同一功能的同时执行
- 避免死锁的设计

### 锁定键规范化

```python
/set/enable/translation  -> /lock/set/translation
/set/disable/translation -> /lock/set/translation
```

## 初始化过程

### 分阶段初始化

1. 控制器初始化
2. 设备管理器初始化
3. 模型初始化
4. 各功能分阶段启用

### 初始化mapping

- 从`/get/data/*`端点自动提取初始化配置
- 系统启动时配置恢复

## 日志功能

### 进程日志

- 记录所有请求·响应
- JSON格式的结构化日志

### 错误日志

- 详细记录异常
- 保存堆栈跟踪

## 依赖关系

### 直接依赖

- `controller`: 业务逻辑控制
- `utils`: 工具功能(日志、编码等)

### 间接依赖

- `config`: 配置管理
- `model`: 核心模型功能
- `device_manager`: 设备管理

## 配置项

### 工作者数

```python
DEFAULT_WORKER_COUNT = 3  # 并行处理线程数
```

### 超时

- 队列等待超时: 0.5秒
- 线程停止等待: 2.0秒
- 处理稳定化等待: 0.2秒

## 错误处理

- 适当处理JSON解析错误
- 捕获端点执行错误
- 线程安全的错误日志记录
- 优雅关闭

## 性能特性

### 吞吐量

- 通过多个工作者并行处理
- 非阻塞I/O

### 延迟

- 最小化队列延迟
- 互斥控制导致的临时延迟

### 内存使用

- 请求队列无大小限制(需注意)
- 线程池导致的固定开销

## 注意事项

- 以阻塞方式读取标准输入,假设通过管道使用
- 端点名区分大小写
- Base64数据自动解码
- 长时间阻塞处理可能影响其他请求
