# utils.py - 实用工具函数模块

## 概述

提供VRCT应用程序全局使用的通用实用函数的模块。集中了数据验证、网络连接确认、计算设备管理、日志功能等共同功能。

## 主要功能

### 数据验证功能

- 字典结构的类型安全验证
- IP地址格式验证
- WebSocket服务器的可用性确认

### 系统信息获取

- 可用计算设备(CPU/CUDA)列表获取
- 最佳计算类型自动选择
- 设备特定约束支持

### 日志功能

- 结构化日志输出
- 轮转日志文件管理
- 错误日志和进程日志分离

### 网络功能

- 互联网连接状态确认
- Base64编码/解码处理

## 主要函数

### 数据验证

```python
validateDictStructure(data: dict, structure: dict) -> bool
```

- 判断字典与其预期结构是否完全匹配
- 支持嵌套结构
- 保证类型安全

### 网络相关

```python
isConnectedNetwork(url="http://www.google.com", timeout=3) -> bool
```

- 检查到指定URL的连接可能性
- 可设置超时

```python
isAvailableWebSocketServer(host: str, port: int) -> bool
```

- 确认WebSocket服务器的绑定可能性

```python
isValidIpAddress(ip_address: str) -> bool
```

- 验证IPv4/IPv6地址的有效性

### 计算设备管理

```python
getComputeDeviceList() -> List[Dict[str, Any]]
```

- 获取可用CPU/CUDA计算设备列表
- 提供包含每个设备计算类型的详细信息

```python
getBestComputeType(device: str, device_index: int) -> str
```

- 自动选择设备的最佳计算类型
- 考虑GPU特定约束(GTX、RTX、Tesla、A100、Quadro等)

### 日志功能

```python
setupLogger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger
```

- 设置带轮转功能的日志
- 10MB大小轮转
- UTF-8编码支持

```python
printLog(log: str, data: Any = None) -> None
```

- 结构化进程日志输出
- JSON格式标准输出

```python
printResponse(status: int, endpoint: str, result: Any = None) -> None
```

- API响应的结构化输出
- 安全处理序列化错误

```python
errorLogging() -> None
```

- 异常回溯日志记录
- 带回退功能

### 其他实用工具

```python
encodeBase64(data: str) -> Dict[str, Any]
```

- Base64编码JSON字符串的解码
- 带错误处理

```python
removeLog() -> None
```

- 进程日志文件初始化

## 使用方法

### 基本用法

```python
from utils import validateDictStructure, isConnectedNetwork, printLog

# 字典结构验证
expected_structure = {"name": str, "age": int}
data = {"name": "test", "age": 25}
is_valid = validateDictStructure(data, expected_structure)

# 网络连接确认
is_connected = isConnectedNetwork()

# 日志输出
printLog("处理开始", {"user_id": 123})
```

### 计算设备管理

```python
from utils import getComputeDeviceList, getBestComputeType

# 可用设备列表
devices = getComputeDeviceList()

# 最佳计算类型选择
compute_type = getBestComputeType("cuda", 0)
```

### 日志设置

```python
from utils import setupLogger, errorLogging

# 自定义日志设置
logger = setupLogger("my_module", "my_module.log")
logger.info("处理完成")

# 错误日志记录
try:
    # 某些处理
    pass
except Exception:
    errorLogging()
```

## 依赖关系

### 必需依赖

- `json`: JSON处理
- `logging`: 日志功能
- `requests`: HTTP通信
- `ipaddress`: IP地址验证
- `socket`: 套接字通信

### 可选依赖

- `torch`: CUDA计算设备信息获取
- `ctranslate2`: 计算类型信息获取

## 设备计算类型约束

### GTX系列
- 支持: 仅`float32`
- 原因: 旧架构的约束

### RTX/Tesla/A100/Quadro系列
- 支持: 全功能
- 优先级: `int8_bfloat16` > `int8_float16` > `int8` > `bfloat16` > `float16` > `int8_float32` > `float32`

### CPU
- 支持: 所有计算类型(硬件依赖)

## 错误处理

- 所有函数考虑异常安全性
- 对可选依赖缺失的适当回退
- 日志功能具有多级故障安全机制

## 注意事项

- 计算设备信息获取首次执行时可能需要一些时间
- 日志轮转在10MB大小时自动执行
- 网络连接确认默认3秒超时设置
