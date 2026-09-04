"""The Git commands you will actually type in this course, in the order you type them.

This file only prints. Read it, then run the commands in a scratch repo.

Run:  uv run python prerequisites/backend/03-git-cli-and-docker/code/01_git_workflow_cheatsheet.py
Expect: the cheat sheet below.
"""

# %% cheatsheet
STEPS = [
    ("start a feature", ["git switch -c feat/tool-runner", "# edit files", "git status", "git add -p", "git commit -m 'feat: add tool runner'"]),
    ("keep up with main", ["git fetch origin", "git rebase origin/main", "# fix conflicts in the files git lists, then:", "git add <file>", "git rebase --continue"]),
    ("undo safely", ["git restore <file>            # discard unstaged edits to one file", "git restore --staged <file>   # unstage, keep edits", "git reflog                    # find a commit you thought you lost"]),
    ("share", ["git push -u origin feat/tool-runner", "# open a PR; after review:", "git switch main && git pull --rebase"]),
]

# %% run
if __name__ == "__main__":
    for title, cmds in STEPS:
        print(f"\n## {title}")
        for c in cmds:
            print(f"  {c}")
