# streamlit_app_complete.py
import streamlit as st
import os
import uuid
import re
import json
from notion_client import Client
import time

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import BaseMessage
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_chroma import Chroma

import glob
import config

# === RAG機能付きAI相談機能 ===
def initialize_database():
    """データベースを初期化"""
    try:
        main_path = os.path.dirname(os.path.abspath(__file__))
        documents = []
        
        # PDFファイルの読み込み
        pdf_path = os.path.join(main_path, "キャンピングカー修理マニュアル.pdf")
        if os.path.exists(pdf_path):
            loader = PyPDFLoader(pdf_path)
            documents.extend(loader.load())
        
        # テキストファイルの読み込み
        txt_files = glob.glob(os.path.join(main_path, "*.txt"))
        for txt_file in txt_files:
            try:
                loader = TextLoader(txt_file, encoding='utf-8')
                documents.extend(loader.load())
            except Exception as e:
                st.warning(f"テキストファイル {txt_file} の読み込みに失敗: {e}")
        
        if not documents:
            st.warning("ドキュメントが見つかりません")
            return None
        
        # OpenAIの埋め込みモデルを設定
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("OpenAI APIキーが設定されていません")
            return None
            
        embeddings_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
        
        # ドキュメントの前処理
        for doc in documents:
            if not isinstance(doc.page_content, str):
                doc.page_content = str(doc.page_content)
        
        # Chromaデータベースを作成
        db = Chroma.from_documents(documents=documents, embedding=embeddings_model)
        
        return db
        
    except Exception as e:
        st.error(f"データベース初期化エラー: {e}")
        return None

def search_relevant_documents(db, query, k=3):
    """関連ドキュメントを検索"""
    try:
        if not db:
            return []
        
        # 類似度検索
        results = db.similarity_search(query, k=k)
        return results
        
    except Exception as e:
        st.error(f"ドキュメント検索エラー: {e}")
        return []

def generate_ai_response_with_rag(prompt):
    """RAG機能付きAIの回答を生成"""
    try:
        # OpenAI APIキーの確認
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("OpenAI APIキーが設定されていません")
            return
        
        # LLMの初期化
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=openai_api_key
        )
        
        # データベースから関連ドキュメントを検索
        db = initialize_database()
        relevant_docs = search_relevant_documents(db, prompt)
        
        # 関連ドキュメントの内容を抽出
        context = ""
        if relevant_docs:
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # システムプロンプト（RAG機能付き）
        system_prompt = f"""あなたはキャンピングカーの修理・メンテナンスの専門家です。
以下の点に注意して回答してください：

1. 安全第一：危険な作業は避け、専門家への相談を推奨
2. 具体的な手順：段階的な修理手順を説明
3. 必要な工具・部品：具体的な工具名や部品名を提示
4. 予防メンテナンス：再発防止のためのアドバイス
5. 専門家の判断：複雑な問題は専門店への相談を推奨

以下の関連ドキュメントの情報を参考にして、キャンピングカーの修理について親切で分かりやすく回答してください：

関連ドキュメント:
{context}

ユーザーの質問に基づいて、上記のドキュメント情報を活用して回答してください。"""

        # メッセージの作成
        messages = [
            HumanMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        # AIの回答を生成
        with st.spinner("AIが回答を生成中..."):
            response = llm.invoke(messages)
            
        # 回答をセッションに追加
        st.session_state.messages.append({"role": "assistant", "content": response.content})
        
        # 関連ドキュメントの情報を表示
        if relevant_docs:
            st.session_state.last_relevant_docs = relevant_docs
        
    except Exception as e:
        st.error(f"AI回答生成エラー: {e}")

def show_relevant_documents():
    """関連ドキュメントを表示"""
    if "last_relevant_docs" in st.session_state and st.session_state.last_relevant_docs:
        st.markdown("###    参考ドキュメント")
        for i, doc in enumerate(st.session_state.last_relevant_docs, 1):
            source = doc.metadata.get('source', 'unknown')
            filename = os.path.basename(source)
            with st.expander(f"📄 {filename}"):
                st.markdown(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)

# === Notion連携機能 ===
def initialize_notion_client():
    """Notionクライアントを初期化"""
    try:
        api_key = os.getenv("NOTION_API_KEY")
        if not api_key:
            st.warning("⚠️ NOTION_API_KEYが設定されていません")
            return None
        
        client = Client(auth=api_key)
        return client
    except Exception as e:
        st.error(f"❌ Notionクライアントの初期化に失敗: {e}")
        return None

def load_notion_diagnostic_data():
    """Notionから診断データを読み込み"""
    client = initialize_notion_client()
    if not client:
        return None
    
    try:
        node_db_id = os.getenv("NODE_DB_ID")
        if not node_db_id:
            st.error("❌ NODE_DB_IDが設定されていません")
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
            
            # ノードデータを作成
            node_data = {
                "question": question,
                "category": category,
                "is_start": is_start,
                "is_end": is_end,
                "next_nodes": next_nodes,
                "result": result
            }
            
            diagnostic_nodes[node_id] = node_data
            
            # 開始ノードを記録
            if is_start:
                start_nodes[category] = node_id
        
        return {
            "diagnostic_nodes": diagnostic_nodes,
            "start_nodes": start_nodes
        }
        
    except Exception as e:
        st.error(f"❌ Notionからの診断データ読み込みに失敗: {e}")
        return None

def load_notion_repair_cases():
    """Notionから修理ケースデータを読み込み"""
    client = initialize_notion_client()
    if not client:
        return []
    
    try:
        case_db_id = os.getenv("CASE_DB_ID")
        if not case_db_id:
            st.error("❌ CASE_DB_IDが設定されていません")
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
            
            # ケースデータを作成
            case_data = {
                "case_id": case_id,
                "symptoms": symptoms,
                "repair_steps": repair_steps,
                "parts": parts,
                "tools": tools,
                "difficulty": difficulty
            }
            
            repair_cases.append(case_data)
        
        return repair_cases
        
    except Exception as e:
        st.error(f"❌ Notionからの修理ケース読み込みに失敗: {e}")
        return []

def run_diagnostic_flow(diagnostic_data, current_node_id=None):
    """症状診断フローを実行"""
    if not diagnostic_data:
        st.error("診断データが読み込めませんでした。")
        return

    diagnostic_nodes = diagnostic_data["diagnostic_nodes"]
    start_nodes = diagnostic_data["start_nodes"]

    # セッション状態の初期化
    if "diagnostic_current_node" not in st.session_state:
        st.session_state.diagnostic_current_node = None
        st.session_state.diagnostic_history = []

    # 開始ノードの選択
    if st.session_state.diagnostic_current_node is None:
        st.markdown("###    症状診断システム")
        st.markdown("**症状のカテゴリを選択してください：**")
        
        # 利用可能なカテゴリを表示
        available_categories = list(start_nodes.keys())
        
        if not available_categories:
            st.warning("⚠️ 利用可能な診断カテゴリがありません")
            return
        
        selected_category = st.selectbox(
            "カテゴリを選択",
            available_categories,
            key="category_select"
        )
        
        if st.button("診断開始", key="start_diagnosis"):
            start_node_id = start_nodes[selected_category]
            st.session_state.diagnostic_current_node = start_node_id
            st.session_state.diagnostic_history = [start_node_id]
            st.rerun()
        
        return

    # 現在のノードを取得
    current_node = diagnostic_nodes.get(st.session_state.diagnostic_current_node)
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
            # 症状に基づいて関連ケースをフィルタリング
            category = current_node.get("category", "")
            related_cases = [case for case in repair_cases if category.lower() in case.get("symptoms", "").lower()]
            
            if related_cases:
                for case in related_cases[:3]:  # 上位3件を表示
                    with st.expander(f"   {case['case_id']}: {case['symptoms'][:50]}..."):
                        st.markdown(f"**症状:** {case['symptoms']}")
                        st.markdown(f"**修理手順:** {case['repair_steps']}")
                        st.markdown(f"**必要な部品:** {case['parts']}")
                        st.markdown(f"**必要な工具:** {case['tools']}")
                        st.markdown(f"**難易度:** {case['difficulty']}")
            else:
                st.info("関連する修理ケースが見つかりませんでした。")
        else:
            st.info("修理ケースデータを読み込めませんでした。")
        
        # 診断をリセット
        if st.button("新しい診断を開始", key="reset_diagnosis"):
            st.session_state.diagnostic_current_node = None
            st.session_state.diagnostic_history = []
            st.rerun()
        
        return

    # 次のノードへの選択肢
    next_nodes = current_node.get("next_nodes", [])
    if len(next_nodes) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("はい", key=f"yes_{current_node_id}"):
                next_node_id = next_nodes[0]
                st.session_state.diagnostic_current_node = next_node_id
                st.session_state.diagnostic_history.append(next_node_id)
                st.rerun()
        
        with col2:
            if st.button("いいえ", key=f"no_{current_node_id}"):
                next_node_id = next_nodes[1] if len(next_nodes) > 1 else next_nodes[0]
                st.session_state.diagnostic_current_node = next_node_id
                st.session_state.diagnostic_history.append(next_node_id)
                st.rerun()
    elif len(next_nodes) == 1:
        if st.button("次へ", key=f"next_{current_node_id}"):
            next_node_id = next_nodes[0]
            st.session_state.diagnostic_current_node = next_node_id
            st.session_state.diagnostic_history.append(next_node_id)
            st.rerun()

    # 診断履歴の表示
    if st.session_state.diagnostic_history:
        st.markdown("---")
        st.markdown("**📝 診断履歴**")
        for i, node_id in enumerate(st.session_state.diagnostic_history):
            node = diagnostic_nodes.get(node_id, {})
            question = node.get("question", "")
            if question:
                st.markdown(f"{i+1}. {question}")

# === メインアプリケーション ===
def main():
    st.set_page_config(
        page_title="キャンピングカー修理専門 AIチャット",
        page_icon="  ",
        layout="wide"
    )

    # カスタムCSS
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .feature-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .feature-list {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 20px 0;
    }
    
    .quick-question {
        background: white;
        border: 2px solid #e9ecef;
        border-radius: 8px;
        padding: 10px 15px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-block;
    }
    
    .quick-question:hover {
        border-color: #667eea;
        background: #f8f9fa;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 8px;
        color: #666;
        font-weight: 500;
        padding: 12px 24px;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
        border-color: #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stTabs [aria-selected="false"]:hover {
        background-color: #e8f4fd;
        border-color: #667eea;
        color: #667eea;
    }
    </style>
    """, unsafe_allow_html=True)

    # ヘッダー
    st.markdown("""
    <div class="main-header">
        <h1>🔧 キャンピングカー修理専門 AIチャット</h1>
        <p>経験豊富なAIがキャンピングカーの修理について詳しくお答えします</p>
    </div>
    """, unsafe_allow_html=True)

    # 2つのタブを作成
    tab1, tab2 = st.tabs(["   AIチャット相談", "🔍 対話式症状診断"])

    with tab1:
        # AIチャット相談の説明バナー
        st.markdown("""
        <div class="feature-banner">
            <h3>💬 AIチャット相談</h3>
            <p>経験豊富なAIがキャンピングカーの修理について詳しくお答えします。自由に質問してください。</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 機能説明
        st.markdown("""
        <div class="feature-list">
            <h4>🎯 この機能でできること</h4>
            <ul>
                <li>🔧 修理方法の詳細な説明</li>
                <li>🛠️ 工具や部品の選び方</li>
                <li>⚠️ 安全な作業手順の案内</li>
                <li>   定期メンテナンスのアドバイス</li>
                <li>🔍 トラブルシューティングのヒント</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # よくある質問ボタン
        st.markdown("### 💡 よくある質問 (クリックで質問)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔋 バッテリー上がり", key="battery_question"):
                question = "バッテリーが上がってしまいました。どうすればいいですか？"
                st.session_state.messages.append({"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant", avatar="https://camper-repair.net/blog/wp-content/uploads/2025/05/dummy_staff_01-150x138-1.png"):
                    with st.spinner("   修理アドバイスを生成中..."):
                        generate_ai_response_with_rag(question)
                st.rerun()
            
            if st.button("   水道ポンプ", key="water_pump_question"):
                question = "水道ポンプが動きません。原因と対処法を教えてください。"
                st.session_state.messages.append({"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant", avatar="https://camper-repair.net/blog/wp-content/uploads/2025/05/dummy_staff_01-150x138-1.png"):
                    with st.spinner("   修理アドバイスを生成中..."):
                        generate_ai_response_with_rag(question)
                st.rerun()
        
        with col2:
            if st.button("🔥 ガスコンロ", key="gas_stove_question"):
                question = "ガスコンロの火がつきません。どうすればいいですか？"
                st.session_state.messages.append({"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant", avatar="https://camper-repair.net/blog/wp-content/uploads/2025/05/dummy_staff_01-150x138-1.png"):
                    with st.spinner("   修理アドバイスを生成中..."):
                        generate_ai_response_with_rag(question)
                st.rerun()
            
            if st.button("❄️ 冷蔵庫", key="refrigerator_question"):
                question = "冷蔵庫が冷えません。原因と対処法を教えてください。"
                st.session_state.messages.append({"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant", avatar="https://camper-repair.net/blog/wp-content/uploads/2025/05/dummy_staff_01-150x138-1.png"):
                    with st.spinner("   修理アドバイスを生成中..."):
                        generate_ai_response_with_rag(question)
                st.rerun()
        
        with col3:
            if st.button("📋 定期点検", key="maintenance_question"):
                question = "キャンピングカーの定期点検について教えてください。"
                st.session_state.messages.append({"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant", avatar="https://camper-repair.net/blog/wp-content/uploads/2025/05/dummy_staff_01-150x138-1.png"):
                    with st.spinner("   修理アドバイスを生成中..."):
                        generate_ai_response_with_rag(question)
                st.rerun()
            
            if st.button("🆕 新しい会話", key="new_conversation"):
                st.session_state.messages = []
                st.rerun()
        
        # セッション状態の初期化
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # チャット履歴の表示
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # ユーザー入力
        if prompt := st.chat_input("キャンピングカーの修理について質問してください..."):
            # ユーザーメッセージを追加
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)

            # AIの回答を生成（RAG機能付き）
            with st.chat_message("assistant", avatar="https://camper-repair.net/blog/wp-content/uploads/2025/05/dummy_staff_01-150x138-1.png"):
                with st.spinner("   修理アドバイスを生成中..."):
                    generate_ai_response_with_rag(prompt)

        # 関連ドキュメントの表示
        show_relevant_documents()

    with tab2:
        # 症状診断の説明
        st.markdown("""
        <div class="feature-banner">
            <h3>🔍 対話式症状診断</h3>
            <p>症状を選択して、段階的に診断を行い、最適な対処法をご案内します。</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 症状診断システム
        notion_data = load_notion_diagnostic_data()
        if notion_data:
            run_diagnostic_flow(notion_data)
        else:
            st.error("診断データの読み込みに失敗しました。")
            st.info("環境変数の設定を確認してください。")

if __name__ == "__main__":
    main()