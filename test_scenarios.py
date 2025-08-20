import os
import glob
from langchain_community.document_loaders import TextLoader

def test_scenario_files():
    """シナリオファイルの読み込みテスト"""
    main_path = os.path.dirname(os.path.abspath(__file__))
    
    print("=== シナリオファイル読み込みテスト ===")
    
    # テキストファイルを検索
    txt_pattern = os.path.join(main_path, "*.txt")
    txt_files = glob.glob(txt_pattern)
    
    scenario_files = []
    other_files = []
    
    for txt_path in txt_files:
        filename = os.path.basename(txt_path)
        if "シナリオ" in filename:
            scenario_files.append(txt_path)
        else:
            other_files.append(txt_path)
    
    print(f"\n📁 見つかったシナリオファイル: {len(scenario_files)}個")
    for file_path in sorted(scenario_files):
        filename = os.path.basename(file_path)
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            docs = loader.load()
            content_length = len(docs[0].page_content) if docs else 0
            print(f"✅ {filename} ({content_length}文字)")
        except Exception as e:
            print(f"❌ {filename} - エラー: {e}")
    
    print(f"\n📁 その他のテキストファイル: {len(other_files)}個")
    for file_path in sorted(other_files):
        filename = os.path.basename(file_path)
        print(f"📄 {filename}")
    
    # 各シナリオファイルの内容を確認
    print("\n=== シナリオファイル内容確認 ===")
    for file_path in sorted(scenario_files):
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                first_line = lines[0] if lines else "空のファイル"
                print(f"\n📋 {filename}")
                print(f"   最初の行: {first_line}")
                print(f"   文字数: {len(content)}")
        except Exception as e:
            print(f"❌ {filename} - 読み込みエラー: {e}")

if __name__ == "__main__":
    test_scenario_files() 