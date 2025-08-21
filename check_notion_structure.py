# check_notion_structure.py
from notion_client import Client
import os

# 環境変数から設定を取得
API_KEY = os.getenv("NOTION_API_KEY")
NODE_DB = os.getenv("NODE_DB_ID")
CASE_DB = os.getenv("CASE_DB_ID")
ITEM_DB = os.getenv("ITEM_DB_ID")

client = Client(auth=API_KEY)

def check_database_structure():
    """データベースの構造を確認"""
    print("   Notionデータベースの構造を確認中...")
    
    databases = [
        ("診断フローデータベース", NODE_DB),
        ("修理ケースデータベース", CASE_DB),
        ("部品・工具データベース", ITEM_DB)
    ]
    
    for db_name, db_id in databases:
        print(f"\n   {db_name} (ID: {db_id})")
        try:
            # データベースの詳細を取得
            db_info = client.databases.retrieve(database_id=db_id)
            properties = db_info.get("properties", {})
            
            print(f"利用可能なプロパティ:")
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get("type", "unknown")
                print(f"  - {prop_name} ({prop_type})")
                
                # セレクト型の場合は選択肢も表示
                if prop_type == "select" and "select" in prop_info:
                    options = prop_info["select"].get("options", [])
                    if options:
                        option_names = [opt.get("name", "") for opt in options]
                        print(f"    選択肢: {', '.join(option_names)}")
                        
        except Exception as e:
            print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_database_structure()