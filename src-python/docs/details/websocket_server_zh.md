# websocket_server.py - WebSocket通信服务器

## 概述

提供异步WebSocket通信的综合服务器系统。集成客户端连接管理、消息分发、从外部线程安全操作,实现VRCT应用程序与Web前端间的实时通信。

## 主要功能

### 异步WebSocket通信
- 基于asyncio/websockets的高性能WebSocket服务器
- 支持多客户端同时连接
- 自动连接·断开管理

### 消息功能
- 实时消息接收处理
- 向所有客户端广播分发
- 支持自定义消息处理器

### 线程间通信
- 从GUI等外部线程安全发送消息
- 通过异步队列高效通信控制
- 保证线程安全操作

## 类结构

### WebSocketServer 类

```python
class WebSocketServer:
    def __init__(self, host: str='127.0.0.1', port: int=8765):
        self.host: str                          # 服务器主机
        self.port: int                          # 服务器端口
        self.clients: Set[WebSocketServerProtocol] # 连接客户端集合
        self._message_handler: Optional[Callable]   # 消息处理器
        self._loop: Optional[asyncio.AbstractEventLoop] # 事件循环
        self._server: Optional[websockets.serve]    # WebSocket服务器
        self._thread: Optional[threading.Thread]    # 服务器线程
        self._send_queue: Optional[asyncio.Queue]   # 发送队列
        self.is_running: bool                   # 运行状态标志
```

## 主要方法

### 服务器控制

```python
def start_server(self) -> None
```

启动WebSocket服务器(后台线程)

```python
def stop_server(self) -> None
```

停止WebSocket服务器·释放资源

### 消息处理

```python
def set_message_handler(self, handler: Callable) -> None
```

设置客户端消息接收回调

```python
def send(self, message: str) -> None
```

从外部线程安全地向所有客户端发送消息

```python
def broadcast(self, message: str) -> None
```

异步向所有客户端广播消息

## 使用方法

### 基本WebSocket服务器

```python
from models.websocket.websocket_server import WebSocketServer
import json

def on_message_received(server, websocket, message):
    """客户端消息处理"""
    print(f"收到消息: {message}")
    
    try:
        data = json.loads(message)
        
        if data.get('type') == 'translation_request':
            handle_translation_request(server, data)
        else:
            response = {'type': 'echo', 'data': data}
            server.broadcast(json.dumps(response))
            
    except json.JSONDecodeError:
        server.broadcast(f"收到: {message}")

# 启动WebSocket服务器
ws_server = WebSocketServer(host='127.0.0.1', port=8765)
ws_server.set_message_handler(on_message_received)
ws_server.start_server()

print("WebSocket服务器已启动: ws://127.0.0.1:8765")
```

### VRCT应用程序集成

```python
class VRCTWebSocketInterface:
    """VRCT用WebSocket接口"""
    
    def __init__(self, controller, port=8765):
        self.controller = controller
        self.ws_server = WebSocketServer(host='127.0.0.1', port=port)
        self.ws_server.set_message_handler(self.handle_web_message)
        
    def handle_web_message(self, server, websocket, message):
        """Web客户端消息处理"""
        try:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'get_config':
                self.send_config(server)
            elif command == 'start_translation':
                self.start_translation_service(server, data)
            elif command == 'stop_translation':
                self.stop_translation_service(server)
                
        except Exception as e:
            self.send_error(server, f"消息处理错误: {e}")
    
    def notify_translation_result(self, original, translated, source_lang, target_lang):
        """翻译结果通知(从VRCT控制器调用)"""
        notification = {
            'type': 'live_translation',
            'original': original,
            'translated': translated,
            'source_language': source_lang,
            'target_language': target_lang
        }
        self.ws_server.send(json.dumps(notification))
```

### 实时监控仪表板

```python
class MonitoringDashboard:
    """实时监控仪表板"""
    
    def __init__(self, system_components, port=8766):
        self.components = system_components
        self.ws_server = WebSocketServer(host='127.0.0.1', port=port)
        self.ws_server.set_message_handler(self.handle_dashboard_message)
        
    def monitoring_loop(self, server):
        """实时监控循环"""
        while self.monitoring_active:
            metrics = self.collect_metrics()
            dashboard_data = {
                'type': 'live_metrics',
                'metrics': metrics
            }
            server.broadcast(json.dumps(dashboard_data))
            time.sleep(2)
```

### 高级消息路由

```python
class WebSocketRouter:
    """WebSocket消息路由系统"""
    
    def __init__(self, port=8767):
        self.ws_server = WebSocketServer(host='127.0.0.1', port=port)
        self.routes = {}
        self.middleware = []
        
    def add_route(self, message_type, handler):
        """注册消息类型处理器"""
        self.routes[message_type] = handler
    
    def add_middleware(self, middleware_func):
        """添加中间件"""
        self.middleware.append(middleware_func)
```

## 依赖关系·系统要求

### 必需依赖
- `asyncio`: 异步处理框架
- `websockets`: WebSocket库
- `threading`: 多线程控制
- `json`: JSON格式数据处理

### 系统要求
- Python 3.7以上
- 异步处理支持
- TCP/WebSocket支持
- 足够内存(依连接数)

### 性能特性
- 并发连接: 支持数百~数千连接
- 消息吞吐量: 每秒可处理数千消息
- 延迟: 低延迟(毫秒级)
- 每连接内存: 约1-5MB

## 注意事项·限制

### 网络限制
- 需确认防火墙设置
- 代理环境可能受限
- 浏览器WebSocket连接限制

### 可扩展性限制
- 单进程同时连接数限制
- 内存使用量线性增加
- CPU密集处理性能下降

### 安全考虑
- 推荐实现认证机制
- 适当授权控制
- 实现速率限制
- 必须验证输入数据
- 适当配置CORS设置

## 相关模块

- `config.py`: WebSocket设置管理
- `controller.py`: WebSocket控制接口
- `utils.py`: 错误日志·实用工具
- `model.py`: WebSocket功能集成

## 将来改进点

- 与Redis等消息代理联动
- 负载均衡·集群支持
- 更高级认证·授权系统
- 支持WebRTC等更快通信协议
- GraphQL over WebSocket支持
- 强化实时监控·分析功能
