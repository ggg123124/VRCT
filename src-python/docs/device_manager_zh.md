# device_manager.py 设计文档

## 概要

`device_manager.py` 是 VRCT 应用程序的音频设备管理模块,负责麦克风和扬声器设备的检测、监控和自动选择功能。使用 Windows 的 WASAPI 和 pycaw 库实时检测设备变更,并通过注册的回调函数通知应用程序。采用单例模式实现,通过延迟初始化避免 import 时的性能下降。

## 架构定位

```
┌─────────────┐
│controller.py│ (业务逻辑控制层)
└──────┬──────┘
       │ 回调注册和查询
┌──────▼──────────┐
│device_manager.py│ ◄── 本文件
└──────┬──────────┘
       │ 设备监控和枚举
┌──────▼─────────────────────────────┐
│ 操作系统音频子系统                 │
│ - PyAudio (PortAudio wrapper)      │
│ - pyaudiowpatch (WASAPI loopback)  │
│ - pycaw (COM notifications)        │
│ - comtypes (COM initialization)    │
└────────────────────────────────────┘
```

## 主要组件

### 1. Client 类

**职责:** 接收 Windows 的 COM 事件回调,检测设备变更

**继承:** `pycaw.callbacks.MMNotificationClient`

**设计模式:** 观察者模式的回调实现

#### 构造函数 `__init__()`

**处理:**
```python
try:
    super().__init__()
except Exception:
    pass  # 非 Windows 环境下作为占位对象,忽略异常
self.loop: bool = True
```

**`self.loop` 标志:** 
- True: 无设备变更,继续监控
- False: 检测到设备变更,中断监控循环

#### 事件处理器

##### `on_default_device_changed(*args, **kwargs) -> None`
当默认设备变更时由 Windows 调用。

##### `on_device_added(*args, **kwargs) -> None`
当新设备连接时调用。

##### `on_device_removed(*args, **kwargs) -> None`
当设备移除时调用。

##### `on_device_state_changed(*args, **kwargs) -> None`
当设备状态(启用/禁用/不存在等)变更时调用。

**所有处理器的行为:**
```python
self.loop = False  # 通知监控循环发生了变更
```

**注释掉的方法:**
```python
# def on_property_value_changed(self, device_id, key):
#     self.loop = False
```
设备属性变更事件。未使用的原因不明,推测是为了避免频繁事件触发导致的性能下降。

---

### 2. DeviceManager 类

**职责:** 为整个应用程序提供设备管理功能

**模式:** 单例(`__new__` 控制)

**平台支持:** 
- Windows: 完整功能支持(COM 事件监控、WASAPI loopback)
- 非 Windows: 优雅降级(返回默认值,监控功能受限)

---

### 3. 初始化方法

#### `__new__(cls) -> DeviceManager`

**职责:** 生成单例实例并进行轻量级初始化

**处理流程:**
1. **实例检查:**
   ```python
   if cls._instance is None:
       cls._instance = super(DeviceManager, cls).__new__(cls)
   ```
2. **轻量级初始化:**
   ```python
   cls._instance._initialized = False
   try:
       cls._instance.init()
   except Exception:
       try:
           errorLogging()
       except Exception:
           pass  # 绝对避免 import 时崩溃
   ```
3. **返回现有实例:**
   ```python
   return cls._instance
   ```

**设计思想:**
- `__new__` 避免重量级初始化(不启动线程、不访问操作系统 API)
- 调用 `init()` 但不启动监控线程
- 错误时也必定返回实例(防御性编程)

#### `init() -> None`

**职责:** 初始化内部状态并进行首次设备信息获取

**处理流程:**

**1. 已初始化检查:**
```python
if getattr(self, "_initialized", False):
    return  # 已初始化则什么都不做
```

**2. 设备信息初始化(默认值):**
```python
self.mic_devices: Dict[str, List[Dict[str, Any]]] = {
    "NoHost": [{"index": -1, "name": "NoDevice"}]
}
self.default_mic_device: Dict[str, Any] = {
    "host": {"index": -1, "name": "NoHost"},
    "device": {"index": -1, "name": "NoDevice"}
}
self.speaker_devices: List[Dict[str, Any]] = [
    {"index": -1, "name": "NoDevice"}
]
self.default_speaker_device: Dict[str, Any] = {
    "device": {"index": -1, "name": "NoDevice"}
}
```

**3. 前次状态跟踪器:**
```python
self.prev_mic_host: List[str] = [host for host in self.mic_devices]
self.prev_mic_devices: Dict[str, List[Dict[str, Any]]] = self.mic_devices
self.prev_default_mic_device: Dict[str, Any] = self.default_mic_device
self.prev_speaker_devices: List[Dict[str, Any]] = self.speaker_devices
self.prev_default_speaker_device: Dict[str, Any] = self.default_speaker_device
```

**4. 更新标志:**
```python
self.update_flag_default_mic_device: bool = False
self.update_flag_default_speaker_device: bool = False
self.update_flag_host_list: bool = False
self.update_flag_mic_device_list: bool = False
self.update_flag_speaker_device_list: bool = False
```

**5. 回调函数:**
```python
self.callback_default_mic_device: Optional[Callable[..., None]] = None
self.callback_default_speaker_device: Optional[Callable[..., None]] = None
self.callback_host_list: Optional[Callable[..., None]] = None
self.callback_mic_device_list: Optional[Callable[..., None]] = None
self.callback_speaker_device_list: Optional[Callable[..., None]] = None
self.callback_process_before_update_mic_devices: Optional[Callable[..., None]] = None
self.callback_process_after_update_mic_devices: Optional[Callable[..., None]] = None
self.callback_process_before_update_speaker_devices: Optional[Callable[..., None]] = None
self.callback_process_after_update_speaker_devices: Optional[Callable[..., None]] = None
```

**6. 监控控制:**
```python
self.monitoring_flag: bool = False
self.th_monitoring: Optional[Thread] = None
```

**7. 初始化完成标志:**
```python
self._initialized = True
```

**8. 尽力而为的设备信息获取:**
```python
try:
    if PyAudio is not None:
        try:
            self.update()  # 获取实际设备信息
        except Exception:
            errorLogging()
except Exception:
    pass  # 初始化失败也不崩溃
```

**设计思想:**
- 所有属性以默认值初始化(避免未初始化错误)
- 允许 `update()` 失败(在无设备环境下也能运行)
- 记录错误但不向外抛出异常

---

### 4. 设备信息更新方法

#### `update() -> None`

**职责:** 获取当前音频设备列表和默认设备

**处理流程:**

**1. 缓冲区初始化:**
```python
buffer_mic_devices: Dict[str, List[Dict[str, Any]]] = {}
buffer_default_mic_device: Dict[str, Any] = {
    "host": {"index": -1, "name": "NoHost"},
    "device": {"index": -1, "name": "NoDevice"}
}
buffer_speaker_devices: List[Dict[str, Any]] = []
buffer_default_speaker_device: Dict[str, Any] = {
    "device": {"index": -1, "name": "NoDevice"}
}
```

**2. PyAudio 可用性检查:**
```python
if PyAudio is None:
    # 保持默认值并结束
    self.mic_devices = buffer_mic_devices or {"NoHost": [{"index": -1, "name": "NoDevice"}]}
    # ... 设置其他设备信息
    return
```

**3. 麦克风设备收集:**
```python
with PyAudio() as p:
    for host_index in range(p.get_host_api_count()):
        host = p.get_host_api_info_by_index(host_index)
        device_count = host.get('deviceCount', 0)
        for device_index in range(device_count):
            device = p.get_device_info_by_host_api_device_index(host_index, device_index)
            # 有输入通道且非回环设备
            if device.get("maxInputChannels", 0) > 0 and not device.get("isLoopbackDevice", True):
                buffer_mic_devices.setdefault(host["name"], []).append(device)
```

**主机 API 示例:**
- Windows: "MME", "Windows DirectSound", "Windows WASAPI"
- Linux: "ALSA", "PulseAudio"
- macOS: "Core Audio"

**4. 获取默认麦克风设备:**
```python
api_info = p.get_default_host_api_info()
default_mic_device = api_info.get("defaultInputDevice", -1)

for host_index in range(p.get_host_api_count()):
    host = p.get_host_api_info_by_index(host_index)
    device_count = host.get('deviceCount', 0)
    for device_index in range(device_count):
        device = p.get_device_info_by_host_api_device_index(host_index, device_index)
        if device.get("index") == default_mic_device:
            buffer_default_mic_device = {"host": host, "device": device}
            break
    else:
        continue
    break
```

**5. 扬声器回环设备收集:**
```python
speaker_devices: List[Dict[str, Any]] = []
if paWASAPI is not None:
    try:
        wasapi_info = p.get_host_api_info_by_type(paWASAPI)
        wasapi_name = wasapi_info.get("name")
        for host_index in range(p.get_host_api_count()):
            host = p.get_host_api_info_by_index(host_index)
            if host.get("name") == wasapi_name:
                device_count = host.get('deviceCount', 0)
                for device_index in range(device_count):
                    device = p.get_device_info_by_host_api_device_index(host_index, device_index)
                    if not device.get("isLoopbackDevice", True):
                        # 搜索回环设备
                        for loopback in p.get_loopback_device_info_generator():
                            if device.get("name") in loopback.get("name", ""):
                                speaker_devices.append(loopback)
    except Exception:
        pass  # WASAPI 不可用时忽略
```

**什么是回环设备:**
- 可以"录制"从扬声器输出的音频的虚拟设备
- 名称如 "Stereo Mix" 或 "What U Hear"
- 用于识别 VRChat 对方的语音

**6. 去重和排序:**
```python
speaker_devices = [dict(t) for t in {tuple(d.items()) for d in speaker_devices}] or [{"index": -1, "name": "NoDevice"}]
buffer_speaker_devices = sorted(speaker_devices, key=lambda d: d.get('index', -1))
```

**7. 获取默认扬声器设备:**
```python
if paWASAPI is not None:
    try:
        wasapi_info = p.get_host_api_info_by_type(paWASAPI)
        default_speaker_device_index = wasapi_info.get("defaultOutputDevice", -1)
        for host_index in range(p.get_host_api_count()):
            host_info = p.get_host_api_info_by_index(host_index)
            device_count = host_info.get('deviceCount', 0)
            for device_index in range(0, device_count):
                device = p.get_device_info_by_host_api_device_index(host_index, device_index)
                if device.get("index") == default_speaker_device_index:
                    default_speakers = device
                    if not default_speakers.get("isLoopbackDevice", True):
                        for loopback in p.get_loopback_device_info_generator():
                            if default_speakers.get("name") in loopback.get("name", ""):
                                buffer_default_speaker_device = {"device": loopback}
                                break
                    break
            if buffer_default_speaker_device["device"].get("name") != "NoDevice":
                break
    except Exception:
        pass
```

**8. 错误处理和最终设置:**
```python
except Exception:
    errorLogging()

self.mic_devices = buffer_mic_devices
self.default_mic_device = buffer_default_mic_device
self.speaker_devices = buffer_speaker_devices
self.default_speaker_device = buffer_default_speaker_device
```

**设备信息结构示例:**
```python
# 麦克风设备
self.mic_devices = {
    "Windows WASAPI": [
        {"index": 0, "name": "Microphone (Realtek)", "maxInputChannels": 2, ...},
        {"index": 3, "name": "Line In (USB Audio)", "maxInputChannels": 2, ...}
    ],
    "MME": [
        {"index": 10, "name": "マイク (Realtek)", "maxInputChannels": 2, ...}
    ]
}

# 默认麦克风设备
self.default_mic_device = {
    "host": {"index": 0, "name": "Windows WASAPI", ...},
    "device": {"index": 0, "name": "Microphone (Realtek)", ...}
}
```

---

### 5. 变更检测方法

#### `checkUpdate() -> bool`

**职责:** 检测与上次获取的设备信息的差异,并设置更新标志

**处理:**

**1. 默认麦克风设备变更检查:**
```python
if self.prev_default_mic_device["device"]["name"] != self.default_mic_device["device"]["name"]:
    self.update_flag_default_mic_device = True
    self.prev_default_mic_device = self.default_mic_device
```

**2. 默认扬声器设备变更检查:**
```python
if self.prev_default_speaker_device["device"]["name"] != self.default_speaker_device["device"]["name"]:
    self.update_flag_default_speaker_device = True
    self.prev_default_speaker_device = self.default_speaker_device
```

**3. 麦克风主机列表变更检查:**
```python
if self.prev_mic_host != [host for host in self.mic_devices]:
    self.update_flag_host_list = True
    self.prev_mic_host = [host for host in self.mic_devices]
```

**4. 麦克风设备列表变更检查:**
```python
if ({key: [device['name'] for device in devices] for key, devices in self.prev_mic_devices.items()} !=
    {key: [device['name'] for device in devices] for key, devices in self.mic_devices.items()}):
    self.update_flag_mic_device_list = True
    self.prev_mic_devices = self.mic_devices
```

**比较方法:**
- 仅比较设备名称列表(忽略 `index` 的变化)
- 按主机分组比较

**5. 扬声器设备列表变更检查:**
```python
if [device['name'] for device in self.prev_speaker_devices] != [device['name'] for device in self.speaker_devices]:
    self.update_flag_speaker_device_list = True
    self.prev_speaker_devices = self.speaker_devices
```

**6. 综合更新标志判定:**
```python
update_flag = (
    self.update_flag_default_mic_device or
    self.update_flag_default_speaker_device or
    self.update_flag_host_list or
    self.update_flag_mic_device_list or
    self.update_flag_speaker_device_list
)
return update_flag
```

**返回值:**
- `True`: 任一设备信息发生变更
- `False`: 所有设备信息与上次相同

---

### 6. 监控方法

#### `monitoring() -> None`

**职责:** 在后台监控设备变更,变更时执行回调

**执行环境:** 独立线程(`startMonitoring()` 启动)

**处理流程:**

**1. 监控循环:**
```python
try:
    while self.monitoring_flag is True:
        try:
            # 监控处理
        except Exception:
            errorLogging()
except Exception:
    errorLogging()
```

**2. COM 事件监控(仅 Windows):**
```python
if comtypes is not None and AudioUtilities is not None:
    try:
        comtypes.CoInitialize()  # COM 初始化
        cb = Client()
        enumerator = AudioUtilities.GetDeviceEnumerator()
        enumerator.RegisterEndpointNotificationCallback(cb)
        
        while cb.loop is True and self.monitoring_flag is True:
            sleep(1)  # 等待事件
        
        try:
            enumerator.UnregisterEndpointNotificationCallback(cb)
        except Exception:
            pass  # 尽力而为
        comtypes.CoUninitialize()
    except Exception:
        errorLogging()
```

**COM 监控工作方式:**
- `Client` 类的事件处理器检测设备变更
- `cb.loop` 变为 `False` 时退出循环
- COM 不可用时回退到轮询

**3. 轮询和更新周期:**
```python
# 更新前处理
self.runProcessBeforeUpdateMicDevices()
self.runProcessBeforeUpdateSpeakerDevices()

sleep(2)  # 等待设备状态稳定

# 最多轮询 10 次(20 秒)
for _ in range(10):
    self.update()
    if self.checkUpdate():
        break  # 检测到变更则结束
    sleep(2)

# 回调通知
self.noticeUpdateDevices()

# 更新后处理
self.runProcessAfterUpdateMicDevices()
self.runProcessAfterUpdateSpeakerDevices()
```

**轮询策略:**
- 首次等待 2 秒: 避免设备连接/断开后的不稳定期
- 最多轮询 10 次: 不漏检设备变更
- 检测到变更后立即进行下一步处理

**4. 重复监控周期:**
```python
# 回到 while self.monitoring_flag is True 开头
```

#### `startMonitoring() -> None`

**职责:** 启动监控线程

**处理:**
```python
if self.monitoring_flag:
    return  # 已在运行
self.monitoring_flag = True
self.th_monitoring = Thread(target=self.monitoring)
self.th_monitoring.daemon = True
self.th_monitoring.start()
```

**守护线程:**
- 主线程结束时自动终止
- 不妨碍应用程序退出

#### `stopMonitoring() -> None`

**职责:** 停止监控线程

**处理:**
```python
self.monitoring_flag = False
if getattr(self, "th_monitoring", None) is not None:
    try:
        self.th_monitoring.join(timeout=5)  # 最多等待 5 秒
    except Exception:
        pass  # 尽力而为
```

**超时设置:**
- 5 秒内未结束则放弃等待
- join 失败也忽略错误(防御性)

---

### 7. 回调管理方法

#### 默认设备变更回调

##### `setCallbackDefaultMicDevice(callback: Callable[..., None]) -> None`
注册默认麦克风设备变更时的回调。

**回调签名:**
```python
def callback(host_name: str, device_name: str) -> None:
    pass
```

##### `clearCallbackDefaultMicDevice() -> None`
清除回调。

##### `setCallbackDefaultSpeakerDevice(callback: Callable[..., None]) -> None`
注册默认扬声器设备变更时的回调。

**回调签名:**
```python
def callback(device_name: str) -> None:
    pass
```

##### `clearCallbackDefaultSpeakerDevice() -> None`
清除回调。

#### 设备列表变更回调

##### `setCallbackHostList(callback: Callable[..., None]) -> None`
注册麦克风主机列表变更时的回调。

##### `clearCallbackHostList() -> None`
清除回调。

##### `setCallbackMicDeviceList(callback: Callable[..., None]) -> None`
注册麦克风设备列表变更时的回调。

##### `clearCallbackMicDeviceList() -> None`
清除回调。

##### `setCallbackSpeakerDeviceList(callback: Callable[..., None]) -> None`
注册扬声器设备列表变更时的回调。

##### `clearCallbackSpeakerDeviceList() -> None`
清除回调。

#### 处理钩子回调

##### `setCallbackProcessBeforeUpdateMicDevices(callback: Callable[..., None]) -> None`
注册麦克风设备更新前的处理。

**使用示例:** 停止语音识别以释放设备

##### `clearCallbackProcessBeforeUpdateMicDevices() -> None`
清除回调。

##### `setCallbackProcessAfterUpdateMicDevices(callback: Callable[..., None]) -> None`
注册麦克风设备更新后的处理。

**使用示例:** 用新设备重新启动语音识别

##### `clearCallbackProcessAfterUpdateMicDevices() -> None`
清除回调。

##### `setCallbackProcessBeforeUpdateSpeakerDevices(callback: Callable[..., None]) -> None`
注册扬声器设备更新前的处理。

##### `clearCallbackProcessBeforeUpdateSpeakerDevices() -> None`
清除回调。

##### `setCallbackProcessAfterUpdateSpeakerDevices(callback: Callable[..., None]) -> None`
注册扬声器设备更新后的处理。

##### `clearCallbackProcessAfterUpdateSpeakerDevices() -> None`
清除回调。

---

### 8. 回调执行方法

#### `runProcessBeforeUpdateMicDevices() -> None`

**职责:** 执行麦克风设备更新前的处理回调

**处理:**
```python
if isinstance(self.callback_process_before_update_mic_devices, Callable):
    try:
        self.callback_process_before_update_mic_devices()
    except Exception:
        errorLogging()
```

**类型检查:**
- 用 `isinstance(callback, Callable)` 确认可调用性
- `None` 时不做任何操作

#### `runProcessAfterUpdateMicDevices() -> None`
执行麦克风设备更新后的处理回调(实现类似)。

#### `runProcessBeforeUpdateSpeakerDevices() -> None`
执行扬声器设备更新前的处理回调(实现类似)。

#### `runProcessAfterUpdateSpeakerDevices() -> None`
执行扬声器设备更新后的处理回调(实现类似)。

---

### 9. 通知方法

#### `noticeUpdateDevices() -> None`

**职责:** 根据更新标志调用相应的回调并重置标志

**处理:**
```python
if self.update_flag_default_mic_device is True:
    self.setMicDefaultDevice()
if self.update_flag_default_speaker_device is True:
    self.setSpeakerDefaultDevice()
if self.update_flag_host_list is True:
    self.setMicHostList()
if self.update_flag_mic_device_list is True:
    self.setMicDeviceList()
if self.update_flag_speaker_device_list is True:
    self.setSpeakerDeviceList()

# 重置所有标志
self.update_flag_default_mic_device = False
self.update_flag_default_speaker_device = False
self.update_flag_host_list = False
self.update_flag_mic_device_list = False
self.update_flag_speaker_device_list = False
```

#### `setMicDefaultDevice() -> None`

**职责:** 执行默认麦克风设备变更回调

**处理:**
```python
if isinstance(self.callback_default_mic_device, Callable):
    try:
        self.callback_default_mic_device(
            self.default_mic_device["host"]["name"],
            self.default_mic_device["device"]["name"]
        )
    except Exception:
        errorLogging()
```

#### `setSpeakerDefaultDevice() -> None`

**职责:** 执行默认扬声器设备变更回调

**处理:**
```python
if isinstance(self.callback_default_speaker_device, Callable):
    try:
        self.callback_default_speaker_device(
            self.default_speaker_device["device"]["name"]
        )
    except Exception:
        errorLogging()
```

#### `setMicHostList() -> None`
执行麦克风主机列表变更回调(无参数)。

#### `setMicDeviceList() -> None`
执行麦克风设备列表变更回调(无参数)。

#### `setSpeakerDeviceList() -> None`
执行扬声器设备列表变更回调(无参数)。

---

### 10. 设备信息获取方法

#### `getMicDevices() -> Dict[str, List[Dict[str, Any]]]`

**职责:** 获取麦克风设备列表

**处理:**
```python
if not getattr(self, '_initialized', False):
    try:
        self.init()
    except Exception:
        try:
            errorLogging()
        except Exception:
            pass
return getattr(self, 'mic_devices', {"NoHost": [{"index": -1, "name": "NoDevice"}]})
```

**安全性:**
- 未初始化时调用 `init()`
- 失败时返回默认值

**返回值示例:**
```python
{
    "Windows WASAPI": [
        {"index": 0, "name": "Microphone (Realtek)", ...},
        {"index": 3, "name": "Line In (USB Audio)", ...}
    ],
    "MME": [
        {"index": 10, "name": "マイク (Realtek)", ...}
    ]
}
```

#### `getDefaultMicDevice() -> Dict[str, Any]`

**职责:** 获取默认麦克风设备

**返回值示例:**
```python
{
    "host": {"index": 0, "name": "Windows WASAPI", ...},
    "device": {"index": 0, "name": "Microphone (Realtek)", ...}
}
```

#### `getSpeakerDevices() -> List[Dict[str, Any]]`

**职责:** 获取扬声器设备列表

**返回值示例:**
```python
[
    {"index": 5, "name": "Stereo Mix (Realtek)", "isLoopbackDevice": True, ...},
    {"index": 7, "name": "Speakers (USB Audio) [Loopback]", ...}
]
```

#### `getDefaultSpeakerDevice() -> Dict[str, Any]`

**职责:** 获取默认扬声器设备

**返回值示例:**
```python
{
    "device": {"index": 5, "name": "Stereo Mix (Realtek)", ...}
}
```

---

### 11. 强制更新方法

#### `forceUpdateAndSetMicDevices() -> None`

**职责:** 强制更新麦克风设备信息并执行所有回调

**处理:**
```python
self.update()
self.setMicHostList()
self.setMicDeviceList()
self.setMicDefaultDevice()
```

**使用场景:**
- 自动设备选择功能的首次应用
- 用户手动请求更新

#### `forceUpdateAndSetSpeakerDevices() -> None`

**职责:** 强制更新扬声器设备信息

**处理:**
```python
self.update()
self.setSpeakerDeviceList()
self.setSpeakerDefaultDevice()
```

---

### 12. 模块级使用方法

#### 单例实例

```python
device_manager = DeviceManager()
```

**只需导入模块即可使用:**
```python
from device_manager import device_manager

# 获取设备信息
mic_devices = device_manager.getMicDevices()
```

#### 演示脚本

```python
if __name__ == "__main__":
    print("DeviceManager demo. Call device_manager.init() and device_manager.startMonitoring() to run live monitoring.")
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("exiting")
```

**执行方法:**
```powershell
python device_manager.py
```

---

## 依赖关系

### 外部库

```python
from typing import Callable, Dict, List, Optional, Any
from time import sleep
from threading import Thread
```

### 可选依赖(Windows 专用)

```python
import comtypes  # COM 初始化和终止
from pyaudiowpatch import PyAudio, paWASAPI  # WASAPI loopback 支持
from pycaw.callbacks import MMNotificationClient  # 设备变更事件
from pycaw.utils import AudioUtilities  # 设备枚举
```

**非 Windows 环境下的行为:**
- 所有可选依赖都用 `try-except` 保护
- 导入失败时设置为 `None` 或 placeholder
- 保持返回默认值(`NoDevice`)的功能

### 内部模块

```python
from utils import errorLogging
```

---

## 自动设备选择的工作流程

### Controller 端的设置(示例)

```python
# controller.py 的 applyAutoMicSelect() 方法

def applyAutoMicSelect(self) -> None:
    # 1. 更新前处理: 停止使用设备的功能
    device_manager.setCallbackProcessBeforeUpdateMicDevices(
        self.stopAccessMicDevices
    )
    
    # 2. 默认设备变更时: 选择新设备
    device_manager.setCallbackDefaultMicDevice(
        self.updateSelectedMicDevice
    )
    
    # 3. 更新后处理: 用新设备重启功能
    device_manager.setCallbackProcessAfterUpdateMicDevices(
        self.restartAccessMicDevices
    )
    
    # 4. 首次执行
    device_manager.forceUpdateAndSetMicDevices()
    
    # 5. 开始监控
    device_manager.startMonitoring()
```

### 设备变更时的序列图

```
[用户连接耳机]
        ↓
[Windows 更改默认设备]
        ↓
[pycaw 的 Client.on_device_added() 被调用]
        ↓
[client.loop = False 设置]
        ↓
[monitoring() 的 COM 监控循环结束]
        ↓
[runProcessBeforeUpdateMicDevices() 执行]
        ↓
[controller.stopAccessMicDevices()]
   - 停止语音识别
   - 释放设备
        ↓
[update() 更新设备信息]
        ↓
[checkUpdate() 检测变更]
        ↓
[noticeUpdateDevices() 调用回调]
        ↓
[setMicDefaultDevice() 执行]
        ↓
[controller.updateSelectedMicDevice(host, device)]
   - 更新设置
   - 通知前端
        ↓
[runProcessAfterUpdateMicDevices() 执行]
        ↓
[controller.restartAccessMicDevices()]
   - 用新设备启动语音识别
        ↓
[COM 监控循环重新开始]
```

---

## 错误处理策略

### 1. import 时的错误

**问题:** Windows 专用库在非 Windows 环境下被导入

**对策:**
```python
try:
    import comtypes
except Exception:
    comtypes = None  # type: ignore
```

**结果:**
- 不发生导入错误
- 用 `comtypes is None` 判断可用性
- 功能受限但应用程序可运行

### 2. 初始化时的错误

**问题:** 设备信息获取失败

**对策:**
```python
try:
    self.update()
except Exception:
    errorLogging()
    # 继续使用默认值
```

**结果:**
- 记录错误但不崩溃
- 使用默认设备信息运行

### 3. 监控循环中的错误

**问题:** COM 初始化失败、设备枚举异常

**对策:**
```python
try:
    # COM 监控处理
except Exception:
    errorLogging()
    # 回退到轮询模式
```

**结果:**
- 无法使用事件驱动监控时使用轮询
- 确保监控功能持续

### 4. 回调执行中的错误

**问题:** 用户提供的回调函数抛出异常

**对策:**
```python
try:
    callback(args)
except Exception:
    errorLogging()
```

**结果:**
- 记录错误但不影响监控循环
- 其他回调继续执行

---

## 性能考虑事项

### 1. 延迟初始化

- `__new__` 中不执行重量级处理
- `init()` 调用时机可控制
- 避免 import 时的性能下降

### 2. 事件驱动监控

- Windows 环境下使用 COM 事件(低 CPU 使用率)
- 仅在设备变更时激活
- 无需定期轮询

### 3. 轮询作为回退

- COM 不可用时的轮询间隔: 2 秒
- 最多轮询 10 次(20 秒)
- 平衡响应性和 CPU 使用率

### 4. 单例模式

- 避免重复的设备枚举
- 共享设备信息缓存
- 减少内存使用

---

## 线程安全性

### 1. 监控线程

- 单一监控线程
- 守护线程(不阻止程序退出)
- 标志控制的优雅停止

### 2. 回调执行

- 在监控线程中执行
- 回调内部需要线程安全实现
- 建议使用线程安全的队列进行通信

### 3. 设备信息访问

- 读取时无锁(假设原子更新)
- 更新在单一线程中进行
- 避免竞态条件

---

## 限制事项

1. **平台限制:**
   - 完整功能仅在 Windows 上可用
   - 非 Windows 环境功能受限

2. **设备类型限制:**
   - 扬声器回环功能需要 WASAPI
   - 某些音频 API 可能不支持

3. **权限要求:**
   - 需要音频设备访问权限
   - COM 初始化可能需要特定权限

4. **性能特性:**
   - 设备枚举需要一定时间(通常 < 1 秒)
   - 事件传播有轻微延迟

---

## 未来改进建议

1. **跨平台支持:**
   - macOS Core Audio 支持
   - Linux PulseAudio/ALSA 支持

2. **高级功能:**
   - 设备热插拔历史记录
   - 设备偏好设置持久化
   - 设备别名功能

3. **性能优化:**
   - 设备信息缓存改进
   - 增量更新检测
   - 非阻塞设备枚举

4. **诊断功能:**
   - 设备状态健康检查
   - 详细的设备能力信息
   - 音频流监控

---

## 相关文档

- `controller.md`: Controller 中的使用示例
- `config.md`: 设备设置的持久化
- `utils.md`: 错误日志记录
- `コーディングルール.md`: 编码规范

---

## 许可证

参考项目根目录的 `LICENSE` 文件

---

## 总结

`device_manager.py` 是 VRCT 项目的关键基础设施,提供以下重要功能:

1. **跨平台兼容性**: Windows 完整功能,其他平台优雅降级
2. **实时监控**: 事件驱动的设备变更检测
3. **灵活的回调系统**: 支持多种设备变更场景
4. **强大的错误处理**: 即使在异常情况下也能继续运行
5. **性能优化**: 单例模式、延迟初始化、事件驱动设计

作为所有音频相关功能的基础,该模块保持高可靠性和可维护性。
