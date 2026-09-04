# P02 容器与迭代｜练习

> 第一题照着做就能完成。答案折叠在每题下方。

## 练习 1：换一个切片

打开 `code/02_slicing.py`，在最后加一行，打印 `messages` 的中间两个元素（`m2` 和 `m3`）用负数下标怎么写。

验收：输出 `['m2', 'm3']`。

<details><summary>答案</summary>

`print(messages[-4:-2])`。负数从末尾数，`-4` 是 `m2`，`-2` 是 `m4`，不包含终点。

</details>

## 练习 2：去重并保持顺序

`names = ["amy", "bob", "amy", "cat", "bob"]`。用 set 去重会丢掉顺序。写几行代码，去重后保持第一次出现的顺序，得到 `["amy", "bob", "cat"]`。

验收：输出顺序正确。

<details><summary>答案</summary>

```python
seen = set()
result = []
for name in names:
    if name not in seen:
        seen.add(name)
        result.append(name)
```

set 负责"见过没有"，list 负责顺序。两个容器各干一件事，这是常见的组合。Python 3.7 以后 `list(dict.fromkeys(names))` 一行也能做到，因为 dict 保持插入顺序。

</details>

## 练习 3：从 JSON 里统计

下面是一段模拟的接口返回。解析它，算出所有 `"status"` 为 `"ok"` 的条目的 `"tokens"` 总和，并列出失败条目的 `"id"`。

```python
raw = '''{"runs": [
  {"id": "r1", "status": "ok", "tokens": 120},
  {"id": "r2", "status": "error", "tokens": 0},
  {"id": "r3", "status": "ok", "tokens": 80}
]}'''
```

验收：输出 `ok tokens: 200` 和 `failed: ['r2']`。

<details><summary>答案</summary>

```python
import json
data = json.loads(raw)
runs = data["runs"]
ok_tokens = sum(r["tokens"] for r in runs if r["status"] == "ok")
failed = [r["id"] for r in runs if r["status"] != "ok"]
print(f"ok tokens: {ok_tokens}")
print(f"failed: {failed}")
```

一个生成器表达式配 `sum`，一个列表推导式。这两行在主线第 17 课评测里会以几乎相同的形态出现。

</details>

## 练习 4：生成器还是列表

不写代码。读一个 2 GB 的日志文件，逐行找出包含 `"ERROR"` 的行。你会用 `f.readlines()` 得到一个列表再筛，还是 `for line in f:` 逐行处理？为什么？

<details><summary>答案</summary>

逐行。`readlines()` 会把 2 GB 全读进内存变成一个 list；文件对象本身就是一个迭代器，`for line in f` 一次只拿一行。同样的原因，模型流式返回时也是逐块处理，不是等全部返回再拼。

</details>
