---
status: complete
part: 前置 · Python
estimated_time: 约 2 小时
---

# P05 类型注解

> 类型注解是写给人和工具看的说明：这个参数是什么、返回什么。Python 运行时不检查它，但编辑器和 pyright 会。在 AI 应用里，几乎所有数据都要跨越"模型返回的一堆 JSON"和"程序里的确定结构"这条边界，类型就是那条边界的图纸。

## 学习目标

- 能给函数的参数和返回值写类型注解，包括 `| None`、`list[str]`、`dict[str, int]` 这类组合
- 能用 `TypedDict` 描述一个字典的形状，用 `Literal` 把一个值限制在几个选项里
- 能用 `uvx pyright` 检查一个文件，读懂它报的错，并解释为什么 Python 自己不报

## 前置

- [P04 类、dataclass 与 Protocol](../04-oop-and-dataclasses/README.md)：dataclass 的字段就是靠类型注解定义的

## 核心概念

### 注解长什么样

```python
def area(w, h):                                  # 没有注解，能跑
    return w * h

def area_typed(width: float, height: float) -> float:   # 有注解，也能跑，一样的结果
    return width * height

total: int = 0                                   # 变量也能注解
```

参数名后面加 `: 类型`，括号后面加 `-> 返回类型`。它们是"注解"，Python 只是把它们存在 `area_typed.__annotations__` 里，不拿它做任何检查。

那为什么写？三个理由：编辑器能提示你 `width.` 后面有什么方法；别人（包括三个月后的你）一眼知道该传什么；类型检查器能在运行前找出一类 bug。

### 可能为空：`| None`

```python
def find_user(users: dict[str, int], name: str) -> int | None:
    return users.get(name)

age = find_user(users, "bob")
if age is None:
    print("not found")
else:
    print(age + 1)     # 只有在这个分支里，age 才确定是 int
```

`int | None` 表示"要么是整数，要么是 None"。旧写法是 `Optional[int]`，意思一样。检查器会强迫你在用它之前先排除 None，这正是它最有价值的地方：`None + 1` 这种运行时才炸的错误，在写代码时就被指出来。

### 容器里装什么

```python
scores: list[float] = [0.9, 0.7]
by_name: dict[str, list[str]] = {"lance": ["python", "ai"]}
pair: tuple[str, int] = ("amy", 10)

from collections.abc import Callable
def apply_twice(func: Callable[[int], int], value: int) -> int:
    return func(func(value))
```

`list[float]` 是"元素都是 float 的列表"。`dict[键类型, 值类型]`。`Callable[[参数类型...], 返回类型]` 描述一个函数。Python 3.9 以后直接用小写的 `list`、`dict`，不需要从 typing 导入 `List`、`Dict`。

### TypedDict 和 Literal

```python
from typing import Literal, TypedDict

class WeatherReply(TypedDict):
    city: str
    temp_c: float
    condition: Literal["sunny", "cloudy", "rain"]

reply: WeatherReply = {"city": "Shenzhen", "temp_c": 31.0, "condition": "sunny"}
```

`TypedDict` 给一个字典规定"有哪些键、每个键什么类型"。它运行时还是普通 dict，只是检查器知道形状了。`Literal["sunny", "cloudy", "rain"]` 表示这个值只能是三个字符串之一。

```python
Unit = Literal["celsius", "fahrenheit"]

def convert(temp: float, unit: Unit) -> float: ...

convert(31, "kelvin")   # 能跑！只有 pyright 会说这一行不对
```

### 注解不影响运行，检查器是另一个工具

```python
def double(n: int) -> int:
    return n * 2

print(double("ab"))   # 打印 abab，Python 不报错
```

这一点必须亲眼看到一次。注解说 `int`，你传了字符串，Python 照样运行，字符串乘 2 得到 `"abab"`。要让类型发挥作用，需要跑一个检查器：

```bash
uvx pyright prerequisites/python/05-typing/code/05_types_dont_run.py
```

输出：

```text
05_types_dont_run.py:15:14 - error: Argument of type "Literal['ab']" cannot be assigned to parameter "n" of type "int" in function "double"
    "Literal['ab']" is not assignable to "int" (reportArgumentType)
1 error, 0 warnings, 0 informations
```

`uvx` 会临时下载 pyright 运行，不装进项目。mypy 是另一个同类工具，`uvx mypy 文件.py`，两者选一个用就行。VS Code 的 Python 扩展内置了 pyright 的引擎，把设置里 `Type Checking Mode` 从 off 改成 basic，写代码时就会划红线，不用手动跑命令。

### Protocol 从类型的角度看

P04 讲的 Protocol，对检查器来说是"结构类型"：一个类只要有 Protocol 要求的方法和签名，就算满足，不需要继承。

```python
class Greeter(Protocol):
    def greet(self, name: str) -> str: ...

def welcome(greeter: Greeter, name: str) -> None: ...

welcome(Formal(), "Lance")    # Formal 有 greet(self, name: str) -> str，通过
welcome(Silent(), "Lance")    # Silent 只有 wave()，pyright 报错，Python 运行到调用时才报
```

## 动手

| 文件 | 演示什么 |
|---|---|
| [`code/01_annotations_basics.py`](./code/01_annotations_basics.py) | 有无注解行为相同；注解存在 `__annotations__` 里 |
| [`code/02_optional_and_generics.py`](./code/02_optional_and_generics.py) | `int | None` 的正确用法；`list[float]`、`dict[str, list[str]]`、`Callable` |
| [`code/03_typeddict_and_literal.py`](./code/03_typeddict_and_literal.py) | 用 TypedDict 描述一个接口返回；Literal 限定选项；最后一行故意传非法值，照样能跑 |
| [`code/04_protocol_types.py`](./code/04_protocol_types.py) | 两个类满足 Protocol，第三个不满足。取消注释那一行再跑 pyright |
| [`code/05_types_dont_run.py`](./code/05_types_dont_run.py) | 先 `uv run` 看它正常运行，再 `uvx pyright` 看它报错 |

## 常见错误

**pyright：`Argument of type "Literal['ab']" cannot be assigned to parameter "x" of type "int"`**

传的类型和注解不符。要么改调用方，要么注解本来就写错了。这条不是 Python 的报错，是检查器的，所以文件照样能跑。

**pyright：`Operator "+" not supported for "None" (reportOptionalOperand)`**

```python
def f(x: int) -> int | None: ...
y = f(1) + 1
```

返回值可能是 None，你直接拿它做加法。先 `if y is not None:`。如果不检查直接跑，运行时是 `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`，出现在用户那里而不是你的屏幕上。

**以为注解会做校验**

写了 `def f(age: int)`，然后传了 `"30"`，期待报错。不会。注解不是校验。需要运行时真正检查和转换数据，用 P06 的 Pydantic，那是它存在的理由。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

主线第 02 课要让模型返回"结构化输出"，也就是一个形状固定的 JSON。你先用类型（或 P06 的 Pydantic 模型）定义这个形状，工具把它转成 JSON Schema 发给模型，模型返回后再按同一个定义校验。类型注解就是那个形状的第一手描述。

第 05 课的工具定义里，`Literal["celsius", "fahrenheit"]` 这样的注解会直接变成 schema 里的枚举，模型传了 `"kelvin"` 会被拦下来。你在本课 `03_typeddict_and_literal.py` 最后一行看到的"能跑但不该跑"，到那里就变成"跑不了"。

## 延伸阅读

- [typing 模块文档](https://docs.python.org/3/library/typing.html)（访问日期 2026-09-04）：所有注解形式的官方参考，查用。
- [mypy 速查表](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)（访问日期 2026-09-04）：一页纸看完常用注解写法，对 pyright 同样适用。
- [pyright 文档](https://microsoft.github.io/pyright/)（访问日期 2026-09-04）：安装、配置、错误类别说明。
- [PEP 544 · Protocols](https://peps.python.org/pep-0544/)（访问日期 2026-09-04）：结构类型的设计文档。

---

[← P04](../04-oop-and-dataclasses/README.md) · [P06 →](../06-pydantic/README.md)
