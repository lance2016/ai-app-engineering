# P03 模块、异常与日志｜练习

> 第一题照着做就能完成。答案折叠在每题下方。

## 练习 1：给包加一个函数

在 `code/shapes/area.py` 里加一个 `triangle_area(base, height)`，在 `shapes/__init__.py` 里导出它，然后在 `01_modules_and_imports.py` 末尾调用并打印。

验收：运行输出多一行 `triangle: 6.0`（用 base=3, height=4）。

<details><summary>答案</summary>

`area.py` 加：

```python
def triangle_area(base: float, height: float) -> float:
    return base * height / 2
```

`__init__.py` 的 import 和 `__all__` 各加上 `triangle_area`。脚本里 `print("triangle:", shapes.triangle_area(3, 4))`。

</details>

## 练习 2：安全地读一个配置

写一个函数 `read_port(config: dict) -> int`：从 `config["port"]` 读端口并转成 int。键不存在时返回默认值 8000；值不是合法数字时抛出一个自定义的 `ConfigError`，消息里带上原始值。

验收：`read_port({})` 返回 8000；`read_port({"port": "9000"})` 返回 9000；`read_port({"port": "abc"})` 抛 `ConfigError: invalid port 'abc'`。

<details><summary>答案</summary>

```python
class ConfigError(Exception):
    pass


def read_port(config: dict) -> int:
    raw = config.get("port", 8000)
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(f"invalid port {raw!r}") from None
```

两种"不正常"用了两种处理：键缺失是预期内的情况，用默认值；值非法是配置错误，必须报出来。`from None` 让报错只显示你的 ConfigError，不带内部的 ValueError。

</details>

## 练习 3：把 print 换成 logging

下面这段代码用 print 输出。改成 logging：进度用 INFO，跳过的项用 WARNING，异常用 `log.exception`。运行时默认不显示 DEBUG，`LOG_LEVEL=DEBUG` 时显示每一项的原始值。

```python
items = ["1", "2", "x", "4"]
total = 0
for item in items:
    print("processing", item)
    try:
        total += int(item)
    except ValueError:
        print("skip", item)
print("total", total)
```

验收：默认运行看到一条 WARNING 和一条 INFO 的 total；加 `LOG_LEVEL=DEBUG` 看到四条 processing。

<details><summary>答案</summary>

```python
import logging
import os

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

items = ["1", "2", "x", "4"]
total = 0
for item in items:
    log.debug("processing %s", item)
    try:
        total += int(item)
    except ValueError:
        log.warning("skip %s", item)
log.info("total %s", total)
```

注意 `log.debug("processing %s", item)` 用 `%s` 占位而不是 f-string：级别不够时这条根本不会被格式化，省一点性能，也是 logging 的惯用写法。

</details>

## 练习 4：finally 到底跑不跑

不写代码，先判断再验证：下面函数返回什么？`finally` 里的 print 会执行吗？

```python
def f():
    try:
        return "from try"
    finally:
        print("cleanup")
```

<details><summary>答案</summary>

打印 `cleanup`，返回 `"from try"`。`return` 也拦不住 `finally`，这正是它存在的意义：无论函数怎么退出，清理都会发生。

</details>
