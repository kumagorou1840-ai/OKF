# Rich Markdown Renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python helper script `rich_renderer.py` that reads Markdown with LaTeX equations from standard input and renders it beautifully on the terminal using the `Rich` library.

**Architecture:** A simple Python utility that accepts Markdown text via stdin (piping) or file arguments, custom-parses AI thought blocks (`<thought>...</thought>`), and displays it using `rich.markdown.Markdown` and `rich.console.Console`.

**Tech Stack:** Python 3, `rich` library (already installed in `.venv`).

---

### Task 1: Create Test Data

**Files:**
- Create: `scratch/test_math.md`

- [ ] **Step 1: Write mock Markdown data containing LaTeX equations and thought blocks**
  Write a Markdown file that simulates typical `agy` output, including lists, headers, inline math, math blocks, and `<thought>` tags.

  Create `scratch/test_math.md` with:
  ```markdown
  # 二次関数について

  <thought>
  二次関数 $y = ax^2 + bx + c$ につての基本的な概念と、その平方完成のステップを分かりやすく解説するプランを作成します。
  思考プロセスの枠組みが正しくレンダリングされるかテストするためのブロックです。
  </thought>

  二次関数の標準形は以下の通り定義されます。

  $$
  y = ax^2 + bx + c \quad (a \neq 0)
  $$

  ここで、頂点の座標を求めるためには**平方完成 (Completing the Square)**を行います。

  ### 平方完成の手順
  1. $x$ の項を $a$ でくくります。
     $$ y = a \left( x^2 + \frac{b}{a}x \right) + c $$
  2. カッコ内を平方の形にします。
     $$ y = a \left( x + \frac{b}{2a} \right)^2 - \frac{b^2}{4a} + c $$
  3. よって、頂点は $\left( -\frac{b}{2a}, c - \frac{b^2}{4a} \right)$ となります。
  ```

---

### Task 2: Implement Rich Renderer

**Files:**
- Create: `scratch/rich_renderer.py`

- [ ] **Step 1: Implement the renderer logic**
  Create the python script `scratch/rich_renderer.py` that:
  1. Reads from stdin or file paths.
  2. Dynamically parses and highlights `<thought>` ... `</thought>` blocks.
  3. Renders Markdown via `rich`.

  Create `scratch/rich_renderer.py` with:
  ```python
  import sys
  import re
  from rich.console import Console
  from rich.markdown import Markdown
  from rich.panel import Panel

  def render_thought_and_markdown(text: str, console: Console):
      # <thought>...</thought> ブロックを正規表現で分離
      pattern = re.compile(r'<thought>(.*?)</thought>', re.DOTALL)
      
      last_end = 0
      for match in pattern.finditer(text):
          # thoughtの前の通常のMarkdownを描画
          before_text = text[last_end:match.start()].strip()
          if before_text:
              console.print(Markdown(before_text))
          
          # thoughtブロックを描画（特別なパネルで包む）
          thought_content = match.group(1).strip()
          if thought_content:
              thought_markdown = Markdown(thought_content)
              panel = Panel(
                  thought_markdown,
                  title="[bold yellow]🧠 Thought Process[/bold yellow]",
                  border_style="yellow",
                  expand=False,
                  padding=(1, 2)
              )
              console.print(panel)
              console.print()  # 改行
          
          last_end = match.end()
      
      # 残りのMarkdownを描画
      remaining_text = text[last_end:].strip()
      if remaining_text:
          console.print(Markdown(remaining_text))

  def main():
      console = Console()
      
      # 引数があればファイルから、なければ標準入力から読み込む
      if len(sys.argv) > 1:
          try:
              with open(sys.argv[1], "r", encoding="utf-8") as f:
                  content = f.read()
          except Exception as e:
              console.print(f"[bold red]Error reading file {sys.argv[1]}: {e}[/bold red]")
              sys.exit(1)
      else:
          content = sys.stdin.read()
      
      if not content.strip():
          console.print("[dim]No input received.[/dim]")
          return

      render_thought_and_markdown(content, console)

  if __name__ == "__main__":
      main()
  ```

---

### Task 3: Verification

**Files:**
- Test execution only

- [ ] **Step 1: Verify output using the test mock file**
  Run the renderer using the mock file created in Task 1.
  
  Run: `Get-Content scratch/test_math.md | python scratch/rich_renderer.py`
  Expected output: The mathematical equations, lists, and headings should be formatted nicely. The thought block should be wrapped inside a yellow border box labeled "🧠 Thought Process".
