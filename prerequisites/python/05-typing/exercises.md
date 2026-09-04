# P05 类型注解｜练习

> 第一题照着做就能完成。答案折叠在每题下方。

## 练习 1：让 pyright 报一个错，再修好

运行 `uvx pyright prerequisites/python/05-typing/code/05_types_dont_run.py`，看到 1 error。把 `double("ab")` 改成 `double(2)`，再跑一次。

验收：第二次输出 `0 errors, 0 warnings, 0 informations`。

<details><summary>提示</summary>

第一次运行 `uvx` 会下载 pyright，慢一点是正常的。如果想看 Python 本身对错误版本的态度，先 `uv run python` 跑一下：它打印 `abab`，一个字不抱怨。

</details>

## 练习 2：给一段没有注解的代码加注解

```python
def summarize(runs):
    ok = [r for r in runs if r["status"] == "ok"]
    return {"ok": len(ok), "total_tokens": sum(r["tokens"] for r in ok)}
```

`runs` 是字典的列表，每个字典有 `id`（字符串）、`status`（只能是 `"ok"` 或 `"error"`）、`tokens`（整数）。用 `TypedDict` 和 `Literal` 描述它，给函数加完整注解，跑 pyright 通过。

验收：pyright 0 errors；然后故意把某个 `status` 改成 `"failed"` 传进去，pyright 报错。

<details><summary>答案</summary>

```python
from typing import Literal, TypedDict


class Run(TypedDict):
    id: str
    status: Literal["ok", "error"]
    tokens: int


class Summary(TypedDict):
    ok: int
    total_tokens: int


def summarize(runs: list[Run]) -> Summary:
    ok = [r for r in runs if r["status"] == "ok"]
    return {"ok": len(ok), "total_tokens": sum(r["tokens"] for r in ok)}
```

</details>

## 练习 3：处理可能为空的值

写 `first_error(runs: list[Run]) -> str | None`，返回第一个 `status == "error"` 的 `id`，没有就返回 None。然后写调用代码打印它，要让 pyright 不报 `reportOptionalMemberAccess` 之类的错。

验收：pyright 0 errors；有错误项时打印 id，没有时打印 `no errors`。

<details><summary>答案</summary>

```python
def first_error(runs: list[Run]) -> str | None:
    for r in runs:
        if r["status"] == "error":
            return r["id"]
    return None


result = first_error(runs)
if result is None:
    print("no errors")
else:
    print(result.upper())
```

检查器知道 `else` 分支里 `result` 是 `str`，所以 `.upper()` 不报错。如果把 `if` 删掉直接 `result.upper()`，它会指出 `"upper" is not a known attribute of "None"`。

</details>

## 练习 4：为什么 Python 不在运行时检查类型

一句话回答，然后说出这个设计带来的一个好处和一个代价。

<details><summary>参考答案</summary>

因为类型注解被设计成可选的、渐进的：老代码不写注解照样跑，新代码可以慢慢加。好处是零成本引入，任何项目任何阶段都能开始用；代价是注解可能撒谎，保证正确性靠的是检查器和测试，不是解释器。所以数据从外部进来（用户输入、模型输出、文件）时，必须有一层真正的运行时校验，这就是 P06 的 Pydantic。

</details>
