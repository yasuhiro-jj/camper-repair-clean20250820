@echo off
chcp 65001 >nul
echo 🔧 キャンピングカー修理AIチャットアプリ
echo ================================================

REM 現在のディレクトリを確認
echo 📁 現在のディレクトリ: %CD%

REM Pythonがインストールされているかチェック
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Pythonがインストールされていません
    echo Python 3.8以上をインストールしてください
    pause
    exit /b 1
)

echo ✅ Pythonがインストールされています

REM 仮想環境の確認とアクティベート
if exist "venv\Scripts\activate.bat" (
    echo 🔄 仮想環境をアクティベート中...
    call venv\Scripts\activate.bat
    echo ✅ 仮想環境がアクティベートされました
) else (
    echo ⚠️ 仮想環境が見つかりません
    echo システムのPythonを使用します
)

REM 依存関係のインストール
echo 📦 依存関係をチェック中...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ❌ 依存関係のインストールに失敗しました
    echo 手動でインストールしてください: pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✅ 依存関係がインストールされています

REM .envファイルの確認
if exist ".env" (
    echo ✅ .envファイルが見つかりました
) else (
    echo ⚠️ .envファイルが見つかりません
    echo 環境変数を設定してください
)

echo.
echo 🚀 Streamlitアプリを起動中...
echo 📱 ブラウザで http://localhost:8501 にアクセスしてください
echo 🛑 停止するには Ctrl+C を押してください
echo.

REM Streamlitアプリを起動
python -m streamlit run streamlit_app.py --server.port 8501 --server.address localhost --browser.gatherUsageStats false

echo.
echo �� アプリが停止されました
pause
