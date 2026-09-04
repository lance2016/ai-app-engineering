---
status: complete
part: 前置 · 后端工程
estimated_time: 约 1.5 小时
---

# B02 pytest 与测试思维

> 测试就是"把你脑子里那句'这段代码应该这样'写成能自动运行的断言"。这一模块学 pytest 的五个基本工具，然后回答一个 AI 应用特有的问题：模型每次输出都不一样，怎么测？

## 学习目标

- 能写出 pytest 能发现并运行的测试，读懂失败时它打印的对比信息
- 能用 fixture 准备测试数据、用参数化一次覆盖多组输入、用 `raises` 和 mock 处理异常和外部依赖
- 能给一个输出不确定的函数写出稍改就不会误报的测试

## 前置

- [P03 模块、异常与日志](../../python/03-modules-errors-and-logging/README.md)：异常
- [P04 类、dataclass 与 Protocol](../../python/04-oop-and-dataclasses/README.md)

## 核心概念

### 一个测试就是一个 `assert`

```python
def word_count(text: str) -> int:
    return len(text.split())

def test_counts_words():
    assert word_count("hello world") == 2
```

pytest 的规则很少：文件名 `test_*.py` 或 `*_test.py`，函数名 `test_*`，里面写 `assert`。跑 `uv run pytest`，它会自己找到并运行。断言失败时它会把两边的值都打出来：

```text
>   def test_add(): assert add(2, 3) == 5
E   assert -1 == 5
E    +  where -1 = add(2, 3)
```

第二行直接告诉你实际得到的是 `-1`。这比 `print` 调试快得多，因为它每次都自动跑。

本模块的 code 文件把被测代码和测试放在同一个文件里，末尾用 `pytest.main([__file__])` 跑自己，这样 `uv run python 文件名` 就能看到结果。真实项目里测试放在 `tests/` 目录，被测代码放在别处。

### fixture：准备好东西再测

```python
@pytest.fixture
def cart() -> Cart:
    c = Cart()
    c.add("tea", 2)
    return c

def test_total(cart: Cart):        # 参数名和 fixture 同名，pytest 就会把它传进来
    assert cart.total_qty() == 2
```

十个测试都需要一个"已经放了两杯茶的购物车"，不能复制十遍。fixture 是一个函数，测试的参数名和它同名，pytest 就调它并把返回值传进来。每个测试拿到的是**新的一份**，互相不影响。

### 参数化：一个测试跑多组数据

```python
@pytest.mark.parametrize(("sku", "qty", "expected"), [("tea", 1, 3), ("coffee", 5, 7)])
def test_add(cart, sku, qty, expected):
    cart.add(sku, qty)
    assert cart.total_qty() == expected
```

同一个逻辑，五组输入，pytest 报告里是五个独立的测试。哪一组挂了一眼看到。边界值（0、负数、空字符串、超长）最适合这么放。

### `raises`：错误也是要测的行为

```python
def test_empty_sku_rejected():
    with pytest.raises(ValueError, match="sku required"):
        price_with_tax("")
```

"传空字符串应该报错"是需求的一部分。`pytest.raises` 里的代码**必须**抛出指定的异常，没抛就算测试失败。`match` 顺便检查错误信息。

### mock：把慢的、外部的、危险的东西换掉

```python
def test_tax_applied():
    with patch.object(sys.modules[__name__], "fetch_price", return_value=100.0) as fake:
        assert price_with_tax("tea") == 113.0
        fake.assert_called_once_with("tea")
```

`fetch_price` 真去调 API，测试就会慢、不稳定、花钱。`patch` 在 `with` 块里把它换成一个假函数，你规定它返回 100，测的是"税算对了没"。`side_effect=TimeoutError()` 还能模拟它出错，测你的代码遇到超时怎么办。测试结束自动换回真的。

原则：测你写的逻辑，不测别人的服务。

### 先写测试，再写代码

`04_test_first.py` 的测试写在实现前面。顺序是：写下你想要的行为（测试）→ 跑一次看它红 → 写最少的代码让它绿 → 整理。好处不是"测试覆盖率"，而是写代码前你已经想清楚了输入输出和边界，而且立刻有一个能验证的标准，不需要反复手动试。

### 模型输出每次不同，测什么

```python
def test_confidence_in_range():
    for _ in range(20):
        assert 0.5 <= summarise(TEXT)["confidence"] <= 1.0

def test_summary_is_shorter_than_source():
    out = summarise(TEXT)
    assert len(out["summary"]) < out["source_chars"]
```

不能 `assert summary == "某句话"`，明天就挂。能测的是**契约**：有哪些字段、类型对不对、数值在什么范围、长度关系、是否包含必须出现的内容。`05_testing_uncertain_output.py` 里的 `summarise` 每次输出都不一样，三个测试永远通过。真去测模型的**质量**（回答得好不好）是另一套方法，主线第 17 课讲。

## 动手

| 文件 | 一个知识点 |
|---|---|
| [`code/01_first_tests.py`](./code/01_first_tests.py) | 三个 `assert`，看 pytest 怎么发现和报告 |
| [`code/02_fixtures_and_parametrize.py`](./code/02_fixtures_and_parametrize.py) | fixture 准备数据，参数化跑五组 |
| [`code/03_raises_and_mock.py`](./code/03_raises_and_mock.py) | 测异常，mock 掉外部调用 |
| [`code/04_test_first.py`](./code/04_test_first.py) | 测试写在实现前面 |
| [`code/05_testing_uncertain_output.py`](./code/05_testing_uncertain_output.py) | 给不确定输出测契约不测原文 |

改一个断言让它失败，看看报错长什么样，再改回来。

## 常见错误

**看不懂失败输出。**

```text
E   assert -1 == 5
E    +  where -1 = add(2, 3)
```

`E` 开头的行是 pytest 的解释。第一行是断言两边的值，`where` 那行说 `-1` 是怎么算出来的。绝大多数时候看这两行就知道问题在哪。

**fixture 名字打错或没定义。**

```text
E       fixture 'cart' not found
>       available fixtures: anyio_backend, cache, capfd, caplog, capsys, monkeypatch, tmp_path, ...
```

测试的参数名 pytest 找不到对应的 fixture。检查拼写，或者 fixture 是否定义在这个文件或 `conftest.py` 里。顺便看看列表里的内置 fixture：`tmp_path` 给你一个临时目录，`monkeypatch` 是另一种 mock，`capsys` 能捕获 `print` 输出。

**mock 的路径不对。** `patch("requests.get")` 换掉的是 `requests` 模块里的 `get`，但你的代码如果写的是 `from requests import get`，它已经拿到了自己的引用，patch 不到。规则：patch **使用方**看到的那个名字，通常是 `patch("your_module.get")`。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

主线落点：[17 评测](../../../lessons/17-evaluation/README.md)、主项目全部里程碑。

具体场景：本仓库自己就是例子。`tests/test_lesson_code_runs.py` 用参数化把每一课的 code 文件都跑一遍，任何一个报错就红；第 05 课的四个守卫，每一个都能写成"给一个坏输入，断言拿到 `is_error=True` 的结果而不是异常"。而给 Agent 写测试时，模型那一层永远用 fake adapter（就是这一模块的 mock 思想）：剧本里写好模型"会"输出什么，测的是运行时对这个输出的处理对不对。模型本身好不好，那是评测，不是测试，第 17 课会讲两者怎么分工。

## 延伸阅读

- [pytest · Get Started](https://docs.pytest.org/en/stable/getting-started.html)（访问日期 2026-09-04）：十分钟读完，知道发现规则和基本命令。
- [pytest · How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)（访问日期 2026-09-04）：fixture 的作用域、清理、组合，用到时查。
- [unittest.mock 官方文档](https://docs.python.org/3/library/unittest.mock.html)（访问日期 2026-09-04）："Where to patch"那一节解释了上面第三个常见错误。

---

[← B01](../01-sql-and-sqlalchemy/README.md) · [B03 →](../03-git-cli-and-docker/README.md)
