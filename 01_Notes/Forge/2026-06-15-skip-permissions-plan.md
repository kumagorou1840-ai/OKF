# 📋 --dangerously-skip-permissions Option Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `--dangerously-skip-permissions` option to both `run_loop.py` and `agy_chat.py` to enable automatic execution approval for AI agent tools.

**Architecture:** Modify the list of subprocess arguments representing the `agy` command within both script files to directly append `"--dangerously-skip-permissions"`. This bypasses user confirmation prompts when executing agent tools.

**Tech Stack:** Python (subprocess module)

---

### Task 1: Modify run_loop.py

**Files:**
- Modify: `scratch/run_loop.py:17-25`

- [ ] **Step 1: Check existing run_loop.py behavior**

Run:
```pwsh
python scratch/run_loop.py "hello とだけ出力してください。"
```
Expected: The CLI starts but might prompt for tool permissions if any tool is called, or at least displays normal execution logs.

- [ ] **Step 2: Modify scratch/run_loop.py**

Replace lines 17-25 in `scratch/run_loop.py` to add `"--dangerously-skip-permissions"` argument to the `agy` command list.

Code modification:
```python
        process = subprocess.run(
            ["agy", "--print", prompt, "--dangerously-skip-permissions"], # --printオプションを指定して非対話実行
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            check=True
        )
```

- [ ] **Step 3: Run run_loop.py to verify it works without prompting**

Run:
```pwsh
python scratch/run_loop.py "hello とだけ出力してください。"
```
Expected: Executes and terminates successfully with output from agy, rendered by rich_renderer.py.

- [ ] **Step 4: Commit changes**

Run:
```bash
git add scratch/run_loop.py
git commit -m "feat: add --dangerously-skip-permissions to run_loop.py"
```

---

### Task 2: Modify agy_chat.py

**Files:**
- Modify: `scratch/agy_chat.py:30-35`

- [ ] **Step 1: Check existing agy_chat.py behavior**

Run:
```pwsh
python scratch/agy_chat.py
```
Expected: The interactive chat starts. Type a message like "hello" and verify execution. Quit with `exit`.

- [ ] **Step 2: Modify scratch/agy_chat.py**

Replace lines 30-35 in `scratch/agy_chat.py` to include `"--dangerously-skip-permissions"` in the initial `cmd` list construction.

Code modification:
```python
            # 2. Antigravity CLI (agy) のコマンドライン引数を組み立て
            # 2回目以降は自動的に文脈を引き継ぐフラグを付与（例: --continue）
            cmd = ["agy", "--print", user_input, "--dangerously-skip-permissions"]
            if is_continued:
                cmd.append("--continue")  # 文脈引き継ぎフラグを自動付与
```

- [ ] **Step 3: Run agy_chat.py to verify**

Run:
```pwsh
python scratch/agy_chat.py
```
Type any prompt (e.g. `hello`) and ensure it runs automatically and securely passes the flag to `agy`. Exit using `exit`.

- [ ] **Step 4: Commit changes**

Run:
```bash
git add scratch/agy_chat.py
git commit -m "feat: add --dangerously-skip-permissions to agy_chat.py"
```
