# キャンピングカー修理AIチャットアプリ

キャンピングカーの修理に関する質問にAIが回答するStreamlitアプリケーションです。

## �� クイックスタート

### 方法1: Streamlit Cloud（推奨・本番環境）

1. **GitHubにプッシュ**
   ```bash
   git add .
   git commit -m "Streamlit Cloud用に設定を更新"
   git push origin main
   ```

2. **Streamlit Cloudでデプロイ**
   - https://share.streamlit.io/ にアクセス
   - GitHubアカウントでログイン
   - リポジトリを選択
   - メインファイル: `streamlit_app.py`
   - 環境変数を設定:
     ```
     OPENAI_API_KEY = sk-your-openai-api-key
     NOTION_API_KEY = your-notion-api-key
     NODE_DB_ID = your-notion-node-database-id
     CASE_DB_ID = your-notion-case-database-id
     ```
   - "Deploy!" ボタンをクリック

3. **アクセス**
   ```
   https://your-app-name.streamlit.app
   ```

### 方法2: Windows環境（ローカル開発）

1. **バッチファイルをダブルクリック**
   ```
   start_app.bat
   ```

2. **ブラウザでアクセス**
   ```
   http://localhost:8501
   ```

### 方法3: Pythonスクリプト

1. **起動スクリプトを実行**
   ```bash
   python run_app.py
   ```

2. **ブラウザでアクセス**
   ```
   http://localhost:8501
   ```

### 方法4: 手動起動

1. **依存関係をインストール**
   ```bash
   pip install -r requirements.txt
   ```

2. **Streamlitアプリを起動**
   ```bash
   streamlit run streamlit_app.py
   ```

3. **ブラウザでアクセス**
   ```
   http://localhost:8501
   ```

## ⚙️ 環境設定

### 必須設定

1. **OpenAI APIキーを設定**
   - `env_example.txt`を`.env`にリネーム
   - `OPENAI_API_KEY`に実際のAPIキーを設定

```bash
# .envファイルの例
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Notion連携設定（推奨）

Notionデータベースとの連携により、診断機能が大幅に強化されます。

1. **Notion APIキーを設定**
   ```bash
   # 以下のいずれかの形式で設定
   NOTION_API_KEY=your_notion_integration_token_here
   # または
   NOTION_TOKEN=your_notion_integration_token_here
   ```

2. **データベースIDを設定**
   ```bash
   # 診断フローデータベース（以下のいずれかで設定）
   NODE_DB_ID=your_notion_diagnostic_database_id_here
   # または
   NOTION_DIAGNOSTIC_DB_ID=your_notion_diagnostic_database_id_here
   
   # 修理ケースデータベース（以下のいずれかで設定）
   CASE_DB_ID=your_notion_repair_case_database_id_here
   # または
   NOTION_REPAIR_CASE_DB_ID=your_notion_repair_case_database_id_here
   
   # 部品・工具データベース（オプション）
   ITEM_DB_ID=your_notion_item_database_id_here
   ```

3. **接続テスト**
   ```bash
   streamlit run test_notion_connection.py
   ```

### その他のオプション設定

- **SerpAPI**: 検索機能の追加
- **LangSmith**: 開発・デバッグ支援

## 🔧 機能

- **AI修理アドバイス**: キャンピングカーの修理に関する質問に回答
- **診断システム**: 症状に基づく対話式診断（Notion連携版あり）
- **よくある質問**: 8つのカテゴリのクイック質問
- **自由質問チャット**: カスタム質問への回答
- **Notion連携診断**: リアルタイムでNotionデータベースから診断フローを取得
- **修理ケース検索**: Notionデータベースから関連する修理ケースを自動検索
- **データキャッシュ**: パフォーマンス向上のためのセッションキャッシュ機能
- **修理マニュアル検索**: PDF・テキストファイルからの情報取得

## 📋 システム要件

- Python 3.8以上
- Windows 10/11（ローカル開発）
- インターネット接続

## 🚀 Streamlit Cloud デプロイメント

### 事前準備

1. **GitHubリポジトリの準備**
   - コードをGitHubにプッシュ
   - `streamlit_app.py`がメインファイルとして存在

2. **環境変数の準備**
   - OpenAI APIキー
   - Notion APIキー（オプション）
   - データベースID（オプション）

### デプロイ手順

1. **Streamlit Cloudにアクセス**
   ```
   https://share.streamlit.io/
   ```

2. **リポジトリを選択**
   - GitHubアカウントでログイン
   - 対象リポジトリを選択

3. **設定を入力**
   - **Main file path**: `streamlit_app.py`
   - **Python version**: 3.9以上を選択

4. **環境変数を設定**
   ```
   OPENAI_API_KEY = sk-your-openai-api-key
   NOTION_API_KEY = your-notion-api-key
   NODE_DB_ID = your-notion-node-database-id
   CASE_DB_ID = your-notion-case-database-id
   ```

5. **デプロイ実行**
   - "Deploy!" ボタンをクリック
   - 数分でデプロイ完了

### デプロイ後の確認

✅ **動作確認**
- AIチャット機能
- 症状診断機能
- Notion連携機能

✅ **セキュリティ確認**
- APIキーが正しく設定されているか
- 環境変数が適切に管理されているか

## 🛠️ トラブルシューティング

### アプリが起動しない場合

1. **Pythonバージョンを確認**
   ```bash
   python --version
   ```

2. **依存関係を再インストール**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **環境変数を確認**
   - `.env`ファイルが存在するか確認
   - `OPENAI_API_KEY`が正しく設定されているか確認

4. **ポート8501が使用中の場合**
   ```bash
   streamlit run streamlit_app.py --server.port 8502
   ```

### Streamlit Cloudでの問題

1. **デプロイエラー**
   - ログを確認してエラーメッセージを確認
   - 環境変数が正しく設定されているか確認

2. **依存関係エラー**
   - `requirements.txt`のバージョンを確認
   - 互換性の問題がないか確認

3. **ファイル読み込みエラー**
   - PDFやテキストファイルがリポジトリに含まれているか確認

### よくあるエラー

- **ModuleNotFoundError**: 依存関係が不足
- **ImportError**: ライブラリのバージョン不整合
- **ConnectionError**: インターネット接続の問題

## 📞 サポート

問題が解決しない場合は、以下をご確認ください：

1. **ログの確認**: アプリ起動時のエラーメッセージ
2. **環境変数**: `.env`ファイルの設定
3. **依存関係**: `requirements.txt`の内容

## 🔄 更新履歴

- **v1.0.0**: 初回リリース
- **v1.1.0**: Windows環境対応の改善
- **v1.2.0**: 起動スクリプトの追加
- **v1.3.0**: Streamlit Cloud対応 