# osc.py - OSC通信·OSCQuery协议管理

## 概述

管理与VRChat的高级OSC(Open Sound Control)通信的综合系统。除了基本的OSC消息发送外,还提供OSCQuery协议的双向通信、参数监控、自动服务发现功能。

## 主要功能

### OSC通信功能
- 向VRChat聊天框发送消息
- 控制打字状态
- 动态获取参数值

### OSCQuery对应
- 自动服务发现·连接
- 实时参数监控
- 双向端点公开

### 鲁棒性功能
- 防御性编程设计
- 优雅处理缺失库
- 自动错误恢复机制

## 类结构

### OSCHandler 类

```python
class OSCHandler:
    def __init__(self, ip_address: str = "127.0.0.1", port: int = 9000) -> None:
        self.is_osc_query_enabled: bool
        self.osc_ip_address: str
        self.osc_port: int
        self.udp_client: udp_client.SimpleUDPClient
        self.osc_server: Optional[osc_server.ThreadingOSCUDPServer]
        self.osc_query_service: Optional[OSCQueryService]
        self.browser: Optional[OSCQueryBrowser]
```

OSC通信的核心管理类

#### 属性
- **is_osc_query_enabled**: OSCQuery功能的有效性标志
- **osc_ip_address**: 发送目标IP地址
- **osc_port**: UDP通信端口
- **udp_client**: OSC发送客户端
- **osc_server**: 本地OSC服务器
- **osc_query_service**: OSCQuery服务实例
- **browser**: OSCQuery浏览器

## 主要方法

### 消息发送

```python
def sendMessage(self, message: str = "", notification: bool = True) -> None
```

向VRChat聊天框发送消息

#### 参数
- **message**: 要发送的文本消息
- **notification**: 通知标志(声音·显示的有无)

```python
def sendTyping(self, flag: bool = False) -> None
```

向VRChat发送打字状态

#### 参数
- **flag**: 打字中标志

### 参数监控

```python
def getOSCParameterMuteSelf() -> Optional[bool]
```

获取VRChat的MuteSelf参数值

#### 返回值
- **Optional[bool]**: 静音状态(获取失败时为None)

```python
def getOSCParameterValue(self, address: str) -> Any
```

获取任意OSC参数值

#### 参数
- **address**: OSC地址(例: "/avatar/parameters/MuteSelf")

#### 返回值
- **Any**: 参数值(获取失败时为None)

### 配置更改

```python
def setOscIpAddress(self, ip_address: str) -> None
```

更改发送目标IP地址并重新初始化服务

#### 参数
- **ip_address**: 新IP地址

```python
def setOscPort(self, port: int) -> None
```

更改发送端口并重新初始化服务

#### 参数
- **port**: 新UDP端口号

## 使用方法

### 基本消息发送

```python
from models.osc.osc import OSCHandler

# OSC处理器初始化
osc = OSCHandler(ip_address="127.0.0.1", port=9000)

# 向聊天框发送消息
osc.sendMessage("你好, VRChat!", notification=True)

# 控制打字状态
osc.sendTyping(True)   # 开始打字
# ... 实际打字处理 ...
osc.sendTyping(False)  # 结束打字

# 再次发送消息
osc.sendMessage("翻译完成", notification=False)
```

### 连接到远程VRChat

```python
# 连接到远程VRChat实例
remote_osc = OSCHandler(ip_address="192.168.1.100", port=9000)

# OSCQuery功能自动禁用
print(f"OSCQuery启用: {remote_osc.getIsOscQueryEnabled()}")  # False

# 可使用基本消息发送
remote_osc.sendMessage("来自远程的翻译结果", notification=True)
```

### 参数监控(仅本地连接时)

```python
# 本地连接参数监控
local_osc = OSCHandler(ip_address="127.0.0.1", port=9000)

if local_osc.getIsOscQueryEnabled():
    # 监控MuteSelf参数
    mute_status = local_osc.getOSCParameterMuteSelf()
    
    if mute_status is not None:
        if mute_status:
            print("用户已静音")
        else:
            print("用户未静音")
    else:
        print("获取MuteSelf参数失败")
    
    # 监控自定义参数
    custom_value = local_osc.getOSCParameterValue("/avatar/parameters/CustomParam")
    if custom_value is not None:
        print(f"自定义参数值: {custom_value}")
```

### 双向OSC通信设置

```python
def handle_mute_change(address, *args):
    """静音状态变更处理器"""
    print(f"静音状态已变更: {args}")

def handle_typing_change(address, *args):
    """打字状态变更处理器"""  
    print(f"打字状态: {args}")

def handle_chatbox_input(address, *args):
    """聊天框输入处理器"""
    print(f"聊天框输入: {args}")

# OSC参数处理器设置
osc_handlers = {
    "/avatar/parameters/MuteSelf": handle_mute_change,
    "/chatbox/typing": handle_typing_change,
    "/chatbox/input": handle_chatbox_input
}

osc = OSCHandler()
osc.setDictFilterAndTarget(osc_handlers)

# 启动OSC服务器(OSCQuery自动公开)
osc.receiveOscParameters()

print("OSC接收服务器已启动")
print("正在监控来自VRChat的参数变更...")

# 消息发送测试
import time
time.sleep(2)
osc.sendMessage("双向通信测试", notification=True)

# 长时间运行
time.sleep(30)

# 清理
osc.oscServerStop()
```

### 动态配置更改

```python
# 运行时IP·端口更改
osc = OSCHandler(ip_address="127.0.0.1", port=9000)

# 初始配置本地连接
osc.sendMessage("本地连接测试")

print("切换到远程连接...")
osc.setOscIpAddress("192.168.1.150")  # 自动禁用OSCQuery
osc.sendMessage("远程连接测试")

print("更改端口...")
osc.setOscPort(9001)
osc.sendMessage("新端口测试")

print("返回本地连接...")
osc.setOscIpAddress("127.0.0.1")  # 再次启用OSCQuery
osc.sendMessage("本地连接恢复测试")
```

## OSCQuery详细功能

### 自动服务发现

```python
class VRChatMonitor:
    """VRChat服务监控类"""
    
    def __init__(self):
        self.osc = OSCHandler()
        self.monitoring = False
    
    def start_monitoring(self):
        """开始持续监控VRChat参数"""
        
        if not self.osc.getIsOscQueryEnabled():
            print("OSCQuery功能已禁用(仅支持本地连接)")
            return
        
        # OSC处理器设置
        handlers = {
            "/avatar/parameters/MuteSelf": self.on_mute_change,
            "/avatar/parameters/Voice": self.on_voice_change,
            "/avatar/parameters/Viseme": self.on_viseme_change,
            "/avatar/parameters/GestureLeft": self.on_gesture_left,
            "/avatar/parameters/GestureRight": self.on_gesture_right
        }
        
        self.osc.setDictFilterAndTarget(handlers)
        self.osc.receiveOscParameters()
        
        self.monitoring = True
        print("VRChat参数监控已启动")
    
    def on_mute_change(self, address, *args):
        print(f"静音状态变更: {args[0] if args else 'Unknown'}")
    
    def on_voice_change(self, address, *args):
        print(f"语音级别: {args[0] if args else 'Unknown'}")
    
    def on_viseme_change(self, address, *args):
        print(f"口型变化: {args[0] if args else 'Unknown'}")
    
    def on_gesture_left(self, address, *args):
        print(f"左手手势: {args[0] if args else 'Unknown'}")
    
    def on_gesture_right(self, address, *args):
        print(f"右手手势: {args[0] if args else 'Unknown'}")
    
    def stop_monitoring(self):
        """停止监控"""
        self.osc.oscServerStop()
        self.monitoring = False
        print("VRChat参数监控已停止")

# 使用示例
monitor = VRChatMonitor()
monitor.start_monitoring()

# 监控中执行其他处理
time.sleep(60)  # 监控1分钟

monitor.stop_monitoring()
```

## 依赖关系·要求

### 必需依赖
- `pythonosc`: 基本OSC通信库
- `threading`: 并发处理控制
- `time`: 时间管理功能

### 可选依赖
- `tinyoscquery`: OSCQuery功能(仅本地连接时)
- `utils`: 错误日志功能(有降级处理)

### 系统要求
```python
# 最小系统要求
requirements = {
    "python_version": "3.7+",
    "network": "UDP通信支持",
    "vrchat_version": "OSC支持版(2022年8月以后)",
    "local_ports": "空闲UDP/TCP端口(使用OSCQuery时)"
}

# 推荐环境
recommended = {
    "network_latency": "< 10ms(本地连接)",
    "cpu_usage": "使用OSCQuery时额外CPU负载",
    "memory": "使用tinyoscquery时额外内存"
}
```

## 注意事项·限制

### OSCQuery限制
- 仅localhost (127.0.0.1/localhost)连接时可用
- 需要tinyoscquery库
- 根据防火墙设置可能无法工作

### 通信限制
- UDP协议因此无送达保证
- VRChat的OSC接收限制(有速率限制)
- 根据网络环境的延迟·数据包丢失

### 平台依赖
```python
# 已知限制
limitations = {
    "windows": "可能需要Windows防火墙设置",
    "macos": "可能因安全设置导致端口限制",
    "linux": "部分Linux发行版的兼容性问题",
    "vrchat_platform": "仅PC版VRChat支持OSC"
}
```

## 相关模块

- `config.py`: OSC配置管理
- `controller.py`: OSC功能控制接口
- `model.py`: OSC功能集成
- `utils.py`: 错误日志·网络工具

## 未来改进点

- 更高级的OSCQuery参数监控
- 自定义OSC协议扩展
- 性能监控·分析功能
- 自动重连·恢复机制改进
- VRChat avatar特定参数对应
