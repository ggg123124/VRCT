# VRCT backend — 编码规范

目的：
- 在保持可读性和可维护性的同时尊重现有风格。
- 逐步引入类型注解，符合 mypy 和 ruff 的检查要求。
- 便于导出到自动化（CI / pre-commit）。

注意：现有的命名和结构（函数名、类名、变量名、run mapping 的键等）为了代码兼容性保持原样。以下是新实现或重构时应遵循的规则。

## 目录
- 命名规则
- 模块和包的组织结构
- 导入
- 类型注解和 mypy 方针
- 文档注释 / docstrings
- 错误处理和日志记录
- 异步 / 线程 / 队列的处理
- 测试和 CI
- 重构和兼容性考虑

---

## 命名规则
- 模块名：小写，用下划线分隔（例如：`overlay_utils.py`）。遵循现有文件。
- 包名：小写（`models`、`websocket` 等）。
- 类名：CapWords（PascalCase）。遵循现有类（`Controller`、`Model`、`Overlay`）。
- 函数/方法名：snake_case。
- 变量名：snake_case。短的临时变量可以使用 `i`、`j`、`buf` 等传统缩写，但优先使用有意义的名称。
- 常量：UPPER_SNAKE_CASE（与 `config.py` 中的常量保持一致）。
- run_mapping 的键：目前内部使用短键（例如：`transcription_mic`），在 `run_mapping` 中放置 `/run/...`。维持这一惯例。允许在 Controller 内直接引用 `self.run_mapping[...]` 的实现。

## 模块和包的组织结构
- 各子领域（ocr、overlay、transcription、translation、websocket 等）已在 `models/` 下整理，新功能应按相同粒度添加。
- 包必须包含 `__init__.py`（用于静态分析 / mypy）。空的 `__init__.py` 也可以。这样可以稳定相对导入。

## 导入
- 按标准库、第三方、本地的顺序组织导入。
- 引用本地模块时可以使用相对导入，但要确保项目整体可以加入 PYTHONPATH 进行测试/静态分析。
- 示例：
```python
import os
import json

import numpy as np

from . import overlay_utils
```

## 类型注解和 mypy 方针
- 策略：宽松 + 增量注解（渐进式类型）。遵循以下规则：
  - 新代码尽可能添加类型注解（函数签名、返回值）。
  - 现有的大型函数分阶段注解。首先为模块边界（public API）的签名添加注解。内部细节变量可以稍后处理。
  - CI 初期阶段用宽松模式运行 mypy，如 `--ignore-missing-imports --allow-untyped-defs --allow-redefinition`。逐步启用 `--check-untyped-defs`。
  - 不要过度使用 `Any` 类型。如果确实需要，添加 `# type: ignore[assignment]` 并在注释中说明原因。

## docstrings / 注释
- 为重要的 public 函数、方法和类添加简短的 docstring（概述目的、参数、返回值）。不需要统一 Google/Numpy 风格，但项目内应保持简洁一致。
- 对于实现复杂的地方，留下 `# NOTE:` 或 `# FIXME:` 注释，必要时关联 issue（例如：`# NOTE: keep in sync with mainloop.run_mapping`）。

## 错误处理和日志记录
- 捕获异常时在日志中留下有用的上下文（使用 `errorLogging()` 等工具函数）。
- 使用 broad except: 时至少调用 `errorLogging()`，必要时用 `raise` 向上层传播。

## 异步 / 线程 / 队列的处理
- 由于部分代码使用 `threading.Thread`，线程间通信应基于 `queue.Queue` 实现。
- 生成线程的函数使用 `start_` 前缀命名（例如：`start_transcription_thread`）会更清晰。

## 测试和 CI
- 首先引入轻量级 CI 工作流：
  - ruff check
  - mypy（宽松模式）
  - 自动测试（未来添加 pytest）
- 推荐引入 pre-commit 钩子：可以采用 ruff auto-fix 和 isort（导入整理）。

## 重构和兼容性
- 现有 public API（stdin/stdout 的 endpoint 规范、`run_mapping` 的键、Controller 的方法名）优先考虑向后兼容。如需更改，必须在 CHANGELOG 中明确说明。

## 小型编码规范检查清单（PR 模板）
- 新的 public 方法是否添加了 docstring
- 是否遵循现有命名规则（snake_case / PascalCase / UPPER_SNAKE_CASE）
- 是否为签名添加了类型注解（尽可能）
- 直接向 stdout 输出 JSON 的地方是否通过 `printResponse` 等工具函数

---

本文档旨在尊重现有风格的同时提供最小限度的规则。如果希望进一步：
- 创建 PR 将 ruff/mypy 集成到 CI
- 添加 pre-commit 配置文件（`.pre-commit-config.yaml`）引入自动格式化
- 为类型注解和测试进行任务划分（按优先级排列的 TODO）

如有需要，可以基于此创建 `.pre-commit-config.yaml`、`pyproject.toml` 的 ruff 配置，或 CI 工作流模板（GitHub Actions）。

## 与 Copilot 协作的具体示例和模板
以下是便于向 Copilot 提供推荐提示以及 PR 创建时使用的模板。可以直接复制粘贴使用。

### 函数模板（类型注解 + docstring）
```python
from typing import Any, Dict, Optional

def example_handler(endpoint: str, data: Any) -> Dict[str, Any]:
    """处理示例端点。

    Args:
        endpoint: 传入的端点字符串（例如 '/get/data/version'）
        data: 请求负载（许多 GET 请求为 None）

    Returns:
        适合 printResponse(status, endpoint, result) 的字典
    """
    # 实现...
    result = {"status": 200, "endpoint": endpoint, "result": data}
    return result
```

### Controller 的 run 调用模式（推荐）
在 Controller 内调用 run 时，请保持 `self.run(self.run_mapping["key"], payload)` 的形式。向 Copilot 询问时可以问"这个 run key 对应的 payload 形式是什么？"这样更容易生成负载示例。

### Docstring 示例（Google 风格）
```python
def set_selected_tab_no(tab_no: int) -> Dict[str, Any]:
    """设置当前标签页。

    Args:
        tab_no: 要选择的标签页索引

    Returns:
        包含状态和新标签页号的响应字典
    """
    ...
```

### PR 检查清单（扩展版）
- 是否遵循编码规则
- 新的 public API 是否有 docstring
- 是否添加了最基本的类型注解（特别是函数签名）
- ruff check 是否通过
- mypy（宽松模式）是否没有重大类型错误
- 如有 API 更改，是否更新了文档（必要部分）

### 推荐 `.pre-commit-config.yaml`（示例）
```yaml
repos:
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
        args: ["--fix"]
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.18.2
    hooks:
      - id: mypy
        args: ["--ignore-missing-imports", "--allow-untyped-defs", "--allow-redefinition"]
```

### 推荐 ruff 配置（pyproject.toml 的最小配置示例）
```toml
[tool.ruff]
line-length = 88
extend-ignore = ["E203"]
select = ["E", "F", "W", "C90"]
```

---

如需更新，我可以创建 `.pre-commit-config.yaml`、`pyproject.toml` 以及 CI 工作流（GitHub Actions）模板并提交。您希望优先处理哪个？
