# P04 类、dataclass 与 Protocol｜练习

> 第一题照着做就能完成。答案折叠在每题下方。

## 练习 1：给 Counter 加一个方法

在 `code/01_class_and_instance.py` 的 `Counter` 里加一个 `reset()` 方法，把 `total` 清零。在文件末尾对 `tokens_in` 调用它，再打印 `describe()`。

验收：最后一行输出 `input tokens: 0`。

<details><summary>答案</summary>

```python
    def reset(self) -> None:
        self.total = 0
```

记得第一个参数是 `self`，调用时写 `tokens_in.reset()` 不传参数。

</details>

## 练习 2：用 dataclass 建模一次对话

定义 `Message`（role、content）和 `Conversation`（messages 列表，默认为空）两个 dataclass。给 `Conversation` 加一个 `add(role, content)` 方法和一个 `last()` 方法返回最后一条消息。造两个 Conversation，往第一个加两条消息，确认第二个仍然为空。

验收：`c1.last().content` 是你加的第二条；`len(c2.messages)` 是 0。

<details><summary>答案</summary>

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass
class Conversation:
    messages: list[Message] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role, content))

    def last(self) -> Message:
        return self.messages[-1]
```

如果 `messages` 写成了 `= []`，Python 会直接拒绝，这个坑绕不过去。`Message` 冻住、`Conversation` 不冻，因为消息是记录、对话会增长。

</details>

## 练习 3：写一个 Protocol 并让两个类满足它

定义 `Storage` Protocol，要求有 `save(key: str, value: str) -> None` 和 `load(key: str) -> str | None`。实现 `MemoryStorage`（用 dict）和 `FileStorage`（用一个文件夹，每个 key 一个文件）。写一个函数 `remember(store: Storage)` 存一个值再读出来打印。两个实现都传进去。

验收：两次都打印出存进去的值；两个类都没有继承 `Storage`。

<details><summary>提示</summary>

`FileStorage` 用 `pathlib.Path(folder) / key` 定位文件，`write_text` / `read_text`；`load` 时先 `exists()`。文件夹用 `tempfile.mkdtemp()` 造一个临时的。这题的重点不在实现，在于 `remember()` 完全不知道也不关心传进来的是哪个类。

</details>

## 练习 4：该不该写类

三个需求，各选"函数 / 类 / dataclass"并说一句理由：

1. 把摄氏度转成华氏度
2. 记录一次工具调用的名字、参数、耗时
3. 一个限速器，记住最近 60 秒内发了多少请求，超过就拒绝

<details><summary>答案</summary>

1. 函数。输入到输出，没有状态。
2. dataclass，而且 `frozen=True`。纯数据记录，造好不该改。
3. 类。"最近 60 秒的请求时间戳"是需要在多次调用之间保存的状态，`allow()` 和 `record()` 两个方法都要用它。

</details>
