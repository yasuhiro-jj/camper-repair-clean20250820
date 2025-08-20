import requests


def test_search():
    """検索機能をテストする"""
    print("=== 検索機能テスト ===")
    
    # SerpAPIWrapperを使用したテスト
    from langchain_community.utilities import SerpAPIWrapper
    
    try:
        search_wrapper = SerpAPIWrapper(serpapi_api_key=os.getenv("SERP_API_KEY"))
        result = search_wrapper.run("LangChain株式会社 最新ニュース")
        print(f"✅ 検索成功: {result[:200]}...")
        return True
    except Exception as e:
        print(f"❌ 検索エラー: {e}")
        return False

if __name__ == "__main__":
    test_search() 