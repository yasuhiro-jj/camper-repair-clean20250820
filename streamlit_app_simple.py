import streamlit as st
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

def get_relevant_blog_links(query):
    """クエリに基づいて関連ブログを返す"""
    query_lower = query.lower()
    
    blog_links = [
        {
            "title": "バッテリー・バッテリーの故障と修理方法",
            "url": "https://camper-repair.net/blog/repair1/",
            "keywords": ["バッテリー", "充電", "電圧", "上がり", "始動"]
        },
        {
            "title": "基本修理・キャンピングカー修理の基本",
            "url": "https://camper-repair.net/blog/risk1/",
            "keywords": ["修理", "基本", "手順", "工具", "部品"]
        },
        {
            "title": "定期点検・定期点検とメンテナンス",
            "url": "https://camper-repair.net/battery-selection/",
            "keywords": ["点検", "メンテナンス", "定期", "予防", "保守"]
        }
    ]
    
    relevant_blogs = []
    for blog in blog_links:
        score = 0
        for keyword in blog["keywords"]:
            if keyword in query_lower:
                score += 1
        
        if score > 0:
            relevant_blogs.append((blog, score))
    
    relevant_blogs.sort(key=lambda x: x[1], reverse=True)
    return [blog for blog, score in relevant_blogs[:3]]

def generate_ai_response(prompt):
    """AIの回答を生成"""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("OpenAI APIキーが設定されていません")
            return
        
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=openai_api_key
        )
        
        blog_links = get_relevant_blog_links(prompt)
        
        system_prompt = f"""あなたはキャンピングカーの修理・メンテナンスの専門家です。
以下の点に注意して回答してください：

1. 安全第一：危険な作業は避け、専門家への相談を推奨
2. 具体的な手順：段階的な修理手順を説明
3. 必要な工具・部品：具体的な工具名や部品名を提示
4. 予防メンテナンス：再発防止のためのアドバイス
5. 専門家の判断：複雑な問題は専門店への相談を推奨

ユーザーの質問に基づいて、上記の形式で回答してください。"""

        messages = [
            HumanMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        with st.spinner("AIが回答を生成中..."):
            response = llm.invoke(messages)
            
        ai_response = response.content
        if blog_links:
            ai_response += "\n\n🔗 関連ブログ\n"
            for blog in blog_links:
                ai_response += f"• {blog['title']}: {blog['url']}\n"
        
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        
    except Exception as e:
        st.error(f"AI回答生成エラー: {e}")
        fallback_response = f"""申し訳ございません。一時的なエラーが発生しました。

{prompt}について、基本的なアドバイスをお答えします：

【基本的な対処法】
1. 安全確認を最優先に行ってください
2. 専門的な作業は専門店に相談することをお勧めします
3. 応急処置が必要な場合は、安全な方法で行ってください

📞 お問い合わせ
直接スタッフにお尋ねをご希望の方は、お問い合わせフォームまたはお電話（086-206-6622）で受付けております。

【営業時間】年中無休（9:00～21:00）
※不在時は折り返しお電話差し上げます。"""
        
        st.session_state.messages.append({"role": "assistant", "content": fallback_response})

def main():
    st.set_page_config(
        page_title="キャンピングカー修理専門 AIチャット",
        page_icon="🔧",
        layout="wide"
    )

    st.markdown("""
    <div style="text-align: center; padding: 30px 20px; background: rgba(255, 255, 255, 0.95); border-radius: 20px; margin-bottom: 30px;">
        <h1 style="font-size: 2.5em; font-weight: 700; margin-bottom: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🔧 キャンピングカー修理専門 AIチャット</h1>
        <p style="font-size: 1.1em; color: #6c757d;">経験豊富なAIがキャンピングカーの修理について詳しくお答えします</p>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # よくある質問ボタン
    st.markdown("### 💡 よくある質問 (クリックで質問)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔋 バッテリー上がり"):
            question = "バッテリーが上がってエンジンが始動しない時の対処法を教えてください。"
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                generate_ai_response(question)
            st.rerun()
    
    with col2:
        if st.button("💧 水道ポンプ"):
            question = "水道ポンプが動かない時の対処法と修理手順を教えてください。"
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                generate_ai_response(question)
            st.rerun()
    
    with col3:
        if st.button("🆕 新しい会話"):
            st.session_state.messages = []
            st.rerun()

    # チャット履歴の表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ユーザー入力
    if prompt := st.chat_input("キャンピングカーの修理について質問してください..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            generate_ai_response(prompt)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"アプリケーションエラー: {e}")
        st.info("ページを再読み込みしてください。")
