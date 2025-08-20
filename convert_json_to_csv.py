import json
import pandas as pd
import os

def convert_json_to_csv():
    """JSONファイルをCSVに変換して既存のCSVファイルに追加"""
    
    # JSONファイルを読み込み
    with open('mock_diagnostic_nodes.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # 既存のCSVファイルを読み込み
    existing_csv = pd.read_csv('diag_nodes_linked_5nodes.csv', encoding='utf-8')
    
    # JSONデータをCSV形式に変換
    new_rows = []
    for node_id, node_data in json_data.items():
        # 既存のCSVに同じnode_idがあるかチェック
        if node_id not in existing_csv['node_id'].values:
            new_row = {
                'node_id': node_id,
                '質問ID': node_id.replace('_', '-'),
                '対象名称': node_data['question'] or '診断結果',
                '質問内容': node_data['question'],
                '回答パターン': 'はい<br>いいえ' if node_data['question'] else '',
                '次の質問ID': ','.join(node_data['next_nodes']),
                '診断結果': node_data['result'],
                '信頼度': 90 if node_data['is_end'] else 30,
                'カテゴリ': node_data['category'],
                '優先度': '高',
                '終端フラグ': 1 if node_data['is_end'] else 0,
                'terminal_case_id': f'CASE-{node_id.upper()}' if node_data['is_end'] else ''
            }
            new_rows.append(new_row)
    
    # 新しい行をDataFrameに追加
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        combined_df = pd.concat([existing_csv, new_df], ignore_index=True)
        
        # CSVファイルに保存
        combined_df.to_csv('diag_nodes_linked_5nodes.csv', index=False, encoding='utf-8')
        print(f"✅ {len(new_rows)}個の新しい診断ノードを追加しました")
    else:
        print("ℹ️ 追加する新しい診断ノードはありません")

def add_control_panel_diagnostic():
    """制御パネル診断データを直接追加"""
    
    # 既存のCSVファイルを読み込み
    existing_csv = pd.read_csv('diag_nodes_linked_5nodes.csv', encoding='utf-8')
    
    # 制御パネル診断データ
    control_panel_data = [
        {
            'node_id': 'NODE-5001',
            '質問ID': '5001',
            '対象名称': '制御パネルに関する問題ですか？',
            '質問内容': '制御パネルに関する問題ですか？',
            '回答パターン': 'はい<br>いいえ',
            '次の質問ID': '5002,5008',
            '診断結果': '',
            '信頼度': 30,
            'カテゴリ': '制御',
            '優先度': '高',
            '終端フラグ': 0,
            'terminal_case_id': ''
        },
        {
            'node_id': 'NODE-5002',
            '質問ID': '5002',
            '対象名称': '制御パネル電源確認',
            '質問内容': 'パネルに電源は来ていますか？',
            '回答パターン': 'はい<br>いいえ',
            '次の質問ID': '5003,5009',
            '診断結果': '',
            '信頼度': 50,
            'カテゴリ': '制御',
            '優先度': '高',
            '終端フラグ': 0,
            'terminal_case_id': ''
        },
        {
            'node_id': 'NODE-5003',
            '質問ID': '5003',
            '対象名称': '制御パネル表示確認',
            '質問内容': '表示は正常に点灯していますか？',
            '回答パターン': 'はい<br>いいえ',
            '次の質問ID': '5004,5009',
            '診断結果': '',
            '信頼度': 65,
            'カテゴリ': '制御',
            '優先度': '高',
            '終端フラグ': 0,
            'terminal_case_id': ''
        },
        {
            'node_id': 'NODE-5004',
            '質問ID': '5004',
            '対象名称': '制御パネル操作確認',
            '質問内容': 'ボタン操作に反応しますか？',
            '回答パターン': 'はい<br>いいえ',
            '次の質問ID': '5005,5009',
            '診断結果': '',
            '信頼度': 80,
            'カテゴリ': '制御',
            '優先度': '高',
            '終端フラグ': 0,
            'terminal_case_id': ''
        },
        {
            'node_id': 'NODE-5005',
            '質問ID': '5005',
            '対象名称': '制御パネルセンサー確認',
            '質問内容': 'センサー値（電圧/水量など）は正しく表示されていますか？',
            '回答パターン': 'はい<br>いいえ',
            '次の質問ID': '5006,5009',
            '診断結果': '',
            '信頼度': 90,
            'カテゴリ': '制御',
            '優先度': '高',
            '終端フラグ': 0,
            'terminal_case_id': ''
        },
        {
            'node_id': 'NODE-5006',
            '質問ID': '5006',
            '対象名称': '制御パネル異常診断',
            '質問内容': '',
            '回答パターン': '',
            '次の質問ID': '',
            '診断結果': '**制御パネル異常**\n\n**対処法：**\n1. 再起動/リセット\n2. 配線・センサー点検',
            '信頼度': 90,
            'カテゴリ': '制御',
            '優先度': '高',
            '終端フラグ': 1,
            'terminal_case_id': 'CASE-CTRL-001'
        },
        {
            'node_id': 'NODE-5008',
            '質問ID': '5008',
            '対象名称': '制御パネル他系統問題',
            '質問内容': '',
            '回答パターン': '',
            '次の質問ID': '',
            '診断結果': '**別系統の問題**\n\n**対処法：**\n1. 他の診断フローを試してください\n2. 専門業者への相談',
            '信頼度': 90,
            'カテゴリ': '制御',
            '優先度': '高',
            '終端フラグ': 1,
            'terminal_case_id': 'CASE-CTRL-003'
        },
        {
            'node_id': 'NODE-5009',
            '質問ID': '5009',
            '対象名称': '制御パネル正常診断',
            '質問内容': '',
            '回答パターン': '',
            '次の質問ID': '',
            '診断結果': '**正常動作**\n\n**対処法：**\n1. 通常の使用を継続\n2. 定期的な点検',
            '信頼度': 90,
            'カテゴリ': '制御',
            '優先度': '高',
            '終端フラグ': 1,
            'terminal_case_id': 'CASE-CTRL-002'
        }
    ]
    
    # 新しいデータをDataFrameに変換
    new_df = pd.DataFrame(control_panel_data)
    
    # 既存のCSVと結合
    combined_df = pd.concat([existing_csv, new_df], ignore_index=True)
    
    # CSVファイルに保存
    combined_df.to_csv('diag_nodes_linked_5nodes.csv', index=False, encoding='utf-8')
    print(f"✅ 制御パネル診断データを追加しました")

if __name__ == "__main__":
    print("CSVファイルに診断データを追加します...")
    
    # 方法1: JSONから変換
    if os.path.exists('mock_diagnostic_nodes.json'):
        convert_json_to_csv()
    
    # 方法2: 制御パネル診断データを直接追加
    add_control_panel_diagnostic()
    
    print("✅ 完了しました！")
