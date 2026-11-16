# Obsidian PC-スマホ同期手順メモ（Google Drive + DriveSync）

## 1. フォルダの保存場所
- **PC側:** `G:\マイドライブ\Obsidian_2`
- **スマホ側:** `内部ストレージ/Documents/obsidian_1/Obsidian_2`

## 2. PC側の注意点
- Cドライブ直下ではなく、必ずGoogle Drive（Gドライブ）内の `マイドライブ/Obsidian_2` にデータを配置する。

## 3. スマホ側（DriveSync）の設定
- **同期方式:** 双方向（Two-way）
- **リモートフォルダ:** `/Obsidian_2`
- **ローカルフォルダ:** `/Documents/obsidian_1/Obsidian_2`
- 設定変更後は「状態」タブで同期ボタンを押して「準備完了」にする。

## 4. スマホ側（Obsidian）の開き方
1. 左下メニューの「保管庫の管理（Manage vaults）」を開く。
2. 「Open folder as vault」を選択。
3. `Documents` > `obsidian_1` > `Obsidian_2` を選び、「このフォルダーを使用」をタップ。