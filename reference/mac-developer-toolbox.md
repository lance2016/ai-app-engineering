---
status: complete
updated: 2026-09-10
---

# Mac 工程效率工具箱

> 这页给在 macOS 上写 Python、后端和 AI 应用的人。目标不是把菜单栏塞满，而是把安装、切换环境、查问题和维护项目这几件事做顺。
>
> 先装基础工具，再按工作内容加软件。下面的命令以 Apple Silicon 为例；Intel Mac 的 Homebrew 路径通常是 `/usr/local`，先用 `uname -m` 和 `brew --prefix`确认。

## 先装这几样

| 工具 | 解决什么问题 | 安装方式 | 建议 |
|---|---|---|---|
| Xcode Command Line Tools | 提供 `git`、编译器和 macOS SDK；不需要完整 Xcode | `xcode-select --install` | 新 Mac 第一件事 |
| [Homebrew](https://brew.sh/) | 安装和更新命令行工具、桌面应用 | 先看[官方安装说明](https://docs.brew.sh/Installation) | 命令行工具的统一入口 |
| [OrbStack](https://docs.orbstack.dev/) | 在 Mac 上运行 Docker 容器和 Linux | `brew install --cask orbstack` | 要跑参考项目的 Compose 时安装 |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Python 版本、虚拟环境、依赖和锁文件 | `brew install uv` | Python 项目默认用它，不要把包装进系统 Python |
| [GitHub CLI](https://cli.github.com/) | 在终端登录 GitHub、查 PR、看 Actions | `brew install gh` | 经常提交或排查 CI 时安装 |
| VS Code、Cursor 或 PyCharm | 编辑器只选一个主力 | 从官网安装 | 不要同时维护三套插件和快捷键 |

资料和命令均按 2026-09-10 的页面核对。Homebrew 的安装脚本会先打印将要执行的操作；看清安装前后的 shell 配置，再继续。

初始化基础环境可以按下面顺序做：

```bash
# 只在系统还没有 Command Line Tools 时执行
xcode-select --install
# 从 Homebrew 官网复制安装命令，确认安装器显示的内容后再执行
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# 完成安装器提示的 shellenv 配置、重新打开终端后，再运行下面两行
brew install git gh jq yq ripgrep fd fzf bat eza zoxide uv
brew install --cask orbstack raycast rectangle
```

第一行只在系统还没有 Command Line Tools 时执行，弹出系统对话框后按提示完成；第二行安装 Homebrew。完成安装器提示的 shellenv 配置后，重新打开终端；第三行装终端工具，第四行装 OrbStack、Raycast 和窗口管理器。桌面应用可以按需要删减，不必一次全部安装。

## 桌面工具：减少来回切换

| 工具 | 用法 | 取舍 |
|---|---|---|
| [Raycast](https://www.raycast.com/) | 用一个快捷键启动应用、搜索文件、粘贴历史、运行脚本和扩展 | 核心功能够日常使用；扩展从 [Store](https://www.raycast.com/store) 安装，别装一堆重复的启动器 |
| [Rectangle](https://rectangleapp.com/) | 用快捷键把窗口放到左右半屏、四角或全屏 | 免费开源版先够用；多显示器布局再考虑 Pro |
| OrbStack | 从菜单栏查看容器、镜像、卷和 Linux 实例 | 已经使用 OrbStack 就不要再让 Docker Desktop、Colima 同时接管默认 Docker context |
| macOS 自带 `open`、`pbcopy`、`pbpaste`、`sips` | 打开项目、复制命令、查看或缩放图片 | 先用系统命令，只有确实缺功能时再装替代软件 |

Raycast 的扩展是小命令，不是另一个应用商店。建议先装四个：**GitHub**（查 PR 和 Actions）、**Brew**（搜 formula 和 cask）、**Visual Studio Code**（打开项目）、**Kill Process**（结束占用端口的进程）。它们都能在 Store 中按名字找到；扩展会从 Store 自动更新。Raycast 的[扩展说明](https://manual.raycast.com/extensions)访问日期为 2026-09-10。

## 终端工具：每个只解决一类事

| 命令 | 替代或补充 | 典型用法 |
|---|---|---|
| `rg` | 搜文本，比 `grep` 更适合代码库 | `rg "timeout|retry" src tests` |
| `fd` | 找文件，比 `find` 的默认行为更直观 | `fd -e py runtime` |
| `fzf` | 在文件、分支和历史里模糊筛选 | `git branch --all \| fzf` |
| `jq` / `yq` | 查询和修改 JSON / YAML | `jq '.choices[0].message' response.json` |
| `bat` | 带语法高亮和 Git 标记的文件查看器 | `bat pyproject.toml` |
| `eza` | 更容易扫读的目录列表 | `eza -lah --git` |
| `zoxide` | 记住常去的目录 | `z ai-app-engineering` |
| `gh` | GitHub 的终端入口 | `gh pr checks`、`gh run watch` |
| `lazygit`（按需） | 在终端查看提交、分支和 diff | `brew install lazygit` |

这些工具的官方说明：[fzf](https://github.com/junegunn/fzf)、[fd](https://github.com/sharkdp/fd)、[bat](https://github.com/sharkdp/bat)、[GitHub CLI](https://cli.github.com/manual/)（访问日期均为 2026-09-10）。先记住 `rg`、`fd`、`jq` 和 `gh`，其他命令按实际需要加。

## zsh 只加必要的几行

macOS 默认使用 zsh。不要为了换一个主题安装一整套 shell 框架；把环境初始化和两个高频工具接进 `~/.zshrc` 就够了：

```bash
if [[ -x /opt/homebrew/bin/brew ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
elif [[ -x /usr/local/bin/brew ]]; then
  eval "$(/usr/local/bin/brew shellenv)"
fi

command -v fzf >/dev/null && source <(fzf --zsh)
command -v zoxide >/dev/null && eval "$(zoxide init zsh)"
alias ll='eza -lah --git'
```

Homebrew 的两条路径分别对应 Apple Silicon 和 Intel；`fzf`、`zoxide` 的判断让这段配置在尚未安装它们的机器上也能启动。改完后执行 `exec zsh`，再用 `type ll` 和 `fzf --version`检查。

## Python 和多语言环境

Python 项目只保留一条路径：仓库里有 `pyproject.toml` 和 `uv.lock` 就用 `uv sync` 建环境，用 `uv run` 执行命令；不要再单独激活一个手工创建的 `.venv`：

```bash
uv sync
uv run python --version
uv run pytest -q
```

需要同时维护 Node、Go、Rust 或多个 Python 版本时，再加 [mise](https://mise.jdx.dev/)：

```bash
brew install mise
mise use --global node@lts
mise use --global python@3.13
```

安装后在 `~/.zshrc` 中加入一次 `eval "$(mise activate zsh)"`，再重新打开终端。`mise.toml` 应该提交到项目里，写清版本和任务；个人机器上的全局版本只作为默认值。mise 的[入门说明](https://mise.jdx.dev/getting-started.html)访问日期为 2026-09-10。

## 编辑器插件：Python 项目装这几项

下面以 VS Code 为例。使用 Cursor 或其他兼容编辑器时，先确认它是否支持同一套扩展；不要为了“功能齐全”把多个格式化器和语言服务器叠在一起。

| 扩展 | 作用 | 建议 |
|---|---|---|
| [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) | 解释器选择、调试、测试和环境管理 | 必装；会带上 Pylance 这个可选依赖 |
| [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) | 补全、类型检查、跳转和诊断 | 使用微软官方 VS Code 时启用 |
| [Ruff](https://docs.astral.sh/ruff/editors/setup/) | lint、格式化和 import 排序 | 让 Ruff 负责格式化时，别再同时启用 Black 和 isort |
| [Docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker) | 查看镜像、容器、Compose 和日志 | 使用 OrbStack 的 Docker context 也能接 |
| [Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers) | 在容器内打开项目，统一工具链 | 项目提供 `devcontainer.json` 时再装 |
| YAML | 编辑 Compose、CI 和配置文件 | 只在经常维护 YAML 时装 |

如果 `code` 命令已经加入 PATH，可以一次装基础扩展：

```bash
code --install-extension ms-python.python
code --install-extension charliermarsh.ruff
code --install-extension ms-azuretools.vscode-docker
code --install-extension ms-vscode-remote.remote-containers
code --install-extension redhat.vscode-yaml
```

Python 扩展、Pylance、Ruff 和 Dev Containers 的功能与安装方式，以[Python 扩展说明](https://marketplace.visualstudio.com/items?itemName=ms-python.python)、[Ruff 设置](https://docs.astral.sh/ruff/editors/setup/)和 [Dev Containers 文档](https://code.visualstudio.com/docs/devcontainers/create-dev-container)为准，访问日期均为 2026-09-10。

## Mac 自带命令，工程里很有用

| 目的 | 命令 | 说明 |
|---|---|---|
| 在编辑器打开当前目录 | `open -a "Visual Studio Code" .` | 把目录交给 GUI 应用，避免手动拖文件 |
| 复制和读取剪贴板 | `pbcopy < error.log`、`pbpaste` | 把日志或 JSON 送进编辑器、工单或模型 |
| 查看图片尺寸 | `sips -g pixelWidth -g pixelHeight image.png` | 先确认尺寸，再决定是否发给视觉模型 |
| 缩放图片 | `sips -Z 1600 image.png --out image-small.png` | 降低上传体积，也减少视觉 token |
| 搜索 Spotlight 索引 | `mdfind "kMDItemFSName == '*.md'"` | 查散落在本机的 Markdown 文档 |
| 查看谁占用端口 | `lsof -nP -iTCP:8000 -sTCP:LISTEN` | 启动服务报端口冲突时先查它 |
| 看完整 HTTP 握手 | `curl -v http://localhost:8000/healthz` | 区分 DNS、连接、TLS、HTTP 和应用错误 |
| 让 Mac 读出一段文字 | `say "服务已启动"` | 本地演示或语音开发时做最小反馈 |

## 参考项目的 Mac 启动顺序

这门课的参考项目使用 `uv`、Docker Compose 和 `pytest`。OrbStack 启动后，在项目目录里按下面顺序检查：

```bash
git clone https://github.com/lance2016/ai-app-engineering-ref.git
cd ai-app-engineering-ref
uv sync
docker context show
docker compose up -d
docker compose ps
uv run pytest tests/project/m1 -q
```

`docker context show` 应该显示当前 Docker CLI 正在使用的 context；`docker compose ps` 能看出 PostgreSQL、Redis 和应用是否起来。项目的完整里程碑、截图和故障演练见[参考项目路线](./project-playbook.md)。不要把 API key 写进仓库；参考项目的 `.env.example` 只作配置名示例。

参考项目仓库和上面的启动命令按 2026-09-10 的 `main` 分支核对；如果仓库后来改了服务名或端口，以仓库当前 README 为准。

## 更新、诊断和备份

```bash
brew update
brew outdated
brew upgrade
brew cleanup

which -a python3 uv docker
brew --prefix
docker version
gh auth status
```

这组命令回答四个问题：Homebrew 索引是否最新、哪些包能升级、当前实际调用的是哪一个 Python/uv/Docker、GitHub 登录是否还有效。升级前先看项目的锁文件和 CI，不要在发布当天顺手升级所有工具。

把 `~/.zshrc`、`~/.config/mise/config.toml` 和编辑器设置放进私有 dotfiles 仓库，密钥放 Keychain 或密码管理器。项目里的 `.env` 加进 `.gitignore`；提交前用 `git diff --cached`检查有没有把 token 带进去。

## 三个常见误区

!!! warning "容器运行时只选一个"
    Docker Desktop、OrbStack 和 Colima 都可能提供 Docker context。一次只让一个工具接管默认 context；遇到“容器明明在运行但 CLI 看不到”，先查 `docker context show` 和 `docker context ls`。

**不要用 `sudo pip install` 改系统 Python。** 项目依赖写入 `pyproject.toml`，用 `uv add`；只想安装一个命令行工具，用 `uv tool install`。这样项目环境和全局工具不会互相覆盖。

**不要把插件数量当效率。** 一个 formatter、一个语言服务器、一套 Git 操作入口就够了。遇到补全慢、保存时文件被改两次、诊断重复出现，先停掉重复扩展，再加新的。

**不要把“能启动”当“可排查”。** 服务启动后至少跑一次健康检查、一次测试和一次日志查看；参考项目的[工程基础页](../prerequisites/engineering-foundations.md)解释了进程、端口、HTTP、容器和日志之间的关系。

---

[工程能力基础](../prerequisites/engineering-foundations.md) · [工程进阶](../prerequisites/engineering-advanced.md) · [参考项目路线](./project-playbook.md)
