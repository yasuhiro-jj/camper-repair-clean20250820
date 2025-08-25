#!/usr/bin/env python
# -*- coding: utf-8 -*-
import streamlit as st
import os
import re
import subprocess
import sys
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
import json

# 必要なライブラリの自動インストール
def install_required_packages():
    """必要なライブラリを自動インストール"""
    required_packages = [
        "notion-client==2.2.1",
        "python-dotenv"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace("==", "").replace("-", "_"))
        except ImportError:
            # st.info(f"📦 {package}をインストール中...")  # 非表示化
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                # st.success(f"✅ {package}のインストール完了")  # 非表示化
            except subprocess.CalledProcessError:
                st.error(f"❌ {package}のインストールに失敗しました")
                st.info("💡 手動でインストールしてください: pip install notion-client==2.2.1")

# アプリ起動時にライブラリをチェック
install_required_packages()

# .envファイルの読み込みを試行
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    st.warning("python-dotenvがインストールされていません。環境変数を手動で設定します。")

# 環境変数の設定
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = "camper-repair-ai"

# OpenAI APIキーの安全な設定
# 1. 環境変数から取得
# 2. Streamlitシークレットから取得
# 3. どちらもない場合は設定を促す

openai_api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)

if not openai_api_key:
    # APIキーが設定されていない場合は静かに処理を続行
    # 実際のAPI呼び出し時にエラーハンドリングを行う
    st.warning("⚠️ OpenAI APIキーが設定されていません。チャット機能を使用するにはAPIキーを設定してください。")

# 環境変数として設定
os.environ["OPENAI_API_KEY"] = openai_api_key

# Notion APIキーの設定
notion_api_key = st.secrets.get("NOTION_API_KEY") or st.secrets.get("NOTION_TOKEN") or os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")

# NotionDB接続の初期化
def initialize_notion_client():
    """Notionクライアントを初期化（改善版）"""
    try:
        # APIキーの確認
        if not notion_api_key:
            st.error("❌ Notion APIキーが設定されていません")
            st.info("💡 解決方法:")
            st.info("1. .streamlit/secrets.tomlにNOTION_API_KEYを設定")
            st.info("2. 環境変数NOTION_API_KEYを設定")
            st.info("3. Notion統合でAPIキーを生成")
            return None
        
        # APIキーの形式確認
        if not notion_api_key.startswith("secret_") and not notion_api_key.startswith("ntn_"):
            st.warning("⚠️ Notion APIキーの形式が正しくない可能性があります")
            st.info("💡 正しい形式: secret_... または ntn_...")
        
        from notion_client import Client
        client = Client(auth=notion_api_key)
        
        # 接続テスト
        try:
            # ユーザー情報を取得して接続をテスト
            user = client.users.me()
            user_name = user.get('name', 'Unknown User')
            # st.success(f"✅ Notion接続成功: {user_name}")  # 非表示化
            
            # データベースIDの確認
            node_db_id = st.secrets.get("NODE_DB_ID") or st.secrets.get("NOTION_DIAGNOSTIC_DB_ID") or os.getenv("NODE_DB_ID") or os.getenv("NOTION_DIAGNOSTIC_DB_ID")
            case_db_id = st.secrets.get("CASE_DB_ID") or st.secrets.get("NOTION_REPAIR_CASE_DB_ID") or os.getenv("CASE_DB_ID") or os.getenv("NOTION_REPAIR_CASE_DB_ID")
            item_db_id = st.secrets.get("ITEM_DB_ID") or os.getenv("ITEM_DB_ID")
            
            # データベースアクセス権限のテスト
            test_results = []
            
            if node_db_id:
                try:
                    response = client.databases.query(database_id=node_db_id)
                    nodes_count = len(response.get("results", []))
                    test_results.append(f"✅ 診断フローDB: {nodes_count}件のノード")
                except Exception as e:
                    test_results.append(f"❌ 診断フローDB: アクセス失敗 - {str(e)[:100]}")
            
            if case_db_id:
                try:
                    response = client.databases.query(database_id=case_db_id)
                    cases_count = len(response.get("results", []))
                    test_results.append(f"✅ 修理ケースDB: {cases_count}件のケース")
                except Exception as e:
                    test_results.append(f"❌ 修理ケースDB: アクセス失敗 - {str(e)[:100]}")
            
            if item_db_id:
                try:
                    response = client.databases.query(database_id=item_db_id)
                    items_count = len(response.get("results", []))
                    test_results.append(f"✅ 部品・工具DB: {items_count}件のアイテム")
                except Exception as e:
                    test_results.append(f"❌ 部品・工具DB: アクセス失敗 - {str(e)[:100]}")
            
            # テスト結果を表示（非表示化）
            # st.info("📊 データベースアクセステスト:")
            # for result in test_results:
            #     st.write(f"  {result}")
            
            return client
            
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Notion接続テスト失敗: {error_msg}")
            
            # エラーの種類に応じた解決方法を提示
            if "unauthorized" in error_msg.lower() or "401" in error_msg:
                st.info("💡 解決方法: APIキーが無効です。新しいAPIキーを生成してください")
            elif "not_found" in error_msg.lower() or "404" in error_msg:
                st.info("💡 解決方法: データベースIDが間違っているか、アクセス権限がありません")
            elif "rate_limited" in error_msg.lower() or "429" in error_msg:
                st.info("💡 解決方法: API制限に達しました。しばらく待ってから再試行してください")
            else:
                st.info("💡 解決方法: ネットワーク接続とAPIキーの権限を確認してください")
            
            return None
            
    except ImportError as e:
        st.error(f"❌ notion-clientライブラリがインストールされていません: {e}")
        st.info("💡 解決方法: pip install notion-client==2.2.1")
        return None
    except Exception as e:
        st.error(f"❌ Notionクライアントの初期化に失敗: {e}")
        return None

def load_notion_diagnostic_data():
    """Notionから診断データを読み込み（改善版）"""
    client = initialize_notion_client()
    if not client:
        st.error("❌ Notionクライアントの初期化に失敗しました")
        st.info("💡 システム情報タブで接続状況を確認してください")
        return None
    
    try:
        # データベースIDの取得（複数の設定方法に対応）
        node_db_id = st.secrets.get("NODE_DB_ID") or st.secrets.get("NOTION_DIAGNOSTIC_DB_ID") or os.getenv("NODE_DB_ID") or os.getenv("NOTION_DIAGNOSTIC_DB_ID")
        case_db_id = st.secrets.get("CASE_DB_ID") or st.secrets.get("NOTION_REPAIR_CASE_DB_ID") or os.getenv("CASE_DB_ID") or os.getenv("NOTION_REPAIR_CASE_DB_ID")
        item_db_id = st.secrets.get("ITEM_DB_ID") or os.getenv("ITEM_DB_ID")
        
        if not node_db_id:
            st.error("❌ 診断フローDBのIDが設定されていません")
            st.info("💡 解決方法:")
            st.info("1. .streamlit/secrets.tomlにNODE_DB_IDを設定")
            st.info("2. 環境変数NODE_DB_IDを設定")
            st.info("3. NotionデータベースのIDを確認")
            return None
        
        # st.info(f"🔍 診断フローDBに接続中... (ID: {node_db_id[:8]}...)")  # 非表示化

        # Notionから診断フローデータを取得（改善されたエラーハンドリング）
        try:
            response = client.databases.query(database_id=node_db_id)
            nodes = response.get("results", [])
            
            if not nodes:
                st.warning("⚠️ 診断フローDBにデータがありません")
                st.info("💡 Notionデータベースに診断ノードを追加してください")
                return None
                
            # st.success(f"✅ 診断フローDBから{len(nodes)}件のノードを取得しました")  # 非表示化
            
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ 診断フローDBのクエリに失敗: {error_msg}")
            
            # エラーの種類に応じた解決方法を提示
            if "not_found" in error_msg.lower() or "404" in error_msg:
                st.info("💡 解決方法: データベースIDが間違っています")
                st.info(f"   現在のID: {node_db_id}")
                st.info("   NotionでデータベースのIDを確認してください")
            elif "unauthorized" in error_msg.lower() or "401" in error_msg:
                st.info("💡 解決方法: APIキーにデータベースへのアクセス権限がありません")
                st.info("   Notion統合の設定でデータベースへのアクセスを許可してください")
            elif "rate_limited" in error_msg.lower() or "429" in error_msg:
                st.info("💡 解決方法: API制限に達しました。しばらく待ってから再試行してください")
            else:
                st.info("💡 解決方法: ネットワーク接続とAPIキーの権限を確認してください")
            
            return None
        
        diagnostic_data = {
            "nodes": [],
            "start_nodes": []
        }
        
        for node in nodes:
            properties = node.get("properties", {})
            
            # ノードの基本情報を抽出
            node_info = {
                "id": node.get("id"),
                "title": "",
                "category": "",
                "symptoms": [],
                "next_nodes": [],
                "related_cases": [],  # 関連する修理ケース
                "related_items": []   # 関連する部品・工具
            }
            
            # タイトルの抽出
            title_prop = properties.get("タイトル", {})
            if title_prop.get("type") == "title" and title_prop.get("title"):
                node_info["title"] = title_prop["title"][0].get("plain_text", "")
            
            # カテゴリの抽出
            category_prop = properties.get("カテゴリ", {})
            if category_prop.get("type") == "select" and category_prop.get("select"):
                node_info["category"] = category_prop["select"].get("name", "")
            
            # 症状の抽出
            symptoms_prop = properties.get("症状", {})
            if symptoms_prop.get("type") == "multi_select":
                node_info["symptoms"] = [item.get("name", "") for item in symptoms_prop.get("multi_select", [])]
            
            # 関連修理ケースの抽出（リレーション対応）
            cases_prop = properties.get("関連修理ケース", {})
            if cases_prop.get("type") == "relation":
                for relation in cases_prop.get("relation", []):
                    try:
                        case_response = client.pages.retrieve(page_id=relation["id"])
                        case_properties = case_response.get("properties", {})
                        
                        case_info = {
                            "id": relation["id"],
                            "title": "",
                            "category": "",
                            "solution": ""
                        }
                        
                        # ケースタイトルの抽出
                        title_prop = case_properties.get("タイトル", {})
                        if title_prop.get("type") == "title" and title_prop.get("title"):
                            case_info["title"] = title_prop["title"][0].get("plain_text", "")
                        
                        # カテゴリの抽出
                        cat_prop = case_properties.get("カテゴリ", {})
                        if cat_prop.get("type") == "select" and cat_prop.get("select"):
                            case_info["category"] = cat_prop["select"].get("name", "")
                        
                        # 解決方法の抽出
                        solution_prop = case_properties.get("解決方法", {})
                        if solution_prop.get("type") == "rich_text" and solution_prop.get("rich_text"):
                            case_info["solution"] = solution_prop["rich_text"][0].get("plain_text", "")
                        
                        node_info["related_cases"].append(case_info)
                    except Exception as e:
                        st.warning(f"修理ケース情報の取得に失敗: {e}")
            
            # 関連部品・工具の抽出（リレーション対応）
            items_prop = properties.get("関連部品・工具", {})
            if items_prop.get("type") == "relation":
                for relation in items_prop.get("relation", []):
                    try:
                        item_response = client.pages.retrieve(page_id=relation["id"])
                        item_properties = item_response.get("properties", {})
                        
                        item_info = {
                            "id": relation["id"],
                            "name": "",
                            "category": "",
                            "price": "",
                            "supplier": ""
                        }
                        
                        # アイテム名の抽出
                        name_prop = item_properties.get("名前", {})
                        if name_prop.get("type") == "title" and name_prop.get("title"):
                            item_info["name"] = name_prop["title"][0].get("plain_text", "")
                        
                        # カテゴリの抽出
                        cat_prop = item_properties.get("カテゴリ", {})
                        if cat_prop.get("type") == "select" and cat_prop.get("select"):
                            item_info["category"] = cat_prop["select"].get("name", "")
                        
                        # 価格の抽出
                        price_prop = item_properties.get("価格", {})
                        if price_prop.get("type") == "number":
                            item_info["price"] = str(price_prop.get("number", ""))
                        
                        # サプライヤーの抽出
                        supplier_prop = item_properties.get("サプライヤー", {})
                        if supplier_prop.get("type") == "rich_text" and supplier_prop.get("rich_text"):
                            item_info["supplier"] = supplier_prop["rich_text"][0].get("plain_text", "")
                        
                        node_info["related_items"].append(item_info)
                    except Exception as e:
                        st.warning(f"部品・工具情報の取得に失敗: {e}")
            
            diagnostic_data["nodes"].append(node_info)
            
            # 開始ノードの判定
            if node_info["category"] == "開始":
                diagnostic_data["start_nodes"].append(node_info)
        
        return diagnostic_data
        
    except Exception as e:
        st.error(f"❌ Notionからの診断データ読み込みに失敗: {e}")
        return None

def perform_detailed_notion_test():
    """詳細なNotion接続テストを実行"""
    test_results = {
        "overall_success": False,
        "databases": {},
        "success_count": 0,
        "total_count": 0
    }
    
    try:
        # クライアント初期化テスト
        client = initialize_notion_client()
        if not client:
            test_results["databases"]["クライアント初期化"] = {
                "status": "error",
                "message": "Notionクライアントの初期化に失敗",
                "solution": "APIキーの形式と権限を確認してください"
            }
            return test_results
        
        test_results["databases"]["クライアント初期化"] = {
            "status": "success",
            "message": "Notionクライアントの初期化に成功"
        }
        test_results["success_count"] += 1
        test_results["total_count"] += 1
        
        # データベースIDの取得
        node_db_id = st.secrets.get("NODE_DB_ID") or st.secrets.get("NOTION_DIAGNOSTIC_DB_ID") or os.getenv("NODE_DB_ID") or os.getenv("NOTION_DIAGNOSTIC_DB_ID")
        case_db_id = st.secrets.get("CASE_DB_ID") or st.secrets.get("NOTION_REPAIR_CASE_DB_ID") or os.getenv("CASE_DB_ID") or os.getenv("NOTION_REPAIR_CASE_DB_ID")
        item_db_id = st.secrets.get("ITEM_DB_ID") or os.getenv("ITEM_DB_ID")
        
        # 診断フローDBテスト
        if node_db_id:
            test_results["total_count"] += 1
            try:
                response = client.databases.query(database_id=node_db_id)
                nodes = response.get("results", [])
                if nodes:
                    test_results["databases"]["診断フローDB"] = {
                        "status": "success",
                        "message": f"{len(nodes)}件のノードを取得"
                    }
                    test_results["success_count"] += 1
                else:
                    test_results["databases"]["診断フローDB"] = {
                        "status": "warning",
                        "message": "データベースにアクセス可能だが、データがありません",
                        "solution": "Notionデータベースに診断ノードを追加してください"
                    }
            except Exception as e:
                error_msg = str(e)
                if "not_found" in error_msg.lower() or "404" in error_msg:
                    solution = "データベースIDが間違っています。NotionでデータベースのIDを確認してください"
                elif "unauthorized" in error_msg.lower() or "401" in error_msg:
                    solution = "APIキーにデータベースへのアクセス権限がありません。Notion統合の設定を確認してください"
                else:
                    solution = "ネットワーク接続とAPIキーの権限を確認してください"
                
                test_results["databases"]["診断フローDB"] = {
                    "status": "error",
                    "message": f"アクセス失敗: {error_msg[:100]}",
                    "solution": solution
                }
        else:
            test_results["databases"]["診断フローDB"] = {
                "status": "error",
                "message": "データベースIDが設定されていません",
                "solution": ".streamlit/secrets.tomlにNODE_DB_IDを設定してください"
            }
        
        # 修理ケースDBテスト
        if case_db_id:
            test_results["total_count"] += 1
            try:
                response = client.databases.query(database_id=case_db_id)
                cases = response.get("results", [])
                if cases:
                    test_results["databases"]["修理ケースDB"] = {
                        "status": "success",
                        "message": f"{len(cases)}件のケースを取得"
                    }
                    test_results["success_count"] += 1
                else:
                    test_results["databases"]["修理ケースDB"] = {
                        "status": "warning",
                        "message": "データベースにアクセス可能だが、データがありません",
                        "solution": "Notionデータベースに修理ケースを追加してください"
                    }
            except Exception as e:
                error_msg = str(e)
                if "not_found" in error_msg.lower() or "404" in error_msg:
                    solution = "データベースIDが間違っています。NotionでデータベースのIDを確認してください"
                elif "unauthorized" in error_msg.lower() or "401" in error_msg:
                    solution = "APIキーにデータベースへのアクセス権限がありません。Notion統合の設定を確認してください"
                else:
                    solution = "ネットワーク接続とAPIキーの権限を確認してください"
                
                test_results["databases"]["修理ケースDB"] = {
                    "status": "error",
                    "message": f"アクセス失敗: {error_msg[:100]}",
                    "solution": solution
                }
        else:
            test_results["databases"]["修理ケースDB"] = {
                "status": "error",
                "message": "データベースIDが設定されていません",
                "solution": ".streamlit/secrets.tomlにCASE_DB_IDを設定してください"
            }
        
        # 部品・工具DBテスト
        if item_db_id:
            test_results["total_count"] += 1
            try:
                response = client.databases.query(database_id=item_db_id)
                items = response.get("results", [])
                if items:
                    test_results["databases"]["部品・工具DB"] = {
                        "status": "success",
                        "message": f"{len(items)}件のアイテムを取得"
                    }
                    test_results["success_count"] += 1
                else:
                    test_results["databases"]["部品・工具DB"] = {
                        "status": "warning",
                        "message": "データベースにアクセス可能だが、データがありません",
                        "solution": "Notionデータベースに部品・工具を追加してください"
                    }
            except Exception as e:
                error_msg = str(e)
                if "not_found" in error_msg.lower() or "404" in error_msg:
                    solution = "データベースIDが間違っています。NotionでデータベースのIDを確認してください"
                elif "unauthorized" in error_msg.lower() or "401" in error_msg:
                    solution = "APIキーにデータベースへのアクセス権限がありません。Notion統合の設定を確認してください"
                else:
                    solution = "ネットワーク接続とAPIキーの権限を確認してください"
                
                test_results["databases"]["部品・工具DB"] = {
                    "status": "error",
                    "message": f"アクセス失敗: {error_msg[:100]}",
                    "solution": solution
                }
        else:
            test_results["databases"]["部品・工具DB"] = {
                "status": "error",
                "message": "データベースIDが設定されていません",
                "solution": ".streamlit/secrets.tomlにITEM_DB_IDを設定してください"
            }
        
        # 全体の成功判定
        if test_results["success_count"] > 0:
            test_results["overall_success"] = True
        
        return test_results
        
    except Exception as e:
        test_results["databases"]["全体テスト"] = {
            "status": "error",
            "message": f"テスト実行エラー: {str(e)}",
            "solution": "システムエラーが発生しました。アプリケーションを再起動してください"
        }
        return test_results

def load_notion_repair_cases():
    """Notionから修理ケースデータを読み込み（リレーション対応）"""
    client = initialize_notion_client()
    if not client:
        return []
    
    try:
        case_db_id = st.secrets.get("CASE_DB_ID") or st.secrets.get("NOTION_REPAIR_CASE_DB_ID") or os.getenv("CASE_DB_ID") or os.getenv("NOTION_REPAIR_CASE_DB_ID")
        if not case_db_id:
            return []
        
        # Notionから修理ケースを取得
        response = client.databases.query(database_id=case_db_id)
        cases = response.get("results", [])
        
        repair_cases = []
        
        for case in cases:
            properties = case.get("properties", {})
            
            case_info = {
                "id": case.get("id"),
                "title": "",
                "category": "",
                "symptoms": [],
                "solution": "",
                "parts": [],
                "tools": [],
                "related_nodes": [],  # 関連する診断ノード
                "related_items": []   # 関連する部品・工具
            }
            
            # タイトルの抽出
            title_prop = properties.get("タイトル", {})
            if title_prop.get("type") == "title" and title_prop.get("title"):
                case_info["title"] = title_prop["title"][0].get("plain_text", "")
            
            # カテゴリの抽出
            category_prop = properties.get("カテゴリ", {})
            if category_prop.get("type") == "select" and category_prop.get("select"):
                case_info["category"] = category_prop["select"].get("name", "")
            
            # 症状の抽出
            symptoms_prop = properties.get("症状", {})
            if symptoms_prop.get("type") == "multi_select":
                case_info["symptoms"] = [item.get("name", "") for item in symptoms_prop.get("multi_select", [])]
            
            # 解決方法の抽出
            solution_prop = properties.get("解決方法", {})
            if solution_prop.get("type") == "rich_text" and solution_prop.get("rich_text"):
                case_info["solution"] = solution_prop["rich_text"][0].get("plain_text", "")
            
            # 必要な部品の抽出（リレーション対応）
            parts_prop = properties.get("必要な部品", {})
            if parts_prop.get("type") == "relation":
                # リレーションから部品情報を取得
                for relation in parts_prop.get("relation", []):
                    try:
                        item_response = client.pages.retrieve(page_id=relation["id"])
                        item_properties = item_response.get("properties", {})
                        
                        item_info = {
                            "id": relation["id"],
                            "name": "",
                            "category": "",
                            "price": "",
                            "supplier": ""
                        }
                        
                        # 部品名の抽出
                        name_prop = item_properties.get("名前", {})
                        if name_prop.get("type") == "title" and name_prop.get("title"):
                            item_info["name"] = name_prop["title"][0].get("plain_text", "")
                        
                        # カテゴリの抽出
                        cat_prop = item_properties.get("カテゴリ", {})
                        if cat_prop.get("type") == "select" and cat_prop.get("select"):
                            item_info["category"] = cat_prop["select"].get("name", "")
                        
                        # 価格の抽出
                        price_prop = item_properties.get("価格", {})
                        if price_prop.get("type") == "number":
                            item_info["price"] = str(price_prop.get("number", ""))
                        
                        # サプライヤーの抽出
                        supplier_prop = item_properties.get("サプライヤー", {})
                        if supplier_prop.get("type") == "rich_text" and supplier_prop.get("rich_text"):
                            item_info["supplier"] = supplier_prop["rich_text"][0].get("plain_text", "")
                        
                        case_info["related_items"].append(item_info)
                    except Exception as e:
                        st.warning(f"部品情報の取得に失敗: {e}")
            elif parts_prop.get("type") == "multi_select":
                # 従来のmulti_select形式
                case_info["parts"] = [item.get("name", "") for item in parts_prop.get("multi_select", [])]
            
            # 必要な工具の抽出（リレーション対応）
            tools_prop = properties.get("必要な工具", {})
            if tools_prop.get("type") == "relation":
                # リレーションから工具情報を取得
                for relation in tools_prop.get("relation", []):
                    try:
                        item_response = client.pages.retrieve(page_id=relation["id"])
                        item_properties = item_response.get("properties", {})
                        
                        tool_info = {
                            "id": relation["id"],
                            "name": "",
                            "category": "",
                            "price": "",
                            "supplier": ""
                        }
                        
                        # 工具名の抽出
                        name_prop = item_properties.get("名前", {})
                        if name_prop.get("type") == "title" and name_prop.get("title"):
                            tool_info["name"] = name_prop["title"][0].get("plain_text", "")
                        
                        # カテゴリの抽出
                        cat_prop = item_properties.get("カテゴリ", {})
                        if cat_prop.get("type") == "select" and cat_prop.get("select"):
                            tool_info["category"] = cat_prop["select"].get("name", "")
                        
                        # 価格の抽出
                        price_prop = item_properties.get("価格", {})
                        if price_prop.get("type") == "number":
                            tool_info["price"] = str(price_prop.get("number", ""))
                        
                        # サプライヤーの抽出
                        supplier_prop = item_properties.get("サプライヤー", {})
                        if supplier_prop.get("type") == "rich_text" and supplier_prop.get("rich_text"):
                            tool_info["supplier"] = supplier_prop["rich_text"][0].get("plain_text", "")
                        
                        case_info["related_items"].append(tool_info)
                    except Exception as e:
                        st.warning(f"工具情報の取得に失敗: {e}")
            elif tools_prop.get("type") == "multi_select":
                # 従来のmulti_select形式
                case_info["tools"] = [item.get("name", "") for item in tools_prop.get("multi_select", [])]
            
            # 関連診断ノードの抽出（リレーション対応）
            nodes_prop = properties.get("関連診断ノード", {})
            if nodes_prop.get("type") == "relation":
                for relation in nodes_prop.get("relation", []):
                    try:
                        node_response = client.pages.retrieve(page_id=relation["id"])
                        node_properties = node_response.get("properties", {})
                        
                        node_info = {
                            "id": relation["id"],
                            "title": "",
                            "category": "",
                            "symptoms": []
                        }
                        
                        # ノードタイトルの抽出
                        title_prop = node_properties.get("タイトル", {})
                        if title_prop.get("type") == "title" and title_prop.get("title"):
                            node_info["title"] = title_prop["title"][0].get("plain_text", "")
                        
                        # カテゴリの抽出
                        cat_prop = node_properties.get("カテゴリ", {})
                        if cat_prop.get("type") == "select" and cat_prop.get("select"):
                            node_info["category"] = cat_prop["select"].get("name", "")
                        
                        # 症状の抽出
                        symptoms_prop = node_properties.get("症状", {})
                        if symptoms_prop.get("type") == "multi_select":
                            node_info["symptoms"] = [item.get("name", "") for item in symptoms_prop.get("multi_select", [])]
                        
                        case_info["related_nodes"].append(node_info)
                    except Exception as e:
                        st.warning(f"診断ノード情報の取得に失敗: {e}")
            
            repair_cases.append(case_info)
        
        return repair_cases
        
    except Exception as e:
        st.error(f"❌ Notionからの修理ケース読み込みに失敗: {e}")
        return []

# 知識ベースの読み込み
def load_knowledge_base():
    """テキストファイルから知識ベースを読み込み"""
    knowledge_base = {}
    
    # テキストファイルのリスト
    text_files = [
        "インバーター.txt", "バッテリー.txt", "水道ポンプ.txt", "冷蔵庫.txt",
        "車体外装の破損.txt", "ウインドウ.txt", "排水タンク.txt", "雨漏り.txt",
        "外部電源.txt", "家具.txt", "ルーフベント　換気扇.txt", "電装系.txt",
        "FFヒーター.txt", "ガスコンロ.txt", "トイレ.txt", "室内LED.txt",
        "ソーラーパネル.txt", "異音.txt"
    ]
    
    for file_name in text_files:
        if os.path.exists(file_name):
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # ファイル名からカテゴリを抽出
                category = file_name.replace('.txt', '')
                knowledge_base[category] = content
                
            except Exception as e:
                st.error(f"ファイル読み込みエラー {file_name}: {e}")
    
    return knowledge_base

def extract_relevant_knowledge(query, knowledge_base):
    """クエリに関連する知識を抽出"""
    query_lower = query.lower()
    relevant_content = []
    
    # キーワードマッピング
    keyword_mapping = {
        "インバーター": ["インバーター", "DC-AC", "正弦波", "電源変換"],
        "バッテリー": ["バッテリー", "サブバッテリー", "充電", "電圧"],
        "トイレ": ["トイレ", "カセット", "マリン", "フラッパー"],
        "ルーフベント": ["ルーフベント", "換気扇", "マックスファン", "ファン"],
        "水道": ["水道", "ポンプ", "給水", "水"],
        "冷蔵庫": ["冷蔵庫", "冷凍", "コンプレッサー"],
        "ガス": ["ガス", "コンロ", "ヒーター", "FF"],
        "電気": ["電気", "LED", "照明", "電装"],
        "雨漏り": ["雨漏り", "防水", "シール"],
        "異音": ["異音", "音", "騒音", "振動"]
    }
    
    # 関連カテゴリを特定
    relevant_categories = []
    for category, keywords in keyword_mapping.items():
        for keyword in keywords:
            if keyword in query_lower:
                relevant_categories.append(category)
                break
    
    # 関連コンテンツを抽出
    for category in relevant_categories:
        if category in knowledge_base:
            content = knowledge_base[category]
            
            # トラブル事例を抽出
            case_pattern = r'## 【Case.*?】.*?(?=##|$)'
            cases = re.findall(case_pattern, content, re.DOTALL)
            
            for case in cases:
                if any(keyword in case.lower() for keyword in query_lower.split()):
                    relevant_content.append(f"【{category}】\n{case}")
    
    return relevant_content

def extract_urls_from_text(content):
    """テキストからURLを抽出"""
    import re
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, content)
    return urls

def determine_blog_category(blog, query):
    """ブログのカテゴリーを判定"""
    query_lower = query.lower()
    title_lower = blog['title'].lower()
    url_lower = blog['url'].lower()
    keywords_lower = [kw.lower() for kw in blog['keywords']]
    
    # インバーター関連
    if any(keyword in query_lower for keyword in ['インバーター', 'inverter', 'dc-ac', '正弦波', '電源変換']):
        if any(keyword in title_lower or keyword in url_lower or keyword in keywords_lower 
               for keyword in ['インバーター', 'inverter', '正弦波', '矩形波', 'dc-ac']):
            return "🔌 インバーター関連"
    
    # バッテリー関連
    if any(keyword in query_lower for keyword in ['バッテリー', 'battery', '充電', '電圧']):
        if any(keyword in title_lower or keyword in url_lower or keyword in keywords_lower 
               for keyword in ['バッテリー', 'battery', '充電', '電圧', 'agm', 'リチウム']):
            return "🔋 バッテリー関連"
    
    # 水道ポンプ関連
    if any(keyword in query_lower for keyword in ['水道', 'ポンプ', 'water', 'pump', '給水']):
        if any(keyword in title_lower or keyword in url_lower or keyword in keywords_lower 
               for keyword in ['水道', 'ポンプ', 'water', 'pump', '給水']):
            return "💧 水道・ポンプ関連"
    
    # 雨漏り関連
    if any(keyword in query_lower for keyword in ['雨漏り', 'rain', 'leak', '防水', 'シール']):
        if any(keyword in title_lower or keyword in url_lower or keyword in keywords_lower 
               for keyword in ['雨漏り', 'rain', 'leak', '防水', 'シール']):
            return "🌧️ 雨漏り・防水関連"
    
    # 電気・電装系関連
    if any(keyword in query_lower for keyword in ['電気', '電装', 'electrical', 'led', '照明']):
        if any(keyword in title_lower or keyword in url_lower or keyword in keywords_lower 
               for keyword in ['電気', '電装', 'electrical', 'led', '照明']):
            return "⚡ 電気・電装系関連"
    
    # 冷蔵庫関連
    if any(keyword in query_lower for keyword in ['冷蔵庫', '冷凍', 'コンプレッサー']):
        if any(keyword in title_lower or keyword in url_lower or keyword in keywords_lower 
               for keyword in ['冷蔵庫', '冷凍', 'コンプレッサー']):
            return "❄️ 冷蔵庫・冷凍関連"
    
    # ガス関連
    if any(keyword in query_lower for keyword in ['ガス', 'gas', 'コンロ', 'ヒーター', 'ff']):
        if any(keyword in title_lower or keyword in url_lower or keyword in keywords_lower 
               for keyword in ['ガス', 'gas', 'コンロ', 'ヒーター', 'ff']):
            return "🔥 ガス・ヒーター関連"
    
    # トイレ関連
    if any(keyword in query_lower for keyword in ['トイレ', 'toilet', 'カセット', 'マリン']):
        if any(keyword in title_lower or keyword in url_lower or keyword in keywords_lower 
               for keyword in ['トイレ', 'toilet', 'カセット', 'マリン']):
            return "🚽 トイレ関連"
    
    # ルーフベント関連
    if any(keyword in query_lower for keyword in ['ルーフベント', '換気扇', 'ファン', 'vent']):
        if any(keyword in title_lower or keyword in url_lower or keyword in keywords_lower 
               for keyword in ['ルーフベント', '換気扇', 'ファン', 'vent']):
            return "💨 ルーフベント・換気扇関連"
    
    # 異音・騒音関連
    if any(keyword in query_lower for keyword in ['異音', '騒音', '音', '振動', 'noise']):
        if any(keyword in title_lower or keyword in url_lower or keyword in keywords_lower 
               for keyword in ['異音', '騒音', '音', '振動', 'noise']):
            return "🔊 異音・騒音関連"
    
    # 基本修理・メンテナンス関連
    if any(keyword in query_lower for keyword in ['修理', 'メンテナンス', 'repair', 'maintenance']):
        if any(keyword in title_lower or keyword in url_lower or keyword in keywords_lower 
               for keyword in ['修理', 'メンテナンス', 'repair', 'maintenance']):
            return "🔧 基本修理・メンテナンス関連"
    
    # デフォルトカテゴリー
    return "📚 その他関連記事"

def determine_query_category(query):
    """クエリのカテゴリーを判定"""
    query_lower = query.lower()
    
    # インバーター関連
    if any(keyword in query_lower for keyword in ['インバーター', 'inverter', 'dc-ac', '正弦波', '電源変換']):
        return "🔌 インバーター関連"
    
    # バッテリー関連
    if any(keyword in query_lower for keyword in ['バッテリー', 'battery', '充電', '電圧']):
        return "🔋 バッテリー関連"
    
    # 水道ポンプ関連
    if any(keyword in query_lower for keyword in ['水道', 'ポンプ', 'water', 'pump', '給水']):
        return "💧 水道・ポンプ関連"
    
    # 雨漏り関連
    if any(keyword in query_lower for keyword in ['雨漏り', 'rain', 'leak', '防水', 'シール']):
        return "🌧️ 雨漏り・防水関連"
    
    # 電気・電装系関連
    if any(keyword in query_lower for keyword in ['電気', '電装', 'electrical', 'led', '照明']):
        return "⚡ 電気・電装系関連"
    
    # 冷蔵庫関連
    if any(keyword in query_lower for keyword in ['冷蔵庫', '冷凍', 'コンプレッサー']):
        return "❄️ 冷蔵庫・冷凍関連"
    
    # ガス関連
    if any(keyword in query_lower for keyword in ['ガス', 'gas', 'コンロ', 'ヒーター', 'ff']):
        return "🔥 ガス・ヒーター関連"
    
    # トイレ関連
    if any(keyword in query_lower for keyword in ['トイレ', 'toilet', 'カセット', 'マリン']):
        return "🚽 トイレ関連"
    
    # ルーフベント関連
    if any(keyword in query_lower for keyword in ['ルーフベント', '換気扇', 'ファン', 'vent']):
        return "💨 ルーフベント・換気扇関連"
    
    # 異音・騒音関連
    if any(keyword in query_lower for keyword in ['異音', '騒音', '音', '振動', 'noise']):
        return "🔊 異音・騒音関連"
    
    # 基本修理・メンテナンス関連
    if any(keyword in query_lower for keyword in ['修理', 'メンテナンス', 'repair', 'maintenance']):
        return "🔧 基本修理・メンテナンス関連"
    
    # デフォルトカテゴリー
    return "📚 その他関連記事"

def get_relevant_blog_links(query, knowledge_base=None):
    """クエリとテキストデータに基づいて関連ブログを返す"""
    query_lower = query.lower()
    
    # 質問から直接キーワードを抽出
    query_keywords = []
    
    # 主要な技術用語を質問から直接抽出
    main_keywords = [
        "バッテリー", "インバーター", "ポンプ", "冷蔵庫", "ヒーター", "コンロ",
        "トイレ", "ルーフベント", "換気扇", "水道", "給水", "排水", "雨漏り",
        "防水", "シーリング", "配線", "電装", "LED", "ソーラーパネル",
        "ガス", "電気", "異音", "振動", "故障", "修理", "メンテナンス",
        "シャワー", "水", "電圧", "充電", "出力", "電源", "音", "騒音"
    ]
    
    for keyword in main_keywords:
        if keyword in query_lower:
            query_keywords.append(keyword)
    
    # トラブル関連キーワードを質問から直接抽出
    trouble_keywords = [
        "水が出ない", "圧力不足", "異音", "過熱", "電圧低下", "充電されない",
        "電源入らない", "出力ゼロ", "水漏れ", "臭い", "ファン故障", "開閉不良",
        "配管漏れ", "雨漏り", "防水", "シール", "音", "騒音", "振動"
    ]
    
    for keyword in trouble_keywords:
        if keyword in query_lower:
            query_keywords.append(keyword)
    
    # テキストデータからキーワードとURLを抽出
    extracted_keywords = []
    extracted_urls = []
    
    if knowledge_base:
        for category, content in knowledge_base.items():
            # カテゴリ名をキーワードとして追加
            if category.lower() in query_lower:
                extracted_keywords.append(category.lower())
            
            # コンテンツから重要なキーワードを抽出
            content_lower = content.lower()
            
            # 技術用語の抽出
            tech_keywords = [
                "バッテリー", "インバーター", "ポンプ", "冷蔵庫", "ヒーター", "コンロ",
                "トイレ", "ルーフベント", "換気扇", "水道", "給水", "排水", "雨漏り",
                "防水", "シーリング", "配線", "電装", "LED", "ソーラーパネル",
                "ガス", "電気", "異音", "振動", "故障", "修理", "メンテナンス"
            ]
            
            for keyword in tech_keywords:
                if keyword in content_lower and keyword in query_lower:
                    extracted_keywords.append(keyword)
            
            # トラブル関連キーワードの抽出
            trouble_keywords = [
                "水が出ない", "圧力不足", "異音", "過熱", "電圧低下", "充電されない",
                "電源入らない", "出力ゼロ", "水漏れ", "臭い", "ファン故障", "開閉不良",
                "配管漏れ", "雨漏り", "防水", "シール", "音", "騒音", "振動"
            ]
            
            for keyword in trouble_keywords:
                if keyword in content_lower and keyword in query_lower:
                    extracted_keywords.append(keyword)
            
            # URLを抽出
            urls = extract_urls_from_text(content)
            for url in urls:
                if url not in extracted_urls:
                    extracted_urls.append(url)
    
    # 質問から抽出したキーワードとテキストデータから抽出したキーワードを結合
    all_keywords = list(set(query_keywords + extracted_keywords))
    
    # 重複を除去
    extracted_keywords = list(set(extracted_keywords))
    
    # テキストデータから抽出したURLを基にブログリンクを生成
    blog_links = []
    
    # 抽出したURLからブログリンクを作成
    for url in extracted_urls:
        # URLにカンマが含まれている場合は分割
        individual_urls = url.split(',')
        
        for individual_url in individual_urls:
            individual_url = individual_url.strip()  # 前後の空白を除去
            if not individual_url:  # 空のURLはスキップ
                continue
                
            # URLから正確なタイトルを推測
            title = ""
            if "water-pump" in individual_url or "水道" in individual_url or "ポンプ" in individual_url:
                title = "水道ポンプ関連記事"
            elif "battery" in individual_url or "バッテリー" in individual_url:
                title = "バッテリー関連記事"
            elif "inverter" in individual_url or "インバーター" in individual_url:
                title = "インバーター関連記事"
            elif "rain-leak" in individual_url or "雨漏り" in individual_url:
                title = "雨漏り関連記事"
            elif "electrical" in individual_url or "電気" in individual_url or "電装" in individual_url:
                title = "電気・電装系関連記事"
            elif "shower" in individual_url:
                title = "シャワー・給水関連記事"
            elif "repair" in individual_url or "修理" in individual_url:
                title = "修理関連記事"
            else:
                title = "キャンピングカー関連記事"
            
            # キーワードを質問のキーワードとテキストデータから抽出したキーワードから設定
            keywords = all_keywords.copy()
            
            blog_links.append({
                "title": title,
                "url": individual_url,
                "keywords": keywords
            })
    
    # 基本的なブログリンクデータベース（フォールバック用）
    fallback_blog_links = [
        {
            "title": "サブバッテリーの種類と選び方",
            "url": "https://camper-repair.net/blog/battery-types/",
            "keywords": ["バッテリー", "AGM", "リチウム", "ニッケル水素", "価格比較", "容量計算", "選び方"]
        },
        {
            "title": "サブバッテリー容量計算のコツ",
            "url": "https://camper-repair.net/battery-selection/",
            "keywords": ["バッテリー", "容量計算", "消費電力", "連続運用", "充電サイクル", "最大負荷"]
        },
        {
            "title": "サブバッテリーの充電方法・充電器比較",
            "url": "https://camper-repair.net/blog/risk1/",
            "keywords": ["バッテリー", "充電方法", "走行充電", "外部電源", "ソーラーパネル", "AC充電器", "DC-DC充電器"]
        },
        {
            "title": "サブバッテリーとインバーターの組み合わせ",
            "url": "https://camper-repair.net/blog/battery-inverter/",
            "keywords": ["バッテリー", "インバーター", "DC-AC変換", "正弦波", "容量選定", "消費電力"]
        },
        {
            "title": "サブバッテリーとソーラーパネルの連携",
            "url": "https://camper-repair.net/blog/battery-solar/",
            "keywords": ["バッテリー", "ソーラーパネル", "充電制御", "MPPTコントローラー", "PWM制御", "発電量"]
        },
        {
            "title": "サブバッテリーの寿命と交換時期",
            "url": "https://camper-repair.net/blog/battery-life/",
            "keywords": ["バッテリー", "寿命", "サイクル回数", "容量低下", "経年劣化", "交換目安"]
        },
        {
            "title": "サブバッテリー運用時の注意点",
            "url": "https://camper-repair.net/blog/battery-care/",
            "keywords": ["バッテリー", "過放電", "過充電", "ショート防止", "ヒューズ", "温度上昇"]
        },
        {
            "title": "サブバッテリーのメンテナンス方法",
            "url": "https://camper-repair.net/battery-selection/",
            "keywords": ["バッテリー", "定期点検", "端子清掃", "バッテリー液", "比重測定", "電圧測定"]
        },
        {
            "title": "サブバッテリーの取り付け・配線例",
            "url": "https://camper-repair.net/blog/risk1/",
            "keywords": ["バッテリー", "取り付け", "配線方法", "配線図", "ヒューズ", "ケーブルサイズ"]
        },
        {
            "title": "サブバッテリーのトラブル・故障事例",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["バッテリー", "故障", "電圧低下", "容量不足", "過放電", "過充電", "膨張"]
        },
        {
            "title": "サブバッテリーの容量アップ・増設術",
            "url": "https://camper-repair.net/battery-selection/",
            "keywords": ["バッテリー", "容量アップ", "増設", "並列接続", "直列接続", "配線図"]
        },
        {
            "title": "サブバッテリーと家庭用家電の利用",
            "url": "https://camper-repair.net/blog/risk1/",
            "keywords": ["バッテリー", "家庭用家電", "インバーター", "消費電力", "冷蔵庫", "電子レンジ", "エアコン"]
        },
        {
            "title": "サブバッテリー残量管理・インジケーター活用",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["バッテリー", "残量管理", "インジケーター", "電圧計", "電流計", "モニター"]
        },
        {
            "title": "サブバッテリーと外部電源切替運用",
            "url": "https://camper-repair.net/battery-selection/",
            "keywords": ["バッテリー", "外部電源", "切替リレー", "優先給電", "AC/DC切替", "手動/自動切替"]
        },
        {
            "title": "サブバッテリーのDIYカスタム事例",
            "url": "https://camper-repair.net/blog/risk1/",
            "keywords": ["バッテリー", "DIY", "カスタム", "容量アップ", "配線見直し", "充電方法"]
        },
        {
            "title": "サブバッテリーの廃棄・リサイクル方法",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["バッテリー", "廃棄", "リサイクル", "回収業者", "鉛バッテリー", "リチウムバッテリー"]
        },
        {
            "title": "サブバッテリー車検・法規制まとめ",
            "url": "https://camper-repair.net/battery-selection/",
            "keywords": ["バッテリー", "車検", "保安基準", "追加装備", "配線基準", "容量制限"]
        },
        {
            "title": "サブバッテリーQ&A・よくある質問集",
            "url": "https://camper-repair.net/blog/risk1/",
            "keywords": ["バッテリー", "Q&A", "FAQ", "容量選定", "充電方法", "運用方法", "DIY"]
        },
        {
            "title": "サブバッテリー運用の体験談・口コミ",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["バッテリー", "体験談", "運用失敗", "成功事例", "トラブル事例", "口コミ"]
        },
        
        # インバーター関連（20テーマ）
        {
            "title": "インバーター完全ガイド",
            "url": "https://camper-repair.net/blog/inverter1/",
            "keywords": ["インバーター", "正弦波", "矩形波", "DC-AC変換", "容量選定", "出力波形", "連続出力"]
        },
        {
            "title": "インバーターの仕組みと役割",
            "url": "https://camper-repair.net/blog/inverter-selection/",
            "keywords": ["インバーター", "変換回路", "DC入力", "AC出力", "電圧変換", "周波数変換", "回路構成"]
        },
        {
            "title": "インバーターの種類と特徴",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["インバーター", "正弦波インバーター", "修正正弦波", "矩形波", "定格容量", "連続出力", "ピーク出力"]
        },
        {
            "title": "インバーター容量の選び方",
            "url": "https://camper-repair.net/blog/inverter1/",
            "keywords": ["インバーター", "容量選定", "必要容量計算", "家電消費電力", "ピーク電力", "同時使用機器"]
        },
        {
            "title": "インバーターの配線・設置方法",
            "url": "https://camper-repair.net/blog/inverter-selection/",
            "keywords": ["インバーター", "配線手順", "接続ケーブル", "端子加工", "アース線", "ヒューズ設置"]
        },
        {
            "title": "インバーター運用時の安全対策",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["インバーター", "安全基準", "ヒューズ設置", "ブレーカー", "アース接続", "ショート対策"]
        },
        {
            "title": "インバーターで使える家電リスト",
            "url": "https://camper-repair.net/blog/inverter1/",
            "keywords": ["インバーター", "家電使用可否", "冷蔵庫", "電子レンジ", "IH調理器", "エアコン", "TV"]
        },
        {
            "title": "インバーターとサブバッテリーの関係",
            "url": "https://camper-repair.net/blog/inverter-selection/",
            "keywords": ["インバーター", "サブバッテリー", "直結接続", "容量配分", "バッテリー消耗", "電圧降下"]
        },
        {
            "title": "インバーター切替運用のポイント",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["インバーター", "外部電源", "切替スイッチ", "サブバッテリー連動", "優先給電", "手動切替"]
        },
        {
            "title": "インバータートラブル事例と対策",
            "url": "https://camper-repair.net/blog/inverter1/",
            "keywords": ["インバーター", "電源入らない", "出力ゼロ", "波形異常", "ヒューズ切れ", "過熱停止"]
        },
        {
            "title": "インバーターの定期メンテナンス",
            "url": "https://camper-repair.net/blog/inverter-selection/",
            "keywords": ["インバーター", "メンテナンス", "定期点検", "端子清掃", "配線緩み", "ヒューズ確認"]
        },
        {
            "title": "インバーター選びの失敗例と注意点",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["インバーター", "容量不足", "波形選定ミス", "安価モデル", "発熱問題", "ノイズ問題"]
        },
        {
            "title": "インバーターと冷蔵庫の相性",
            "url": "https://camper-repair.net/blog/inverter1/",
            "keywords": ["インバーター", "冷蔵庫", "起動電流", "定格消費電力", "コンプレッサー方式", "正弦波必須"]
        },
        {
            "title": "インバーターのノイズ・電波障害対策",
            "url": "https://camper-repair.net/blog/inverter-selection/",
            "keywords": ["インバーター", "ノイズ対策", "電波障害", "出力波形", "アース強化", "配線分離"]
        },
        {
            "title": "インバーターの消費電力と省エネ運用",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["インバーター", "消費電力", "待機電力", "負荷効率", "省エネ家電", "エコ運転"]
        },
        {
            "title": "インバーターのDIY設置手順",
            "url": "https://camper-repair.net/blog/inverter1/",
            "keywords": ["インバーター", "DIY設置", "作業手順", "配線設計", "部品選定", "固定方法"]
        },
        {
            "title": "インバーターの人気モデル比較",
            "url": "https://camper-repair.net/blog/inverter-selection/",
            "keywords": ["インバーター", "人気モデル", "メーカー比較", "スペック比較", "容量別", "波形別"]
        },
        {
            "title": "インバーターと発電機の連携運用",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["インバーター", "発電機", "連動運転", "入力切替", "出力安定", "発電量制御"]
        },
        {
            "title": "インバーターとソーラー発電の組み合わせ",
            "url": "https://camper-repair.net/blog/inverter1/",
            "keywords": ["インバーター", "ソーラーパネル", "チャージコントローラー", "バッテリー充電", "連携運用", "出力安定化"]
        },
        {
            "title": "インバーターの保証・サポート活用法",
            "url": "https://camper-repair.net/blog/inverter-selection/",
            "keywords": ["インバーター", "メーカー保証", "保証期間", "保証内容", "初期不良対応", "修理サポート"]
        },
        
        # 電気・電装系関連
        {
            "title": "電気・電装系トラブル完全ガイド",
            "url": "https://camper-repair.net/blog/electrical/",
            "keywords": ["電気", "電装", "配線", "LED", "照明", "電装系"]
        },
        {
            "title": "ソーラーパネル・電気システム連携",
            "url": "https://camper-repair.net/blog/electrical-solar-panel/",
            "keywords": ["ソーラーパネル", "電気", "発電", "充電", "太陽光", "電装系"]
        },
        
        # 基本修理・メンテナンス
        {
            "title": "基本修理・キャンピングカー修理の基本",
            "url": "https://camper-repair.net/blog/risk1/",
            "keywords": ["修理", "基本", "手順", "工具", "部品", "故障", "メンテナンス"]
        },
        {
            "title": "定期点検・定期点検とメンテナンス",
            "url": "https://camper-repair.net/battery-selection/",
            "keywords": ["点検", "メンテナンス", "定期", "予防", "保守", "チェック", "定期点検"]
        },
        
        # その他のカテゴリ
        {
            "title": "ルーフベント・換気扇の選び方",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["ルーフベント", "換気扇", "ファン", "換気", "ベント"]
        },
        {
            "title": "トイレ・カセットトイレのトラブル対処",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["トイレ", "カセット", "マリン", "フラッパー", "トイレ"]
        },
                 {
             "title": "水道ポンプ・給水システム",
             "url": "https://camper-repair.net/blog/repair1/",
             "keywords": ["水道", "ポンプ", "給水", "水", "水道ポンプ"]
         },
         {
             "title": "水道ポンプ完全ガイド",
             "url": "https://camper-repair.net/blog/water-pump/",
             "keywords": ["水道ポンプ", "給水ポンプ", "ポンプ", "水道", "給水", "水", "圧力", "流量"]
         },
         {
             "title": "水道ポンプの種類と選び方",
             "url": "https://camper-repair.net/blog/water-pump-selection/",
             "keywords": ["水道ポンプ", "種類", "選び方", "圧力式", "流量式", "DCポンプ", "ACポンプ"]
         },
         {
             "title": "水道ポンプの取り付け・設置方法",
             "url": "https://camper-repair.net/blog/water-pump-installation/",
             "keywords": ["水道ポンプ", "取り付け", "設置", "配管", "配線", "固定", "アース"]
         },
         {
             "title": "水道ポンプのトラブル・故障事例",
             "url": "https://camper-repair.net/blog/water-pump-trouble/",
             "keywords": ["水道ポンプ", "故障", "トラブル", "水が出ない", "圧力不足", "異音", "過熱"]
         },
         {
             "title": "水道ポンプのメンテナンス方法",
             "url": "https://camper-repair.net/blog/water-pump-maintenance/",
             "keywords": ["水道ポンプ", "メンテナンス", "定期点検", "清掃", "フィルター", "オイル交換"]
         },
         {
             "title": "水道ポンプとタンクの関係",
             "url": "https://camper-repair.net/blog/water-pump-tank/",
             "keywords": ["水道ポンプ", "タンク", "給水タンク", "容量", "水位", "空焚き防止"]
         },
         {
             "title": "水道ポンプの配管・配線工事",
             "url": "https://camper-repair.net/blog/water-pump-piping/",
             "keywords": ["水道ポンプ", "配管", "配線", "工事", "ケーブル", "ヒューズ", "スイッチ"]
         },
         {
             "title": "水道ポンプの省エネ運用",
             "url": "https://camper-repair.net/blog/water-pump-energy/",
             "keywords": ["水道ポンプ", "省エネ", "消費電力", "効率", "運転時間", "自動停止"]
         },
         {
             "title": "水道ポンプのDIY修理術",
             "url": "https://camper-repair.net/blog/water-pump-diy/",
             "keywords": ["水道ポンプ", "DIY", "修理", "分解", "部品交換", "調整"]
         },
         {
             "title": "水道ポンプの人気モデル比較",
             "url": "https://camper-repair.net/blog/water-pump-comparison/",
             "keywords": ["水道ポンプ", "人気モデル", "比較", "スペック", "価格", "メーカー"]
         },
        {
            "title": "冷蔵庫・冷凍システム",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["冷蔵庫", "冷凍", "コンプレッサー", "冷蔵"]
        },
        {
            "title": "ガスシステム・FFヒーター",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["ガス", "コンロ", "ヒーター", "FF", "ガスシステム"]
        },
        # 雨漏り関連（20テーマ）
        {
            "title": "雨漏り完全ガイド",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["雨漏り", "屋根防水", "シーリング", "パッキン", "ウインドウ周り", "天窓"]
        },
        {
            "title": "雨漏りしやすい箇所と見分け方",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["雨漏り箇所", "屋根継ぎ目", "ウインドウ", "ドア", "ルーフベント", "天窓"]
        },
        {
            "title": "雨漏り点検のコツと頻度",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["雨漏り点検", "目視点検", "シーリングチェック", "パッキン硬化", "隙間確認"]
        },
        {
            "title": "雨漏り応急処置の方法",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["応急処置", "防水テープ", "ブルーシート", "シーリング材", "パテ", "止水スプレー"]
        },
        {
            "title": "雨漏りのDIY補修術",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["DIY補修", "シーリング打ち直し", "防水テープ貼付", "パッキン交換", "コーキング"]
        },
        {
            "title": "プロに依頼するべき雨漏り修理",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["プロ修理", "専門業者", "診断機器", "調査手法", "補修提案", "見積もり"]
        },
        {
            "title": "屋根防水の見直しポイント",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["屋根防水", "防水塗料", "トップコート", "シーリング材", "ジョイント部", "パネル接合部"]
        },
        {
            "title": "シーリング材の選び方と施工",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["シーリング材", "種類比較", "ウレタン系", "シリコン系", "ブチル系", "耐久性"]
        },
        {
            "title": "ウインドウ・天窓の防水対策",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["ウインドウ", "天窓", "ゴムパッキン", "パッキン交換", "シーリング", "結露防止"]
        },
        {
            "title": "ルーフベント・サイドオーニングの漏水防止",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["ルーフベント", "サイドオーニング", "取付部", "シーリング補修", "防水テープ", "構造確認"]
        },
        {
            "title": "配線取り出し部の雨対策",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["配線出口", "グロメット", "パッキン", "シーリング", "経年硬化", "結束バンド"]
        },
        {
            "title": "経年劣化による雨漏り原因",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["経年劣化", "パッキン硬化", "シーリングひび割れ", "コーキング剥がれ", "樹脂部品変形"]
        },
        {
            "title": "雨漏りと結露の違い",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["雨漏り", "結露", "現象比較", "発生タイミング", "場所の違い", "水滴の性状"]
        },
        {
            "title": "カビ・悪臭防止と室内換気",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["カビ", "悪臭", "湿度管理", "雨漏り", "室内換気", "換気扇", "ルーフベント"]
        },
        {
            "title": "雨漏りの再発防止策",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["再発防止", "予防点検", "定期シーリング補修", "パッキン交換", "塗装メンテナンス"]
        },
        {
            "title": "雨漏り補修後の確認ポイント",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["補修確認", "漏水チェック", "水かけ試験", "シーリング乾燥", "補修跡観察"]
        },
        {
            "title": "DIYでできる雨漏り対策グッズ",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["防水テープ", "シーリング材", "パテ", "防水スプレー", "ブルーシート", "コーキングガン"]
        },
        {
            "title": "雨漏りのプロ診断・高精度調査法",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["プロ診断", "散水テスト", "サーモグラフィ", "蛍光剤", "漏水検知機", "音響調査"]
        },
        {
            "title": "雨漏りと保険・保証制度",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["保険適用", "車両保険", "雨漏り補償", "修理保証", "自然災害対応", "補修範囲"]
        },
        {
            "title": "雨漏りトラブル体験談・事例集",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["雨漏り体験談", "修理事例", "失敗例", "DIY体験", "プロ修理体験", "再発例"]
        },
        {
            "title": "雨漏りトラブルを未然に防ぐ習慣",
            "url": "https://camper-repair.net/blog/rain-leak/",
            "keywords": ["予防習慣", "定期点検", "屋根掃除", "排水路確認", "パッキン保湿", "シーリング補修"]
        },
        {
            "title": "異音・騒音対策",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["異音", "音", "騒音", "振動", "ノイズ"]
                 }
     ]
    
    # テキストデータからURLが見つからない場合のみフォールバックを使用
    if not blog_links:
        # フォールバック用のブログリンクを使用
        blog_links = fallback_blog_links
    
    relevant_blogs = []
    for blog in blog_links:
        score = 0
        
        # テキストデータから抽出したURLかどうかを判定
        is_extracted_url = blog["url"] in extracted_urls
        
        # 質問のキーワードとの直接マッチング（最高優先度）
        for query_keyword in query_keywords:
            if query_keyword in blog["title"].lower():
                score += 20  # 質問キーワードがタイトルに含まれる場合は高スコア
            if query_keyword in blog["url"].lower():
                score += 15  # 質問キーワードがURLに含まれる場合も高スコア
            if query_keyword in blog["keywords"]:
                score += 10  # 質問キーワードがキーワードに含まれる場合
        
        # 基本キーワードマッチング
        for keyword in blog["keywords"]:
            if keyword in query_lower:
                score += 1
        
        # テキストデータから抽出したキーワードとのマッチング
        for extracted_keyword in extracted_keywords:
            if extracted_keyword in blog["keywords"]:
                score += 2  # テキストデータからのキーワードは重みを高く
        
        # カテゴリマッチング（より高い重み）
        for extracted_keyword in extracted_keywords:
            if extracted_keyword in blog["title"].lower():
                score += 3
        
        # カテゴリー判定による重み付け
        blog_category = determine_blog_category(blog, query)
        query_category = determine_query_category(query)
        
        # カテゴリーが一致する場合は大幅にスコアを上げる
        if blog_category == query_category:
            score += 10
        
        # テキストデータから抽出したURLの場合は大幅にスコアを上げる
        if is_extracted_url:
            score += 50  # テキストデータからのURLを最優先
        
        if score > 0:
            relevant_blogs.append((blog, score))
    
    relevant_blogs.sort(key=lambda x: x[1], reverse=True)
    
    # テキストデータから抽出したURLを最優先で返す
    result_blogs = []
    added_urls = set()  # 追加済みURLを追跡
    
    # まず、テキストデータから抽出したURLを含むブログを最優先で追加
    for blog, score in relevant_blogs:
        if blog["url"] in extracted_urls and blog["url"] not in added_urls:
            result_blogs.append(blog)
            added_urls.add(blog["url"])
    
    # 次に、その他の関連ブログを追加（重複を避ける）
    for blog, score in relevant_blogs:
        if blog["url"] not in added_urls and len(result_blogs) < 5:
            result_blogs.append(blog)
            added_urls.add(blog["url"])
    
    # 最終的に重複を除去してユニークなURLのみを返す
    final_blogs = []
    final_urls = set()
    
    for blog in result_blogs:
        if blog["url"] not in final_urls:
            final_blogs.append(blog)
            final_urls.add(blog["url"])
    
    # 最大5件まで返す（一つ一つ個別のブログ）
    return final_blogs[:5]

def generate_ai_response_with_knowledge(prompt, knowledge_base):
    """知識ベースを活用したAI回答を生成"""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return "⚠️ **OpenAI APIキーが設定されていません。**\n\nAPIキーを設定してから再度お試しください。\n\n## 🛠️ 岡山キャンピングカー修理サポートセンター\n専門的な修理やメンテナンスが必要な場合は、お気軽にご相談ください：\n\n**🏢 岡山キャンピングカー修理サポートセンター**\n📍 **住所**: 〒700-0921 岡山市北区東古松485-4 2F\n📞 **電話**: 086-206-6622\n📧 **お問合わせ**: https://camper-repair.net/contact/\n🌐 **ホームページ**: https://camper-repair.net/blog/\n⏰ **営業時間**: 年中無休（9:00～21:00）\n※不在時は折り返しお電話差し上げます。\n\n**（運営）株式会社リクエストプラス**"
        
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=openai_api_key
        )
        
        # 関連知識を抽出
        relevant_knowledge = extract_relevant_knowledge(prompt, knowledge_base)
        blog_links = get_relevant_blog_links(prompt, knowledge_base)
        
        # 知識ベースの内容をシステムプロンプトに含める
        knowledge_context = ""
        if relevant_knowledge:
            knowledge_context = "\n\n【関連する専門知識】\n" + "\n\n".join(relevant_knowledge[:3])
        
        system_prompt = f"""あなたは岡山キャンピングカー修理サポートセンターの専門スタッフです。
以下の専門知識ベースを参考にして、具体的で実用的な回答を提供し、必要に応じて当センターへの相談を促してください。

{knowledge_context}

以下の形式で回答してください：

- 問題の詳細な状況を確認
- 安全上の注意点を明示
- 緊急度の判断

1. **応急処置**（必要な場合）
2. **具体的な修理手順**
3. **必要な工具・部品**
4. **予防メンテナンスのアドバイス**
5. **専門家への相談タイミング**
   - 複雑な作業や不安がある場合は、岡山キャンピングカー修理サポートセンターにご相談ください
   - 当センターでは、安全で確実な修理作業を承ります

**重要**: 
- 危険な作業は避け、安全第一で対応してください
- 複雑な問題や電気・ガス関連の作業は専門店への相談を強く推奨します
- 当センターでは、バッテリー・インバーター・電装系・雨漏り・各種家電設備の修理に対応しています
- ご不明な点や不安な場合は、お気軽にご相談ください

ユーザーの質問に基づいて、上記の形式で回答してください。"""

        messages = [
            HumanMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        
        # 岡山キャンピングカー修理サポートセンター情報を追加
        support_section = "\n\n## 🛠️ 岡山キャンピングカー修理サポートセンター\n"
        support_section += "専門的な修理やメンテナンスが必要な場合は、お気軽にご相談ください：\n\n"
        support_section += "**🏢 岡山キャンピングカー修理サポートセンター**\n"
        support_section += "📍 **住所**: 〒700-0921 岡山市北区東古松485-4 2F\n"
        support_section += "📞 **電話**: 086-206-6622\n"
        support_section += "📧 **お問合わせ**: https://camper-repair.net/contact/\n"
        support_section += "🌐 **ホームページ**: https://camper-repair.net/blog/\n"
        support_section += "⏰ **営業時間**: 年中無休（9:00～21:00）\n"
        support_section += "※不在時は折り返しお電話差し上げます。\n\n"
        support_section += "**（運営）株式会社リクエストプラス**\n\n"
        support_section += "**🔧 対応サービス**:\n"
        support_section += "• バッテリー・インバーター修理・交換\n"
        support_section += "• 電気配線・電装系トラブル対応\n"
        support_section += "• 雨漏り・防水工事\n"
        support_section += "• 各種家電・設備の修理\n"
        support_section += "• 定期点検・メンテナンス\n"
        support_section += "• 緊急対応・出張修理（要相談）\n\n"
        support_section += "**💡 ご相談の際は**:\n"
        support_section += "• 車種・年式\n"
        support_section += "• 症状の詳細\n"
        support_section += "• 希望する対応方法\n"
        support_section += "をお教えください。\n\n"
        
        response.content += support_section
        
        # 関連ブログを追加
        if blog_links:
            blog_section = "\n\n## 📚 関連ブログ・参考記事\n"
            blog_section += "より詳しい情報や実践的な対処法については、以下の記事もご参考ください：\n\n"
            
            # デバッグ情報（開発時のみ表示）
            # blog_section += f"**🔍 抽出されたキーワード**: {', '.join(all_keywords[:5])}\n\n"
            
            # 重複するURLを除去して、ユニークなURLのみを表示
            unique_blogs = []
            seen_urls = set()
            
            for blog in blog_links:
                # URLにカンマが含まれている場合は分割
                urls = blog['url'].split(',')
                
                for url in urls:
                    url = url.strip()  # 前後の空白を除去
                    if url and url not in seen_urls:
                        # 分割されたURLごとに個別のブログエントリを作成
                        unique_blogs.append({
                            'title': blog['title'],
                            'url': url,
                            'keywords': blog['keywords']
                        })
                        seen_urls.add(url)
            
            # カテゴリーごとにブログを分類
            categorized_blogs = {}
            for blog in unique_blogs:
                category = determine_blog_category(blog, prompt)
                if category not in categorized_blogs:
                    categorized_blogs[category] = []
                categorized_blogs[category].append(blog)
            
            # カテゴリーごとに表示
            for category, blogs in categorized_blogs.items():
                if blogs:
                    blog_section += f"### {category}\n"
                    for i, blog in enumerate(blogs[:3], 1):  # 各カテゴリー最大3件
                        # テキストデータから抽出したURLかどうかを判定
                        is_extracted = blog['url'] in extracted_urls if 'extracted_urls' in locals() else False
                        source_indicator = "📄" if is_extracted else "📖"
                        blog_section += f"**{i}. {blog['title']}** {source_indicator}\n"
                        blog_section += f"   {blog['url']}\n\n"
            
            response.content += blog_section
        
        return response.content
        
    except Exception as e:
        return f"""⚠️ **エラーが発生しました: {str(e)}**

申し訳ございませんが、一時的に回答を生成できませんでした。
しばらく時間をおいてから再度お試しください。

## 🛠️ 岡山キャンピングカー修理サポートセンター
専門的な修理やメンテナンスが必要な場合は、お気軽にご相談ください：

**🏢 岡山キャンピングカー修理サポートセンター**
📍 **住所**: 〒700-0921 岡山市北区東古松485-4 2F
📞 **電話**: 086-206-6622
📧 **お問合わせ**: https://camper-repair.net/contact/
🌐 **ホームページ**: https://camper-repair.net/blog/
⏰ **営業時間**: 年中無休（9:00～21:00）
※不在時は折り返しお電話差し上げます。

**（運営）株式会社リクエストプラス**

**🔧 対応サービス**:
• バッテリー・インバーター修理・交換
• 電気配線・電装系トラブル対応
• 雨漏り・防水工事
• 各種家電・設備の修理
• 定期点検・メンテナンス
• 緊急対応・出張修理（要相談）"""

def run_diagnostic_flow():
    """対話式症状診断（NotionDB連携版）"""
    st.subheader("🔍 対話式症状診断")
    
    # NotionDBの接続状況を確認
    notion_status = "❌ 未接続"
    diagnostic_data = None
    repair_cases = []
    
    if notion_api_key:
        try:
            diagnostic_data = load_notion_diagnostic_data()
            repair_cases = load_notion_repair_cases()
            if diagnostic_data or repair_cases:
                notion_status = "✅ 接続済み"
            else:
                notion_status = "⚠️ データなし"
        except Exception as e:
            notion_status = f"❌ エラー: {str(e)[:50]}"
    
    # 接続状況を表示（非表示化）
    # st.info(f"**NotionDB接続状況**: {notion_status}")
    
    if notion_status == "❌ 未接続":
        st.warning("NotionDBに接続できません。環境変数の設定を確認してください。")
        st.info("**必要な環境変数**:")
        st.code("NOTION_API_KEY=your_notion_token\nNODE_DB_ID=your_diagnostic_db_id\nCASE_DB_ID=your_repair_case_db_id")
    
    # 診断モードの選択
    diagnostic_mode = st.radio(
        "診断モードを選択してください:",
        ["🤖 AI診断（推奨）", "📋 対話式診断", "🔍 詳細診断"]
    )
    
    if diagnostic_mode == "🤖 AI診断（推奨）":
        run_ai_diagnostic(diagnostic_data, repair_cases)
    elif diagnostic_mode == "📋 対話式診断":
        run_interactive_diagnostic(diagnostic_data, repair_cases)
    else:
        run_detailed_diagnostic(diagnostic_data, repair_cases)

def run_ai_diagnostic(diagnostic_data, repair_cases):
    """AI診断モード（リレーション活用版）"""
    st.markdown("### 🤖 AI診断")
    st.markdown("症状を詳しく説明してください。最適な診断と解決策を提案します。")
    
    # 症状入力
    symptoms_input = st.text_area(
        "症状を詳しく説明してください:",
        placeholder="例: バッテリーの電圧が12V以下に下がって、インバーターが動作しません。充電器を接続しても充電されない状態です。",
        height=150
    )
    
    if st.button("🔍 AI診断開始", type="primary"):
        if symptoms_input.strip():
            with st.spinner("AIがリレーションデータを活用して診断中..."):
                # 知識ベースを読み込み
                knowledge_base = load_knowledge_base()
                
                # リレーションデータを活用した高度なコンテキスト作成
                context = create_relation_context(symptoms_input, diagnostic_data, repair_cases)
                
                # 診断プロンプトを作成
                diagnosis_prompt = f"""症状: {symptoms_input}

{context}

上記の症状について、3つのデータベースのリレーション情報を活用して、以下の形式で詳細な診断と解決策を提供してください：

1. **診断結果**
2. **関連する修理ケース**
3. **必要な部品・工具（価格・サプライヤー情報付き）**
4. **具体的な修理手順**
5. **予防メンテナンスのアドバイス**"""
                
                # AI診断を実行
                diagnosis_result = generate_ai_response_with_knowledge(diagnosis_prompt, knowledge_base)
                
                st.markdown("## 📋 AI診断結果")
                st.markdown(diagnosis_result)
                
                # リレーションデータの詳細表示
                show_relation_details(symptoms_input, diagnostic_data, repair_cases)
        else:
            st.warning("症状を入力してください。")

def create_relation_context(symptoms_input, diagnostic_data, repair_cases):
    """リレーションデータを活用したコンテキストを作成"""
    context = ""
    
    # 症状に基づいて関連する診断ノードを特定
    relevant_nodes = []
    if diagnostic_data and diagnostic_data.get("nodes"):
        for node in diagnostic_data["nodes"]:
            if any(symptom in symptoms_input.lower() for symptom in node.get("symptoms", [])):
                relevant_nodes.append(node)
    
    # 関連する修理ケースを特定
    relevant_cases = []
    for case in repair_cases:
        if any(symptom in symptoms_input.lower() for symptom in case.get("symptoms", [])):
            relevant_cases.append(case)
    
    # コンテキストの構築
    if relevant_nodes:
        context += "\n\n【関連診断ノード】\n"
        for node in relevant_nodes[:3]:
            context += f"- {node['title']} ({node['category']}): {', '.join(node['symptoms'])}\n"
            
            # 関連修理ケースの追加
            if node.get("related_cases"):
                context += "  関連修理ケース:\n"
                for case in node["related_cases"][:2]:
                    context += f"    • {case['title']}: {case['solution'][:100]}...\n"
            
            # 関連部品・工具の追加
            if node.get("related_items"):
                context += "  関連部品・工具:\n"
                for item in node["related_items"][:3]:
                    price_info = f" (¥{item['price']})" if item.get('price') else ""
                    supplier_info = f" - {item['supplier']}" if item.get('supplier') else ""
                    context += f"    • {item['name']}{price_info}{supplier_info}\n"
    
    if relevant_cases:
        context += "\n\n【関連修理ケース】\n"
        for case in relevant_cases[:3]:
            context += f"- {case['title']} ({case['category']}): {case['solution'][:150]}...\n"
            
            # 関連部品・工具の追加
            if case.get("related_items"):
                context += "  必要な部品・工具:\n"
                for item in case["related_items"][:3]:
                    price_info = f" (¥{item['price']})" if item.get('price') else ""
                    supplier_info = f" - {item['supplier']}" if item.get('supplier') else ""
                    context += f"    • {item['name']}{price_info}{supplier_info}\n"
    
    return context

def show_relation_details(symptoms_input, diagnostic_data, repair_cases):
    """リレーションデータの詳細を表示"""
    st.markdown("## 🔗 リレーションデータ詳細")
    
    # 関連診断ノードの表示
    if diagnostic_data and diagnostic_data.get("nodes"):
        relevant_nodes = []
        for node in diagnostic_data["nodes"]:
            if any(symptom in symptoms_input.lower() for symptom in node.get("symptoms", [])):
                relevant_nodes.append(node)
        
        if relevant_nodes:
            st.markdown("### 📊 関連診断ノード")
            for node in relevant_nodes[:3]:
                with st.expander(f"🔹 {node['title']} ({node['category']})"):
                    st.write("**症状**:", ", ".join(node["symptoms"]))
                    
                    if node.get("related_cases"):
                        st.write("**関連修理ケース**:")
                        for case in node["related_cases"][:2]:
                            st.write(f"  • {case['title']}: {case['solution'][:100]}...")
                    
                    if node.get("related_items"):
                        st.write("**関連部品・工具**:")
                        for item in node["related_items"][:3]:
                            price_info = f" (¥{item['price']})" if item.get('price') else ""
                            supplier_info = f" - {item['supplier']}" if item.get('supplier') else ""
                            st.write(f"  • {item['name']}{price_info}{supplier_info}")
    
    # 関連修理ケースの表示
    relevant_cases = []
    for case in repair_cases:
        if any(symptom in symptoms_input.lower() for symptom in case.get("symptoms", [])):
            relevant_cases.append(case)
    
    if relevant_cases:
        st.markdown("### 🔧 関連修理ケース")
        for case in relevant_cases[:3]:
            with st.expander(f"🔧 {case['title']} ({case['category']})"):
                st.write("**症状**:", ", ".join(case["symptoms"]))
                st.write("**解決方法**:", case["solution"])
                
                if case.get("related_items"):
                    st.write("**必要な部品・工具**:")
                    for item in case["related_items"][:5]:
                        price_info = f" (¥{item['price']})" if item.get('price') else ""
                        supplier_info = f" - {item['supplier']}" if item.get('supplier') else ""
                        st.write(f"  • {item['name']}{price_info}{supplier_info}")
                
                if case.get("related_nodes"):
                    st.write("**関連診断ノード**:")
                    for node in case["related_nodes"][:2]:
                        st.write(f"  • {node['title']}: {', '.join(node['symptoms'])}")

def display_blog_links(blog_links, query):
    """関連ブログリンクを表示"""
    if not blog_links:
        st.info("📚 関連するブログ記事が見つかりませんでした")
        return
    
    st.markdown("### 📚 関連ブログ記事")
    st.info(f"「{query}」に関連するブログ記事です")
    
    for i, blog in enumerate(blog_links, 1):
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{i}. {blog['title']}**")
                st.caption(f"関連キーワード: {', '.join(blog['keywords'])}")
            with col2:
                if st.button(f"📖 読む", key=f"blog_{i}"):
                    st.markdown(f"[記事を開く]({blog['url']})")
                    st.info(f"新しいタブで {blog['url']} が開きます")
        
        st.divider()

def run_interactive_diagnostic(diagnostic_data, repair_cases):
    """対話式診断モード（NotionDB活用版）"""
    st.markdown("### 📋 対話式診断")
    
    # NotionDBからカテゴリを取得、または詳細なデフォルトを使用
    if diagnostic_data and diagnostic_data.get("start_nodes"):
        categories = {}
        for node in diagnostic_data["start_nodes"]:
            if node["title"]:
                categories[node["title"]] = node["symptoms"]
        st.success("✅ NotionDBから診断データを読み込みました")
    else:
        # 詳細なデフォルトのカテゴリ（NotionDBが利用できない場合）
        categories = {
            "🔋 バッテリー関連": [
                "電圧が12V以下に低下", "充電されない", "急激な消耗", "バッテリー液の減少",
                "端子の腐食", "充電時の異臭", "バッテリーの膨張", "充電器が動作しない",
                "エンジン始動時の異音", "電装品の動作不良", "バッテリーの温度上昇"
            ],
            "🔌 インバーター関連": [
                "電源が入らない", "出力ゼロ", "異音がする", "過熱する", "LEDが点滅する",
                "正弦波出力が不安定", "負荷時に停止", "ファンが回らない", "エラーコードが表示",
                "電圧が不安定", "周波数がずれる", "ノイズが発生"
            ],
            "🚽 トイレ関連": [
                "水漏れがする", "フラッパーが故障", "臭いがする", "水が流れない", "タンクが満杯",
                "パッキンが劣化", "レバーが動かない", "水が止まらない", "タンクの亀裂",
                "配管の詰まり", "排水ポンプが動作しない"
            ],
            "🌪️ ルーフベント・換気扇関連": [
                "ファンが回らない", "雨漏りがする", "開閉が不良", "異音がする", "モーターが過熱",
                "スイッチが効かない", "風量が弱い", "振動が激しい", "電源が入らない",
                "シャッターが動かない", "防水シールが劣化"
            ],
            "💧 水道・ポンプ関連": [
                "ポンプが動作しない", "水が出ない", "配管から漏れる", "水圧が弱い", "異音がする",
                "ポンプが過熱する", "タンクが空になる", "フィルターが詰まる", "配管が凍結",
                "水質が悪い", "ポンプが頻繁に動作"
            ],
            "❄️ 冷蔵庫関連": [
                "冷えない", "冷凍室が凍らない", "コンプレッサーが動作しない", "異音がする",
                "霜が付く", "ドアが閉まらない", "温度設定が効かない", "過熱する",
                "ガス漏れの臭い", "電気代が高い", "ドアパッキンが劣化"
            ],
            "🔥 ガス・ヒーター関連": [
                "火が付かない", "不完全燃焼", "異臭がする", "温度が上がらない", "安全装置が作動",
                "ガス漏れ", "点火音がしない", "炎が不安定", "過熱する", "ガス栓が固い"
            ],
            "⚡ 電気・電装系関連": [
                "LEDが点灯しない", "配線がショート", "ヒューズが切れる", "電圧が不安定",
                "スイッチが効かない", "配線が熱い", "漏電する", "コンセントが使えない",
                "バッテリーが消耗する", "電装品が動作不良"
            ],
            "🌧️ 雨漏り・防水関連": [
                "屋根から雨漏り", "ウインドウ周りから漏れる", "ドアから水が入る", "シーリングが劣化",
                "パッキンが硬化", "天窓から漏れる", "配線取り出し部から漏れる",
                "ルーフベントから漏れる", "継ぎ目から漏れる", "コーキングが剥がれる"
            ],
            "🔧 その他の故障": [
                "異音がする", "振動が激しい", "動作が不安定", "部品が破損", "配管が詰まる",
                "ドアが閉まらない", "窓が開かない", "家具が壊れる", "床が抜ける", "壁が剥がれる"
            ]
        }
        st.warning("⚠️ NotionDBが利用できないため、デフォルトの診断データを使用しています")
        st.info("💡 NotionDB接続を改善するには:")
        st.info("1. .streamlit/secrets.tomlの設定を確認")
        st.info("2. Notion APIキーとデータベースIDが正しいか確認")
        st.info("3. データベースへのアクセス権限を確認")
    
    # カテゴリ選択
    selected_category = st.selectbox("症状のカテゴリを選択してください:", list(categories.keys()))
    
    if selected_category:
        st.write(f"**{selected_category}**の症状を詳しく教えてください:")
        
        # 症状選択（より詳細な選択肢）
        symptoms = categories[selected_category]
        selected_symptoms = st.multiselect(
            "該当する症状を選択（複数選択可）:", 
            symptoms,
            help="該当する症状を複数選択してください。より詳細な診断結果が得られます。"
        )
        
        if selected_symptoms:
            st.write("**選択された症状**:", ", ".join(selected_symptoms))
            
            # 診断結果の生成
            if st.button("🔍 診断開始", type="primary"):
                with st.spinner("診断中..."):
                    diagnosis_prompt = f"{selected_category}の症状: {', '.join(selected_symptoms)}"
                    knowledge_base = load_knowledge_base()
                    diagnosis_result = generate_ai_response_with_knowledge(diagnosis_prompt, knowledge_base)
                    
                    st.markdown("## 📋 診断結果")
                    st.markdown(diagnosis_result)
                    
                    # 関連ブログの表示
                    blog_links = get_relevant_blog_links(diagnosis_prompt, knowledge_base)
                    if blog_links:
                        st.markdown("## 📚 関連ブログ")
                        display_blog_links(blog_links, diagnosis_prompt)

def run_detailed_diagnostic(diagnostic_data, repair_cases):
    """詳細診断モード（リレーション活用版）"""
    st.markdown("### 🔍 詳細診断")
    st.markdown("NotionDBの3つのデータベースのリレーションを活用した詳細な診断を行います。")
    
    if not diagnostic_data:
        st.warning("NotionDBの診断データが利用できません。")
        return
    
    # リレーション統計の表示
    st.markdown("#### 📈 データベースリレーション統計")
    
    total_nodes = len(diagnostic_data.get("nodes", []))
    total_cases = len(repair_cases)
    
    # リレーションを持つノードとケースの数を計算
    nodes_with_relations = sum(1 for node in diagnostic_data.get("nodes", []) 
                              if node.get("related_cases") or node.get("related_items"))
    cases_with_relations = sum(1 for case in repair_cases 
                              if case.get("related_nodes") or case.get("related_items"))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("診断ノード", total_nodes, f"{nodes_with_relations}件にリレーション")
    with col2:
        st.metric("修理ケース", total_cases, f"{cases_with_relations}件にリレーション")
    with col3:
        # st.metric("リレーション活用率", 
        #          f"{((nodes_with_relations + cases_with_relations) / (total_nodes + total_cases) * 100):.1f}%")  # 非表示化
        pass
    
    # 診断フローの表示（リレーション情報付き）
    if diagnostic_data.get("nodes"):
        st.markdown("#### 📊 診断ノード（リレーション情報付き）")
        for node in diagnostic_data["nodes"][:10]:  # 最初の10件を表示
            relation_count = len(node.get("related_cases", [])) + len(node.get("related_items", []))
            relation_badge = f"🔗 {relation_count}件のリレーション" if relation_count > 0 else "❌ リレーションなし"
            
            with st.expander(f"🔹 {node['title']} ({node['category']}) {relation_badge}"):
                if node["symptoms"]:
                    st.write("**症状**:", ", ".join(node["symptoms"]))
                
                # 関連修理ケースの表示
                if node.get("related_cases"):
                    st.write("**関連修理ケース**:")
                    for case in node["related_cases"][:3]:
                        st.write(f"  • {case['title']}: {case['solution'][:100]}...")
                
                # 関連部品・工具の表示
                if node.get("related_items"):
                    st.write("**関連部品・工具**:")
                    for item in node["related_items"][:3]:
                        price_info = f" (¥{item['price']})" if item.get('price') else ""
                        supplier_info = f" - {item['supplier']}" if item.get('supplier') else ""
                        st.write(f"  • {item['name']}{price_info}{supplier_info}")
    
    # 修理ケースの表示（リレーション情報付き）
    if repair_cases:
        st.markdown("#### 🔧 修理ケース（リレーション情報付き）")
        for case in repair_cases[:5]:  # 最初の5件を表示
            relation_count = len(case.get("related_nodes", [])) + len(case.get("related_items", []))
            relation_badge = f"🔗 {relation_count}件のリレーション" if relation_count > 0 else "❌ リレーションなし"
            
            with st.expander(f"🔧 {case['title']} ({case['category']}) {relation_badge}"):
                if case["symptoms"]:
                    st.write("**症状**:", ", ".join(case["symptoms"]))
                if case["solution"]:
                    st.write("**解決方法**:", case["solution"][:100] + "..." if len(case["solution"]) > 100 else case["solution"])
                
                # 関連診断ノードの表示
                if case.get("related_nodes"):
                    st.write("**関連診断ノード**:")
                    for node in case["related_nodes"][:3]:
                        st.write(f"  • {node['title']}: {', '.join(node['symptoms'])}")
                
                # 関連部品・工具の表示
                if case.get("related_items"):
                    st.write("**必要な部品・工具**:")
                    for item in case["related_items"][:5]:
                        price_info = f" (¥{item['price']})" if item.get('price') else ""
                        supplier_info = f" - {item['supplier']}" if item.get('supplier') else ""
                        st.write(f"  • {item['name']}{price_info}{supplier_info}")
                
                # 従来の形式（互換性のため）
                if case.get("parts"):
                    st.write("**必要な部品（従来形式）**:", ", ".join(case["parts"]))
                if case.get("tools"):
                    st.write("**必要な工具（従来形式）**:", ", ".join(case["tools"]))

def test_notion_connection():
    """NotionDB接続をテスト"""
    try:
        client = initialize_notion_client()
        if not client:
            return False, "Notionクライアントの初期化に失敗"
        
        # ユーザー情報を取得して接続をテスト
        user = client.users.me()
        
        # データベース接続テスト
        test_results = {}
        
        # 診断フローDBテスト
        node_db_id = st.secrets.get("NODE_DB_ID") or st.secrets.get("NOTION_DIAGNOSTIC_DB_ID") or os.getenv("NODE_DB_ID") or os.getenv("NOTION_DIAGNOSTIC_DB_ID")
        if node_db_id:
            try:
                response = client.databases.query(database_id=node_db_id)
                test_results["diagnostic_db"] = {
                    "status": "success",
                    "count": len(response.get("results", [])),
                    "message": f"✅ 診断フローDB: {len(response.get('results', []))}件のノード"
                }
            except Exception as e:
                test_results["diagnostic_db"] = {
                    "status": "error",
                    "message": f"❌ 診断フローDB: {str(e)}"
                }
        else:
            test_results["diagnostic_db"] = {
                "status": "warning",
                "message": "⚠️ 診断フローDB: ID未設定"
            }
        
        # 修理ケースDBテスト
        case_db_id = st.secrets.get("CASE_DB_ID") or st.secrets.get("NOTION_REPAIR_CASE_DB_ID") or os.getenv("CASE_DB_ID") or os.getenv("NOTION_REPAIR_CASE_DB_ID")
        if case_db_id:
            try:
                response = client.databases.query(database_id=case_db_id)
                test_results["repair_case_db"] = {
                    "status": "success",
                    "count": len(response.get("results", [])),
                    "message": f"✅ 修理ケースDB: {len(response.get('results', []))}件のケース"
                }
            except Exception as e:
                test_results["repair_case_db"] = {
                    "status": "error",
                    "message": f"❌ 修理ケースDB: {str(e)}"
                }
        else:
            test_results["repair_case_db"] = {
                "status": "warning",
                "message": "⚠️ 修理ケースDB: ID未設定"
            }
        
        return True, test_results
        
    except Exception as e:
        return False, f"接続テスト失敗: {str(e)}"

def main():
    st.set_page_config(
        page_title="キャンピングカー修理AI相談",
        page_icon="🚐",
        layout="wide"
    )
    
    # カスタムCSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    
        /* レスポンシブデザイン - スマホ対応 */
        @media (max-width: 768px) {
            .main-header h1 {
                font-size: 1.0rem !important;
                line-height: 1.2;
            }
            .main-header p {
                font-size: 0.7rem !important;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 8px 12px;
                font-size: 0.9rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # ヘッダー
        st.markdown("""
    <div class="main-header">
        <h1 style="font-size: 1.3rem; margin-bottom: 0.5rem;">🚐 キャンピングカー修理専門AI相談</h1>
        <p style="font-size: 0.8rem; margin-top: 0;">豊富な知識ベースを活用した専門的な修理・メンテナンスアドバイス</p>
    </div>
    """, unsafe_allow_html=True)
    
    # タブ作成（システム情報タブを非表示）
    tab1, tab2 = st.tabs(["💬 AIチャット相談", "🔍 対話式症状診断"])
    
    with tab1:
        st.markdown("### 💬 AIチャット相談")
        st.markdown("キャンピングカーの修理・メンテナンスについて何でもお聞きください。")
        
        # チャット履歴の初期化
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # 知識ベースの読み込み
        knowledge_base = load_knowledge_base()
        
        # チャット履歴の表示
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                with st.chat_message("assistant", avatar="https://camper-repair.net/blog/wp-content/uploads/2025/05/dummy_staff_01-150x138-1.png"):
                    st.markdown(message["content"])
            else:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # ユーザー入力
        if prompt := st.chat_input("修理やメンテナンスについて質問してください..."):
            # ユーザーメッセージを追加
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # AI回答を生成
            with st.chat_message("assistant", avatar="https://camper-repair.net/blog/wp-content/uploads/2025/05/dummy_staff_01-150x138-1.png"):
                with st.spinner("専門知識を活用して回答を生成中..."):
                    response = generate_ai_response_with_knowledge(prompt, knowledge_base)
                    st.markdown(response)
                
                # AIメッセージを追加
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    with tab2:
        run_diagnostic_flow()
    
    # サイドバーを非表示にする
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)
    
    # 追加質問エリア
    st.markdown("---")
    st.markdown("### 💬 追加の質問がありますか？")
    st.markdown("他にもキャンピングカーの修理・メンテナンスについて質問があれば、お気軽にお聞きください。")
    
    # 追加質問用の入力フォーム
    additional_question = st.text_area(
        "追加の質問を入力してください:",
        placeholder="例: バッテリーの寿命はどのくらいですか？\n例: 雨漏りの応急処置方法を教えてください。",
        height=100
    )
    
    if st.button("📤 追加質問を送信", type="primary"):
        if additional_question.strip():
            # 追加質問をチャット履歴に追加
            st.session_state.messages.append({"role": "user", "content": additional_question})
            
            # 追加質問の回答を生成
            with st.chat_message("assistant", avatar="https://camper-repair.net/blog/wp-content/uploads/2025/05/dummy_staff_01-150x138-1.png"):
                with st.spinner("追加質問への回答を生成中..."):
                    additional_response = generate_ai_response_with_knowledge(additional_question, knowledge_base)
                    st.markdown(additional_response)
            
            # AI回答をチャット履歴に追加
            st.session_state.messages.append({"role": "assistant", "content": additional_response})
            
            # 入力フォームをクリア
            st.rerun()
        else:
                                 st.warning("質問を入力してください。")

def show_system_info():
    """システム情報とNotionDB接続状況を表示"""
    st.markdown("### 🔧 システム情報")
    
    # OpenAI API設定状況
    st.markdown("#### 🤖 OpenAI API設定")
    if openai_api_key:
        st.success(f"✅ OpenAI API: 設定済み ({openai_api_key[:10]}...)")
    else:
        st.error("❌ OpenAI API: 未設定")
    
    # Notion API設定状況
    st.markdown("#### 📊 Notion API設定")
    if notion_api_key:
        st.success(f"✅ Notion API: 設定済み ({notion_api_key[:10]}...)")
        
        # NotionDB接続テスト
        st.markdown("##### 🔍 NotionDB接続テスト")
        
        # 接続テストボタン
        if st.button("🔄 接続テスト実行", type="secondary"):
            with st.spinner("接続テスト中..."):
                try:
                    # 詳細な接続テスト
                    test_results = perform_detailed_notion_test()
                    
                    if test_results["overall_success"]:
                        st.success("✅ 接続テスト完了")
                        
                        # 各データベースの結果を表示
                        for db_name, result in test_results["databases"].items():
                            if result["status"] == "success":
                                st.success(f"✅ {db_name}: {result['message']}")
                            elif result["status"] == "error":
                                st.error(f"❌ {db_name}: {result['message']}")
                                if result.get("solution"):
                                    st.info(f"💡 解決方法: {result['solution']}")
                            else:
                                st.warning(f"⚠️ {db_name}: {result['message']}")
                        
                        # 接続統計
                        st.info(f"📊 接続統計: {test_results['success_count']}/{test_results['total_count']}個のデータベースに接続成功")
                        
                    else:
                        st.error("❌ 接続テスト失敗")
                        st.info("💡 詳細なエラー情報を確認してください")
                        
                except Exception as e:
                    st.error(f"❌ 接続テスト実行エラー: {str(e)}")
        
        st.markdown("---")
        
        # クライアント初期化テスト
        client = initialize_notion_client()
        if client:
            st.success("✅ Notionクライアント: 初期化成功")
            
            # 診断フローデータベース
            node_db_id = st.secrets.get("NODE_DB_ID") or st.secrets.get("NOTION_DIAGNOSTIC_DB_ID") or os.getenv("NODE_DB_ID") or os.getenv("NOTION_DIAGNOSTIC_DB_ID")
            if node_db_id:
                st.info(f"📋 診断フローDB: {node_db_id[:8]}...")
                try:
                    diagnostic_data = load_notion_diagnostic_data()
                    if diagnostic_data and diagnostic_data.get('nodes'):
                        st.success(f"✅ 診断フローDB: 接続成功 ({len(diagnostic_data.get('nodes', []))}件のノード)")
                        
                        # リレーション統計
                        nodes_with_relations = sum(1 for node in diagnostic_data.get('nodes', []) 
                                                  if node.get("related_cases") or node.get("related_items"))
                        # st.info(f"🔗 リレーション活用: {nodes_with_relations}/{len(diagnostic_data.get('nodes', []))}件のノード")  # 非表示化
                    else:
                        st.warning("⚠️ 診断フローDB: データなしまたは接続失敗")
                except Exception as e:
                    st.error(f"❌ 診断フローDB: 接続失敗 - {str(e)}")
                    st.info("💡 データベースIDとAPIキーの権限を確認してください")
            else:
                st.warning("⚠️ 診断フローDB: ID未設定")
                st.info("💡 .streamlit/secrets.tomlにNODE_DB_IDを設定してください")
            
            # 修理ケースデータベース
            case_db_id = st.secrets.get("CASE_DB_ID") or st.secrets.get("NOTION_REPAIR_CASE_DB_ID") or os.getenv("CASE_DB_ID") or os.getenv("NOTION_REPAIR_CASE_DB_ID")
            if case_db_id:
                st.info(f"🔧 修理ケースDB: {case_db_id[:8]}...")
                try:
                    repair_cases = load_notion_repair_cases()
                    if repair_cases:
                        st.success(f"✅ 修理ケースDB: 接続成功 ({len(repair_cases)}件のケース)")
                        
                        # リレーション統計
                        cases_with_relations = sum(1 for case in repair_cases 
                                                  if case.get("related_nodes") or case.get("related_items"))
                        # st.info(f"🔗 リレーション活用: {cases_with_relations}/{len(repair_cases)}件のケース")  # 非表示化
                    else:
                        st.warning("⚠️ 修理ケースDB: データなし")
                except Exception as e:
                    st.error(f"❌ 修理ケースDB: 接続失敗 - {str(e)}")
                    st.info("💡 データベースIDとAPIキーの権限を確認してください")
            else:
                st.warning("⚠️ 修理ケースDB: ID未設定")
                st.info("💡 .streamlit/secrets.tomlにCASE_DB_IDを設定してください")
            
            # 部品・工具データベース
            item_db_id = st.secrets.get("ITEM_DB_ID") or os.getenv("ITEM_DB_ID")
            if item_db_id:
                st.info(f"🛠️ 部品・工具DB: {item_db_id[:8]}...")
                st.info("ℹ️ 部品・工具DBの接続テストは実装予定")
            else:
                st.warning("⚠️ 部品・工具DB: ID未設定")
                st.info("💡 .streamlit/secrets.tomlにITEM_DB_IDを設定してください")
        else:
            st.error("❌ Notionクライアント: 初期化失敗")
            st.info("💡 notion-clientライブラリのインストールとAPIキーの確認が必要です")
        
    else:
        st.error("❌ Notion API: 未設定")
        st.info("**設定方法**:")
        st.code("NOTION_API_KEY=your_notion_token\nNODE_DB_ID=your_diagnostic_db_id\nCASE_DB_ID=your_repair_case_db_id")
    
    # 知識ベース状況
    st.markdown("#### 📚 知識ベース状況")
    knowledge_base = load_knowledge_base()
    if knowledge_base:
        st.success(f"✅ 知識ベース: 読み込み成功 ({len(knowledge_base)}件のファイル)")
        for category in list(knowledge_base.keys())[:5]:  # 最初の5件を表示
            st.write(f"  - {category}")
        if len(knowledge_base) > 5:
            st.write(f"  - ... 他{len(knowledge_base) - 5}件")
    else:
        st.warning("⚠️ 知識ベース: ファイルが見つかりません")
    
    # 環境変数一覧
    st.markdown("#### 🌐 環境変数一覧")
    env_vars = {
        "OPENAI_API_KEY": openai_api_key,
        "NOTION_API_KEY": notion_api_key,
        "NODE_DB_ID": st.secrets.get("NODE_DB_ID") or st.secrets.get("NOTION_DIAGNOSTIC_DB_ID") or os.getenv("NODE_DB_ID") or os.getenv("NOTION_DIAGNOSTIC_DB_ID"),
        "CASE_DB_ID": st.secrets.get("CASE_DB_ID") or st.secrets.get("NOTION_REPAIR_CASE_DB_ID") or os.getenv("CASE_DB_ID") or os.getenv("NOTION_REPAIR_CASE_DB_ID"),
        "ITEM_DB_ID": st.secrets.get("ITEM_DB_ID") or os.getenv("ITEM_DB_ID")
    }
    
    for key, value in env_vars.items():
        if value:
            if "KEY" in key or "TOKEN" in key:
                st.write(f"**{key}**: {value[:10]}...{value[-4:] if len(value) > 14 else ''}")
            else:
                st.write(f"**{key}**: {value}")
        else:
            st.write(f"**{key}**: ❌ 未設定")
    
    # トラブルシューティングガイド
    st.markdown("#### 🔧 トラブルシューティング")
    with st.expander("NotionDB接続の問題を解決するには"):
        st.markdown("""
        **よくある問題と解決方法:**
        
        1. **APIキーが無効**
           - Notionの設定ページで新しいAPIキーを生成
           - `.streamlit/secrets.toml`を更新
        
        2. **データベースIDが間違っている**
           - Notionでデータベースを開き、URLからIDを確認
           - 例: `https://notion.so/workspace/256709bb38f18069a903f7ade8f76c73`
        
        3. **データベースへのアクセス権限がない**
           - Notionでデータベースを開き、右上の「共有」ボタンをクリック
           - 統合（Integration）にアクセス権限を付与
        
        4. **ライブラリがインストールされていない**
           - ターミナルで実行: `pip install notion-client==2.2.1`
        
        5. **ネットワーク接続の問題**
           - インターネット接続を確認
           - ファイアウォールの設定を確認
        """)
        
        st.markdown("**設定ファイルの例:**")
        st.code("""
# .streamlit/secrets.toml
NOTION_API_KEY = "ntn_your_api_key_here"
NODE_DB_ID = "your_diagnostic_db_id"
CASE_DB_ID = "your_repair_case_db_id"
ITEM_DB_ID = "your_items_db_id"
        """)

if __name__ == "__main__":
    main()
