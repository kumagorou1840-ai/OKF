from pathlib import Path

vault = Path(r"G:\マイドライブ\Obsidian_2")
(vault / "templates").mkdir(parents=True, exist_ok=True)
(vault / "00_Inbox" / "processed").mkdir(parents=True, exist_ok=True)
(vault / "01_Contracts").mkdir(parents=True, exist_ok=True)
(vault / "Logs" / "Healing").mkdir(parents=True, exist_ok=True)

# テンプレート
(vault / "templates" / "contract_template.md").write_text('''---
contract_id: "{contract_id}"
property_name: "{property_name}"
room_number: "{room_number}"
tenant_name: "{tenant_name}"
current_rent: {current_rent}
new_rent: {new_rent}
rent_diff: {rent_diff}
renewal_date: "{renewal_date}"
contact: "{contact}"
created_at: "{created_at}"
updated_at: "{updated_at}"
initial_author: "{initial_author}"
last_editor: "{last_editor}"
flag: "{flag}"
---

# 📄 賃貸契約更新シート：{property_name} {room_number}号室
- **契約ID**: {contract_id}
- **入居者名**: {tenant_name} 様
- **新賃料**: {new_rent:,} 円 (差額: {rent_diff:+,} 円)
- **フラグ**: {flag} / **メモ**: {memo}
''', encoding='utf-8')

print('✔ フォルダとテンプレートの自動生成が完了しました！')
