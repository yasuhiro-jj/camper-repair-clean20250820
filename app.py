from flask import Flask, render_template, request, jsonify, g, session
from typing import Literal
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma

import os
import uuid

# 設定ファイルをインポート
from config import OPENAI_API_KEY, SERP_API_KEY, LANGSMITH_API_KEY

# LangSmith設定（APIキーが設定されている場合のみ）
if LANGSMITH_API_KEY:
    import os
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

# === Flask アプリケーションの設定 ===
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # セッション管理用

# 会話履歴を保存する辞書
conversation_history = {}

# === PDFとChromaのセットアップ ===
main_path = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(main_path, "キャンピングカー修理マニュアル.pdf")
loader = PyPDFLoader(pdf_path)
documents = loader.load()

# OpenAIの埋め込みモデルを設定
embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

for doc in documents:
    if not isinstance(doc.page_content, str):
        doc.page_content = str(doc.page_content)

# Chromaデータベースを作成
db = Chroma.from_documents(documents=documents, embedding=embeddings_model)

# === キャンピングカー修理専用プロンプトテンプレート ===
template = """
あなたはキャンピングカーの修理専門家です。提供された文書抜粋とツールを活用して質問に答えてください。
以下の文書抜粋を参照して質問に答えるか、必要に応じて、"search"ツールを使用してください。

文書抜粋：{document_snippet}

質問：{question}

以下の形式で自然な会話の流れで回答してください：

【状況確認】
まず、{question}について詳しくお聞かせください。どのような症状が現れていますか？

【修理アドバイス】
• 最初の対処法（具体的な手順）
• 次の手順（段階的なアプローチ）
• 注意点（安全に作業するためのポイント）
• 必要な工具・部品（準備すべきもの）

【追加の質問】
他に気になる症状や、この対処法で解決しない場合は、以下の点について教えてください：
• エンジンの状態はどうですか？
• 電気系統に異常はありますか？
• 最近のメンテナンス状況は？

【次のステップ】
この対処法を試してみて、結果を教えてください。うまくいかない場合は、別のアプローチをご提案します。

【最後に】
直接お電話で担当者とお話するサポートセンター

【営業時間】年中無休（9:00～21:00）
※不在時は折り返しお電話差し上げます。

※お気軽にご相談ください。

答え：
"""

# === ツールの設定 ===
@tool
def search(query: str):
    """キャンピングカー修理に関する情報を検索します。"""
    try:
        from langchain_community.utilities import SerpAPIWrapper
        
        search_wrapper = SerpAPIWrapper(serpapi_api_key=SERP_API_KEY)
        result = search_wrapper.run(query)
        
        # 検索結果を箇条書き形式で処理
        if result:
            # 基本的なリンクを箇条書き形式で生成
            links = [
                f"[検索] Google検索: {query} についての詳細情報",
                f"[動画] YouTube動画: {query} の修理手順動画",
                f"[購入] Amazon商品: {query} 関連の部品・工具",
                f"[情報] 専門サイト: キャンピングカー修理専門情報"
            ]
            g.search_results = links
        else:
            # デフォルトのリンクを箇条書き形式で生成
            g.search_results = [
                f"[検索] Google検索: キャンピングカー {query} 修理方法",
                f"[動画] YouTube動画: キャンピングカー {query} 修理手順",
                f"[購入] Amazon商品: キャンピングカー修理部品",
                f"[情報] 専門サイト: キャンピングカー修理専門情報"
            ]
        
        return g.search_results
    except Exception as e:
        # エラー時もデフォルトのリンクを箇条書き形式で生成
        g.search_results = [
            f"[検索] Google検索: キャンピングカー {query} 修理方法",
            f"[動画] YouTube動画: キャンピングカー {query} 修理手順",
            f"[購入] Amazon商品: キャンピングカー修理部品",
            f"[情報] 専門サイト: キャンピングカー修理専門情報"
        ]
        return g.search_results

tools = [search]
tool_node = ToolNode(tools)

# === モデルのセットアップ ===
model = ChatOpenAI(api_key=OPENAI_API_KEY, model_name="gpt-4o-mini").bind_tools(tools)

# === 条件判定 ===
def should_continue(state: MessagesState) -> Literal["tools", END]:
    messages = state['messages']
    last_message = messages[-1]
    
    if last_message.tool_calls:
        return "tools"
    
    return END

# === モデルの応答生成関数 ===
def call_model(state: MessagesState):
    messages = state['messages']
    try:
        response = model.invoke(messages)
        return {"messages": [response]}
    except Exception as e:
        # エラーが発生した場合のフォールバック
        from langchain_core.messages import AIMessage
        error_message = f"申し訳ございませんが、エラーが発生しました: {str(e)}"
        return {"messages": [AIMessage(content=error_message)]}

# === RAG用ロジック ===
def rag_retrieve(question: str):
    question_embedding = embeddings_model.embed_query(question)
    docs = db.similarity_search_by_vector(question_embedding, k=3)
    return "\n".join([doc.page_content for doc in docs])

# === メッセージの前処理 ===
def preprocess_message(question: str, conversation_id: str):
    document_snippet = rag_retrieve(question)
    content = template.format(document_snippet=document_snippet, question=question)
    
    # 会話履歴を取得
    history = conversation_history.get(conversation_id, [])
    
    # 新しいメッセージを追加
    messages = history + [HumanMessage(content=content)]
    
    return messages

# === ワークフローの構築 ===
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", 'agent')
checkpointer = MemorySaver()
app_flow = workflow.compile(checkpointer=checkpointer)

# === Flaskルート設定 ===
@app.route("/")
def index():
    # セッションに会話IDがなければ生成
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    return render_template("index.html")

@app.route("/start_conversation", methods=["POST"])
def start_conversation():
    """新しい会話を開始"""
    conversation_id = str(uuid.uuid4())
    session['conversation_id'] = conversation_id
    conversation_history[conversation_id] = []
    return jsonify({"conversation_id": conversation_id})

@app.route("/ask", methods=["POST"])
def ask():
    try:
        question = request.form["question"]
        conversation_id = session.get('conversation_id', str(uuid.uuid4()))
        g.search_results = []
        
        inputs = preprocess_message(question, conversation_id)
        thread = {"configurable": {"thread_id": conversation_id}}

        response = ""
        for event in app_flow.stream({"messages": inputs}, thread, stream_mode="values"):
            if "messages" in event and event["messages"]:
                response = event["messages"][-1].content

        # 会話履歴を更新
        if conversation_id not in conversation_history:
            conversation_history[conversation_id] = []
        
        # ユーザーの質問とAIの回答を履歴に追加
        conversation_history[conversation_id].extend([
            HumanMessage(content=question),
            AIMessage(content=response)
        ])

        search_results = getattr(g, "search_results", [])
        
        # リンク処理を改善
        if search_results and len(search_results) > 0:
            # 検索結果をそのまま使用
            links = []
            for result in search_results:
                if isinstance(result, str):
                    links.append(result)
                else:
                    links.append(str(result))
            
            if links:
                links_text = "\n".join(links)
            else:
                # デフォルトのリンクを箇条書き形式で生成
                default_links = [
                    f"[検索] Google検索: キャンピングカー {question} 修理方法",
                    f"[動画] YouTube動画: キャンピングカー {question} 修理手順",
                    f"[購入] Amazon商品: キャンピングカー修理部品",
                    f"[情報] 専門サイト: キャンピングカー修理専門情報"
                ]
                links_text = "\n".join(default_links)
        else:
            # デフォルトのリンクを箇条書き形式で生成
            default_links = [
                f"[検索] Google検索: キャンピングカー {question} 修理方法",
                f"[動画] YouTube動画: キャンピングカー {question} 修理手順",
                f"[購入] Amazon商品: キャンピングカー修理部品",
                f"[情報] 専門サイト: キャンピングカー修理専門情報"
            ]
            links_text = "\n".join(default_links)

        return jsonify({"answer": response, "links": links_text})
    
    except Exception as e:
        import traceback
        error_message = f"エラーが発生しました: {str(e)}"
        print(f"詳細エラー: {traceback.format_exc()}")
        return jsonify({"answer": error_message, "links": "エラーによりリンクを取得できませんでした"})

# === Flaskの起動 ===
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)