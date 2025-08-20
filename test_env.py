#!/usr/bin/env python3
"""
環境変数の読み込みテストスクリプト
"""

import os
from dotenv import load_dotenv

def test_env_loading():
    """環境変数の読み込みをテスト"""
    print("🔍 環境変数読み込みテスト開始")
    
    # .envファイルを読み込み
    try:
        load_dotenv()
        print("✅ .envファイルを読み込みました")
    except Exception as e:
        print(f"❌ .envファイルの読み込みに失敗: {e}")
        return
    
    # Notion関連の環境変数を確認
    notion_token = os.getenv("NOTION_TOKEN")
    notion_db_id = os.getenv("NOTION_DIAGNOSTIC_DB_ID")
    
    print(f"\n📋 環境変数確認:")
    print(f"NOTION_TOKEN: {'✅ 設定済み' if notion_token else '❌ 未設定'}")
    if notion_token:
        print(f"  Token: {notion_token[:10]}...{notion_token[-4:]}")
    
    print(f"NOTION_DIAGNOSTIC_DB_ID: {'✅ 設定済み' if notion_db_id else '❌ 未設定'}")
    if notion_db_id:
        print(f"  DB ID: {notion_db_id}")
    
    # 全環境変数を表示
    print(f"\n🌐 全環境変数:")
    env_vars = {k: v for k, v in os.environ.items() if 'NOTION' in k or 'OPENAI' in k}
    for key, value in env_vars.items():
        if 'TOKEN' in key or 'KEY' in key:
            print(f"  {key}: {value[:10]}...{value[-4:] if len(value) > 14 else ''}")
        else:
            print(f"  {key}: {value}")
    
    if notion_token and notion_db_id:
        print("\n✅ 環境変数が正しく設定されています")
        return True
    else:
        print("\n❌ 環境変数の設定が不完全です")
        return False

if __name__ == "__main__":
    test_env_loading()

