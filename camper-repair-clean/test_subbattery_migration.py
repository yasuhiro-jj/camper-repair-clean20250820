# test_subbattery_migration.py
import json
from notion_client import Client
import os

# 環境変数から設定を取得
API_KEY = os.getenv("NOTION_API_KEY")
NODE_DB = os.getenv("NODE_DB_ID")
CASE_DB = os.getenv("CASE_DB_ID")
ITEM_DB = os.getenv("ITEM_DB_ID")

client = Client(auth=API_KEY)

def migrate_subbattery_test():
    """サブバッテリーカテゴリのみをテスト移行"""
    print("   サブバッテリーカテゴリのテスト移行を開始...")
    
    # サブバッテリー関連のノードのみを抽出
    subbattery_nodes = {
        "start_subbattery": {
            "question": "サブバッテリー（補助バッテリー）に関するトラブルでお困りですか？\n（電装品が使えない・一部機器の電源が入らない等も含みます）",
            "category": "サブバッテリー",
            "is_start": True,
            "is_end": False,
            "next_nodes": ["subbattery_charge", "subbattery_other"],
            "result": ""
        },
        "subbattery_dead": {
            "question": "",
            "category": "サブバッテリー",
            "is_start": False,
            "is_end": True,
            "next_nodes": [],
            "result": "   サブバッテリーが完全放電・使用不可の可能性があります。\n\n【対処法】\n1. ブースターケーブル（おすすめ：エーモン バッテリー用ケーブル）で応急措置可能。\n2. ポータブルバッテリーチャージャー（例：CTEK MXS 5.0）での充電も有効です。\n3. 数年以上使っている場合は新品交換（例：Panasonic ブルーバッテリー caos）がおすすめです。\n\n【ワンポイント】\nバッテリーの寿命（3-5年が目安）や使用頻度を考慮し、早めの交換で安心です。"
        },
        "subbattery_connection": {
            "question": "",
            "category": "サブバッテリー",
            "is_start": False,
            "is_end": True,
            "next_nodes": [],
            "result": "   サブバッテリー端子/配線の接続不良が疑われます。\n\n【対処法】\n1. 端子の清掃にはワイヤーブラシ（例：エーモン 端子クリーナー）を使うと便利です。\n2. 端子・配線の締め付けや接触状態をしっかり確認しましょう。\n3. 汚れや腐食がひどい場合は交換も視野に入れてください。\n\n【ワンポイント】\nDIYが不安な場合や難しい場合は、整備工場や購入店へご依頼ください。"
        }
    }
    
    created_pages = {}
    
    # 各診断ノードをNotionに追加
    for node_id, node_data in subbattery_nodes.items():
        print(f"📝 {node_id} を追加中...")
        
        # Notionページを作成
        properties = {
            "Name": {"title": [{"text": {"content": node_id}}]},
            "terminal_case_id": {"rich_text": [{"text": {"content": node_id}}]},
            "終端フラグ": {"checkbox": node_data.get("is_end", False)},
            "質問": {"rich_text": [{"text": {"content": node_data.get("question", "")}}]},
            "結果": {"rich_text": [{"text": {"content": node_data.get("result", "")}}]},
            "カテゴリ": {"select": {"name": node_data.get("category", "")}}
        }
        
        try:
            response = client.pages.create(
                parent={"database_id": NODE_DB},
                properties=properties
            )
            created_pages[node_id] = response["id"]
            print(f"✅ {node_id} を追加しました (ID: {response['id']})")
        except Exception as e:
            print(f"❌ {node_id} の追加に失敗: {e}")
    
    print(f"\n📊 移行結果:")
    print(f"成功: {len(created_pages)}件")
    print(f"失敗: {len(subbattery_nodes) - len(created_pages)}件")
    
    return created_pages

def test_repair_case_migration():
    """サブバッテリー関連の修理ケースをテスト移行"""
    print("\n   サブバッテリー関連修理ケースのテスト移行...")
    
    # サブバッテリー関連の修理ケース
    subbattery_cases = [
        {
            "name": "サブバッテリー完全放電",
            "case_id": "CASE-SUB-001",
            "症状": "サブバッテリーが完全放電・使用不可",
            "原因": "過放電、経年劣化",
            "修理手順": "1. ブースターケーブルで応急措置\n2. ポータブルバッテリーチャージャーで充電\n3. 新品交換（3-5年使用の場合）",
            "必要な部品": ["ブースターケーブル", "ポータブルバッテリーチャージャー", "サブバッテリー"],
            "必要な工具": ["テスター", "レンチ"],
            "推定コスト": 15000,
            "難易度": "初級",
            "作業時間": 30
        },
        {
            "name": "サブバッテリー端子接続不良",
            "case_id": "CASE-SUB-002", 
            "症状": "サブバッテリー端子/配線の接続不良",
            "原因": "端子の汚れ・腐食、配線の緩み",
            "修理手順": "1. 端子の清掃（ワイヤーブラシ使用）\n2. 端子・配線の締め直し\n3. 必要に応じて端子交換",
            "必要な部品": ["端子クリーナー", "バッテリー端子", "バッテリーグリス"],
            "必要な工具": ["ワイヤーブラシ", "レンチ", "ドライバー"],
            "推定コスト": 3000,
            "難易度": "初級",
            "作業時間": 20
        }
    ]
    
    created_cases = {}
    
    for case in subbattery_cases:
        print(f"   {case['name']} を追加中...")
        
        properties = {
            "Name": {"title": [{"text": {"content": case["name"]}}]},
            "case_id": {"rich_text": [{"text": {"content": case["case_id"]}}]},
            "症状": {"rich_text": [{"text": {"content": case["症状"]}}]},
            "原因": {"rich_text": [{"text": {"content": case["原因"]}}]},
            "修理手順": {"rich_text": [{"text": {"content": case["修理手順"]}}]},
            "必要な部品": {"multi_select": [{"name": item} for item in case["必要な部品"]]},
            "必要な工具": {"multi_select": [{"name": item} for item in case["必要な工具"]]},
            "推定コスト": {"number": case["推定コスト"]},
            "難易度": {"select": {"name": case["難易度"]}},
            "作業時間": {"number": case["作業時間"]}
        }
        
        try:
            response = client.pages.create(
                parent={"database_id": CASE_DB},
                properties=properties
            )
            created_cases[case["case_id"]] = response["id"]
            print(f"✅ {case['name']} を追加しました (ID: {response['id']})")
        except Exception as e:
            print(f"❌ {case['name']} の追加に失敗: {e}")
    
    print(f"\n📊 修理ケース移行結果:")
    print(f"成功: {len(created_cases)}件")
    print(f"失敗: {len(subbattery_cases) - len(created_cases)}件")
    
    return created_cases

if __name__ == "__main__":
    print("   サブバッテリーカテゴリのテスト移行を開始します...")
    print(f"📋 使用するデータベース:")
    print(f"  診断フローDB: {NODE_DB}")
    print(f"  修理ケースDB: {CASE_DB}")
    print(f"  部品・工具DB: {ITEM_DB}")
    print()
    
    # 診断ノードの移行
    created_nodes = migrate_subbattery_test()
    
    # 修理ケースの移行
    created_cases = test_repair_case_migration()
    
    print("\n✅ テスト移行完了！")
    print(f"📈 総合結果:")
    print(f"  診断ノード: {len(created_nodes)}件")
    print(f"  修理ケース: {len(created_cases)}件")