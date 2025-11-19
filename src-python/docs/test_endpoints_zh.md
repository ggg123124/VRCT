# test_endpoints.py - API端点测试模块

## 概要
用于全面测试VRCT应用程序API端点的模块。通过随机访问测试主循环的各种功能,验证系统的稳定性和健壮性。

### 2025-10 更新点(提交 a54538e 反映)

对于需要动态值的 `/set/data/*` 端点,改为事先调用对应的 `/get/data/...` 端点获取最新值并缓存到 `self.config_dict`,然后再进行随机选择的方式。这改进了以下方面:

- 翻译/转写引擎选择时防止发送不存在的键
- 计算设备/权重类型选择的稳定化(列表更新后再选择)
- 麦克风/扬声器相关超时值的正常范围检查(以获取的最新值为基准进行验证)
- Whisper / CTranslate2 权重类型字典的键集合变化跟随

示例: `"/set/data/selected_translation_engines"` 测试前调用 `"/get/data/selectable_translation_engines"`,从获取的列表中 `random.choice()`。从原来的初始缓存依赖迁移到运行时获取。

## 主要功能

### Color 类

- 使用ANSI转义序列进行控制台输出颜色管理
- 测试结果的视觉化显示(成功・失败・跳过等)

### TestMainloop 类

- API端点的全面测试执行
- 随机访问测试
- 测试结果的记录・分析
- 与VRCT主循环的集成测试

## 主要方法

### 测试执行方法

- `test_endpoints_on_off_all()`: ON/OFF系端点的全测试
- `test_set_data_endpoints_all()`: 数据设置系端点的全测试
- `test_run_endpoints_all()`: 执行系端点的全测试
- `test_endpoints_all_random()`: 全端点的随机访问测试

### 特定功能测试

- `test_translate_all_language_pairs()`: 全语言对的翻译测试
- `test_endpoints_on_off_continuous()`: ON/OFF连续切换测试
- `test_endpoints_specific_random()`: 特定端点的随机测试

### 结果分析

- `generate_summary()`: 测试结果摘要生成
- `record_test_result()`: 测试结果记录

## 使用方法

### 基本用法

```python
# 创建测试实例
test = TestMainloop()

# 执行各种测试
test.test_endpoints_on_off_all()
test.test_set_data_endpoints_all()
test.test_run_endpoints_all()

# 显示测试结果摘要
test.generate_summary()
```

### 随机测试的执行

```python
# 全端点的随机访问测试
test.test_endpoints_all_random()

# 特定端点的随机测试
test.test_endpoints_specific_random()
```

## 依赖关系

- `mainloop`: VRCT主循环模块
- `random`: 随机测试数据生成
- `time`: 测试间隔控制

## 测试对象端点

### 控制系

- `/set/enable/*`: 功能启用
- `/set/disable/*`: 功能禁用

### 数据设置系

- `/set/data/*`: 各种设置数据的更新

动态获取对象(代表例):

- `selected_translation_engines` → `/get/data/selectable_translation_engines`
- `selected_transcription_engine` → `/get/data/selectable_transcription_engines`
- `selected_translation_compute_device` → `/get/data/selectable_translation_compute_device_list`
- `ctranslate2_weight_type` → `/get/data/selectable_ctranslate2_weight_type_dict`
- `whisper_weight_type` → `/get/data/selectable_whisper_weight_type_dict`
- `selected_mic_host` / `selected_mic_device` → `/get/data/selectable_mic_host_list` / `/get/data/selectable_mic_device_list`
- `selected_speaker_device` → `/get/data/selectable_speaker_device_list`

### 执行系

- `/run/*`: 各种功能的执行

### 数据删除系

- `/delete/data/*`: 数据的删除

## 注意事项

- 测试执行前删除`config.json`进行初始化
- 使用重型AI模型的测试请注意执行时间
- 随机测试执行指定次数(默认1000-10000次)
- 测试结束时自动禁用所有功能

## 错误处理

- 各测试独立执行,一个失败不影响整体
- 比较期望的状态码与实际结果
- VRAM不足等资源错误也会适当处理

## 测试结果分类

- **PASS**: 与期望状态码一致
- **ERROR**: 与期望状态码不一致
- **SKIP**: 测试无法执行(401状态)
- **Invalid**: 无效端点(404状态)
