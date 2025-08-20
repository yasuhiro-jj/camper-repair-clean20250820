#!/usr/bin/env python3
"""
キャンピングカー修理AIチャットアプリ起動スクリプト
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Pythonバージョンをチェック"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8以上が必要です。現在のバージョン:", sys.version)
        return False
    print(f"✅ Pythonバージョン: {sys.version}")
    return True

def check_dependencies():
    """依存関係をチェック"""
    required_packages = [
        'streamlit',
        'langchain',
        'langchain-openai',
        'openai',
        'pandas'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: インストール済み")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}: 未インストール")
    
    if missing_packages:
        print(f"\n⚠️ 不足しているパッケージ: {', '.join(missing_packages)}")
        print("以下のコマンドでインストールしてください:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def install_requirements():
    """requirements.txtから依存関係をインストール"""
    try:
        print("📦 依存関係をインストール中...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依存関係のインストールが完了しました")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依存関係のインストールに失敗しました: {e}")
        return False

def check_env_file():
    """環境変数ファイルをチェック"""
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ {env_file}ファイルが見つかりました")
        return True
    else:
        print(f"⚠️ {env_file}ファイルが見つかりません")
        print("環境変数を設定してください:")
        print("OPENAI_API_KEY=your_openai_api_key")
        print("NOTION_TOKEN=your_notion_token (オプション)")
        print("NOTION_DIAGNOSTIC_DB_ID=your_notion_db_id (オプション)")
        return False

def run_streamlit():
    """Streamlitアプリを起動"""
    try:
        print("🚀 Streamlitアプリを起動中...")
        print("📱 ブラウザで http://localhost:8501 にアクセスしてください")
        print("🛑 停止するには Ctrl+C を押してください")
        
        # Streamlitアプリを起動
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 アプリを停止しました")
    except Exception as e:
        print(f"❌ アプリの起動に失敗しました: {e}")

def main():
    """メイン関数"""
    print("🔧 キャンピングカー修理AIチャットアプリ")
    print("=" * 50)
    
    # Pythonバージョンチェック
    if not check_python_version():
        return
    
    # 依存関係チェック
    if not check_dependencies():
        print("\n📦 依存関係を自動インストールしますか？ (y/n): ", end="")
        if input().lower() == 'y':
            if not install_requirements():
                return
        else:
            return
    
    # 環境変数ファイルチェック
    check_env_file()
    
    print("\n" + "=" * 50)
    
    # Streamlitアプリを起動
    run_streamlit()

if __name__ == "__main__":
    main()
