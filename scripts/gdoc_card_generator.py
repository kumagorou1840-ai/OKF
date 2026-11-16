import re, time, urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Set
from pydantic import BaseModel, Field, field_validator
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

GDRIVE_ROOT = Path(r"G:\マイドライブ\MOC")
TARGET_FOLDERS = ["AI_Outputs", "管理", "管理案件", "資料", "思考", "プロジェクト", "書籍", "日記", "notebookLM"]
TARGET_EXTS = {".gdoc", ".pdf"}
WATCH_DIRS = [GDRIVE_ROOT / n for n in TARGET_FOLDERS]
VAULT_ROOT = Path(r"C:\Users\PC_User\Obsidian_2")
CARDS_OUTPUT_DIR = VAULT_ROOT / "03_Resources" / "GDoc_Cards"
MOC_OUTPUT_DIR = VAULT_ROOT / "00_Dashboard"

def scan_existing_notes(vp: Path) -> Set[str]:
    return {p.stem for p in vp.rglob("*.md")} if vp.exists() else set()

class GDocCardSchema(BaseModel):
    title: str = Field(..., min_length=1)
    gdoc_url: str = Field(..., pattern=r"^https://.*")
    file_kind: str = Field(default="Googleドキュメント")
    summary: str = Field(default="（要約未記入）")
    raw_tags: List[str] = Field(default_factory=list, max_length=5)
    existing_notes: Set[str] = Field(default_factory=set)
    resolved_links: List[str] = Field(default_factory=list)

    @field_validator("resolved_links", mode="before")
    @classmethod
    def resolve_links(cls, v, info):
        tags = info.data.get("raw_tags", [])[:5]
        ex = info.data.get("existing_notes", set())
        fmt, seen = [], set()
        for t in tags:
            c = t.replace("#", "").replace("[[", "").replace("]]", "").strip()
            if not c: continue
            tgt = c if c in ex else (f"{c}_MOC" if f"{c}_MOC" in ex or not c.endswith("_MOC") else c)
            if tgt not in seen:
                seen.add(tgt)
                fmt.append(f'"[[{tgt}]]"')
        return fmt if fmt else ['"[[Cockpit_MOC]]"']

class Obsidian2CardManager:
    def __init__(self, vr: Path, cd: Path, md: Path):
        self.vault_root, self.cards_dir, self.moc_dir = vr, cd, md
        cd.mkdir(parents=True, exist_ok=True); md.mkdir(parents=True, exist_ok=True)
    def parse_filename(self, s: str):
        return re.sub(r"\s*#[^\s#]+", "", s).strip(), re.findall(r"#([^\s#]+)", s)[:5]
    def detect_folder_tag(self, p: Path):
        return [n for n in TARGET_FOLDERS if n != "AI_Outputs" and (GDRIVE_ROOT / n) in p.parents][:1]
    def ensure_moc_exists(self, wl: str):
        nn = wl.strip('"').replace("[[", "").replace("]]", "")
        if not nn.endswith("_MOC") or nn in scan_existing_notes(self.vault_root): return
        mp = self.moc_dir / f"{nn}.md"
        now = datetime.now().strftime("%Y-%m-%d")
        f = "`" * 3
        mp.write_text(f'---\ncreated: {now}\ntype: moc\n---\n\n# {nn}\n\n## 紐づくGoogleドキュメント・PDF一覧（自動集約）\n{f}dataview\nTABLE WITHOUT ID\n  "[[" + file.name + "|📝カード]]" AS "詳細",\n  "[🔗 " + file.name + "](" + gdoc_url + ")" AS "Googleドライブ",\n  summary AS "要約",\n  filter(links, (x) => x != this.file.link) AS "他の関連テーマ",\n  dateformat(file.ctime, "yyyy-MM-dd") AS "登録日"\nFROM "03_Resources/GDoc_Cards"\nWHERE type = "gdoc-card" AND contains(links, this.file.link)\nSORT file.ctime DESC\n{f}\n\n## 思考メモ・全体方針\n- \n', encoding="utf-8")
        print(f"[NEW MOC] 新規上位目次を作成しました: {mp.name}")
    def process_file(self, tp: Path):
        ext = tp.suffix.lower()
        if ext not in TARGET_EXTS or tp.stem.startswith(("新規 Google Docs", "無題のドキュメント", "Untitled")): return
        time.sleep(1.5)
        try:
            ct, ft = self.parse_filename(tp.stem)
            tags = (self.detect_folder_tag(tp) + ft)[:5]
            kl = "PDFファイル" if ext == ".pdf" else "Googleドキュメント"
            q = urllib.parse.quote(tp.name if ext == ".pdf" else tp.stem)
            card = GDocCardSchema(title=ct, gdoc_url=f"https://drive.google.com/drive/search?q={q}", file_kind=kl, summary=f"{ct}（{kl}）", raw_tags=tags, existing_notes=scan_existing_notes(self.vault_root), resolved_links=[])
            for l in card.resolved_links: self.ensure_moc_exists(l)
            tmd = self.cards_dir / (re.sub(r'[\\/:*?"<>|]', "_", card.title) + ".md")
            if tmd.exists():
                print(f"[SKIP] 既にカードが存在します: {tmd.name}"); return
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            ly = "\n".join([f"  - {l}" for l in card.resolved_links])
            tmd.write_text(f'---\ncreated: {now}\ntype: gdoc-card\nfile_type: "{ext.lstrip(".")}"\ngdoc_url: "{card.gdoc_url}"\nsummary: "{card.summary}"\nlinks:\n{ly}\n---\n\n# {card.title}\n\n- **{card.file_kind}：** [Googleドライブで開く]({card.gdoc_url})\n- **要約・検索キーワード：** {card.summary}\n\n## 思考メモ・気づき\n- \n', encoding="utf-8")
            print(f"[SUCCESS] 中継カード生成 ({ext}): {tmd.name} -> {card.resolved_links}")
        except Exception as e:
            print(f"[ERROR] {tp.name}: {e}")

class GDocWatcher(FileSystemEventHandler):
    def __init__(self, m): self.m = m
    def on_created(self, e):
        if not e.is_directory and Path(e.src_path).suffix.lower() in TARGET_EXTS: self.m.process_file(Path(e.src_path))
    def on_moved(self, e):
        if not e.is_directory and Path(e.dest_path).suffix.lower() in TARGET_EXTS: self.m.process_file(Path(e.dest_path))

if __name__ == "__main__":
    m = Obsidian2CardManager(VAULT_ROOT, CARDS_OUTPUT_DIR, MOC_OUTPUT_DIR)
    obs = Observer(); ad = []
    for wd in WATCH_DIRS:
        if wd.exists():
            print(f"初回スキャン中: {wd.name}")
            for f in wd.rglob("*"):
                if f.is_file() and f.suffix.lower() in TARGET_EXTS: m.process_file(f)
            obs.schedule(GDocWatcher(m), str(wd), recursive=True); ad.append(wd.name)
    obs.start()
    print(f"複数フォルダ監視開始（{len(ad)}個 / 対象: .gdoc, .pdf / Ctrl+Cで停止）: {', '.join(ad)}")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()
