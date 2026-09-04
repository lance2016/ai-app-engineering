---
status: complete
part: 前置 · Python
estimated_time: 约 1.5 小时
---

# P06 Pydantic v2

> 用一个 Python 类同时做三件事：说清数据长什么样、检查外面传进来的数据对不对、把数据变成 JSON 或从 JSON 变回来。写 API 和调模型时，每一份进出的数据都要经过它。

## 学习目标

- 能用 `BaseModel` 定义一份数据的形状，并读懂校验失败时的报错
- 能用默认值、`| None` 和 `Field` 约束表达"可以不填""不能为负"这类规则
- 能在模型、字典、JSON 三者之间来回转换，并解释 `model_json_schema()` 输出的是什么

## 前置

- [P04 类、dataclass 与 Protocol](../04-oop-and-dataclasses/README.md)：知道类和实例是什么
- [P05 类型注解](../05-typing/README.md)：看得懂 `name: str`、`list[int]`、`str | None`

## 核心概念

### 一个类就是一份"数据说明书"

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str

u = User(name="Ada", age=36, email="ada@example.com")
print(u.age + 1)   # 37，age 真的是 int
```

和普通类的区别：普通类你传什么它存什么；`BaseModel` 会**按注解检查**。传 `age="thirty"`，它不会存进去，而是抛一个 `ValidationError`，里面写清楚哪个字段、什么问题、你传了什么。

### 读懂报错

```python
from pydantic import ValidationError

try:
    User(name="Bob", age="thirty", email=None)
except ValidationError as exc:
    for err in exc.errors():
        print(err["loc"], err["msg"], err["input"])
# ('age',) Input should be a valid integer, unable to parse string as an integer thirty
# ('email',) Input should be a valid string None
```

`errors()` 返回一个列表，每一项有 `loc`（哪个字段）、`msg`（什么问题）、`input`（你给的值）。所有错误一次报完，不是遇到第一个就停。

### 可选、默认值、约束

```python
from pydantic import Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    price: float = Field(gt=0)
    tags: list[str] = []          # 有默认值就可以不传
    note: str | None = None       # 可以不传，也可以传 None
```

`Field()` 用来写"值必须满足什么"：`gt=0` 是大于 0，`min_length=1` 是至少一个字符。注意 `tags: list[str] = []` 在普通类里是经典 bug（所有实例共用一个列表），Pydantic 会给每个实例拷一份，是安全的。

### 模型、字典、JSON 互转

```python
raw = {"order_id": "o_1", "items": [{"sku": "A1", "qty": "2"}]}
order = Order.model_validate(raw)      # dict -> 模型，"2" 会被转成 2
order.model_dump()                     # 模型 -> dict
text = order.model_dump_json()         # 模型 -> JSON 字符串
Order.model_validate_json(text)        # JSON 字符串 -> 模型
```

模型可以嵌套：`items: list[Item]` 里的每个字典都会被校验成 `Item`。API 收到的请求体、模型返回的 JSON，都是先 `model_validate` 再用，不直接用裸字典。

### `model_json_schema()`：把说明书交给别人

```python
class GetWeather(BaseModel):
    """Current weather for a city."""
    city: str = Field(description="City name")
    unit: Literal["celsius", "fahrenheit"] = "celsius"

GetWeather.model_json_schema()
# {'properties': {'city': {...}, 'unit': {'enum': [...], 'default': 'celsius'}}, 'required': ['city'], ...}
```

这个字典是 **JSON Schema**，一种和语言无关的"数据长什么样"的描述。它就是主线第 05 课里告诉大模型"这个工具接受什么参数"的那份东西。你用同一个类校验模型传回来的参数，schema 和校验永远不会对不上。

### 自定义规则

```python
from pydantic import field_validator, model_validator

class Booking(BaseModel):
    email: str
    start: int
    end: int

    @field_validator("email")
    @classmethod
    def normalise(cls, v: str) -> str:
        return v.strip().lower()

    @model_validator(mode="after")
    def end_after_start(self) -> "Booking":
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self
```

`field_validator` 管一个字段，可以顺手改值（比如统一小写）。`model_validator(mode="after")` 在所有字段都通过之后跑，用来做跨字段检查。抛 `ValueError` 就会变成一条正常的校验错误。

## 动手

| 文件 | 一个知识点 |
|---|---|
| [`code/01_define_and_validate.py`](./code/01_define_and_validate.py) | 定义模型，好数据通过，坏数据报错并逐条读 |
| [`code/02_defaults_and_constraints.py`](./code/02_defaults_and_constraints.py) | 默认值、`| None`、`Field` 约束 |
| [`code/03_nested_and_dump.py`](./code/03_nested_and_dump.py) | 嵌套模型，dict / JSON 来回转 |
| [`code/04_json_schema.py`](./code/04_json_schema.py) | `model_json_schema()` 输出什么、给谁看 |
| [`code/05_validators.py`](./code/05_validators.py) | 单字段校验器和跨字段校验器 |

每个文件顶部写了运行命令和预期输出。按顺序跑，改一改里面的值再跑。

## 常见错误

**忘了 Pydantic 会抛异常，直接当普通类用。**

```text
pydantic_core._pydantic_core.ValidationError: 1 validation error for U
age
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='x', input_type=str]
```

在系统边界（接收请求、解析模型输出）构造模型时要 `try/except ValidationError`，把错误变成一个像样的响应，而不是让程序崩掉。内部代码之间传递已经校验过的模型，不需要再 try。

**少传了字段。**

```text
1 validation error for U
age
  Field required [type=missing, input_value={'name': 'a'}, input_type=dict]
```

`Field required` 就是"必填字段没给"。要么传，要么在类里给默认值或写成 `int | None = None`。

**把 dataclass 的经验搬过来，以为 `list = []` 会共享。** Pydantic 会为每个实例复制默认值，`02` 里打印的 `tags is its own list: False` 证明了这一点。反过来，如果你在普通 `dataclass` 里这么写，会直接报 `ValueError: mutable default ... is not allowed`。两个库行为不同，别记混。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

主线落点：[02 模型调用、结构化输出与流式](../../../lessons/02-model-api-structured-output-streaming/README.md)、[05 Tool Calling](../../../lessons/05-tool-calling/README.md)。

具体场景：你让模型从一段客服对话里抽取"用户想退的订单号和原因"。你定义 `class Refund(BaseModel): order_id: str; reason: str`，把 `Refund.model_json_schema()` 交给模型，要求它按这个格式输出；模型返回 JSON 后，你用 `Refund.model_validate_json()` 解析。模型少了字段、类型不对，你在这一行就知道，而不是在三层调用之后拿到一个 `None` 才发现。第 05 课的工具参数校验就是这个流程原样搬过去。

## 延伸阅读

- [Pydantic · Models](https://docs.pydantic.dev/latest/concepts/models/)（访问日期 2026-09-04）：官方概念页，看"Basic model usage"和"Error handling"两节就够。
- [Pydantic · Validators](https://docs.pydantic.dev/latest/concepts/validators/)（访问日期 2026-09-04）：`field_validator` 的 `mode="before"` 和 `"after"` 区别在这里。
- [Pydantic · JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)（访问日期 2026-09-04）：想知道 `Field(description=...)` 和 docstring 怎么进 schema，看这一页。

---

[← P05](../05-typing/README.md) · [P07 →](../07-asyncio/README.md)
