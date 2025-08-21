#!/usr/bin/env python3
"""
Notion接続テストスクリプト
"""

import os
import streamlit as st
from notion_client import Client
from dotenv import load_dotenv

# .envファイルを読み込み
if os.path.exists('.env'):
    load_dotenv()

def test_notion_connection():
    """Notion接続とデータベースアクセスのテスト"""
    st.title("🔧 Notion接続テスト")
    
    # 環境変数の確認
    st.header("📋 環境変数確認")
    
    # APIキーの確認
    api_key = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
    if api_key:
        st.success(f"✅ APIキー: {api_key[:10]}...")
    else:
        st.error("❌ APIキーが設定されていません")
        st.info("環境変数 NOTION_API_KEY または NOTION_TOKEN を設定してください")
        return
    
    # データベースIDの確認
    node_db_id = os.getenv("NODE_DB_ID") or os.getenv("NOTION_DIAGNOSTIC_DB_ID")
    case_db_id = os.getenv("CASE_DB_ID") or os.getenv("NOTION_REPAIR_CASE_DB_ID")
    item_db_id = os.getenv("ITEM_DB_ID")
    
    st.info(f"📊 診断フローDB: {node_db_id or '未設定'}")
    st.info(f"🔧 修理ケースDB: {case_db_id or '未設定'}")
    st.info(f"  ️ 部品・工具DB: {item_db_id or '未設定'}")
    
    # Notionクライアントの初期化テスト
    st.header("🔌 Notion接続テスト")
    
    try:
        client = Client(auth=api_key)
        st.success("✅ Notionクライアントの初期化に成功しました")
        
        # データベースアクセステスト
        if node_db_id:
            st.subheader("📋 診断フローデータベーステスト")
            try:
                response = client.databases.query(database_id=node_db_id)
                nodes = response.get("results", [])
                st.success(f"✅ 診断フローデータベースにアクセス成功: {len(nodes)}件のノード")
                
                # 最初のノードの詳細を表示
                if nodes:
                    first_node = nodes[0]
                    properties = first_node.get("properties", {})
                    st.json(properties)
                
            except Exception as e:
                st.error(f"❌ 診断フローデータベースアクセス失敗: {e}")
        
        if case_db_id:
            st.subheader("🔧 修理ケースデータベーステスト")
            try:
                response = client.databases.query(database_id=case_db_id)
                cases = response.get("results", [])
                st.success(f"✅ 修理ケースデータベースにアクセス成功: {len(cases)}件のケース")
                
                # 最初のケースの詳細を表示
                if cases:
                    first_case = cases[0]
                    properties = first_case.get("properties", {})
                    st.json(properties)
                
            except Exception as e:
                st.error(f"❌ 修理ケースデータベースアクセス失敗: {e}")
        
        if item_db_id:
            st.subheader("  ️ 部品・工具データベーステスト")
            try:
                response = client.databases.query(database_id=item_db_id)
                items = response.get("results", [])
                st.success(f"✅ 部品・工具データベースにアクセス成功: {len(items)}件のアイテム")
                
                # 最初のアイテムの詳細を表示
                if items:
                    first_item = items[0]
                    properties = first_item.get("properties", {})
                    st.json(properties)
                
            except Exception as e:
                st.error(f"❌ 部品・工具データベースアクセス失敗: {e}")
        
    except Exception as e:
        st.error(f"❌ Notionクライアントの初期化に失敗: {e}")
        st.info("APIキーが正しく設定されているか確認してください")

if __name__ == "__main__":
    test_notion_connection()
