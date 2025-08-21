# streamlit_app_beautiful_ui.py
import streamlit as st
import os
import uuid
import re
import json
import time

# Notionクライアントのインポート
try:
    from notion_client import Client
except ImportError:
    st.error("notion-client モジュールが見つかりません。requirements.txtに notion-client==2.2.1 を追加してください。")
    Client = None

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import BaseMessage
from langchain_core.messages import HumanMessage, AIMessage

# Windows互換性のため、個別にインポート
try:
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
except ModuleNotFoundError as e:
    if "pwd" in str(e):
        import sys
        import platform
        if platform.system() == "Windows":
            from langchain_community.document_loaders.pdf import PyPDFLoader
            from langchain_community.document_loaders.text import TextLoader
    else:
        raise e

import glob
import config

# === Notion連携機能 ===
def initialize_notion_client():
    """Notionクライアントを初期化"""
    if Client is None:
        st.error("❌ notion-client モジュールが利用できません")
        return None
    
    try:
        # 複数の環境変数名に対応
        api_key = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
        if not api_key:
            st.warning("⚠️ NOTION_API_KEYまたはNOTION_TOKENが設定されていません")
            return None
        
        client = Client(auth=api_key)
        return client
    except Exception as e:
        st.error(f"❌ Notionクライアントの初期化に失敗: {e}")
        return None

def load_notion_diagnostic_data():
    """Notionから診断データを読み込み（キャッシュ対応）"""
    # セッション状態でキャッシュをチェック
    if "notion_diagnostic_data" in st.session_state:
        # st.info("📋 キャッシュされた診断データを使用しています")  # 非表示
        return st.session_state.notion_diagnostic_data
    
    client = initialize_notion_client()
    if not client:
        return None
    
    try:
        # 複数の環境変数名に対応
        node_db_id = os.getenv("NODE_DB_ID") or os.getenv("NOTION_DIAGNOSTIC_DB_ID")
        if not node_db_id:
            st.error("❌ NODE_DB_IDまたはNOTION_DIAGNOSTIC_DB_IDが設定されていません")
            return None
        
        # Notionから診断ノードを取得
        response = client.databases.query(database_id=node_db_id)
        nodes = response.get("results", [])
        
        # データを変換
        diagnostic_nodes = {}
        start_nodes = {}
        
        for node in nodes:
            properties = node.get("properties", {})
            
            # ノードIDを取得
            node_id_prop = properties.get("ノードID", {})
            node_id = ""
            if node_id_prop.get("type") == "title":
                title_content = node_id_prop.get("title", [])
                if title_content:
                    node_id = title_content[0].get("plain_text", "")
            
            if not node_id:
                continue
            
            # 各プロパティを取得
            question_prop = properties.get("質問内容", {})
            question = ""
            if question_prop.get("type") == "rich_text":
                rich_text_content = question_prop.get("rich_text", [])
                if rich_text_content:
                    question = rich_text_content[0].get("plain_text", "")
            
            result_prop = properties.get("診断結果", {})
            result = ""
            if result_prop.get("type") == "rich_text":
                rich_text_content = result_prop.get("rich_text", [])
                if rich_text_content:
                    result = rich_text_content[0].get("plain_text", "")
            
            category_prop = properties.get("カテゴリ", {})
            category = ""
            if category_prop.get("type") == "rich_text":
                rich_text_content = category_prop.get("rich_text", [])
                if rich_text_content:
                    category = rich_text_content[0].get("plain_text", "")
            
            is_start = properties.get("開始フラグ", {}).get("checkbox", False)
            is_end = properties.get("終端フラグ", {}).get("checkbox", False)
            
            next_nodes_prop = properties.get("次のノード", {})
            next_nodes = []
            if next_nodes_prop.get("type") == "rich_text":
                rich_text_content = next_nodes_prop.get("rich_text", [])
                if rich_text_content:
                    next_nodes_text = rich_text_content[0].get("plain_text", "")
                    next_nodes = [node.strip() for node in next_nodes_text.split(",") if node.strip()]
            
            # 修理ケースの関連付けを取得
            repair_cases_relation = properties.get("修理ケース", {})
            related_repair_cases = []
            if repair_cases_relation.get("type") == "relation":
                relation_data = repair_cases_relation.get("relation", [])
                for relation in relation_data:
                    related_repair_cases.append(relation.get("id", ""))
            
            # ノードデータを作成
            node_data = {
                "question": question,
                "category": category,
                "is_start": is_start,
                "is_end": is_end,
                "next_nodes": next_nodes,
                "result": result,
                "related_repair_cases": related_repair_cases
            }
            
            diagnostic_nodes[node_id] = node_data
            
            # 開始ノードを記録
            if is_start:
                start_nodes[category] = node_id
        
        # セッション状態にキャッシュ
        result_data = {
            "diagnostic_nodes": diagnostic_nodes,
            "start_nodes": start_nodes
        }
        st.session_state.notion_diagnostic_data = result_data
        
        return result_data
        
    except Exception as e:
        st.error(f"❌ Notionからの診断データ読み込みに失敗: {e}")
        return None

def load_notion_repair_cases():
    """Notionから修理ケースデータを読み込み（キャッシュ対応）"""
    # セッション状態でキャッシュをチェック
    if "notion_repair_cases" in st.session_state:
        # st.info("📋 キャッシュされた修理ケースデータを使用しています")  # 非表示
        return st.session_state.notion_repair_cases
    
    client = initialize_notion_client()
    if not client:
        return []
    
    try:
        # 複数の環境変数名に対応
        case_db_id = os.getenv("CASE_DB_ID") or os.getenv("NOTION_REPAIR_CASE_DB_ID")
        if not case_db_id:
            st.error("❌ CASE_DB_IDまたはNOTION_REPAIR_CASE_DB_IDが設定されていません")
            return []
        
        # Notionから修理ケースを取得
        response = client.databases.query(database_id=case_db_id)
        cases = response.get("results", [])
        
        repair_cases = []
        
        for case in cases:
            properties = case.get("properties", {})
            
            # ケースIDを取得
            case_id_prop = properties.get("ケースID", {})
            case_id = ""
            if case_id_prop.get("type") == "title":
                title_content = case_id_prop.get("title", [])
                if title_content:
                    case_id = title_content[0].get("plain_text", "")
            
            if not case_id:
                continue
            
            # 各プロパティを取得
            symptoms_prop = properties.get("症状", {})
            symptoms = ""
            if symptoms_prop.get("type") == "rich_text":
                rich_text_content = symptoms_prop.get("rich_text", [])
                if rich_text_content:
                    symptoms = rich_text_content[0].get("plain_text", "")
            
            repair_steps_prop = properties.get("修理手順", {})
            repair_steps = ""
            if repair_steps_prop.get("type") == "rich_text":
                rich_text_content = repair_steps_prop.get("rich_text", [])
                if rich_text_content:
                    repair_steps = rich_text_content[0].get("plain_text", "")
            
            parts_prop = properties.get("必要な部品", {})
            parts = ""
            if parts_prop.get("type") == "rich_text":
                rich_text_content = parts_prop.get("rich_text", [])
                if rich_text_content:
                    parts = rich_text_content[0].get("plain_text", "")
            
            tools_prop = properties.get("必要な工具", {})
            tools = ""
            if tools_prop.get("type") == "rich_text":
                rich_text_content = tools_prop.get("rich_text", [])
                if rich_text_content:
                    tools = rich_text_content[0].get("plain_text", "")
            
            difficulty_prop = properties.get("難易度", {})
            difficulty = ""
            if difficulty_prop.get("type") == "rich_text":
                rich_text_content = difficulty_prop.get("rich_text", [])
                if rich_text_content:
                    difficulty = rich_text_content[0].get("plain_text", "")
            
            # 診断ノードの関連付けを取得
            diagnostic_nodes_relation = properties.get("診断ノード", {})
            related_diagnostic_nodes = []
            if diagnostic_nodes_relation.get("type") == "relation":
                relation_data = diagnostic_nodes_relation.get("relation", [])
                for relation in relation_data:
                    related_diagnostic_nodes.append(relation.get("id", ""))
            
            # 必要部品の関連付けを取得
            required_parts_relation = properties.get("必要部品", {})
            related_parts = []
            if required_parts_relation.get("type") == "relation":
                relation_data = required_parts_relation.get("relation", [])
                for relation in relation_data:
                    related_parts.append(relation.get("id", ""))
            
            # ケースデータを作成
            case_data = {
                "case_id": case_id,
                "symptoms": symptoms,
                "repair_steps": repair_steps,
                "parts": parts,
                "tools": tools,
                "difficulty": difficulty,
                "related_diagnostic_nodes": related_diagnostic_nodes,
                "related_parts": related_parts
            }
            
            repair_cases.append(case_data)
        
        # セッション状態にキャッシュ
        st.session_state.notion_repair_cases = repair_cases
        
        return repair_cases
        
    except Exception as e:
        st.error(f"❌ Notionからの修理ケース読み込みに失敗: {e}")
        return []

def clear_notion_cache():
    """Notionデータのキャッシュをクリア"""
    if "notion_diagnostic_data" in st.session_state:
        del st.session_state.notion_diagnostic_data
    if "notion_repair_cases" in st.session_state:
        del st.session_state.notion_repair_cases
    if "notion_diagnostic_current_node" in st.session_state:
        del st.session_state.notion_diagnostic_current_node
    if "notion_diagnostic_history" in st.session_state:
        del st.session_state.notion_diagnostic_history

# === AIチャット機能 ===
def initialize_chat_model():
    """チャットモデルを初期化"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.warning("⚠️ OPENAI_API_KEYが設定されていません")
            return None
        
        model = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=api_key
        )
        return model
    except Exception as e:
        st.error(f"❌ チャットモデルの初期化に失敗: {e}")
        return None

def get_ai_response(model, user_message, chat_history):
    """AIからの応答を取得"""
    try:
        # システムプロンプト
        system_prompt = """あなたはキャンピングカーの修理専門のAIアシスタントです。
以下の点に注意して回答してください：

1. 安全第一：危険な作業は避け、専門家への相談を推奨
2. 具体的な手順：段階的な修理手順を説明
3. 必要な工具・部品：具体的な工具名や部品名を明示
4. 予防策：再発防止のためのメンテナンス方法を提案
5. 専門知識：キャンピングカーの特性を考慮したアドバイス

ユーザーの質問に対して、親切で分かりやすく回答してください。"""

        # メッセージの構築
        messages = [{"role": "system", "content": system_prompt}]
        
        # チャット履歴を追加
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                messages.append({"role": "assistant", "content": msg["content"]})
        
        # 現在のユーザーメッセージを追加
        messages.append({"role": "user", "content": user_message})
        
        # AIからの応答を取得
        response = model.invoke(messages)
        return response.content
        
    except Exception as e:
        return f"申し訳ございません。エラーが発生しました: {str(e)}"

def run_ai_chat():
    """AIチャット機能を実行"""
    # セッション状態の初期化
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "chat_model" not in st.session_state:
        st.session_state.chat_model = initialize_chat_model()
    
    # AIチャット相談セクション
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px; color: white;">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 1.5em; margin-right: 10px;">  </span>
            <h3 style="margin: 0;">AIチャット相談</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("経験豊富なAIがキャンピングカーの修理について詳しくお答えします。自由に質問してください。")
    
    # この機能でできること
    st.markdown("### 🔴 この機能でできること")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("🔧 **修理方法の詳細な説明**")
        st.markdown("🔧 **工具や部品の選び方**")
        st.markdown("⚠️ **安全な作業手順の案内**")
    
    with col2:
        st.markdown("   **定期メンテナンスのアドバイス**")
        st.markdown("🔍 **トラブルシューティングのヒント**")
        st.markdown("💡 **予防策とメンテナンス方法**")
    
    # よくある質問ボタン
    st.markdown("###    よくある質問（クリックで質問）")
    
    common_questions = {
        "バッテリー上がり": "キャンピングカーのバッテリーが上がってしまいました。対処法を教えてください。",
        "水道ポンプ": "水道ポンプが正常に動作しません。点検方法と修理手順を教えてください。",
        "ガスコンロ": "ガスコンロの火が弱いです。調整方法を教えてください。",
        "定期点検": "キャンピングカーの定期点検項目と頻度を教えてください。",
        "冷蔵庫": "冷蔵庫が冷えません。故障の原因と対処法を教えてください。",
        "新しい会話": "新しい会話を開始"
    }
    
    # 3列でボタンを配置
    cols = st.columns(3)
    
    for i, (question, prompt) in enumerate(common_questions.items()):
        with cols[i % 3]:
            icon = "🔋" if "バッテリー" in question else \
                   "💧" if "ポンプ" in question else \
                   "🔥" if "ガス" in question else \
                   "📅" if "点検" in question else \
                   "❄️" if "冷蔵庫" in question else \
                   "🔄"
            
            if st.button(f"{icon} {question}", key=f"common_q_{i}"):
                if question == "新しい会話":
                    st.session_state.chat_history = []
                    st.rerun()
                else:
                    # 質問をチャット履歴に追加
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    st.rerun()
    
    # チャット履歴の表示
    if st.session_state.chat_history:
        st.markdown("### 💬 チャット履歴")
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.markdown(f"**👤 あなた:** {message['content']}")
            else:
                st.markdown(f"**🤖 AI:** {message['content']}")
            st.markdown("---")
    
    # 新しいメッセージの入力
    user_input = st.text_input(
        "キャンピングカーの修理について質問してください...",
        key="chat_input"
    )
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("送信", key="send_message"):
            if user_input and st.session_state.chat_model:
                # ユーザーメッセージを履歴に追加
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # AIからの応答を取得
                with st.spinner("AIが回答を生成中..."):
                    ai_response = get_ai_response(st.session_state.chat_model, user_input, st.session_state.chat_history)
                
                # AI応答を履歴に追加
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                
                st.rerun()

def run_notion_diagnostic_flow(diagnostic_data, current_node_id=None):
    """Notionデータを使用した診断フローを実行"""
    if not diagnostic_data:
        st.error("Notion診断データが読み込めませんでした。")
        return

    diagnostic_nodes = diagnostic_data["diagnostic_nodes"]
    start_nodes = diagnostic_data["start_nodes"]

    # セッション状態の初期化
    if "notion_diagnostic_current_node" not in st.session_state:
        st.session_state.notion_diagnostic_current_node = None
        st.session_state.notion_diagnostic_history = []

    # 開始ノードの選択
    if st.session_state.notion_diagnostic_current_node is None:
        # タイトルを非表示
        # st.markdown("###    対話式症状診断システム（Notion連携版）")
        st.markdown("**症状のカテゴリを選択してください：**")
        
        # 利用可能なカテゴリを表示
        available_categories = list(start_nodes.keys())
        
        if not available_categories:
            st.warning("⚠️ 利用可能な診断カテゴリがありません")
            return
        
        selected_category = st.selectbox(
            "カテゴリを選択",
            available_categories,
            key="notion_category_select"
        )
        
        if st.button("診断開始", key="notion_start_diagnosis"):
            start_node_id = start_nodes[selected_category]
            st.session_state.notion_diagnostic_current_node = start_node_id
            st.session_state.notion_diagnostic_history = [start_node_id]
            st.rerun()
        
        return

    # 現在のノードを取得
    current_node = diagnostic_nodes.get(st.session_state.notion_diagnostic_current_node)
    if not current_node:
        st.error("診断ノードが見つかりませんでした。")
        return

    # 質問の表示
    question = current_node.get("question", "")
    if question:
        st.markdown(f"### ❓ {question}")
    
    # 終端ノードの場合
    if current_node.get("is_end", False):
        result = current_node.get("result", "")
        if result:
            st.markdown("###    診断結果")
            st.markdown(result)
        
        # 関連する修理ケースを表示
        st.markdown("### 📋 関連する修理ケース")
        repair_cases = load_notion_repair_cases()
        
        if repair_cases:
            # リレーションに基づく関連ケースフィルタリング（優先）
            current_node_id = st.session_state.notion_diagnostic_current_node
            related_cases = []
            
            # 1. リレーションに基づく関連ケースを検索
            for case in repair_cases:
                related_nodes = case.get("related_diagnostic_nodes", [])
                if current_node_id in related_nodes:
                    related_cases.append((case, 10))  # 最高スコア
            
            # 2. リレーションが見つからない場合、キーワードマッチング
            if not related_cases:
                category = current_node.get("category", "").lower()
                question = current_node.get("question", "").lower()
                result = current_node.get("result", "").lower()
                
                for case in repair_cases:
                    symptoms = case.get("symptoms", "").lower()
                    repair_steps = case.get("repair_steps", "").lower()
                    
                    # 複数の条件でマッチング
                    score = 0
                    
                    # カテゴリマッチング
                    if category and category in symptoms:
                        score += 3
                    if category and category in repair_steps:
                        score += 2
                    
                    # キーワードマッチング
                    keywords = ["インバーター", "バッテリー", "電圧", "充電", "配線"]
                    for keyword in keywords:
                        if keyword in symptoms and (keyword in question or keyword in result):
                            score += 2
                        if keyword in repair_steps and (keyword in question or keyword in result):
                            score += 1
                    
                    # 症状の類似性チェック
                    if any(word in symptoms for word in ["電圧", "不足", "弱い", "重い"]) and any(word in result for word in ["電圧", "不足", "弱い", "重い"]):
                        score += 2
                    
                    if score >= 2:  # スコアが2以上の場合に関連ケースとして追加
                        related_cases.append((case, score))
            
            # スコアでソート
            related_cases.sort(key=lambda x: x[1], reverse=True)
            
            if related_cases:
                st.success(f"   {len(related_cases)}件の関連ケースが見つかりました")
                for case, score in related_cases[:3]:  # 上位3件を表示
                    with st.expander(f"   {case['case_id']}: {case['symptoms'][:50]}... (関連度: {score})"):
                        st.markdown(f"**症状:** {case['symptoms']}")
                        st.markdown(f"**修理手順:** {case['repair_steps']}")
                        st.markdown(f"**必要な部品:** {case['parts']}")
                        st.markdown(f"**必要な工具:** {case['tools']}")
                        st.markdown(f"**難易度:** {case['difficulty']}")
            else:
                st.info("関連する修理ケースが見つかりませんでした。")
                st.info("   ヒント: Notionで診断ノードと修理ケースの関連付けを設定してください。")
        else:
            st.info("修理ケースデータを読み込めませんでした。")
        
        # 診断をリセット
        if st.button("新しい診断を開始", key="notion_reset_diagnosis"):
            st.session_state.notion_diagnostic_current_node = None
            st.session_state.notion_diagnostic_history = []
            st.rerun()
        
        return

    # 次のノードへの選択肢
    next_nodes = current_node.get("next_nodes", [])
    if len(next_nodes) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("はい", key=f"notion_yes_{current_node_id}"):
                next_node_id = next_nodes[0]
                st.session_state.notion_diagnostic_current_node = next_node_id
                st.session_state.notion_diagnostic_history.append(next_node_id)
                st.rerun()
        
        with col2:
            if st.button("いいえ", key=f"notion_no_{current_node_id}"):
                next_node_id = next_nodes[1] if len(next_nodes) > 1 else next_nodes[0]
                st.session_state.notion_diagnostic_current_node = next_node_id
                st.session_state.notion_diagnostic_history.append(next_node_id)
                st.rerun()
    elif len(next_nodes) == 1:
        if st.button("次へ", key=f"notion_next_{current_node_id}"):
            next_node_id = next_nodes[0]
            st.session_state.notion_diagnostic_current_node = next_node_id
            st.session_state.notion_diagnostic_history.append(next_node_id)
            st.rerun()

    # 診断履歴の表示
    if st.session_state.notion_diagnostic_history:
        st.markdown("---")
        st.markdown("**📝 診断履歴**")
        for i, node_id in enumerate(st.session_state.notion_diagnostic_history):
            node = diagnostic_nodes.get(node_id, {})
            question = node.get("question", "")
            if question:
                st.markdown(f"{i+1}. {question}")

# === メインアプリケーション ===
# === メインアプリケーション ===
# === メインアプリケーション ===
def main():
    st.set_page_config(
        page_title="キャンピングカー修理専門 AIチャット",
        page_icon="  ",
        layout="wide"
    )

    # ヘッダー（画像のような美しいデザイン）
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px; flex-wrap: wrap;">
            <span style="font-size: 2em; margin-right: 10px;">🔧</span>
            <h1 style="margin: 0; font-size: 1.8em; font-weight: bold; line-height: 1.2;">キャンピングカー修理専門 AIチャット</h1>
        </div>
        <p style="font-size: 1em; margin: 0; opacity: 0.9; line-height: 1.3;">経験豊富なAIがキャンピングカーの修理について詳しくお答えします</p>
    </div>
    """, unsafe_allow_html=True)

    # データ更新ボタン（完全に非表示）
    # if st.button("🔄 Notionデータを再読み込み", key="reload_notion_data"):
    #     clear_notion_cache()
    #     st.success("✅ キャッシュをクリアしました。ページを再読み込みしてください。")
    #     st.rerun()

    # タブを作成（システム情報タブを削除）
    tab1, tab2 = st.tabs(["   AIチャット相談", "🔧 対話式症状診断"])

    with tab1:
        run_ai_chat()

    with tab2:
        # 説明文を非表示
        # st.markdown("""
        # <div style="background: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        #     <h3>   対話式症状診断システム（Notion連携版）</h3>
        #     <p>Notionデータベースから取得した最新の診断データを使用して、症状を段階的に診断し、最適な対処法をご案内します。</p>
        # </div>
        # """, unsafe_allow_html=True)
        
        # Notion連携版の診断
        notion_data = load_notion_diagnostic_data()
        if notion_data:
            run_notion_diagnostic_flow(notion_data)
        else:
            st.error("Notionデータの読み込みに失敗しました。")
            st.info("環境変数の設定を確認してください。")

if __name__ == "__main__":
    main()