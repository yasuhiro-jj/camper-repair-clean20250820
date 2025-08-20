import streamlit_app
import os

def test_rag_system():
    print("=== RAGシステムテスト開始 ===")
    
    # ドキュメントの読み込みテスト
    print("\n1. ドキュメント読み込みテスト")
    documents = streamlit_app.initialize_database()
    print(f"読み込まれたドキュメント数: {len(documents)}")
    
    for i, doc in enumerate(documents[:10]):  # 最初の10件のみ表示
        source = doc.metadata.get('source', 'unknown')
        print(f"  {i+1}. {os.path.basename(source)}")
        if hasattr(doc, 'page_content'):
            content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
            print(f"     内容プレビュー: {content_preview}")
    
    # 関連ブログ抽出テスト
    print("\n2. 関連ブログ抽出テスト")
    test_questions = [
        "バッテリーの調子が悪い",
        "バッテリーが上がった",
        "サブバッテリーの充電ができない",
        "冷蔵庫が冷えない",
        "水道ポンプが動かない"
    ]
    
    for question in test_questions:
        print(f"\n質問: '{question}'")
        related_blogs = streamlit_app.extract_scenario_related_blogs(documents, question)
        print(f"見つかった関連ブログ数: {len(related_blogs)}")
        
        for i, blog in enumerate(related_blogs[:3]):  # 上位3件のみ表示
            print(f"  {i+1}. {blog['category']} (スコア: {blog['relevance_score']}点)")
            print(f"     タイトル: {blog['title']}")
            print(f"     ソースファイル: {blog['source_file']}")

if __name__ == "__main__":
    test_rag_system()
