# test_client.py 文档

## 概要
`test_client.py` 是通过 stdin/stdout 与后端 (`mainloop.py`) 通信,自动/半自动测试各种 API 端点的客户端工具。具备初始化完成等待、日志 (status=348) 展开显示、静默模式、结果导出(JSON/CSV)、Watchdog 心跳发送 (/run/feed_watchdog) 等辅助功能。

## 主要职责
- 后端进程启动和初始化完成等待 (`/run/initialization_complete`)
- 端点单次发送/响应等待 (Base64 编码/解码)
- status=348 日志条目全文展开显示
- 超时/异常发生时的恢复消息输出
- Watchdog 心跳发送线程管理
- 自动测试器 (`AutomatedEndpointTester`) 进行全面端点测试
- 测试结果 JSON / CSV 导出 (交互式指定)

## 类结构
### `Color`
定义 ANSI 颜色常量,实现可读性高的输出。

### `TestClient`
管理与后端的 1 进程・1 通道通信。

| 属性 | 作用 |
|------|------|
| `process` | 启动的 Python 后端 subprocess |
| `_watchdog_stop_event` | Watchdog 线程停止控制用 Event |
| `_watchdog_thread` | /run/feed_watchdog 发送线程 |

#### 初始化流程
1. `subprocess.Popen([sys.executable, 'mainloop.py'], ...)` 启动后端
2. 调用 `_wait_for_initialization()` 等待接收 `/run/initialization_complete`
   - 如有 VRCT_INIT_TIMEOUT 环境变量,作为 soft timeout 使用 (超时时仅 WARN)
   - 每 30 秒记录进度日志 (最后接收的 endpoint)
   - status=348 记录全文展开 JSON
3. 初始化完成后 `_start_watchdog()` 在后台每 30 秒间隔发送 /run/feed_watchdog

#### 重要方法
- `send_request(endpoint, data=None, timeout=30.0, silent=False)`
  - 构建并发送请求 JSON
  - `data` 经 JSON 序列化 → Base64 → `data` 字段
  - 逐行读取到指定 endpoint 的响应行 (其他 endpoint 的日志行跳过)
  - status=348 时作为日志全文显示(silent=False 时)
  - 超时时合成 504 响应

- `_wait_for_initialization(timeout=None)`
  - 无期限或 soft timeout 等待
  - 进程死亡检测时抛出 RuntimeError

- `_start_watchdog()` / `cleanup()`
  - Watchdog 线程启动和安全停止 (设置 Event 后 join)

### `AutomatedEndpointTester`
`backend_test.py` 逻辑移植版(针对 stdin/stdout 协议)。

| 属性 | 说明 |
|------|------|
| `silent` | True 时抑制客户端详细输出 |
| `export_path` | JSON 导出目标 (None 时不输出) |
| `export_csv` | CSV 追加输出是否 |
| `results` | 收集的测试记录列表 |

#### 端点分类 (硬编码临时)
- 启用/禁用: `/set/enable/*`, `/set/disable/*`
- 设置更新: `/set/data/*`
- 执行系: `/run/*`
- 删除系: `/delete/data/*`

#### 主要方法
- `test_validity_single(endpoint)` 启用/禁用系单次测试
- `test_set_data_single(endpoint)` 设置更新系单次测试(需事先动态获取的值通过 `/get/data/...` 调用获取最新值缓存)
- `test_run_single(endpoint)` 执行系单次测试
- `test_delete_single(endpoint)` 删除系单次测试
- `run_all()` 全类别顺序执行
- `run_random(count=1000)` 从全端点池随机选择
- `run_specific_random(category, count)` 指定类别内随机
- `summary()` 结果汇总输出,必要时 JSON/CSV 导出

#### 结果记录结构
```json
{
  "endpoint": "/set/data/transparency",
  "status": 200,
  "result": 85,
  "expected": "status==200"
}
```

CSV 示例:
```
endpoint,status,expected,success
/set/data/transparency,200,status==200,True
```

## status=348 日志处理
- 初始化等待中: 展开并缩进显示
- 请求响应处理中: silent=False 时优先显示日志条目全文
- 与普通 API 响应 (status != 348) 的区分明确化,便于调试

## Watchdog 心跳
- 每 30 秒间隔发送 `/run/feed_watchdog` (fire-and-forget)
- 发送失败时显示警告并结束循环
- 客户端结束时设置停止事件并 join 线程防止泄漏

## 导出功能
### JSON 导出
- 指定 `export_path` 时将 `results` 以 UTF-8 / ensure_ascii=False 格式化输出
- 字段: endpoint, status, result, expected, success

### CSV 导出
- 从 JSON 路径替换扩展名(`.csv`)派生 (内部 `_derive_csv_path` 相当逻辑)
- 成功判定: 依赖 `status` 和 `expected` 字符串评估结果 (简单比较)

## 异常/错误处理方针
| 情况 | 对应 |
|--------|------|
| 后端结束检测 | 初始化等待中: 抛出 RuntimeError / 普通通信: 合成 500 响应 |
| JSONDecodeError | 作为日志行跳过 (初始化中作为进度日志显示) |
| BrokenPipe / OSError | 视为通信断开返回 500 响应 |
| 超时 | 返回 504 响应 (附带 endpoint) |

## 限制事项
- 端点列表是硬编码而非动态获取 (未来改进空间)
- 不支持响应并行接收(1 请求同步等待)
- status=200 以外的详细语义验证有限 (expected = 简单条件)
- Watchdog 响应不读取,因此仅通过异常路径检测发送失败

## 未来改进候选
1. CLI 参数支持 (`--mode random --count 500 --silent --export result.json`)
2. 添加动态端点枚举 API 后自动反映
3. 引入重试策略 (指数退避)
4. 响应时间测量和性能报告输出
5. 并行测试执行 (多个 subprocess / async IO)

## 参考
- `backend_test.py` : 原始逻辑
- `utils.py` : status=348 日志输出规格
- `mainloop.md` : 通信协议详情

## 总结
`test_client.py` 是用一个文件实现对 VRCT 后端进行全面测试和运维辅助的工具。通过初始化等待的健壮化(无期限 + soft timeout)、Watchdog 心跳、日志展开、静音选项、结果导出,提供了便于长时间运行、回归测试、CI 集成的基础。
