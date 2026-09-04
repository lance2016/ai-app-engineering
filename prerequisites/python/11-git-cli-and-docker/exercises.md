# P11 Git、命令行与 Docker Compose｜练习

> 每题写清：任务、验收标准、提示。答案折叠。第一题照着做就能完成。

## 练习 1：制造并解决一次冲突

在一个临时目录里 `git init`，建一个 `a.txt` 写一行 `hello`，提交。开分支 `feat` 把这行改成 `hello from feat` 并提交；切回 `main` 把同一行改成 `hello from main` 并提交。然后在 `feat` 上 `git rebase main`。

验收：看到冲突标记；手动改成 `hello from both`，`git add a.txt && git rebase --continue` 成功；`git log --oneline` 显示 feat 的提交在 main 之后。

<details><summary>提示</summary>

命令顺序：

```bash
git init && echo hello > a.txt && git add . && git commit -m init
git switch -c feat && echo "hello from feat" > a.txt && git commit -am feat
git switch main && echo "hello from main" > a.txt && git commit -am main
git switch feat && git rebase main      # 冲突
# 编辑 a.txt，删掉标记
git add a.txt && git rebase --continue
```

做完再来一次，这次在冲突时 `git rebase --abort`，确认一切回到 rebase 前。

</details>

## 练习 2：找回"删掉"的提交

在上面的仓库里，`git reset --hard HEAD~1` 删掉最新一次提交。然后用 `git reflog` 找到它并恢复。

验收：`git log --oneline` 里那次提交回来了。

<details><summary>答案</summary>

`git reflog` 会列出 HEAD 去过的每一个位置，找到 `reset` 之前那一行的 hash，`git reset --hard <hash>` 或 `git switch -c rescue <hash>`。提交过的东西 reflog 默认保留 90 天，这就是"提交过的几乎丢不掉"的底气。

</details>

## 练习 3：用管道数一数

在本仓库根目录，用一条命令数出 `lessons/` 下所有 `.py` 文件里 `# %%` 出现的总次数。

验收：一个数字。

<details><summary>答案</summary>

`grep -rh "# %%" lessons --include="*.py" | wc -l`。`-h` 不打印文件名，`--include` 只看 `.py`，`wc -l` 数行。学会把小命令串起来，很多一次性的统计不需要写脚本。

</details>

## 练习 4：读 compose 文件回答问题

看 `code/compose.yaml`，不运行，回答：

1. 把 `ports` 那两行删掉，容器还能跑吗？你的 Python 程序还能连上吗？
2. `docker compose down` 之后再 `up`，之前建的表还在吗？`down -v` 呢？
3. 为什么 `healthcheck` 用的是 `pg_isready -U app` 而不是 `sleep 5`？

<details><summary>答案</summary>

1. 能跑，但连不上。`ports` 是把容器里的端口映射到你电脑上，没有它容器只在 Docker 自己的网络里可达。
2. `down` 后表还在，因为数据在卷 `pgdata` 里；`down -v` 会删卷，表就没了。
3. `sleep 5` 是猜数据库 5 秒能起来，机器慢的时候猜错。`pg_isready` 是真去问数据库"你好了吗"，好了才算 healthy。以后 API 服务加进 compose 时会写 `depends_on: postgres: condition: service_healthy`，就靠这个。

</details>
