# full_category_migration.py
import json
import csv
from notion_client import Client
import os
import time

# 環境変数から設定を取得
API_KEY = os.getenv("NOTION_API_KEY")
NODE_DB = os.getenv("NODE_DB_ID")
CASE_DB = os.getenv("CASE_DB_ID")
ITEM_DB = os.getenv("ITEM_DB_ID")

client = Client(auth=API_KEY)

def migrate_all_categories():
    """全カテゴリのデータを移行"""
    print("🚀 全カテゴリデータ移行を開始...")
    
    # 利用可能なカテゴリ
    categories = [
        "サブバッテリー", "バッテリー", "走行充電", "換気扇・排気システム",
        "室内収納・家具", "室内灯・LED", "トイレ", "FFヒーター", 
        "インバーター", "冷蔵庫", "水道ポンプ", "ソーラーパネル",
        "ガスコンロ", "ウインドウ", "雨漏り", "車体外装の破損",
        "異音", "電装系", "外部電源", "排水タンク", "家具"
    ]
    
    # mock_diagnostic_nodes.jsonを読み込み
    with open('mock_diagnostic_nodes.json', 'r', encoding='utf-8') as f:
        diagnostic_data = json.load(f)
    
    created_nodes = {}
    total_migrated = 0
    
    print(f"📋 移行対象カテゴリ: {len(categories)}カテゴリ")
    
    # 各カテゴリのノードを移行
    for category in categories:
        print(f"\n   {category}カテゴリの移行中...")
        category_nodes = 0
        
        # そのカテゴリのノードを抽出
        for node_data in diagnostic_data:
            for node_id, node_info in node_data.items():
                if node_info.get("category") == category:
                    try:
                        # Notionに追加
                        properties = {
                            "ノードID": {
                                "title": [{"text": {"content": node_id}}]
                            },
                            "質問内容": {
                                "rich_text": [{"text": {"content": node_info.get("question", "")}}]
                            },
                            "診断結果": {
                                "rich_text": [{"text": {"content": node_info.get("result", "")}}]
                            },
                            "カテゴリ": {
                                "rich_text": [{"text": {"content": category}}]
                            },
                            "開始フラグ": {
                                "checkbox": node_info.get("is_start", False)
                            },
                            "終端フラグ": {
                                "checkbox": node_info.get("is_end", False)
                            },
                            "次のノード": {
                                "rich_text": [{"text": {"content": ", ".join(node_info.get("next_nodes", []))}}]
                            }
                        }
                        
                        response = client.pages.create(
                            parent={"database_id": NODE_DB},
                            properties=properties
                        )
                        
                        created_nodes[node_id] = response["id"]
                        category_nodes += 1
                        
                        if category_nodes % 10 == 0:
                            print(f"  ✅ {category_nodes}件完了")
                            
                    except Exception as e:
                        print(f"  ❌ {node_id} の移行に失敗: {e}")
        
        total_migrated += category_nodes
        print(f"  📊 {category}: {category_nodes}件完了")
        
        # API制限を避けるため少し待機
        time.sleep(1)
    
    print(f"\n🎉 全カテゴリ移行完了！")
    print(f"📈 総移行件数: {total_migrated}件")
    print(f"📋 成功したノード数: {len(created_nodes)}件")
    
    return created_nodes

def migrate_repair_cases():
    """修理ケースデータを移行"""
    print("\n🔧 修理ケースデータの移行を開始...")
    
    # CSVファイルを読み込み
    with open('修理ケースDB 24d709bb38f18039a8b3e0bec10bb7eb.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cases = list(reader)
    
    created_cases = {}
    
    for case in cases:
        try:
            properties = {
                "ケースID": {
                    "title": [{"text": {"content": case.get("case_id", f"CASE-{len(created_cases)+1:04d}")}}]
                },
                "症状": {
                    "rich_text": [{"text": {"content": case.get("症状", "")}}]
                },
                "修理手順": {
                    "rich_text": [{"text": {"content": case.get("修理手順", "")}}]
                },
                "必要な部品": {
                    "rich_text": [{"text": {"content": case.get("必要な部品", "")}}]
                },
                "必要な工具": {
                    "rich_text": [{"text": {"content": case.get("必要な工具", "")}}]
                },
                "推定時間": {
                    "rich_text": [{"text": {"content": case.get("推定時間", "")}}]
                },
                "難易度": {
                    "rich_text": [{"text": {"content": case.get("難易度", "")}}]
                },
                "注意事項": {
                    "rich_text": [{"text": {"content": case.get("注意事項", "")}}]
                }
            }
            
            response = client.pages.create(
                parent={"database_id": CASE_DB},
                properties=properties
            )
            
            case_id = case.get("case_id", f"CASE-{len(created_cases)+1:04d}")
            created_cases[case_id] = response["id"]
            print(f"  ✅ {case_id} を追加しました")
            
        except Exception as e:
            print(f"  ❌ ケースの追加に失敗: {e}")
    
    print(f"📊 修理ケース移行完了: {len(created_cases)}件")
    return created_cases

def migrate_items():
    """部品・工具データを移行"""
    print("\n🔧 部品・工具データの移行を開始...")
    
    # 基本的な部品・工具リスト
    items = [
        {"name": "バッテリー", "category": "バッテリー", "price": "15,000円〜", "supplier": "カー用品店"},
        {"name": "ブースターケーブル", "category": "工具", "price": "3,000円〜", "supplier": "ホームセンター"},
        {"name": "テスター", "category": "工具", "price": "2,000円〜", "supplier": "ホームセンター"},
        {"name": "バッテリーチャージャー", "category": "工具", "price": "8,000円〜", "supplier": "カー用品店"},
        {"name": "端子クリーナー", "category": "工具", "price": "1,500円〜", "supplier": "ホームセンター"},
        {"name": "冷蔵庫", "category": "冷蔵庫", "price": "50,000円〜", "supplier": "キャンピングカー専門店"},
        {"name": "FFヒーター", "category": "ヒーター", "price": "80,000円〜", "supplier": "キャンピングカー専門店"},
        {"name": "インバーター", "category": "電装系", "price": "20,000円〜", "supplier": "カー用品店"},
        {"name": "水道ポンプ", "category": "ポンプ", "price": "5,000円〜", "supplier": "キャンピングカー専門店"},
        {"name": "トイレ", "category": "トイレ", "price": "30,000円〜", "supplier": "キャンピングカー専門店"}
    ]
    
    created_items = {}
    
    for item in items:
        try:
            properties = {
                "部品名": {
                    "title": [{"text": {"content": item["name"]}}]
                },
                "カテゴリ": {
                    "rich_text": [{"text": {"content": item["category"]}}]
                },
                "価格": {
                    "rich_text": [{"text": {"content": item["price"]}}]
                },
                "購入先": {
                    "rich_text": [{"text": {"content": item["supplier"]}}]
                },
                "在庫状況": {
                    "rich_text": [{"text": {"content": "在庫あり"}}]
                }
            }
            
            response = client.pages.create(
                parent={"database_id": ITEM_DB},
                properties=properties
            )
            
            created_items[item["name"]] = response["id"]
            print(f"  ✅ {item['name']} を追加しました")
            
        except Exception as e:
            print(f"  ❌ {item['name']} の追加に失敗: {e}")
    
    print(f"📊 部品・工具移行完了: {len(created_items)}件")
    return created_items

if __name__ == "__main__":
    print("🚀 全カテゴリデータ移行スクリプト開始")
    print("=" * 50)
    
    # 各データベースの移行を実行
    nodes = migrate_all_categories()
    cases = migrate_repair_cases()
    items = migrate_items()
    
    print("\n" + "=" * 50)
    print("✅ 全データ移行完了！")
    print("=" * 50)
    print(f"📈 総合結果:")
    print(f"  診断ノード: {len(nodes)}件")
    print(f"  修理ケース: {len(cases)}件")
    print(f"  部品・工具: {len(items)}件")
    print(f"  合計: {len(nodes) + len(cases) + len(items)}件")
    print("=" * 50)