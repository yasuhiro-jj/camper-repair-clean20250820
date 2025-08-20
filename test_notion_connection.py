#!/usr/bin/env python3
"""
Notion接続テストスクリプト
"""

import os
import requests
from dotenv import load_dotenv

def test_notion_connection():
    """Notion接続をテスト"""
    print("🔍 Notion接続テスト開始")
    
    # .envファイルを読み込み
    try:
        load_dotenv()
        print("✅ .envファイルを読み込みました")
    except Exception as e:
        print(f"❌ .envファイルの読み込みに失敗: {e}")
        return False
    
    # 環境変数を取得
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DIAGNOSTIC_DB_ID")
    
    print(f"\n📋 環境変数確認:")
    print(f"NOTION_TOKEN: {'✅ 設定済み' if notion_token else '❌ 未設定'}")
    if notion_token:
        print(f"  Token: {notion_token[:10]}...{notion_token[-4:]}")
    
    print(f"NOTION_DIAGNOSTIC_DB_ID: {'✅ 設定済み' if database_id else '❌ 未設定'}")
    if database_id:
        print(f"  DB ID: {database_id}")
    
    if not notion_token or not database_id:
        print("❌ 環境変数が設定されていません")
        return False
    
    # Notion API接続テスト
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    print(f"\n🌐 Notion API接続テスト:")
    print(f"URL: {url}")
    
    try:
        response = requests.post(url, headers=headers, timeout=15)
        print(f"📡 レスポンスステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✅ 接続成功: {len(results)}件のレコードを取得")
            
            # データベースの構造を確認
            if results:
                print(f"\n📊 データベース構造:")
                first_result = results[0]
                properties = first_result.get('properties', {})
                print(f"利用可能なプロパティ: {list(properties.keys())}")
            
            return True
            
        else:
            print(f"❌ APIエラー: {response.status_code}")
            print(f"エラー詳細: {response.text}")
            
            if response.status_code == 401:
                print("🔐 認証エラー: Notionトークンが無効です")
            elif response.status_code == 403:
                print("🚫 権限エラー: データベースへのアクセス権限がありません")
            elif response.status_code == 404:
                print("🔍 データベース未発見: データベースが見つかりません")
            else:
                print(f"❓ 予期しないエラー: {response.status_code}")
            
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ タイムアウトエラー: Notion API接続がタイムアウトしました")
        return False
    except requests.exceptions.ConnectionError:
        print("🌐 接続エラー: Notion APIに接続できません")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}")
        return False

def test_multiple_databases():
    """複数のデータベースIDをテスト"""
    print("\n🔄 複数データベースIDテスト")
    
    database_ids = [
        "24d709bb38f18039a8b3e0bec10bb7eb",
        "24d709bb38f180429ad0c464be9f02cb", 
        "24d709bb38f18066961dd81f3f302307"
    ]
    
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        print("❌ NOTION_TOKENが設定されていません")
        return
    
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    for i, db_id in enumerate(database_ids, 1):
        print(f"\n📋 テスト {i}: データベースID {db_id}")
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        
        try:
            response = requests.post(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"✅ 成功: {len(results)}件のレコード")
            else:
                print(f"❌ 失敗: {response.status_code}")
        except Exception as e:
            print(f"❌ エラー: {str(e)}")

if __name__ == "__main__":
    # 単一データベーステスト
    success = test_notion_connection()
    
    if not success:
        # 複数データベーステスト
        test_multiple_databases()
