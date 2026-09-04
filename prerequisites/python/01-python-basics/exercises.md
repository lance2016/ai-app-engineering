# P01 Python 基础语法｜练习

> 第一题照着做就能完成。答案折叠在每题下方。

## 练习 1：改一个温度分级

打开 `code/03_conditions_and_loops.py`，把 `temp = 31` 改成 `temp = 36`，运行；再改成 `temp = 10`，运行。

验收：两次输出分别是 `36 degrees is hot` 和 `10 degrees is cool`。

<details><summary>提示</summary>

不用改 if 语句，只改最上面那个数字。如果想多一档，在 `elif temp >= 25:` 上面再加一行 `elif temp >= 30:`，试试看顺序为什么重要。

</details>

## 练习 2：写一个函数

新建一个文件 `my_first.py`（放在任何地方都行），写一个函数 `describe(name, age)`，返回类似 `"Lance is 30 years old"` 的字符串。`age` 给默认值 0。文件末尾用 `if __name__ == "__main__":` 调用两次并打印：一次传两个参数，一次只传名字。

验收：运行后打印两行，第二行是 `... is 0 years old`。

<details><summary>答案</summary>

```python
def describe(name: str, age: int = 0) -> str:
    return f"{name} is {age} years old"


if __name__ == "__main__":
    print(describe("Lance", 30))
    print(describe("Amy"))
```

</details>

## 练习 3：统计一段文字

给定 `text = "the quick brown fox jumps over the lazy dog the end"`，用循环数出单词 `"the"` 出现了几次，以及最长的单词是哪个。

验收：输出 `the: 3` 和 `longest: quick`（或 `brown`、`jumps`，长度都是 5，任意一个都对）。

<details><summary>答案</summary>

```python
text = "the quick brown fox jumps over the lazy dog the end"
words = text.split(" ")

count = 0
longest = ""
for word in words:
    if word == "the":
        count += 1
    if len(word) > len(longest):
        longest = word

print(f"the: {count}")
print(f"longest: {longest}")
```

P02 学了列表方法后，第一行统计可以写成 `words.count("the")`。

</details>

## 练习 4：读报错

下面这段代码有两个错误。不要运行，先读出来；然后运行验证。

```python
def add(a, b)
    result = a + b
    return reslt
```

<details><summary>答案</summary>

第一行 `def add(a, b)` 缺冒号，Python 会先报 `SyntaxError: expected ':'`。补上冒号再跑，`return reslt` 拼错，报 `NameError: name 'reslt' is not defined`。

语法错误在运行前就被发现，所以一次只报一个；名字错误要执行到那一行才报。这是两类错误的区别。

</details>
