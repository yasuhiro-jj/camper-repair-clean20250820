import os
from dotenv import load_dotenv

# .envファイルを読み込み（存在する場合）
if os.path.exists('.env'):
    try:
        load_dotenv()
    except UnicodeDecodeError:
        # .envファイルのエンコーディングエラーの場合、無視して続行
        print("Warning: .envファイルのエンコーディングエラーを無視して続行します")
    except Exception as e:
        # その他のエラーの場合も無視して続行
        print(f"Warning: .envファイルの読み込みエラーを無視して続行します: {e}")
else:
    print("Info: .envファイルが見つかりません。環境変数を設定してください。")

# APIキーの設定（環境変数から取得）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "default")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

# LangChain Tracing設定
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT

# LangSmith設定（APIキーが設定されている場合のみ）
if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT
    print("Info: LangSmith設定が有効になりました")
else:
    print("Warning: LANGSMITH_API_KEYが設定されていません。LangSmith機能は無効です。")

# APIキーが設定されていない場合の警告
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEYが設定されていません。環境変数を設定してください。")
if not SERP_API_KEY:
    print("Warning: SERP_API_KEYが設定されていません。環境変数を設定してください。")