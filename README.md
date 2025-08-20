# キャンピングカー修理AIチャットアプリ

キャンピングカーの修理に関する質問にAIが回答するStreamlitアプリケーションです。

## 🚀 クイックスタート

### 方法1: Windows環境（推奨）

1. **バッチファイルをダブルクリック**
   ```
   start_app.bat
   ```

2. **ブラウザでアクセス**
   ```
   http://localhost:8501
   ```

### 方法2: Pythonスクリプト

1. **起動スクリプトを実行**
   ```bash
   python run_app.py
   ```

2. **ブラウザでアクセス**
   ```
   http://localhost:8501
   ```

### 方法3: 手動起動

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

### オプション設定

- **Notion API**: 診断機能の強化
- **SerpAPI**: 検索機能の追加
- **LangSmith**: 開発・デバッグ支援

## 🔧 機能

- **AI修理アドバイス**: キャンピングカーの修理に関する質問に回答
- **診断システム**: 症状に基づく対話式診断
- **よくある質問**: 8つのカテゴリのクイック質問
- **自由質問チャット**: カスタム質問への回答
- **修理マニュアル検索**: PDF・テキストファイルからの情報取得

## 📋 システム要件

- Python 3.8以上
- Windows 10/11（推奨）
- インターネット接続

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