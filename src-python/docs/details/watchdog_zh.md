# watchdog.py - 轻量监视系统

## 概述

基于超时的轻量监视(看门狗)系统。通过定期"喂食"(feed)确认正常运行,在指定时间内未喂食时执行回调函数的简单有效监视机制。

## 主要功能

### 超时监视
- 监视距上次喂食时刻的经过时间
- 可配置超时阈值
- 超时时自动执行回调

### 灵活执行模式
- 单次检查(手动调用)
- 后台线程执行
- 自定义检查间隔设置

### 防御性设计
- 回调异常隔离处理
- 线程安全控制机制
- 适当资源管理

## 类结构

### Watchdog 类

```python
class Watchdog:
    def __init__(self, timeout: int = 60, interval: int = 20) -> None:
        self.timeout: int                    # 超时秒数
        self.interval: int                   # 检查间隔秒数  
        self.last_feed_time: float          # 上次喂食时刻
        self.callback: Optional[Callable]    # 超时回调
        self._thread: Optional[Thread]       # 后台线程
        self._stop_event: Optional[Event]    # 停止事件
```

## 主要方法

### 基本控制

```python
def feed(self) -> None
```

喂食看门狗,重置计时器

```python
def setCallback(self, callback: Callable[[], None]) -> None
```

设置超时时执行的回调函数

### 监视执行

```python
def start(self) -> None
```

执行单次看门狗检查并休眠间隔秒数

```python
def start_in_thread(self, daemon: bool = True) -> None
```

在后台线程启动看门狗

```python
def stop(self, timeout: Optional[float] = None) -> None
```

停止后台线程

## 使用方法

### 基本监视系统

```python
from models.watchdog.watchdog import Watchdog
import time

def on_timeout():
    """超时时的处理"""
    print("警告: 系统无响应!")

# 初始化看门狗
watchdog = Watchdog(timeout=30, interval=10)
watchdog.setCallback(on_timeout)

# 后台启动监视
watchdog.start_in_thread(daemon=True)

# 主进程模拟
for i in range(10):
    print(f"处理中... {i}")
    if i % 3 == 0:
        watchdog.feed()
        print("已喂食看门狗")
    time.sleep(5)

# 停止监视
watchdog.stop()
```

### 进程监视系统

```python
class ProcessMonitor:
    """外部进程监视系统"""
    
    def __init__(self, process_name, check_interval=30):
        self.process_name = process_name
        self.watchdog = Watchdog(timeout=60, interval=check_interval)
        self.watchdog.setCallback(self.on_process_timeout)
        
    def on_process_timeout(self):
        """进程响应超时时的处理"""
        print(f"警告: 进程 {self.process_name} 无响应")
        if self.is_process_running():
            self.restart_process()
        else:
            self.start_process()
```

### 多级监视系统

```python
class MultilevelWatchdog:
    """多级警告级别看门狗"""
    
    def __init__(self):
        self.warning_watchdog = Watchdog(timeout=30, interval=10)   # 警告级别
        self.critical_watchdog = Watchdog(timeout=60, interval=15)  # 危险级别
        self.emergency_watchdog = Watchdog(timeout=120, interval=20) # 紧急级别
        
        self.warning_watchdog.setCallback(self.on_warning)
        self.critical_watchdog.setCallback(self.on_critical)
        self.emergency_watchdog.setCallback(self.on_emergency)
```

## 性能·资源考虑

### 轻量设计特征
- 最小内存占用
- 高效线程利用
- CPU使用优化

### 推荐设置值
```python
usage_patterns = {
    "realtime_monitoring": {"timeout": 10, "interval": 2},
    "service_monitoring": {"timeout": 60, "interval": 15},
    "batch_processing": {"timeout": 300, "interval": 60}
}
```

## 依赖关系·要求

### 必需依赖
- `threading`: 线程控制
- `time`: 时刻管理
- 仅标准库(无外部依赖)

### 系统要求
- Python 3.7以上
- 多线程支持OS
- 最小系统资源

## 注意事项·限制

### 设计限制
- 仅基于简单超时的监视
- 不支持复杂条件判定
- 网络监视等需在上层实现

### 使用注意
- 回调函数保持轻量
- 避免长时间阻塞处理
- 适当设置超时值很重要

## 相关模块

- `config.py`: 监视设置管理
- `controller.py`: 监视控制接口
- `utils.py`: 错误日志·实用工具

## 将来改进点

- 支持更复杂监视条件
- 监视统计·指标收集功能
- 可配置恢复策略
- 与分布式监视系统联动
