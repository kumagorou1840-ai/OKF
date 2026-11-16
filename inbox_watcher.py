import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

VAULT_DIR = Path(r"G:\マイドライブ\Obsidian_2")
INBOX_DIR = VAULT_DIR / "00_Inbox"
RUNNER_PATH = VAULT_DIR / "inner_loop_runner.py"

class InboxHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".json"):
            print(f"\n📥 新規JSON検知: {Path(event.src_path).name}")
            time.sleep(0.5)
            subprocess.run(["python", str(RUNNER_PATH)], cwd=str(VAULT_DIR))

if __name__ == "__main__":
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    observer = Observer()
    observer.schedule(InboxHandler(), path=str(INBOX_DIR), recursive=False)
    observer.start()
    print(f"👀 Watchdog 起動中... 監視フォルダ: {INBOX_DIR}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
