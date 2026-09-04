---
status: complete
part: 前置 · Python
estimated_time: 约 3 小时
---

# P02 容器与迭代

> list、dict、set、tuple 四种容器，切片、推导式、生成器三种处理方式，最后用 json 模块把一段 JSON 变成字典再拆开。处理程序之间传来传去的数据，靠的全是这些。

## 学习目标

- 能为一个具体需求选对容器：有序可改用 list，按键查找用 dict，去重用 set，固定不变用 tuple
- 能用切片和推导式把一个列表变成另一个列表，不写显式循环
- 能把一段 JSON 文本解析成 Python 对象，取出嵌套在里面的值

## 前置

- [P01 Python 基础语法](../01-python-basics/README.md)：变量、for 循环、函数

## 核心概念

### 四种容器

```python
tasks = ["buy milk", "call mom"]        # list：有顺序，可以改
user = {"name": "Lance", "city": "SZ"}  # dict：键找值
tags = {"python", "ai", "python"}       # set：自动去重，无顺序
point = (3, 4)                          # tuple：有顺序，不能改
```

| 容器 | 什么时候用 | 典型操作 |
|---|---|---|
| list | 一串东西，顺序有意义，会增删 | `tasks.append(x)`、`tasks[0]`、`len(tasks)` |
| dict | 按名字查东西 | `user["city"]`、`user.get("email", "n/a")`、`user["age"] = 30` |
| set | 只关心"有没有"，不关心顺序和次数 | `tags.add(x)`、`"ai" in tags` |
| tuple | 几个值绑在一起，不该被改 | `x, y = point`（解包） |

`dict` 用 `user["email"]` 取不存在的键会报 `KeyError`，用 `user.get("email")` 会得到 `None`。不确定键在不在时用 `.get()`。

### 切片

```python
messages = ["m0", "m1", "m2", "m3", "m4", "m5"]
messages[:3]     # ['m0', 'm1', 'm2']  前三个
messages[-2:]    # ['m4', 'm5']        后两个
messages[2:4]    # ['m2', 'm3']        第 2 到第 4 个之前
messages[::-1]   # 倒序
```

`[起点:终点]`，包含起点，不包含终点。负数从末尾数。省略起点就是从头，省略终点就是到尾。字符串也能切。"只保留最近 5 条"就是 `history[-5:]`。

### 推导式

```python
words = ["apple", "kiwi", "banana", "fig"]
lengths = [len(w) for w in words]                    # [5, 4, 6, 3]
long_words = [w.upper() for w in words if len(w) > 4] # ['APPLE', 'BANANA']
word_to_len = {w: len(w) for w in words}             # dict 推导式
```

推导式是"用一个循环造一个新容器"的紧凑写法。读法：`[要放进去的东西 for 每个元素 in 原容器 if 条件]`。能一行说清的转换用推导式，逻辑复杂的还是写普通循环。

### 生成器

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1

total = sum(i for i in range(10_000_000))   # 不会建一个一千万元素的列表
```

`yield` 让函数每次只交出一个值，下次被要求时再继续。列表是一次做好全部放在内存里，生成器是要一个给一个。处理大数据或者流式数据时，生成器省内存。`(表达式 for ...)` 圆括号写法就是生成器版的推导式。

三个常用配套：`enumerate(names, start=1)` 循环时带序号，`zip(a, b)` 把两个列表按位置配对，`sorted(names, key=str.lower)` 按自定义规则排序。

### JSON 与字典

```python
import json
raw = '{"city": "Shenzhen", "forecast": [{"day": "Mon", "high": 33}]}'
data = json.loads(raw)               # 文本 -> dict
data["forecast"][0]["high"]          # 33
json.dumps(data, indent=2)           # dict -> 文本，缩进两格
```

JSON 是程序之间交换数据的通用格式，长得几乎和 Python 的 dict/list 一样。`json.loads` 把文本变成 Python 对象，`json.dumps` 反过来。嵌套的结构一层一层用 `[]` 剥开。

## 动手

| 文件 | 演示什么 |
|---|---|
| [`code/01_list_dict_set_tuple.py`](./code/01_list_dict_set_tuple.py) | 四种容器各做一个典型操作，tuple 改不了会报什么错 |
| [`code/02_slicing.py`](./code/02_slicing.py) | 六种切片写法，以及"保留最近 N 条"这个常用模式 |
| [`code/03_comprehensions.py`](./code/03_comprehensions.py) | 同一件事用循环和推导式各写一遍，再看 dict 和 set 推导式 |
| [`code/04_generators_lazy.py`](./code/04_generators_lazy.py) | yield 逐个产出，一千万求和不占内存，enumerate/zip/sorted |
| [`code/05_parse_json.py`](./code/05_parse_json.py) | 解析一段像天气接口返回的 JSON，取嵌套值，再写回去 |

## 常见错误

**`KeyError: 'b'`**

```python
d = {"a": 1}
d["b"]
```

键不存在。不确定时用 `d.get("b")`，或者先 `if "b" in d:`。

**`IndexError: list index out of range`**

```python
items = [1, 2, 3]
print(items[3])
```

三个元素的下标是 0、1、2，没有 3。最后一个是 `items[-1]`。

**`AttributeError: 'tuple' object has no attribute 'append'`**

tuple 不能改，也没有 `append`。要改就用 list。反过来，把 tuple 当 dict 的键可以，list 不行。

**`json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes`**

```python
json.loads("{'a': 1}")
```

JSON 只认双引号。这段文本是 Python 字典的写法，不是 JSON。模型返回的"看着像 JSON"的文本经常有这个问题，主线第 02 课会讲怎么约束模型输出合法 JSON。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

AI 模型的接口收发的都是 JSON。主线第 02 课里，模型返回的每一条回复解析出来是一个 dict，里面嵌着 list，list 里又是 dict。取"第一个工具调用的参数"就是 `reply["tool_calls"][0]["arguments"]`，和 `code/05_parse_json.py` 里取天气预报一模一样。

对话历史是一个消息 list。上下文放不下时要裁剪，"只保留最近 10 条"就是 `history[-10:]`，主线第 08 课会用到。生成器则是流式输出的基础：模型一个词一个词地返回，程序用 `for chunk in stream:` 一个一个处理，不等全部生成完。

## 延伸阅读

- [Python 官方教程 · 数据结构](https://docs.python.org/3/tutorial/datastructures.html)（访问日期 2026-09-04）：list 方法全表、推导式、dict、set 的官方说明。
- [json 模块文档](https://docs.python.org/3/library/json.html)（访问日期 2026-09-04）：`loads`/`dumps` 的参数，特别是 `ensure_ascii=False` 让中文不变成 `\uXXXX`。
- [廖雪峰 · 高级特性](https://liaoxuefeng.com/books/python/advanced/index.html)（访问日期 2026-09-04）：切片、迭代、列表生成式、生成器，中文讲解。

---

[← P01](../01-python-basics/README.md) · [P03 →](../03-modules-errors-and-logging/README.md)
