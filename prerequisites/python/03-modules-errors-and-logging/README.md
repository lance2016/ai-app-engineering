---
status: complete
part: 前置 · Python
estimated_time: 约 2.5 小时
---

# P03 模块、异常与日志

> 代码多了要拆成文件，出错了要有名有姓地处理，运行过程要留下记录。这三件事分别对应 import、异常和 logging，是从"写脚本"到"写程序"的分界线。

## 学习目标

- 能把代码拆成模块和包，并用三种 import 写法把它们用起来
- 能抛出和捕获特定类型的异常，说出 `try/except/else/finally` 四段各在什么时候执行
- 能用 logging 代替 print，按级别控制输出，并让异常带着调用栈进日志

## 前置

- [P01 Python 基础语法](../01-python-basics/README.md)：函数、`if __name__ == "__main__"`
- [P02 容器与迭代](../02-collections-and-iteration/README.md)：dict 取值时的 KeyError 是本课的例子之一

## 核心概念

### 模块与包

一个 `.py` 文件就是一个模块。一个带 `__init__.py` 的文件夹就是一个包。

```text
code/
├── 01_modules_and_imports.py
└── shapes/              <- 包
    ├── __init__.py      <- import shapes 时读的是它
    └── area.py          <- 模块
```

```python
import math                          # 整个模块，用 math.pi
from pathlib import Path             # 只拿一个名字
import shapes                        # 自己的包
from shapes.area import rectangle_area
import shapes.area as area_tools     # 起别名
```

Python 找模块的顺序：先看脚本所在目录，再看虚拟环境里装的库，再看标准库。所以 `shapes/` 放在脚本旁边就能直接 import。

按仓库的约定，import 都写在文件顶部。

### 异常：错误是可以接住的值

```python
try:
    number = int("forty-two")
except ValueError as exc:
    print("ValueError:", exc)
```

程序出错时 Python 会"抛出"一个异常对象。没人接住，程序就带着一段 Traceback 退出。`try/except` 是接住它的方式。`except ValueError` 只接这一种，别的错照样往上抛，这是对的：你只应该处理你知道怎么处理的错误。

自己也可以抛：

```python
def withdraw(balance, amount):
    if amount > balance:
        raise ValueError(f"cannot withdraw {amount}, balance is {balance}")
    return balance - amount
```

### 自定义异常和四段结构

```python
class PaymentError(Exception):
    """所有支付相关错误的父类"""

class InsufficientFunds(PaymentError):
    def __init__(self, needed, available):
        super().__init__(f"need {needed}, have {available}")
        self.needed = needed
```

继承 `Exception` 就是一个新的异常类型。分层的好处是调用方可以 `except PaymentError` 一次接住整个家族，也可以 `except InsufficientFunds` 只接一种。

```python
try:
    ...           # 可能出错的代码
except SomeError:
    ...           # 出了这种错时执行
else:
    ...           # 没出错时执行
finally:
    ...           # 无论如何都执行，关文件、关连接放这里
```

`else` 和 `finally` 用得少但很有用：`else` 把"成功后做的事"和"可能出错的事"分开，`finally` 保证清理一定发生。

### logging，不是 print

```python
import logging
logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
log = logging.getLogger("demo")

log.debug("详细信息，平时不看")
log.info("正常进度")
log.warning("有点不对但能继续")
log.error("出错了")
log.exception("出错了，并且把 Traceback 一起记下来")   # 只在 except 里用
```

print 只能输出到屏幕、没有时间、没有级别、删不掉。logging 有五个级别，`basicConfig(level=...)` 一行就能决定看到哪些；每条自带时间和来源；上线后可以改成写文件或发到日志系统，代码一行不动。

规矩很简单：调试时想临时看个值可以 print，写完删掉；留在代码里的输出一律用 logging。

## 动手

| 文件 | 演示什么 |
|---|---|
| [`code/01_modules_and_imports.py`](./code/01_modules_and_imports.py) | 三种 import 写法，以及旁边 `shapes/` 包是怎么被找到的。顺便读一下 `shapes/__init__.py` 和 `shapes/area.py` |
| [`code/02_exceptions_basics.py`](./code/02_exceptions_basics.py) | 接住三种常见异常，自己 raise 一个，程序继续跑 |
| [`code/03_custom_exception_and_finally.py`](./code/03_custom_exception_and_finally.py) | 自定义异常层级；成功和失败两条路径下四段结构各执行了哪几段 |
| [`code/04_logging_not_print.py`](./code/04_logging_not_print.py) | 五个级别；`LOG_LEVEL=DEBUG` 再跑一次看多出来的那行；`log.exception` 带 Traceback |

## 常见错误

**`ModuleNotFoundError: No module named 'requests'`**

```python
import requests
```

这个库没装在当前虚拟环境里。要么它不在项目依赖里，要么你没用 `uv run`。先确认用的是 `.venv`，再看 `pyproject.toml` 里有没有它。课程仓库不要自己 `uv add`，缺什么在对应课会说明。

**把所有异常一把抓**

```python
try:
    ...
except Exception:
    pass
```

这不是报错，是比报错更糟的事：错误被吞掉了，程序带着错误的状态继续跑，你在几十行之后才看到莫名其妙的结果。只接你知道怎么处理的异常类型，接住了至少要 `log.exception()`。

**`TypeError: non-default argument 'y' follows default argument`**

这个错在 P04 的 dataclass 里也会见到，本质是函数参数的规则：有默认值的参数必须排在没有默认值的后面。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

主线第 05 课有一个原则：工具执行失败时，不要让异常把整个程序打崩，而是接住它、变成一条"错误结果"告诉模型，让模型有机会换个办法。那一课的代码里 `except ValidationError`、`except TimeoutError` 分别走不同的路，正是本课"只接你会处理的异常"的直接应用。第 06 课把这个做法扩展成一张"失败类型到恢复动作"的表。

第 19 课讲生产环境的可靠性时，日志是排障的第一手材料。那时你会发现 print 出来的东西没有时间戳、没有请求 ID，根本没法用；而从第一天就用 logging 的代码，接上日志系统只是改一行配置。

## 延伸阅读

- [Python 官方教程 · 模块](https://docs.python.org/3/tutorial/modules.html)（访问日期 2026-09-04）：模块搜索路径、包、`__init__.py` 的官方说明。
- [Python 官方教程 · 错误和异常](https://docs.python.org/3/tutorial/errors.html)（访问日期 2026-09-04）：异常层级、`raise`、`finally`、异常链。
- [Logging HOWTO](https://docs.python.org/3/howto/logging.html)（访问日期 2026-09-04）：官方的 logging 入门，看前半部分"基础教程"就够。
- [廖雪峰 · 错误、调试和测试](https://liaoxuefeng.com/books/python/error-debug-test/index.html)（访问日期 2026-09-04）：中文，包含 logging 和调试器的用法。

---

[← P02](../02-collections-and-iteration/README.md) · [P04 →](../04-oop-and-dataclasses/README.md)
