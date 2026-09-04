---
status: complete
part: 前置 · 后端工程
estimated_time: 约 1.5 小时
---

# B03 Git、命令行与 Docker Compose

> 三样东西，每天都要用，但没人正式教：在终端里干活、用 Git 管代码、用 Docker Compose 一条命令把数据库起来。这一模块不求全，只讲本课程用得到的那一部分。

## 学习目标

- 能在终端里移动、查找、看文件、组合命令，遇到不认识的命令知道怎么查
- 能走完"开分支、提交、rebase 到最新 main、解决冲突、推送"这条 Git 流程，并知道哪些操作不会丢东西
- 能读懂一份 `compose.yaml`，用它起停 PostgreSQL 和 Redis，并说出容器、镜像、卷分别是什么

## 前置

- 会打开终端。macOS 用 Terminal 或 iTerm，Windows 用 WSL2 里的 Ubuntu（本课程的命令全部按 Unix shell 写）。

## 核心概念

### 命令行：十几个命令够用一年

```bash
pwd                      # 我在哪
ls -la                   # 这里有什么（含隐藏文件）
cd lessons/05-tool-calling
cat README.md            # 看全文
head -20 file.py         # 看前 20 行
grep -rn "ToolCall" .    # 递归找字符串，带行号
find . -name "*.py"      # 按名字找文件
mkdir -p a/b/c           # 建目录，父目录不存在也一起建
cp / mv / rm             # 复制、移动改名、删除（rm 没有回收站）
```

两个组合技：`|` 把左边的输出交给右边（`grep -rn "TODO" . | wc -l` 数有多少 TODO），`>` 把输出写进文件。环境变量用 `export NAME=value` 设置，`echo $NAME` 查看，这就是 `.env` 文件和 `MODEL_PROVIDER=deepseek uv run ...` 背后的机制。

不认识的命令：`man 命令名` 或 `命令名 --help`。

### Git：三个区域

```text
工作区（你正在改的文件） --git add--> 暂存区（准备提交的） --git commit--> 仓库历史
```

`git status` 随时看三个区的状态。`git add -p` 一块一块地挑要提交的改动，比 `git add .` 更容易写出干净的提交。`git diff` 看工作区和暂存区的差别，`git diff --staged` 看暂存区和上次提交的差别。

### 一条完整的功能流程

```bash
git switch -c feat/tool-runner        # 从当前位置开一个分支
# ...改代码...
git add -p && git commit -m "feat: add tool runner"
git fetch origin                      # 拉最新的远程信息，不动你的文件
git rebase origin/main                # 把你的提交"搬"到最新 main 之后
git push -u origin feat/tool-runner   # 推上去，开 PR
```

`rebase` 和 `merge` 都能把 main 的新改动合进来，区别是 rebase 让历史保持一条直线。本课程约定用 rebase。

### 冲突：Git 不知道该留谁的

rebase 或 merge 时，同一行两边都改了，Git 会停下来，文件里出现：

```text
<<<<<<< HEAD
their version of the line
=======
your version of the line
>>>>>>> feat/tool-runner
```

你手动改成想要的样子，删掉三行标记，然后 `git add 文件` 再 `git rebase --continue`。中途想放弃：`git rebase --abort` 回到 rebase 前的状态，什么都不会丢。

### 哪些操作安全

| 想做什么 | 用什么 | 会丢东西吗 |
|---|---|---|
| 放弃某个文件未暂存的改动 | `git restore 文件` | 会，那些改动没提交过 |
| 把文件从暂存区拿出来 | `git restore --staged 文件` | 不会，改动还在工作区 |
| 撤销最近一次提交但保留改动 | `git reset --soft HEAD~1` | 不会 |
| 找回"消失"的提交 | `git reflog` 然后 `git switch -c 救回 <hash>` | 不会，提交过的东西 reflog 里都有 |
| 彻底回到某个状态 | `git reset --hard` | 会，慎用 |

规律：**提交过的东西几乎丢不掉**，`reflog` 记着你去过的每一个位置。没提交的改动才是危险的，所以小步多提交。

### `.gitignore` 和密钥

`.env`、`.venv/`、`__pycache__/` 不该进仓库。本仓库根目录的 `.gitignore` 已经列了。**API key 一旦 push 到公开仓库就当泄露处理**：立刻去服务商后台作废重新生成，光从 Git 历史里删掉没有用，爬虫几分钟内就抓走了。

### Docker：把"环境"打包

装 PostgreSQL 传统做法是在电脑上装一个服务，不同项目要不同版本就麻烦了。Docker 的思路是：**镜像**（image）是一个打包好的、带完整运行环境的程序快照，**容器**（container）是镜像跑起来的一个实例，用完删掉，电脑上不留痕迹。**卷**（volume）是挂在容器外面的一块硬盘，容器删了数据还在。

### Compose：多个容器一个文件

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
    ports:
      - "5432:5432"           # 电脑上的 5432 → 容器里的 5432
    volumes:
      - pgdata:/var/lib/postgresql/data
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
volumes:
  pgdata:
```

一份 `compose.yaml` 描述几个服务。`docker compose up -d` 全部后台起来，`docker compose ps` 看状态，`docker compose logs postgres` 看日志，`docker compose down` 停掉（数据留在卷里），`down -v` 连数据一起删。主项目从 M2 开始就用 [`code/compose.yaml`](./code/compose.yaml) 这份文件起依赖，镜像选的是带 pgvector 扩展的 PostgreSQL，M4 做向量检索时直接能用。

连接字符串是 `postgresql://app:app@localhost:5432/app`，密码写在 compose 里是因为这是本地开发环境；线上环境的密码走环境变量或密钥管理，永远不进文件。

## 动手

| 文件 | 内容 |
|---|---|
| [`code/01_git_workflow_cheatsheet.py`](./code/01_git_workflow_cheatsheet.py) | 打印本课程会用到的 Git 命令，按使用顺序排 |
| [`code/compose.yaml`](./code/compose.yaml) | 起 PostgreSQL（含 pgvector）和 Redis 的配置，主项目 M2 起会用 |

Git 和 Docker 都是要在终端里亲手敲的，建议：

1. `mkdir /tmp/git-play && cd /tmp/git-play && git init`，照着 cheatsheet 走一遍，故意在两个分支改同一行制造一次冲突并解决。
2. 装好 Docker Desktop（或 OrbStack），`docker compose -f prerequisites/backend/03-git-cli-and-docker/code/compose.yaml up -d`，然后 `docker compose ... ps` 看两个服务是否 healthy，最后 `down -v` 清掉。

## 常见错误

**rebase 时看到一堆 `<<<<<<<` 慌了。** 这是正常的冲突标记，不是文件坏了。每一处都改成你想要的最终样子，删掉三行标记，`git add` 那个文件，`git rebase --continue`。做错了 `git rebase --abort` 回到起点。

**`git push` 被拒绝：`! [rejected] ... (fetch first)`。** 远程分支有你本地没有的提交。`git fetch origin && git rebase origin/你的分支` 再推。不要用 `--force` 推别人也在用的分支。

**Docker 起不来：`port is already allocated`。** 电脑上 5432 端口已经被别的东西占了（多半是以前装的 PostgreSQL）。要么停掉那个服务，要么把 compose 里改成 `"5433:5432"`，连接字符串也跟着改端口。

**`.env` 不小心 `git add .` 加进去了。** 还没 commit 的话 `git restore --staged .env`。已经 commit 但没 push：`git reset --soft HEAD~1` 再重新提交。已经 push 到公开仓库：作废里面所有 key，然后再清历史。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

主线落点：主项目 [M2](../../../project/m2-state-and-storage/README.md) 起。

具体场景：从 M2 开始，每次开始学习都是同一套动作：`docker compose up -d` 起数据库和 Redis，`git switch -c m2/state-storage` 开分支，写代码、跑 `uv run pytest`、`git add -p` 分块提交。第 19 课讲部署时，你会把同一份 `compose.yaml` 加上 API 服务本身，变成一条命令能起整个系统的配置。而模型 key 从头到尾只存在 `.env` 里，这个习惯从这一模块开始养。

## 延伸阅读

- [Pro Git 中文版](https://git-scm.com/book/zh/v2)（访问日期 2026-09-04）：读第 1～3 章（起步、基础、分支）就够用，第 7 章的 rebase 和 reflog 部分遇到问题时查。
- [The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)（访问日期 2026-09-04）：MIT 的一门课，讲 shell、Git、调试这些"没人教"的东西，有中文字幕版。
- [Docker · What is a container?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/)（访问日期 2026-09-04）：容器和镜像的概念，十分钟。
- [Docker Compose 文档](https://docs.docker.com/compose/)（访问日期 2026-09-04）：需要给 compose 加服务时查。

---

[← B02](../02-testing/README.md) · [→ 进入主线第 00 课](../../../lessons/00-setup/README.md)
