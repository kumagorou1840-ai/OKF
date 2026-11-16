 import html                                                                
    import json                                                                
    import re                                                                  
    import webbrowser                                                          
    from datetime import datetime, timezone, timedelta                         
    from pathlib import Path                                                   
                                                                               
    JST = timezone(timedelta(hours=9))                                         
    BRAIN_DIR = Path(r"C:\Users\PC_User\.gemini\antigravity-cli\brain")        
    HISTORY_DIR = Path(r"C:\Users\PC_User\.gemini\history")                    
    OUTPUT_DIR = Path(r"G:\マイドライブ\Obsidian_2\youyaku")                   
                                                                               
                                                                               
    def parse_iso_to_jst(iso_str: str) -> datetime:                            
        if not iso_str:                                                        
            return datetime.now(JST)                                           
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))            
        return dt.astimezone(JST)                                              
                                                                               
                                                                               
    def extract_user_text(content: str) -> str:                                
        match = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", content,
        re.DOTALL)                                                             
        return match.group(1).strip() if match else content.strip()            
                                                                               
                                                                               
    def clean_arg_path(raw_path: str) -> str:                                  
        if not raw_path:                                                       
            return ""                                                          
        return raw_path.strip('"').replace("\\\\", "\\")                       
                                                                               
                                                                               
    def md_to_simple_html(text: str) -> str:                                   
        escaped = html.escape(text)                                            
        # コードブロック ```...```                                             
        escaped = re.sub(                                                      
            r"```(\w*)\n(.*?)```",                                             
            r'<pre><code>\2</code></pre>',                                     
            escaped,                                                           
            flags=re.DOTALL,                                                   
        )                                                                      
        # インラインコード `...`                                               
        escaped = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", escaped)          
        # 太字 **...**                                                         
        escaped = re.sub(r"\*\*([^\*\n]+)\*\*", r"<strong>\1</strong>",        
        escaped)                                                               
        # 見出し ### / ## / #                                                  
        escaped = re.sub(r"^#### (.*)$", r"<h4>\1</h4>", escaped,              
        flags=re.MULTILINE)                                                    
        escaped = re.sub(r"^### (.*)$", r"<h3>\1</h3>", escaped,               
        flags=re.MULTILINE)                                                    
        escaped = re.sub(r"^## (.*)$", r"<h2>\1</h2>", escaped,                
        flags=re.MULTILINE)                                                    
        return escaped.replace("\n", "<br>\n")                                 
                                                                               
                                                                               
    def collect_daily_data(target_date_str: str):                              
        conversations = []                                                     
        edited_files = []                                                      
                                                                               
        if BRAIN_DIR.exists():                                                 
            for conv_dir in BRAIN_DIR.iterdir():                               
                if not conv_dir.is_dir():                                      
                    continue                                                   
                log_file = conv_dir / ".system_generated" / "logs" /           
                "transcript_full.jsonl"                                        
                if not log_file.exists():                                      
                    log_file = conv_dir / ".system_generated" / "logs" /       
                    "transcript.jsonl"                                         
                if not log_file.exists():                                      
                    continue                                                   
                                                                               
                mtime_jst = datetime.fromtimestamp(log_file.stat().st_mtime,   
                JST).strftime("%Y-%m-%d")                                      
                if mtime_jst != target_date_str:                               
                    continue                                                   
                                                                               
                qa_pairs = []                                                  
                try:                                                           
                    with log_file.open("r", encoding="utf-8") as f:            
                        for line in f:                                         
                            line = line.strip()                                
                            if not line:                                       
                                continue                                       
                            step = json.loads(line)                            
                            step_dt = parse_iso_to_jst(step.get("created_at",  
                            ""))                                               
                            if step_dt.strftime("%Y-%m-%d") != target_date_str:
                                continue                                       
                                                                               
                            step_type = step.get("type")                       
                            source = step.get("source")                        
                            time_str = step_dt.strftime("%H:%M:%S")            
                                                                               
                            if source == "USER_EXPLICIT" and step_type ==      
                            "USER_INPUT":                                      
                                q_text = extract_user_text(step.get("content", 
                                ""))                                           
                                if q_text:                                     
                                    qa_pairs.append({"role": "よっちゃん",     
                                    "time": time_str, "text": q_text})         
                                                                               
                            elif source == "MODEL" and step_type ==            
                            "PLANNER_RESPONSE":                                
                                a_text = (step.get("content") or "").strip()   
                                if a_text:                                     
                                    qa_pairs.append({"role": "AI", "time":     
                                    time_str, "text": a_text})                 
                                                                               
                                for tc in step.get("tool_calls", []):          
                                    tool_name = tc.get("name", "")             
                                    if tool_name in ("write_file",             
                                    "edit_file"):                              
                                        file_path =                            
                                        clean_arg_path(tc.get("args",          
                                        {}).get("Path", ""))                   
                                        if file_path:                          
                                            edited_files.append((time_str,     
    tool_name, file_path))                                                     
                except Exception:                                              
                    continue                                                   
                                                                               
                if qa_pairs:                                                   
                    conversations.append({                                     
                        "id": conv_dir.name,                                   
                        "first_time": qa_pairs[0]["time"],                     
                        "messages": qa_pairs,                                  
                    })                                                         
                                                                               
        backup_files = []                                                      
        if HISTORY_DIR.exists():                                               
            for p in HISTORY_DIR.rglob("*"):                                   
                if p.is_file() and ".git" not in p.parts:                      
                    try:                                                       
                        mtime = datetime.fromtimestamp(p.stat().st_mtime, JST) 
                        if mtime.strftime("%Y-%m-%d") == target_date_str:      
                            backup_files.append((mtime.strftime("%H:%M:%S"),   
                            str(p)))                                           
                    except Exception:                                          
                        continue                                               
                                                                               
        conversations.sort(key=lambda x: x["first_time"])                      
        return conversations, edited_files, backup_files                       
                                                                               
                                                                               
    def generate_html(target_date_str: str) -> Path:                           
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)                          
        out_file = OUTPUT_DIR / f"{target_date_str}_Antigravity日報.html"      
                                                                               
        conversations, edited_files, backup_files =                            
        collect_daily_data(target_date_str)                                    
                                                                               
        file_items_html = []                                                   
        for time_str, tool_name, file_path in edited_files:                    
            badge = "新規作成/上書き" if tool_name == "write_file" else        
            "部分編集"                                                         
            file_items_html.append(                                            
                f'<li><span class="time">{time_str}</span> <span               
                class="badge">{badge}</span>                                   
                <code>{html.escape(file_path)}</code></li>'                    
            )                                                                  
        for time_str, b_path in backup_files:                                  
            file_items_html.append(                                            
                f'<li><span class="time">{time_str}</span> <span class="badge  
                backup">バックアップ</span>                                    
                <code>{html.escape(b_path)}</code></li>'                       
            )                                                                  
        files_section = "\n".join(file_items_html) if file_items_html else     
        "<li>本日AIが編集したファイルはありません。</li>"                      
                                                                               
        conv_sections = []                                                     
        for idx, conv in enumerate(conversations, 1):                          
            first_q = next((m["text"].splitlines()[0][:50] for m in            
            conv["messages"] if m["role"] == "よっちゃん"), "会話")            
            msgs_html = []                                                     
            for msg in conv["messages"]:                                       
                is_user = msg["role"] == "よっちゃん"                          
                cls = "msg user" if is_user else "msg ai"                      
                label = "🧑 よっちゃん" if is_user else "🤖 AI"                
                body = md_to_simple_html(msg["text"])                          
                msgs_html.append(                                              
                    f'<div class="{cls}"><div                                  
                    class="msg-header"><strong>{label}</strong> <span          
                    class="time">{msg["time"]}</span></div><div                
                    class="msg-body">{body}</div></div>'                       
                )                                                              
            conv_sections.append(                                              
                f'<section class="card"><h2>{idx}. {html.escape(first_q)}      
                <small>(開始 {conv["first_time"]} / ID:                        
                {conv["id"][:8]})</small></h2>\n'                              
                + "\n".join(msgs_html)                                         
                + "</section>"                                                 
            )                                                                  
                                                                               
        conv_html = "\n".join(conv_sections) if conv_sections else             
        "<p>本日の会話記録はありません。</p>"                                  
                                                                               
        html_doc = f"""<!DOCTYPE html>                                         
    <html lang="ja">                                                           
    <head>                                                                     
    <meta charset="UTF-8">                                                     
    <title>{target_date_str} Antigravity 1日の記録</title>                     
    <style>                                                                    
      body {{ font-family: "Segoe UI", "Meiryo", sans-serif; background:       
      #f4f6f9; color: #222; margin: 0; padding: 24px; }}                       
      .container {{ max-width: 960px; margin: 0 auto; }}                       
      h1 {{ background: #1e293b; color: #fff; padding: 18px 24px;              
      border-radius: 10px; margin-top: 0; }}                                   
      .card {{ background: #fff; border-radius: 10px; padding: 20px;           
      margin-bottom: 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }}          
      h2 {{ margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom:   
      8px; font-size: 1.2rem; color: #0f172a; }}                               
      h2 small {{ color: #64748b; font-weight: normal; font-size: 0.85rem; }}  
      ul.file-list {{ list-style: none; padding: 0; margin: 0; }}              
      ul.file-list li {{ padding: 8px 0; border-bottom: 1px solid #f1f5f9; }}  
      .time {{ color: #64748b; font-family: monospace; font-size: 0.9rem; }}   
      .badge {{ background: #dbeafe; color: #1d4ed8; padding: 2px 8px;         
      border-radius: 4px; font-size: 0.8rem; font-weight: bold; }}             
      .badge.backup {{ background: #fef3c7; color: #b45309; }}                 
      .msg {{ padding: 14px 18px; border-radius: 10px; margin: 12px 0;         
      line-height: 1.6; }}                                                     
      .msg.user {{ background: #eff6ff; border-left: 5px solid #3b82f6; }}     
      .msg.ai {{ background: #f8fafc; border-left: 5px solid #10b981; }}       
      .msg-header {{ margin-bottom: 6px; font-size: 0.95rem; }}                
      code {{ background: #e2e8f0; padding: 2px 6px; border-radius: 4px;       
      font-family: Consolas, monospace; font-size: 0.9em; }}                   
      pre {{ background: #0f172a; color: #f8fafc; padding: 12px; border-radius:
      8px; overflow-x: auto; }}                                                
      pre code {{ background: transparent; color: inherit; padding: 0; }}      
    </style>                                                                   
    </head>                                                                    
    <body>                                                                     
    <div class="container">                                                    
      <h1>📅 {target_date_str} Antigravity 1日の記録（CLI版）</h1>             
      <section class="card">                                                   
        <h2>📝 AIが編集・作成したファイル履歴</h2>                             
        <ul class="file-list">                                                 
          {files_section}                                                      
        </ul>                                                                  
      </section>                                                               
      {conv_html}                                                              
    </div>                                                                     
    </body>                                                                    
    </html>"""                                                                 
                                                                               
        out_file.write_text(html_doc, encoding="utf-8")                        
        return out_file                                                        
                                                                               
                                                                               
    if __name__ == "__main__":                                                 
        today_str = datetime.now(JST).strftime("%Y-%m-%d")                     
        saved_html = generate_html(today_str)                                  
        print(f"Saved HTML: {saved_html}") 