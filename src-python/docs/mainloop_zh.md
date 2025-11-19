# mainloop.py 设计文档

## 概述

`mainloop.py` 是 VRCT 应用程序的后端入口点,负责通过 stdin/stdout 与前端(Tauri/React UI)通信。实现基于 JSON 的请求/响应协议,通过多个工作线程提供并行处理和排他控制。

## 主要组件

### 1. 全局变量

#### `run_mapping` (dict)

前端通知用端点映射。Controller 通过 `run()` 回调向前端通知状态变化时使用。

**主要端点:**

- `/run/enable_translation` - 翻译功能启用/禁用状态
- `/run/transcription_mic_message` - 麦克风语音识别结果
- `/run/transcription_speaker_message` - 扬声器语音识别结果
- `/run/error_*` - 各种错误通知
- `/run/initialization_complete` - 初始化完成通知

#### `mapping` (dict)

处理来自前端请求的函数映射。每个端点包含:

- `status`: 锁状态(True: 可处理, False: 锁定中)
- `variable`: 要执行的 Controller 方法

**端点分类:**

- `/get/data/*` - 获取配置值(初始化时使用)
- `/set/data/*` - 更新配置值
- `/set/enable/*` - 启用功能
- `/set/disable/*` - 禁用功能
- `/run/*` - 执行操作(消息发送、下载等)

#### `init_mapping` (dict)

初始化时执行的 `/get/data/*` 端点子集。用于应用程序启动时向前端发送所有配置值。

### 2. Main 类

#### 构造函数 `__init__(controller_instance, mapping_data, worker_count)`

**参数:**

- `controller_instance`: Controller 实例
- `mapping_data`: 端点映射字典
- `worker_count`: 处理工作线程数(默认: 3)

**初始化处理:**

1. 创建请求队列 (`Queue[Tuple[str, Any]]`)
2. 创建停止事件 (`Event`)
3. 生成端点别 Lock:
   - 将 `/set/enable/xxx` 和 `/set/disable/xxx` 规范化为 `/lock/set/xxx`
   - 同一功能的启用/禁用请求不竞争

**规范化逻辑示例:**

```python
"/set/enable/translation" → "/lock/set/translation"
"/set/disable/translation" → "/lock/set/translation"
# 两者共享同一锁 → 排他执行
```

#### `receiver()` 方法

**职责:** 从 stdin 读取 JSON 请求并投入队列

**处理流程:**

1. 用 `sys.stdin.readline()` 阻塞读取
2. JSON 解析 (`json.loads()`)
3. 提取端点和数据
4. 数据存在时进行 Base64 解码 (`encodeBase64()`)
5. 日志输出 (`printLog()`)
6. 投入队列 `self.queue.put((endpoint, data))`

**错误处理:**

- JSON 解析错误: 日志输出后继续
- EOF 到达: 等待 0.1 秒后重试
- 其他异常: 用 `errorLogging()` 记录跟踪

**线程:** 作为守护线程 `main_receiver` 启动

#### `handler()` 方法

**职责:** 从队列取出请求,获取适当的锁并处理

**处理流程:**

1. 从队列获取 `(endpoint, data)`(0.5 秒超时)
2. 将端点转换为规范化键
3. 尝试获取对应的 Lock(非阻塞)
   - 获取成功 → 执行处理 → 释放锁
   - 获取失败 → 等待 0.05 秒后重新入队
4. 调用 `_call_handler(endpoint, data)`
5. 向 stdout 输出响应 (`printResponse()`)

**排他控制的意义:**

- 例: 翻译功能启用中收到禁用请求时,禁用等待
- 不同功能的请求可并行执行

**重新入队逻辑:**

- status == 423 (Locked): 等待 0.1 秒后重新入队
- 这样初始化中的配置变更请求会适当重试

**工作线程数:** 作为 `worker_count` 个线程 `main_handler_0`, `main_handler_1`, ... 启动

#### `_call_handler(endpoint, data)` 方法

**职责:** 实际业务逻辑执行

**处理流程:**

1. 从 `mapping` 获取对应的处理器
2. 端点不存在 → status 404
3. 处理器的 `status` 为 False → status 423 (Locked)
4. 执行处理器的 `variable` 函数 → `response = handler["variable"](data)`
5. 等待 0.2 秒(为了处理稳定化)
6. 提取 status 和 result 并返回

**错误处理:**

- 异常发生时: 用 `errorLogging()` 记录跟踪,返回 status 500

#### `start()` / `stop(wait)` 方法(2025-10 规格)

**start():**
提交 `5ce281e` 后变为简单的"维持主循环"功能。`start()` 内不调用 `startReceiver()` / `startHandler()`。调用方(`__main__` 块或外部进程管理器)启动所需线程后调用 `start()` 提供以下行为。

```python
def start(self) -> None:
   try:
      while not self._stop_event.is_set():
         time.sleep(1)
   except KeyboardInterrupt:
      self.stop()
```

要点:

- 主线程每 1 秒休眠同时存续,通过 Ctrl+C(KeyboardInterrupt)安全转换到停止。
- 消除现有 receiver / handler 线程重复启动的风险。
- 生命周期明确化: 从 `start()` 分离线程启动职责,提高测试·扩展容易性。

传统规格文档中"`start()` 直接启动线程"的描述已废止,最新代码中不需要。

**stop(wait):**

- `_stop_event.set()` - 向所有线程发送停止信号
- 用 `join(timeout=remaining)` 等待各线程(最大 `wait` 秒)

### 3. 初始化序列

**`if __name__ == "__main__":` 块:**

1. 创建 `main_instance`
2. `startReceiver()` - 开始 stdin 监听
3. `startHandler()` - 开始请求处理
4. **Watchdog 设置:**
   - `controller.setWatchdogCallback(main_instance.stop)`
   - Watchdog 超时时停止整个进程
5. **Controller 初始化:**
   - `controller.init()`
   - Model 延迟初始化、设备枚举、网络连接检查
   - 执行 `init_mapping` 的所有端点向前端发送初始设置
6. **映射解锁:**
   - 将所有 `mapping[key]["status"]` 设置为 True
   - 这样初始化中的功能变为可用
7. `main_instance.start()` - 仅维持主循环(receiver / handler 已事先启动)

### Watchdog 端点协作

后端基于客户端以一定间隔(例: 30 秒)发送 `/run/feed_watchdog` 的设计。测试客户端(`test_client.py`)在初始化完成后在后台线程中自动发送此端点,防止内部监控(controller 端的 Watchdog 回调)超时。

日志上通常不获取响应(fire & forget),因此可以调整心跳频率以减轻负载。

## 并行处理和线程安全

### 线程构成

| 线程名 | 角色 | 生存期间 |
|-----------|------|---------|
| `main_receiver` | 从 stdin 读取 JSON | 直到进程结束 |
| `main_handler_0` ~ `main_handler_N` | 请求处理工作线程 | 直到进程结束 |

### 同步机制

1. **队列 (`Queue`):**
   - 线程安全的 FIFO 队列
   - receiver → handler 的通信通道

2. **端点别 Lock (`dict[str, Lock]`):**
   - 防止对同一资源的竞争访问
   - 通过规范化键统一 enable/disable 对

3. **停止事件 (`Event`):**
   - 优雅关闭用信号

### 避免死锁

- **非阻塞 Lock 获取:** `lock.acquire(blocking=False)`
- **失败时重新入队:** Lock 获取失败时立即放弃并重新入队
- **带超时的队列获取:** 用 `queue.get(timeout=0.5)` 避免无限等待

## 协议规格

### 请求格式 (stdin)

```json
{
  "endpoint": "/set/data/transparency",
  "data": "ODU="  // Base64 编码: "85"
}
```

**字段:**

- `endpoint`: 要执行的端点(必需)
- `data`: 参数(可选,Base64 编码)

### 响应格式 (stdout)

```json
{
  "status": 200,
  "endpoint": "/set/data/transparency",
  "result": 85
}
```

**字段:**

- `status`: 相当于 HTTP 状态码
   - 200: 成功
   - 400: 验证错误
   - 404: 无效端点
   - 423: 锁定中(重试)
   - 500: 内部错误
- `endpoint`: 请求的端点
- `result`: 处理结果(类型取决于端点)

### 日志格式 (stdout)

```json
{
  "status": 348,  // 专用状态码
  "log": "setSelectedTabNo",
  "data": "1"
}
```

## 错误处理

### 1. JSON 解析错误

- **发生位置:** `receiver()` 的 `json.loads()`
- **处理:** 用 `errorLogging()` 记录跟踪,跳过请求

### 2. 处理器执行错误

- **发生位置:** `_call_handler()` 的 `handler["variable"](data)`
- **处理:**
   - 用 `errorLogging()` 记录跟踪
   - 返回 status 500 和 "Internal error"
   - 进程继续

### 3. JSON 序列化错误

- **发生位置:** `printResponse()` 的 `json.dumps()`
- **处理:**
   - 将详细信息记录到错误日志
   - 输出回退 JSON(status 500)
   - 进程继续

### 4. EOF (stdin 结束)

- **发生位置:** `receiver()` 的 `readline()`
- **处理:** 等待 0.1 秒后重试(等待前端重启)

## 性能优化

### 1. 多个工作线程

- 默认 3 线程并行处理
- 优化 CPU 绑定处理(翻译、转录)

### 2. 非阻塞锁

- 锁竞争时立即重新入队
- 最小化线程阻塞时间

### 3. 处理稳定化等待

- 每个处理器执行后等待 0.2 秒
- 避免连续请求导致的竞争状态

## 限制

### 1. 初始化中的限制

- `mapping[key]["status"] = False` 期间请求以 423 重试
- 初始化完成前最多几秒延迟

### 2. stdin 的单向性

- stdin → 队列 → 处理器的单向流
- 不支持多个前端同时连接

### 3. 串行执行保证

- 同一端点的请求排他执行,但
- 不同端点可能并行执行
- 有依赖关系的操作需要调用方控制顺序

## 调试和故障排除

### 日志文件

| 文件名 | 内容 |
|-----------|------|
| `process.log` | 所有请求/响应记录 |
| `error.log` | 异常跟踪 |

### 调试方法

1. **请求跟踪:**
   - 在 `process.log` 中确认 endpoint 和 data
   - Base64 解码手动执行 `base64.b64decode(data).decode('utf-8')`

2. **锁竞争检测:**
   - 同一端点频繁出现 status 423 时
   - 确认 `_canonical_lock_key()` 的规范化逻辑

3. **性能分析:**
   - 从 status 前后时间戳计算各请求处理时间
   - 增加 worker_count 调整并行度

## 未来扩展性

### 1. 双向通信

- 迁移到 WebSocket 改善实时通知
- 为了兼容性维持 stdin/stdout

### 2. 动态工作线程数调整

- 根据队列深度自动调整线程数
- 根据 CPU 负载适应性扩展

### 3. 优先级队列

- 重要请求(错误通知等)优先处理
- 迁移到 `queue.PriorityQueue`

## 相关文件

- `controller.py` - 业务逻辑实现
- `model.py` - 功能门面
- `utils.py` - 日志和工具
- `config.py` - 配置管理

## 编码规范

本文件遵循以下规范:

- PEP 8 样式指南
- 类型提示 (`typing` 模块)
- Docstring 采用 Google 风格
- 防御性错误处理实现

## 测试场景

### 1. 基本操作测试

```python
# 向 stdin 发送 JSON
echo '{"endpoint": "/get/data/version", "data": null}' | python mainloop.py
# 期望输出: {"status": 200, "endpoint": "/get/data/version", "result": "1.0.0"}
```

### 2. 并行请求测试

- 同时发送多个配置变更请求
- 确认所有都正常处理

### 3. 锁竞争测试

- 连续发送翻译的启用和禁用
- 确认两者排他执行

### 4. 错误恢复测试

- 发送非法 JSON、无效端点、非法数据
- 确认进程不崩溃并返回错误响应

## 总结

`mainloop.py` 是 VRCT 核心通信层,实现通过 stdin/stdout 与前端的基于 JSON 的协议。通过多个工作线程和细粒度锁,兼顾高并行性和排他控制。初始化序列和错误处理设计稳健,保证进程稳定运行。
