
from notion_client import Client
import os, re, sys
from typing import Dict, List, Any

# ====== 環境変数 ======
API_KEY   = os.getenv("NOTION_API_KEY", "").strip()
NODE_DB   = os.getenv("NODE_DB_ID", "").strip()
CASE_DB   = os.getenv("CASE_DB_ID", "").strip()
ITEM_DB   = os.getenv("ITEM_DB_ID", "").strip()
DRY_RUN   = os.getenv("DRY_RUN", "").strip().lower() in {"1","true","yes","y","on"}

if not API_KEY or not NODE_DB or not CASE_DB or not ITEM_DB:
    print("環境変数 NOTION_API_KEY / NODE_DB_ID / CASE_DB_ID / ITEM_DB_ID を設定してください。")
    sys.exit(1)

client = Client(auth=API_KEY)

# ====== プロパティ名 ======
# 修理ケースDB
P_CASE_ID           = "case_id"         # 追加する技術用キー（rich_text）
P_HITSUYO_BUHIN     = "必要な部品"       # マルチセレクト or テキスト
P_HITSUYO_KOUGU     = "必要な工具"       # マルチセレクト or テキスト

# 部品・工具DB
P_ITEM_NAME         = "部品名"
P_ITEM_CATEGORY     = "カテゴリ"         # セレクト：バッテリー/冷蔵庫/ヒーター/ポンプ/その他/工具

# 診断フローDB
P_NODE_TERM_ID      = "terminal_case_id" # 追加する技術用キー（rich_text）
P_NODE_ISEND        = "終端フラグ"       # checkbox

# Relation プロパティ名（Notion上で作成）
REL_NODE_TO_CASE    = "修理ケース（Relation）"
REL_CASE_TO_ITEMS   = "必要部品（Rel）"
REL_CASE_TO_TOOLS   = "必要工具（Rel）"

def norm(s: Any) -> str:
    return str(s).strip()

def split_multi_text(s: str):
    if not s: return []
    import re
    s2 = re.sub(r"[、,/・;|]", "|", s)
    return [w.strip() for w in s2.split("|") if w.strip()]

def fetch_all_pages(db_id: str):
    results, cursor = [], None
    while True:
        resp = client.databases.query(database_id=db_id, start_cursor=cursor) if cursor else client.databases.query(database_id=db_id)
        results.extend(resp["results"])
        if not resp.get("has_more"): break
        cursor = resp.get("next_cursor")
    return results

def get_prop_text(prop: dict) -> str:
    t = prop.get("type")
    if t == "title":        return "".join([x.get("plain_text","") for x in prop["title"]])
    if t == "rich_text":    return "".join([x.get("plain_text","") for x in prop["rich_text"]])
    if t == "url":          return prop.get("url") or ""
    if t == "number":       return "" if prop.get("number") is None else str(prop["number"])
    if t == "select":       return prop.get("select",{}).get("name","") if prop.get("select") else ""
    if t == "multi_select": return "｜".join([x.get("name","") for x in prop.get("multi_select",[])])
    if t == "checkbox":     return "1" if prop.get("checkbox") else "0"
    return ""

def get_prop_multi(prop: dict):
    t = prop.get("type")
    if t == "multi_select":
        return [x.get("name","").strip() for x in prop.get("multi_select",[]) if x.get("name","").strip()]
    txt = get_prop_text(prop)
    return split_multi_text(txt)

def update_page_relation(page_id: str, rel_name: str, target_ids):
    if DRY_RUN:
        print(f"[DRY RUN] update relation {rel_name} -> {len(target_ids)}件 on page {page_id}")
        return
    client.pages.update(page_id=page_id, properties={
        rel_name: {"type":"relation","relation":[{"id": rid} for rid in target_ids]}
    })

# ====== 2) マスター辞書の作成 ======
# ケース：case_id -> page_id
cases = fetch_all_pages(CASE_DB)
case_by_id = {}
for p in cases:
    props = p["properties"]
    cid = norm(get_prop_text(props.get(P_CASE_ID, {"type":"rich_text","rich_text":[]})))
    if cid:
        case_by_id[cid] = p["id"]
print(f"[INFO] ケース件数: {len(cases)} / case_idあり: {len(case_by_id)}")

# 部品：部品名 -> (page_id, カテゴリ)
items = fetch_all_pages(ITEM_DB)
item_map = {}
for p in items:
    props = p["properties"]
    name = norm(get_prop_text(props.get(P_ITEM_NAME, {"type":"title","title":[]})))
    cat  = norm(get_prop_text(props.get(P_ITEM_CATEGORY, {"type":"select","select":None})))
    if name:
        item_map[name] = {"id": p["id"], "cat": cat}
print(f"[INFO] 部品・工具件数: {len(items)} / 部品名あり: {len(item_map)}")

# ====== 3) 診断→ケース のリンク（終端だけ） ======
nodes = fetch_all_pages(NODE_DB)
link_count = 0
skip_term_empty = 0
skip_not_found = 0

for p in nodes:
    props = p["properties"]
    is_end = get_prop_text(props.get(P_NODE_ISEND, {"type":"checkbox","checkbox":False})).strip() in {"1","true","True","TRUE"}
    if not is_end:
        continue
    term = norm(get_prop_text(props.get(P_NODE_TERM_ID, {"type":"rich_text","rich_text":[]})))
    if not term:
        skip_term_empty += 1
        continue
    if term not in case_by_id:
        skip_not_found += 1
        continue
    update_page_relation(p["id"], REL_NODE_TO_CASE, [case_by_id[term]])
    link_count += 1

print(f"[DONE] 診断→ケース: リンク {link_count}件 / terminal_case_id 空 {skip_term_empty} / case_id不明 {skip_not_found}")

# ====== 4) ケース→部品/工具 のリンク ======
case_item_links = 0
case_tool_links = 0

for p in cases:
    props = p["properties"]
    # 必要な部品（multi-select or text）
    parts = get_prop_multi(props.get(P_HITSUYO_BUHIN, {"type":"multi_select","multi_select":[]}))
    part_ids = [item_map[n]["id"] for n in parts if n in item_map]
    if part_ids:
        update_page_relation(p["id"], REL_CASE_TO_ITEMS, part_ids)
        case_item_links += 1

    # 必要な工具（multi-select or text）
    tools = get_prop_multi(props.get(P_HITSUYO_KOUGU, {"type":"multi_select","multi_select":[]}))
    tool_ids = []
    for n in tools:
        if n in item_map:
            # カテゴリ=工具を優先（合わなくても名前一致で許容）
            if item_map[n]["cat"] in {"工具","tool","TOOL"} or item_map[n]["cat"] == "":
                tool_ids.append(item_map[n]["id"])
            else:
                tool_ids.append(item_map[n]["id"])
    if tool_ids:
        update_page_relation(p["id"], REL_CASE_TO_TOOLS, tool_ids)
        case_tool_links += 1

print(f"[DONE] ケース→部品/工具: 部品リンク {case_item_links}件 / 工具リンク {case_tool_links}件")
print("完了。DRY_RUN=true で検証のみも可能です。")
