
## 1. よく使う実装プロンプト
- **新規UIコンポーネント作成**:
  > 「設計ルールに従い、[機能名]用のコンポーネントを作成してください。TypeScript、Tailwind CSS、Shadcn UIを使用し、ローディングとエラー状態も含めてください。」
- **API・Webhook連携処理の実装**:
  > 「[サービス名]と連携する処理を書いてください。二重実行を防ぐ冪等性を確保し、通信エラー時のフォールバック処理を含めてください。」
- **リファクタリング・最適化**:
  > 「以下のコードを単一責務の原則に沿って分割し、共通コンポーネントとして再利用できるように整理してください。」
## 2. 定型コード
- **非同期通信・安全なフェッチ処理（TypeScript/React）**:
  ```typescript
  async function safeFetch<T>(url: string, options?: RequestInit): Promise<{ data: T | null; error: string | null }> {
    try {
      const res = await fetch(url, options);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      return { data, error: null };
    } catch (err) {
      console.error("Fetch failed:", err);
      return { data: null, error: err instanceof Error ? err.message : "Unknown error" };
    }
  }
- 

## 3. データ変換・保存処理
- 

## 4. 外部連携処理
- 

## 5. エラー時の原因調査手順
- 

## 6. 自動復旧・再実行パターン
- 

## 7. 動作確認方法
-