---
status: complete
part: 前置 · Python
estimated_time: 约 2.5 小时
---

# P04 类、dataclass 与 Protocol

> 类把数据和操作它的函数放在一起。dataclass 让"只是一堆字段"的类三行写完。Protocol 让"长得像就行"这条 Python 一直遵守的规矩有了名字。这三样在后面的课程里天天见。

## 学习目标

- 能写一个带 `__init__` 和方法的类，说清 `self` 是什么、两个实例为什么互不影响
- 能用 `@dataclass` 定义数据类，知道什么时候加 `frozen=True`，为什么列表字段必须用 `field(default_factory=list)`
- 能解释鸭子类型，并用 `Protocol` 把"需要有某个方法"写成类型

## 前置

- [P01 Python 基础语法](../01-python-basics/README.md)：函数、默认参数
- [P03 模块、异常与日志](../03-modules-errors-and-logging/README.md)：自定义异常已经让你见过一次 `class`

## 核心概念

### 类和实例

```python
class Counter:
    def __init__(self, name: str) -> None:
        self.name = name
        self.total = 0

    def add(self, amount: int = 1) -> None:
        self.total += amount

tokens_in = Counter("input tokens")
tokens_out = Counter("output tokens")
tokens_in.add(120)
```

类是图纸，实例是按图纸造出来的东西。`Counter("input tokens")` 造一个实例，`__init__` 在这时运行，把初始值放到 `self` 上。`self` 就是"当前这个实例"，每个实例有自己的 `name` 和 `total`，所以 `tokens_in` 加了 120 不影响 `tokens_out`。

方法的第一个参数永远是 `self`，调用时不用传，Python 自动填。

### dataclass

同一个"消息"类，手写和用 dataclass：

```python
class MessageByHand:
    def __init__(self, role, content):
        self.role = role
        self.content = content
    def __repr__(self): ...      # 让 print 好看
    def __eq__(self, other): ... # 让 == 比较内容

from dataclasses import dataclass

@dataclass
class Message:
    role: str
    content: str = ""
```

两者行为一样：`Message("user", "hi")` 打印出 `Message(role='user', content='hi')`，两个字段相同的实例 `==` 为真。dataclass 看着字段的类型注解，自动生成 `__init__`、`__repr__`、`__eq__`。凡是"主要就是一堆字段"的类，都用它。

### frozen 和 default_factory

```python
@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict

call = ToolCall("get_weather", {"city": "Shenzhen"})
call.name = "x"   # FrozenInstanceError: cannot assign to field 'name'
```

`frozen=True` 让实例造好后不能改。"一次工具调用请求"这种记录性质的数据就该冻住，谁改了都是 bug。

```python
@dataclass
class Thread:
    events: list[str] = field(default_factory=list)
```

列表、字典这类可变的默认值不能直接写 `= []`，Python 会直接拒绝。原因是默认值只创建一次，所有实例会共用同一个列表，一个实例 append 了另一个也会看到。`default_factory=list` 表示"每造一个实例就调一次 `list()`，给它一个新的"。

### 鸭子类型和 Protocol

Python 不看你"是什么"，只看你"能做什么"。一个函数需要参数有 `speak()` 方法，那任何有这个方法的对象都能传，不管它们有没有共同的父类。这叫鸭子类型：走路像鸭子叫声像鸭子，就当它是鸭子。

```python
from typing import Protocol

class Speaker(Protocol):
    def speak(self) -> str: ...

def announce(who: Speaker) -> None:
    print(who.speak())

announce(Robot())   # Robot 没有继承 Speaker，但有 speak()，可以
announce(Human())   # 同理
```

`Protocol` 就是把"需要有 `speak()`"这个要求写下来。`Robot` 和 `Human` 不需要知道 `Speaker` 的存在。P05 会从类型检查的角度再看它一次。

### 类还是函数

没有需要在多次调用之间保存的状态，就写函数。有几个方法要共享同一份状态，写类。只是一堆字段没有行为，写 dataclass。不要为了"面向对象"而写类。

## 动手

| 文件 | 演示什么 |
|---|---|
| [`code/01_class_and_instance.py`](./code/01_class_and_instance.py) | 两个 Counter 实例各自计数，`self` 指向谁 |
| [`code/02_dataclass.py`](./code/02_dataclass.py) | 手写版和 dataclass 版并排，行为相同 |
| [`code/03_dataclass_frozen_and_factory.py`](./code/03_dataclass_frozen_and_factory.py) | 冻住的实例改不了；`default_factory` 修掉共享列表的坑；直接写 `= []` 报什么错 |
| [`code/04_protocol_duck_typing.py`](./code/04_protocol_duck_typing.py) | 两个无关的类因为都有 `speak()` 被同一个函数接受；没有的那个报 AttributeError |
| [`code/05_class_or_function.py`](./code/05_class_or_function.py) | 同一件事函数版和类版，什么时候该用哪个 |

## 常见错误

**`TypeError: Counter.add() takes 1 positional argument but 2 were given`**

```python
class Counter:
    def add(amount):      # 忘了 self
        pass
Counter().add(1)
```

方法定义漏了 `self`。Python 调方法时自动把实例作为第一个参数传进去，你的 `amount` 就变成了第二个。所有方法第一个参数写 `self`。

**`ValueError: mutable default <class 'list'> for field events is not allowed: use default_factory`**

```python
@dataclass
class Broken:
    events: list[str] = []
```

报错信息已经告诉你修法了：`field(default_factory=list)`。

**`TypeError: non-default argument 'y' follows default argument`**

```python
@dataclass
class A:
    x: int = 1
    y: int
```

有默认值的字段必须放在没有默认值的后面，和函数参数一个规矩。把 `y` 挪到 `x` 前面。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

主线的共享代码 `project/src/aiapp/adapters/base.py` 里，`Message`、`ToolCall`、`ToolSpec` 全是 `@dataclass(frozen=True)`：它们是"发生过的事"的记录，不该被改。`ModelAdapter` 是一个 `Protocol`，只要求有一个 `complete()` 方法，于是假模型和真模型可以随意替换，调用方一行不改。第 05 课的工具注册表、第 07 课的事件线程，都是"几个方法共享一份状态"的类。

学完这一课再去读那个 150 行的文件，你会发现没有一个陌生的语法。

## 延伸阅读

- [Python 官方教程 · 类](https://docs.python.org/3/tutorial/classes.html)（访问日期 2026-09-04）：作用域、类与实例、继承的官方讲解。
- [dataclasses 模块文档](https://docs.python.org/3/library/dataclasses.html)（访问日期 2026-09-04）：`field()` 的全部参数，`frozen`、`order`、`slots` 等选项。
- [PEP 544 · Protocols: Structural subtyping](https://peps.python.org/pep-0544/)（访问日期 2026-09-04）：Protocol 的设计文档，"为什么需要它"那一节值得读。
- [廖雪峰 · 面向对象编程](https://liaoxuefeng.com/books/python/oop/index.html)（访问日期 2026-09-04）：中文，从类和实例到继承。

---

[← P03](../03-modules-errors-and-logging/README.md) · [P05 →](../05-typing/README.md)
