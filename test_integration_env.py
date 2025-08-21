#!/usr/bin/env python3
"""
統合システム用環境変数テストスクリプト
"""

import os
from dotenv import load_dotenv

def test_integration_env():
    """統合システム用の環境変数をテスト"""
    print("🔍 統合システム環境変数テスト開始")
    
    # .envファイルを読み込み
    try:
        # .envファイルが存在するかチェック
        if os.path.exists('.env'):
            # 文字エンコーディングを指定して読み込み
            load_dotenv(encoding='utf-8')
            print("✅ .envファイルを読み込みました")
        else:
            print("⚠️ .envファイルが見つかりません")
            print("💡 .envファイルを作成するには:")
            print("   1. env_example.txtを.envにコピー")
            print("   2. 実際のAPIキーとDB IDを設定")
            print("   3. UTF-8エンコーディングで保存")
            print("環境変数はシステム環境から読み込まれます")
    except UnicodeDecodeError as e:
        print(f"❌ .envファイルの文字エンコーディングエラー: {e}")
        print("💡 解決方法: .envファイルをUTF-8エンコーディングで保存してください")
        print("環境変数はシステム環境から読み込まれます")
    except Exception as e:
        print(f"❌ .envファイルの読み込みに失敗: {e}")
        print("環境変数はシステム環境から読み込まれます")
    
    # 必要な環境変数を確認
    required_vars = {
        "NOTION_API_KEY": "Notion APIキー",
        "NODE_DB_ID": "診断フローDB ID",
        "CASE_DB_ID": "修理ケースDB ID", 
        "ITEM_DB_ID": "部品・工具DB ID"
    }
    
    print(f"\n📋 環境変数確認:")
    all_set = True
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        status = "✅ 設定済み" if value else "❌ 未設定"
        print(f"{var_name} ({description}): {status}")
        
        if value:
            if 'KEY' in var_name:
                print(f"  Value: {value[:10]}...{value[-4:]}")
            else:
                print(f"  Value: {value}")
        else:
            all_set = False
    
    # 全Notion関連環境変数を表示
    print(f"\n🌐 全Notion関連環境変数:")
    notion_vars = {k: v for k, v in os.environ.items() if 'NOTION' in k}
    for key, value in notion_vars.items():
        if 'KEY' in key:
            print(f"  {key}: {value[:10]}...{value[-4:]}")
        else:
            print(f"  {key}: {value}")
    
    if all_set:
        print("\n✅ 統合システム用環境変数が正しく設定されています")
        return True
    else:
        print("\n❌ 環境変数の設定が不完全です")
        print("以下の環境変数を設定してください:")
        for var_name, description in required_vars.items():
            if not os.getenv(var_name):
                print(f"  - {var_name}: {description}")
        return False

if __name__ == "__main__":
    test_integration_env()
