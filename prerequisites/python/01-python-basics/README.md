---
status: complete
part: 前置 · Python
estimated_time: 约 3 小时
---

# P01 Python 基础语法

> 变量、字符串、条件、循环、函数。学完能读懂和写出 50 行以内的脚本。每个概念先看一段能跑的代码，再看解释。

## 学习目标

- 能写一个带条件判断和循环的脚本，处理一个列表里的数据
- 能定义带默认参数的函数，并解释为什么函数里的变量在外面看不到
- 能解释 `if __name__ == "__main__":` 是干什么的，并在自己的脚本里用上

## 前置

- [P00 环境与工具链](../00-setup-and-tooling/README.md)：会用 `uv run` 跑脚本，会用 REPL

## 核心概念

### 变量和类型

```python
name = "Aime"       # str，文本
age = 10            # int，整数
height_m = 1.32     # float，小数
is_robot = True     # bool，真或假
```

变量是给一个值起的名字。`=` 是"把右边的值存到左边的名字里"，不是数学里的等于。每个值都有类型，类型决定它能做什么：数字能加减，文本能拼接，两者不能混。

```python
user_input = "42"           # 从键盘或文件读到的永远是文本
print(user_input + "1")     # "421"，文本拼接
print(int(user_input) + 1)  # 43，先转成整数再算
```

这是初学者最常踩的坑之一：看着像数字的东西，其实是文本。

### 字符串和 f-string

```python
city = "Shenzhen"
temp = 31.456
print(f"It is {temp:.1f} degrees in {city}.")   # It is 31.5 degrees in Shenzhen.
```

引号前加 `f`，花括号里就可以放变量和表达式。`:.1f` 是格式说明，保留一位小数。这是把数据变成人能读的文字的标准方式，比用 `+` 拼接清楚得多。

字符串自带很多方法：`.strip()` 去首尾空格，`.lower()` 转小写，`.split(" ")` 按空格切成列表，`.startswith("Sure")` 判断开头。三个引号 `"""..."""` 可以写多行文本。

### 条件

```python
if temp >= 35:
    label = "hot"
elif temp >= 25:
    label = "warm"
else:
    label = "cool"
```

从上往下试，第一个成立的分支执行，其余跳过。`elif` 可以有多个，`else` 最多一个，都可以没有。注意冒号和缩进：冒号后面的下一行必须缩进，缩进的部分就是这个分支的内容。

### 循环

```python
for number in range(3, 0, -1):   # 3, 2, 1
    print("countdown:", number)

attempts = 0
while attempts < 3:
    attempts += 1
```

`for` 用于"对这一堆东西里的每一个做点事"，`while` 用于"条件成立就一直做"。绝大多数时候用 `for`。`range(3, 0, -1)` 表示从 3 开始、到 0 之前停、每次减 1。

### 函数

```python
def greet(name: str, excited: bool = False) -> str:
    ending = "!" if excited else "."
    return f"Hello, {name}{ending}"

greet("Lance")                  # "Hello, Lance."
greet("Lance", excited=True)    # "Hello, Lance!"
```

函数把一段逻辑打包起来，起个名字，以后反复用。`def` 定义，括号里是参数，`excited: bool = False` 表示这个参数有默认值，调用时可以不给。`return` 把结果交回去。冒号后面的 `str`、`bool` 是类型提示，P05 详细讲，现在只需要知道它不影响运行。

函数里创建的变量只在函数里存在：

```python
def make_message():
    inner = "I only exist inside"
    return inner

print(inner)   # NameError: name 'inner' is not defined
```

这叫作用域。它不是限制，是保护：函数内部随便起名字，不会和外面的变量打架。

### `if __name__ == "__main__":`

```python
def celsius_to_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32

if __name__ == "__main__":
    print(celsius_to_fahrenheit(31))
```

每个 Python 文件既可以直接运行，也可以被别的文件 `import`。直接运行时 `__name__` 是 `"__main__"`；被 import 时是文件名。这行判断的意思是"只有直接运行我的时候才执行下面的代码"。这样别人 import 你的函数时，不会连带跑一遍你的测试打印。课程里所有脚本都这么写。

## 动手

| 文件 | 演示什么 |
|---|---|
| [`code/01_variables_and_types.py`](./code/01_variables_and_types.py) | 四种基本类型，以及"看着像数字的文本"这个坑 |
| [`code/02_strings_and_fstrings.py`](./code/02_strings_and_fstrings.py) | f-string 格式化、常用字符串方法、多行字符串 |
| [`code/03_conditions_and_loops.py`](./code/03_conditions_and_loops.py) | if/elif/else、for、while、循环里筛选 |
| [`code/04_functions_and_scope.py`](./code/04_functions_and_scope.py) | 定义和调用、默认参数、返回值、作用域 |
| [`code/05_main_guard.py`](./code/05_main_guard.py) | `__name__` 在直接运行时是什么 |

建议每个文件跑一遍，然后改一个值再跑，看输出怎么变。

## 常见错误

**`TypeError: can only concatenate str (not "int") to str`**

```python
age = 30
print("age: " + age)
```

文本和数字不能用 `+` 拼。改成 `print(f"age: {age}")` 或 `print("age:", age)`。

**`NameError: name 'nmae' is not defined`**

```python
name = "Lance"
print(nmae)
```

九成是拼错了变量名。Python 区分大小写，`Name` 和 `name` 是两个变量。看报错里 `^^^^` 指的那个词。

**`IndentationError: expected an indented block after 'if' statement on line 1`**

```python
if True:
print("x")
```

冒号后面的下一行忘了缩进。另一种变体是 `IndentationError: unindent does not match any outer indentation level`，通常是空格和 Tab 混用了。VS Code 里统一用四个空格。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

AI 模型接收的是文本，返回的也是文本。主线第 02 课里，你会把用户的问题用 f-string 拼进一段"系统指令"，发给模型，再把模型返回的文本切开、判断、存起来。那一课的代码里全是这一模块的东西：字符串方法处理模型回复，if 判断回复里有没有工具调用，for 循环遍历返回的多个结果。

`if __name__ == "__main__":` 在主线每个代码文件的末尾都会出现，因为那些文件既要能直接跑，也要能被测试导入。

## 延伸阅读

- [Python 官方教程 · 非正式介绍](https://docs.python.org/3/tutorial/introduction.html)（访问日期 2026-09-04）：数字、字符串、列表的官方入门，可以在 REPL 里跟着敲。
- [Python 官方教程 · 控制流](https://docs.python.org/3/tutorial/controlflow.html)（访问日期 2026-09-04）：if、for、函数定义的完整说明，比本课深。
- [廖雪峰 · Python 基础](https://liaoxuefeng.com/books/python/basic/index.html)（访问日期 2026-09-04）：中文，讲得细，适合当第二遍。
- [廖雪峰 · 函数](https://liaoxuefeng.com/books/python/function/index.html)（访问日期 2026-09-04）：参数的几种写法。

---

[← P00](../00-setup-and-tooling/README.md) · [P02 →](../02-collections-and-iteration/README.md)
