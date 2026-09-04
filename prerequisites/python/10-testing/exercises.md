# P10 pytest 与测试思维｜练习

> 每题写清：任务、验收标准、提示。答案折叠。第一题照着做就能完成。

## 练习 1：加一个会失败的测试，再修好它

在 `01_first_tests.py` 里加 `test_punctuation_is_not_a_word`，断言 `word_count("hello , world") == 2`。跑一次看它失败，然后改 `word_count` 让它通过。

验收：先看到 `assert 3 == 2`，改完后 4 passed。

<details><summary>答案</summary>

`word_count` 现在把单独的逗号也算一个词。一种修法：`return len([w for w in text.split() if w.isalnum()])`。注意这会让 `"don't"` 也不算词，这是不是你想要的？测试逼你把"词"的定义想清楚，这就是它的价值。

</details>

## 练习 2：给 fixture 加清理

写一个 fixture `tmp_file`，在临时目录里创建一个文件并写入 `"hello"`，测试结束后删掉它。用 pytest 内置的 `tmp_path`。

验收：测试能读到 `"hello"`；fixture 里用 `yield` 而不是 `return`。

<details><summary>答案</summary>

```python
@pytest.fixture
def tmp_file(tmp_path):
    p = tmp_path / "data.txt"
    p.write_text("hello")
    yield p
    p.unlink()           # yield 之后的代码在测试结束后执行

def test_reads_file(tmp_file):
    assert tmp_file.read_text() == "hello"
```

其实 `tmp_path` 自己会清理整个目录，这里的 `unlink` 只是演示 `yield` 的用法。数据库连接、临时服务都是这样"yield 出去，用完关掉"。

</details>

## 练习 3：mock 一个会花钱的调用

把 `03_raises_and_mock.py` 里的 `price_with_tax` 想成"调一次模型 API"。再写一个测试：mock 让它前两次抛 `TimeoutError`、第三次返回 100，然后测一个带重试的 `price_with_retry(sku, attempts=3)` 最终返回 113。

验收：测试通过，且 `fake.call_count == 3`。

<details><summary>答案</summary>

`side_effect` 可以是一个列表，按顺序取：`side_effect=[TimeoutError(), TimeoutError(), 100.0]`。

```python
def price_with_retry(sku, attempts=3):
    for i in range(attempts):
        try:
            return price_with_tax(sku)
        except TimeoutError:
            if i == attempts - 1:
                raise
```

重试逻辑是你写的，值得测；API 本身不是你写的，mock 掉。第 19 课讲的重试、熔断都是用这种方式测的。

</details>

## 练习 4：这个测试为什么不好

```python
def test_summarise():
    random.seed(42)
    assert summarise(TEXT)["summary"] == "Briefly, The quick brown fox..."
```

它能稳定通过。说出两个它仍然不好的理由。

<details><summary>答案</summary>

一、它测的是随机数生成器在 seed 42 下的行为，不是 `summarise` 的契约。换一个 Python 版本或者 `openers` 列表加一个词，测试就挂，但功能没坏。

二、它对"什么是好的摘要"没有任何表达。换成真实模型后 seed 不起作用，这个测试直接失效。

好的测试写的是不变的东西：字段、范围、长度关系、必含内容。`05` 里的三个测试就是这样。

</details>
