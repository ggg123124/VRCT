# utils.py 文档

## 概述
`utils.py` 是 VRCT 应用程序全局使用的通用工具函数和日志功能提供模块。它集成了字典结构验证、网络连接确认、计算设备管理、Base64编码、结构化日志输出等多个子系统共享的基础功能。

## 主要功能
- 字典结构的严格验证
- 网络连接状态诊断
- WebSocket服务器地址可用性检查
- IP地址验证
- CUDA/CPU计算设备检测与优化
- 结构化日志输出（process.log, error.log）
- Base64编码/解码
- 日志文件轮转管理

## 架构定位

```
┌─────────────────┐
│ All Modules     │ (controller, model, device_manager, etc.)
└────────┬────────┘
         │ Import
┌────────▼────────┐
│   utils.py      │ ◄── 本文件
└─────────────────┘
         │
┌────────▼────────┐
│ External Deps   │ (torch, ctranslate2, requests, ipaddress)
└─────────────────┘
```

作为被所有模块引用的公共基础设施，为避免循环引用，该模块不依赖其他内部模块。

## 依赖关系

### 标准库
```python
import base64
import json
import traceback
import logging
from logging.handlers import RotatingFileHandler
from typing import Any, List, Dict, Optional
```

### 第三方库（可选依赖）
```python
import torch  # GPU检测用（导入失败时回退到None）
from ctranslate2 import get_supported_compute_types  # 获取计算类型
import requests  # 网络连接确认用
import ipaddress  # IP地址验证用
import socket  # WebSocket服务器可用性检查
```

**安全导入：**
```python
try:
    import torch
except Exception:
    torch = None  # type: ignore

try:
    from ctranslate2 import get_supported_compute_types
except Exception:
    def get_supported_compute_types(device: str, device_index: int) -> List[str]:
        return []
```

即使在不满足可选依赖的环境中，模块也能正常加载。

## 函数参考

### 1. 字典结构验证

#### `validateDictStructure(data: dict, structure: dict) -> bool`

**职责：** 验证字典的结构和类型是否与预期规范完全一致

**算法：**
1. 确认两者都是字典类型
2. 检查键的数量和名称是否完全匹配
3. 对于每个键的值：
   - 如果期望值是字典：递归验证（支持多层嵌套）
   - 如果期望值是类型对象：使用 `isinstance()` 进行类型检查

**参数：**
- `data` (dict): 待验证的字典
- `structure` (dict): 预期的结构定义
  - 值可以指定类型（str, int, bool等）或嵌套字典

**返回值：**
- `True`: 结构完全匹配
- `False`: 不匹配（缺少键、多余键、类型不匹配等）

**使用示例：**
```python
# 简单结构验证
data = {"name": "Alice", "age": 30}
structure = {"name": str, "age": int}
assert validateDictStructure(data, structure) is True

# 嵌套结构验证
data = {
    "user": {
        "id": 123,
        "profile": {"name": "Bob", "active": True}
    }
}
structure = {
    "user": {
        "id": int,
        "profile": {"name": str, "active": bool}
    }
}
assert validateDictStructure(data, structure) is True

# 不匹配检测
data = {"name": "Alice", "extra_key": "value"}
structure = {"name": str, "age": int}
assert validateDictStructure(data, structure) is False  # 键不匹配
```

**使用场景：**
- 前端请求负载验证
- 配置文件架构验证
- API响应结构确认

---

### 2. 网络诊断

#### `isConnectedNetwork(url: str = "http://www.google.com", timeout: int = 3) -> bool`

**职责：** 快速检查互联网连接可用性

**处理流程：**
1. 向指定URL发送 HTTP GET 请求
2. 如果在 `timeout` 秒内收到 200 OK 响应，则认为有连接
3. 超时或发生异常时认为无连接

**参数：**
- `url` (str): 连接确认目标URL（默认：Google）
- `timeout` (int): 超时时间（秒）

**返回值：**
- `True`: 网络连接可用
- `False`: 网络连接不可用

**使用示例：**
```python
if isConnectedNetwork():
    # 下载模型权重
    downloadModelWeights()
else:
    # 离线模式运行
    useLocalModels()
```

**注意事项：**
- 在防火墙或代理环境下可能无法正常工作
- 建议仅在初始化时检查一次（避免频繁调用）

---

#### `isAvailableWebSocketServer(host: str, port: int) -> bool`

**职责：** 确认指定的主机/端口是否可以启动WebSocket服务器

**处理流程：**
1. 创建 TCP 套接字
2. 设置 `SO_REUSEADDR` 选项
3. 尝试 `bind()`
4. 成功 → 地址可用，失败 → 地址被占用

**参数：**
- `host` (str): 绑定的IP地址
- `port` (int): 绑定的端口号

**返回值：**
- `True`: 地址可用
- `False`: 地址被占用

**使用示例：**
```python
if isAvailableWebSocketServer("127.0.0.1", 8080):
    startWebSocketServer("127.0.0.1", 8080)
else:
    print("Port 8080 is already in use")
```

**注意事项：**
- 由于使用 `SO_REUSEADDR`，处于 TIME_WAIT 状态的地址也会被判定为可用
- 对于需要管理员权限的端口（小于1024）可能会失败

---

#### `isValidIpAddress(ip_address: str) -> bool`

**职责：** 验证 IPv4/IPv6 地址的有效性

**处理流程：**
- 使用 `ipaddress.ip_address()` 解析
- 成功 → 有效的IP地址，失败 → 无效

**参数：**
- `ip_address` (str): 待验证的IP地址字符串

**返回值：**
- `True`: 有效的IP地址
- `False`: 无效的IP地址

**使用示例：**
```python
assert isValidIpAddress("127.0.0.1") is True
assert isValidIpAddress("2001:db8::1") is True
assert isValidIpAddress("invalid") is False
```

**支持格式：**
- IPv4: "192.168.1.1", "127.0.0.1"
- IPv6: "2001:db8::1", "fe80::1"

---

### 3. 计算设备管理

#### `getComputeDeviceList() -> List[Dict[str, Any]]`

**职责：** 列举可用的计算设备（CPU/GPU）及支持的计算类型

**返回值结构：**
```python
[
    {
        "device": "cpu",
        "device_index": 0,
        "device_name": "cpu",
        "compute_types": ["auto", "float32", "int8", ...]
    },
    {
        "device": "cuda",
        "device_index": 0,
        "device_name": "NVIDIA GeForce RTX 3090",
        "compute_types": ["auto", "int8_bfloat16", "int8_float16", ...]
    },
    ...
]
```

**处理流程：**
1. 始终添加 CPU 设备（保证最低计算环境）
2. 如果 PyTorch 和 CUDA 可用：
   - 列举所有GPU设备
   - 使用 `get_supported_compute_types()` 获取每个GPU的计算类型
   - 根据GPU架构限制计算类型：
     - **GTX 系列**：排除 `int8_bfloat16`, `bfloat16`, `float16`, `int8`
     - **RTX, Tesla, A100, Quadro**：支持所有计算类型
     - **其他**：仅 `float32`

**GPU计算类型限制：**
```python
if "GTX" in gpu_device_name:
    unsupported_types = {"int8_bfloat16", "bfloat16", "float16", "int8"}
    gpu_compute_types = [t for t in gpu_compute_types if t not in unsupported_types]
elif not any(keyword in gpu_device_name for keyword in ["RTX", "Tesla", "A100", "Quadro"]):
    gpu_compute_types = ["float32"]
```

**使用示例：**
```python
devices = getComputeDeviceList()
for device in devices:
    print(f"{device['device_name']}: {', '.join(device['compute_types'])}")

# 输出示例：
# cpu: auto, float32, int8
# NVIDIA GeForce RTX 3090: auto, int8_bfloat16, int8_float16, int8, bfloat16, float16, int8_float32, float32
```

**错误处理：**
- GPU检测过程中的异常会通过 `errorLogging()` 记录，并仅返回 CPU 设备

---

#### `getBestComputeType(device: str, device_index: int) -> str`

**职责：** 根据设备架构自动选择最优计算类型

**优先级：**
```python
preferred_types = {
    "default": [
        "int8_bfloat16",   # 最高效（仅支持的GPU）
        "int8_float16",    # 次高效
        "int8",            # 整数运算加速
        "bfloat16",        # 混合精度
        "float16",         # 半精度浮点数
        "int8_float32",    # 兼容性优先
        "float32"          # 回退选项
    ],
    "GTX": ["float32"],  # GTX系列有限制
    "RTX": ["int8_bfloat16", "int8_float16", ...],
    "Tesla": [...],
    "A100": [...],
    "Quadro": [...]
}
```

**处理流程：**
1. 使用 `get_supported_compute_types()` 获取可用的计算类型
2. 根据设备名称选择优先级列表
3. 按优先级顺序检查计算类型，返回第一个可用的
4. 如果全部不可用，返回 `"float32"`（安全回退）

**参数：**
- `device` (str): "cpu" 或 "cuda"
- `device_index` (int): GPU设备索引（CPU时为0）

**返回值：**
- 最优计算类型字符串（例如："int8_bfloat16", "float32"）

**使用示例：**
```python
best_type = getBestComputeType("cuda", 0)
model.load_model(compute_type=best_type)
```

**计算类型特性：**

| 计算类型 | 内存使用 | 速度 | 精度 | 支持GPU |
|----------|----------|------|------|---------|
| int8_bfloat16 | 最小 | 最快 | 高 | RTX 30xx以上 |
| int8_float16 | 最小 | 最快 | 高 | RTX 20xx以上 |
| int8 | 小 | 快 | 中 | 多数GPU |
| bfloat16 | 中 | 快 | 高 | RTX 30xx以上 |
| float16 | 中 | 快 | 高 | RTX 20xx以上 |
| float32 | 大 | 标准 | 最高 | 所有GPU/CPU |

---

### 4. 编码

#### `encodeBase64(data: str) -> Dict[str, Any]`

**职责：** 解码Base64编码的JSON字符串并解析

**处理流程：**
1. Base64解码
2. 转换为UTF-8字符串
3. JSON解析
4. 失败时返回空字典

**参数：**
- `data` (str): Base64编码的JSON字符串

**返回值：**
- 解析成功：JSON对象
- 解析失败：`{}`（空字典）

**使用示例：**
```python
# 编码示例（参考）
import base64
import json
payload = {"message": "Hello", "id": 123}
encoded = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')

# 解码
decoded = encodeBase64(encoded)
assert decoded == {"message": "Hello", "id": 123}
```

**错误处理：**
- 无效的Base64字符串
- 无效的JSON格式
- 字符编码错误

所有错误都会通过 `errorLogging()` 记录，并返回空字典。

**注意事项：**
- 函数名为 `encodeBase64`，但实际执行的是**解码**操作（历史命名原因）
- 安全性：Base64不是加密，不应用于保护机密信息

---

### 5. 日志记录

#### `removeLog() -> None`

**职责：** 初始化进程日志文件（process.log）

**处理流程：**
- 用空内容覆盖 `process.log`
- 如果文件不存在则新建

**使用示例：**
```python
# 应用启动时清除日志
removeLog()
printLog("Application started")
```

**错误处理：**
- 文件写入失败时通过 `errorLogging()` 记录到错误日志

---

#### `setupLogger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger`

**职责：** 创建带轮转功能的日志记录器实例

**配置：**
- **最大日志大小**：10MB
- **备份数量**：1（最多2个文件）
- **轮转行为**：达到10MB时创建 `.1` 备份并开始新日志
- **编码**：UTF-8
- **延迟写入**：`delay=True`（首次写入时打开文件）

**参数：**
- `name` (str): 日志记录器名称（例如："process", "error"）
- `log_file` (str): 日志文件路径
- `level` (int): 日志级别（默认：`logging.INFO`）

**返回值：**
- 配置完成的 `logging.Logger` 实例

**日志格式：**
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

**输出示例：**
```
2025-10-13 14:30:45,123 - process - INFO - Application started
2025-10-13 14:30:46,456 - error - ERROR - Connection failed
```

**防止重复处理器：**
```python
if not any(isinstance(h, RotatingFileHandler) and getattr(h, 'baseFilename', None) == getattr(file_handler, 'baseFilename', None) for h in logger.handlers):
    logger.addHandler(file_handler)
```

防止向同一文件添加重复处理器，即使多次调用也安全。

---

#### `printLog(log: str, data: Any = None) -> None`

**职责：** 输出结构化进程日志

**输出目标：**
1. `process.log` 文件
2. 标准输出（JSON格式）

**输出格式：**
```python
{
    "status": 348,  # 进程日志专用状态码
    "log": "User action performed",
    "data": "additional context"
}
```

**参数：**
- `log` (str): 日志消息
- `data` (Any): 附加上下文信息（可选）

**使用示例：**
```python
printLog("Model loading started", {"model_type": "whisper", "weight": "medium"})
# 输出（stdout）：
# {"status": 348, "log": "Model loading started", "data": "{'model_type': 'whisper', 'weight': 'medium'}"}
```

**实现细节：**
```python
global process_logger
if process_logger is None:
    process_logger = setupLogger("process", "process.log", logging.INFO)

response = {
    "status": 348,
    "log": log,
    "data": str(data),
}
process_logger.info(response)
serialized = json.dumps(response)
print(serialized, flush=True)
```

**注意事项：**
- `data` 通过 `str()` 字符串化，复杂对象可能难以阅读
- `flush=True` 立即输出（禁用缓冲）

---

#### `printResponse(status: int, endpoint: str, result: Any = None) -> None`

**职责：** 输出结构化API响应

**输出目标：**
1. `process.log` 文件
2. 标准输出（JSON格式）

**输出格式：**
```python
{
    "status": 200,
    "endpoint": "/get/config/version",
    "result": {"version": "3.3.0"}
}
```

**参数：**
- `status` (int): HTTP状态码风格的状态编号
- `endpoint` (str): 端点标识符
- `result` (Any): 响应负载（可选）

**使用示例：**
```python
printResponse(200, "/set/config/language", {"language": "ja"})
printResponse(400, "/set/config/threshold", {"error": "Value out of range"})
```

**JSON序列化错误处理：**
```python
try:
    serialized_response = json.dumps(response)
except Exception as e:
    errorLogging()  # 完整堆栈跟踪记录
    process_logger.error(f"Problematic response object: {response}")
    process_logger.error(f"Exception during json.dumps: {e}")
    # 回退错误负载
    error_json = json.dumps({
        "status": 500,
        "endpoint": endpoint,
        "result": {"error": "Failed to serialize response", "details": str(e)},
    })
    print(error_json, flush=True)
else:
    print(serialized_response, flush=True)
```

**无法序列化的对象示例：**
- `datetime` 对象
- 自定义类实例
- 含循环引用的字典

**对策：**
- 构建 `result` 时仅使用JSON可序列化类型
- 必要时使用 `str()` 或专用序列化器转换

---

#### `errorLogging() -> None`

**职责：** 将当前异常堆栈跟踪记录到错误日志

**处理流程：**
1. 输出堆栈跟踪到 `error.log` 文件
2. 日志记录器初始化失败时回退到标准输出

**使用示例：**
```python
try:
    risky_operation()
except Exception:
    errorLogging()  # 堆栈跟踪记录到error.log
    # 必要时进行额外处理
```

**输出示例（error.log）：**
```
2025-10-13 14:35:12,789 - error - ERROR - Traceback (most recent call last):
  File "model.py", line 123, in loadModel
    model.load()
  File "ctranslate2/model.py", line 456, in load
    raise RuntimeError("CUDA out of memory")
RuntimeError: CUDA out of memory
```

**注意事项：**
- **仅可在异常上下文中调用**（使用 `traceback.format_exc()`）
- 在未捕获异常时调用会记录空堆栈跟踪

**最佳实践：**
```python
try:
    dangerous_function()
except SpecificException as e:
    errorLogging()  # 记录详情
    # 用户友好的错误处理
    printResponse(400, endpoint, {"error": "Operation failed"})
except Exception:
    errorLogging()  # 记录意外错误
    raise  # 向上传播
```

---

## 全局变量

### `process_logger: Optional[logging.Logger] = None`
进程日志用的全局日志记录器实例。在首次调用 `printLog()` 或 `printResponse()` 时初始化。

### `error_logger: Optional[logging.Logger] = None`
错误日志用的全局日志记录器实例。在首次调用 `errorLogging()` 时初始化。

**延迟初始化的原因：**
- 减少模块导入时的开销
- 避免不必要的文件系统访问

---

## 错误处理策略

### 1. 防御性编程
所有工具函数都在内部处理异常，不向调用方传播异常：

```python
def isConnectedNetwork(url="http://www.google.com", timeout=3) -> bool:
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False  # 捕获异常并返回安全值
```

### 2. 回退值
- `encodeBase64()`: 解析失败时返回 `{}`
- `getComputeDeviceList()`: GPU检测失败时仅返回CPU
- `getBestComputeType()`: 全部失败时返回 `"float32"`

### 3. 日志记录
所有错误都通过 `errorLogging()` 记录堆栈跟踪，便于调试。

---

## 性能考虑

### 1. 网络连接检查
`isConnectedNetwork()` 是阻塞操作（最多3秒），建议仅在启动时执行一次：

```python
# 好的例子
if isConnectedNetwork():
    downloadModels()

# 不好的例子（导致UI冻结）
while True:
    if isConnectedNetwork():  # 每次等待3秒
        processData()
```

### 2. 日志轮转
10MB的日志文件轮转控制磁盘空间（最多20MB）。

### 3. 全局日志记录器的延迟初始化
日志记录器在首次使用时初始化，最小化导入开销。

---

## 使用模式

### 模式1: 网络依赖功能初始化
```python
def initialize_online_features():
    if not isConnectedNetwork():
        printLog("Offline mode: skipping model download")
        return

    printLog("Online mode: downloading models")
    downloadModels()
```

### 模式2: 设备自动选择
```python
devices = getComputeDeviceList()
if len(devices) > 1:
    # GPU可用
    best_device = devices[1]  # 第一个GPU
    best_type = getBestComputeType(best_device["device"], best_device["device_index"])
    printLog(f"Using GPU: {best_device['device_name']}", {"compute_type": best_type})
else:
    # 仅CPU
    printLog("No GPU detected, using CPU")
    best_type = "float32"
```

### 模式3: 结构化请求验证
```python
def handle_request(payload):
    expected_structure = {
        "action": str,
        "data": {
            "id": int,
            "value": str
        }
    }

    if not validateDictStructure(payload, expected_structure):
        printResponse(400, "/handle_request", {"error": "Invalid request structure"})
        return

    # 继续处理
    printLog("Valid request received", payload)
```

### 模式4: WebSocket服务器启动
```python
def start_websocket(host, port):
    if not isValidIpAddress(host):
        printResponse(400, "/websocket/start", {"error": "Invalid IP address"})
        return

    if not isAvailableWebSocketServer(host, port):
        printResponse(400, "/websocket/start", {"error": f"Port {port} is in use"})
        return

    # 启动服务器
    printLog(f"Starting WebSocket server", {"host": host, "port": port})
    startServer(host, port)
```

---

## 测试建议

### 单元测试示例

**字典结构验证：**
```python
def test_validate_dict_structure_simple():
    data = {"name": "Alice", "age": 30}
    structure = {"name": str, "age": int}
    assert validateDictStructure(data, structure) is True

def test_validate_dict_structure_nested():
    data = {"user": {"id": 1, "active": True}}
    structure = {"user": {"id": int, "active": bool}}
    assert validateDictStructure(data, structure) is True

def test_validate_dict_structure_invalid():
    data = {"name": "Alice"}
    structure = {"name": str, "age": int}  # 缺少'age'键
    assert validateDictStructure(data, structure) is False
```

**网络诊断：**
```python
def test_network_connection():
    # 测试实际网络连接
    result = isConnectedNetwork()
    assert isinstance(result, bool)

def test_network_timeout():
    # 确认超时行为
    result = isConnectedNetwork(url="http://192.0.2.1", timeout=1)
    assert result is False
```

**计算设备：**
```python
def test_get_compute_device_list():
    devices = getComputeDeviceList()
    assert len(devices) >= 1  # 至少包含CPU
    assert devices[0]["device"] == "cpu"

def test_get_best_compute_type():
    compute_type = getBestComputeType("cpu", 0)
    assert compute_type in ["float32", "int8"]
```

**日志记录：**
```python
def test_print_log(capsys):
    printLog("Test message", {"key": "value"})
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["status"] == 348
    assert output["log"] == "Test message"

def test_print_response(capsys):
    printResponse(200, "/test", {"result": "success"})
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["status"] == 200
    assert output["endpoint"] == "/test"
```

---

## 安全考虑

### 1. IP地址验证
`isValidIpAddress()` 仅进行格式验证，不检查私有地址范围：

```python
# 增强安全性的情况
import ipaddress

def is_public_ip(ip_str):
    if not isValidIpAddress(ip_str):
        return False
    ip = ipaddress.ip_address(ip_str)
    return not (ip.is_private or ip.is_loopback or ip.is_reserved)
```

### 2. Base64解码
`encodeBase64()` 不进行输入验证，处理不可信来源的数据时需注意：

```python
# 安全使用示例
if source_is_trusted:
    data = encodeBase64(base64_string)
else:
    # 执行额外验证
    pass
```

### 3. 日志文件中的机密信息
注意不要在日志中记录机密信息（API密钥、密码等）：

```python
# 不好的例子
printLog("API key loaded", api_key)

# 好的例子
printLog("API key loaded", "***REDACTED***")
```

---

## 限制

1. **平台依赖性：**
   - GPU检测仅在CUDA环境下工作（不支持ROCm/Metal）

2. **网络检查的限制：**
   - 防火墙、代理环境下可能误判
   - IPv6专用环境下的运行未验证

3. **日志文件的线程安全性：**
   - `RotatingFileHandler` 基本上是线程安全的，但高负载下轮转期间可能丢失日志

4. **计算类型优化：**
   - `getBestComputeType()` 的优先级是通用推荐值，对于特定模型或任务可能不是最优

---

## 与依赖模块的关系

### controller.py
- 设备管理配置变更时获取设备列表
- 错误时记录日志
- 网络连接确认

### model.py
- 确定计算设备和类型
- 错误时记录堆栈跟踪

### config.py
- 启动时网络连接确认
- 提供计算设备列表

### mainloop.py
- 请求/响应的结构化日志输出
- 错误时记录堆栈跟踪

---

## 未来扩展性

### 1. 异步网络检查
```python
import asyncio
import aiohttp

async def isConnectedNetworkAsync(url="http://www.google.com", timeout=3) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                return response.status == 200
    except Exception:
        return False
```

### 2. 结构化日志扩展
```python
def printStructuredLog(level: str, message: str, context: dict = None):
    """
    更详细的结构化日志输出
    - timestamp
    - level
    - message
    - context (key-value pairs)
    - stack trace (错误时)
    """
    pass
```

### 3. 指标收集
```python
def recordMetric(metric_name: str, value: float, tags: dict = None):
    """
    性能指标记录
    - function execution time
    - memory usage
    - GPU utilization
    """
    pass
```

---

## 相关文档
- `controller.md`: Controller 中 utils 函数使用示例
- `config.md`: Config 中的计算设备管理
- `model.md`: Model 中的错误处理
- `编码规范_zh.md`: 日志记录和错误处理规约

---

## 许可证
参考项目根目录下的 `LICENSE` 文件

---

## 总结

`utils.py` 作为 VRCT 项目的基础设施，承担以下重要职责：

1. **安全性**：所有函数在内部处理异常，提供安全的回退值
2. **可观测性**：结构化日志和轮转功能使问题诊断更容易
3. **兼容性**：可选依赖的安全防护使其在各种环境下都能运行
4. **优化**：根据GPU架构自动选择计算类型
5. **验证**：字典结构、IP地址、网络连接的严格验证

作为被所有子系统依赖的核心模块，保持高可靠性和可维护性。
