---
status: complete
part: 前置 · Python
estimated_time: 约 1 小时
---

# P00 环境与工具链

> 装好 Python 和 uv，在终端里跑通第一个脚本，知道"虚拟环境"这四个字在说什么。这一课没有难点，只有一堆第一次见会卡住的细节。

## 学习目标

- 能用 uv 装好 Python 3.12，跑通仓库里的任意一个脚本
- 能说出虚拟环境是什么、为什么每个项目要有自己的一个
- 能分辨 `uv run python x.py`、`python x.py` 和在 REPL 里敲代码这三种运行方式

## 前置

- 会打开终端（macOS 的 Terminal 或 iTerm，Windows 的 PowerShell 或 Windows Terminal），会 `cd` 进一个目录。其他都不需要。

## 核心概念

### 终端里的三个命令

```bash
pwd          # 我在哪个目录
ls           # 这个目录里有什么（Windows PowerShell 也能用 ls）
cd 目录名     # 进入目录；cd .. 回上一级
```

后面所有命令都在终端里敲。看到 `$` 或 `%` 开头的提示符就是在等你输入。

### 装 uv，让它替你管 Python

uv 是一个 Python 项目管理工具。它会帮你下载 Python、建虚拟环境、装依赖、运行脚本，一个工具解决以前要四五个工具才能解决的事。

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

uv --version   # 看到版本号就装好了
```

装好后进入仓库目录，一条命令搞定环境：

```bash
cd ai-app-engineering
uv sync
```

`uv sync` 会读仓库根目录的 `.python-version`（写着 3.12），没有就下载一个，然后建一个叫 `.venv` 的文件夹，把项目需要的库装进去。这个过程不碰你电脑上原有的任何 Python。

### 虚拟环境是什么

一台电脑上可能有很多 Python 项目，每个项目依赖的库和版本不同。如果都装在同一个地方，项目 A 要 1.0 版、项目 B 要 2.0 版，就打架了。

虚拟环境就是"每个项目自己的一套 Python 加库"，装在项目目录下的 `.venv` 文件夹里，互不干扰。删掉 `.venv` 再 `uv sync` 就能重建，所以它不需要备份，也不要提交到 git。

```bash
uv run python prerequisites/python/00-setup-and-tooling/code/02_where_am_i.py
```

这个脚本会打印 `Inside a virtual environment: True` 和 `.venv` 的路径。这就是你在虚拟环境里的证据。

### 三种运行代码的方式

| 方式 | 命令 | 什么时候用 |
|---|---|---|
| 用 uv 跑脚本 | `uv run python 文件.py` | 本课程的默认方式。uv 保证用的是 `.venv` 里的 Python |
| 直接跑脚本 | `python 文件.py` | 只有在你自己激活了 `.venv` 之后才等价；否则用的可能是系统 Python，库找不到 |
| REPL 交互 | `uv run python` 然后逐行敲 | 试一个小想法，看某个表达式的值。`exit()` 或 Ctrl+D 退出 |

REPL 长这样：

```text
>>> 1 + 2
3
>>> name = "Lance"
>>> f"hi {name}"
'hi Lance'
```

`>>>` 是它在等你输入。敲一行立刻看到结果，很适合确认"这个函数到底返回什么"。

### 编辑器

推荐 VS Code 加官方 Python 扩展。装好后打开仓库目录，VS Code 会自动发现 `.venv`，右下角显示 `3.12.x ('.venv')`。如果显示的是别的版本，点它切换。

课程里的代码文件用 `# %%` 分成一格一格，VS Code 会在每格上方显示 "Run Cell"，点一下只跑那一格。这比整个文件重跑省时间。

## 动手

按顺序跑三个文件，每个都读一遍源码，很短。

| 文件 | 演示什么 |
|---|---|
| [`code/01_hello.py`](./code/01_hello.py) | 打印一行字，然后打印是哪个 Python 在运行它。路径里应该有 `.venv` |
| [`code/02_where_am_i.py`](./code/02_where_am_i.py) | 当前目录、脚本所在目录、是否在虚拟环境里 |
| [`code/03_script_with_input.py`](./code/03_script_with_input.py) | 从命令行接一个参数。试 `uv run python ...03_script_with_input.py 你的名字` |

## 常见错误

**`zsh: command not found: uv`**（或 Windows 的 `'uv' is not recognized`）。安装脚本跑完了，但当前这个终端窗口还不知道。关掉终端重开一个，或按安装脚本最后一行的提示执行 `source ~/.zshrc`。

**`ModuleNotFoundError: No module named 'aiapp'`**。你用了 `python x.py` 而不是 `uv run python x.py`，跑的是系统 Python，它看不到 `.venv` 里的库。加上 `uv run`。

**`SyntaxError: '(' was never closed`**。

```text
  File "e1.py", line 1
    print("Hello"
         ^
SyntaxError: '(' was never closed
```

括号没配对。Python 会用 `^` 指出它认为出问题的位置，通常在那一行或上一行。

**`IndentationError: expected an indented block after 'if' statement on line 1`**。`if`、`for`、`def` 这类语句后面的代码必须缩进（约定四个空格）。VS Code 会自动缩进，手敲时容易漏。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

主线第 00 课的第一条命令就是 `uv sync`，然后 `uv run python lessons/00-setup/code/01_hello_fake_adapter.py`。那个脚本会调用一个"假的 AI 模型"并打印它的回答。你现在学的这一套，就是为了能一字不差地把那条命令跑通。

再往后，主项目的每个里程碑都是"进入目录、`uv run`、看输出"。环境这件事只需要学一次。

## 延伸阅读

- [uv 安装文档](https://docs.astral.sh/uv/getting-started/installation/)（访问日期 2026-09-04）：各平台安装方式，出问题先看这里。
- [uv · Running commands in projects](https://docs.astral.sh/uv/concepts/projects/run/)（访问日期 2026-09-04）：`uv run` 到底做了什么。
- [Python 官方教程 · 使用解释器](https://docs.python.org/3/tutorial/interpreter.html)（访问日期 2026-09-04）：REPL 的官方说明。
- [venv 模块文档](https://docs.python.org/3/library/venv.html)（访问日期 2026-09-04）：uv 底下建的就是这种虚拟环境，想知道原理看这个。
- [VS Code · Python 入门](https://code.visualstudio.com/docs/python/python-tutorial)（访问日期 2026-09-04）：安装扩展和选择解释器的截图教程。

---

[← 前置总览](../../README.md) · [P01 →](../01-python-basics/README.md)
