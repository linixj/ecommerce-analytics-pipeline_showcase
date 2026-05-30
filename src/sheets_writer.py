import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_client():
    creds = Credentials.from_service_account_file(
        os.getenv("GOOGLE_CREDENTIALS_PATH"),
        scopes=SCOPES
    )
    return gspread.authorize(creds)

def get_spreadsheet(client):
    """open spreadsheet"""
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    spreadsheet = client.open_by_key(spreadsheet_id)
    print(f"open spreadsheet: {spreadsheet.title}")
    return spreadsheet

def get_or_create_worksheet(spreadsheet, title, headers):
    """找到已有的 worksheet，没有就创建并写入 headers"""
    try:
        ws = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(headers))
        ws.append_row(headers)
        print(f"创建新 tab: {title}")
    return ws

def write_orders(spreadsheet, orders):
    """把订单数据写入 Orders tab，追加不重复的记录"""
    headers = [
        "order_id", "platform", "created_at", "sku", "product_name",
        "variant", "quantity", "unit_price", "subtotal", "discount",
        "grand_total", "fulfillment_status", "currency"
    ]
    ws = get_or_create_worksheet(spreadsheet, "Orders", headers)

    # 拿到已有的 order_id + platform 组合，避免重复写入
    existing = ws.get_all_values()
    existing_keys = set()
    if len(existing) > 1:
        id_col = headers.index("order_id")
        platform_col = headers.index("platform")
        for row in existing[1:]:
            if len(row) > platform_col:
                existing_keys.add((row[id_col], row[platform_col]))

    new_rows = []
    for order in orders:
        key = (str(order["order_id"]), order["platform"])
        if key not in existing_keys:
            new_rows.append([str(order.get(h, "")) for h in headers])

    if new_rows:
        ws.append_rows(new_rows, value_input_option="USER_ENTERED")
        print(f"写入 {len(new_rows)} 条新订单记录")
    else:
        print("没有新订单需要写入")

def write_inventory(spreadsheet, inventory):
    """把库存数据写入 Inventory tab，每次全量覆盖"""
    headers = ["sku", "product_name", "platform", "quantity_available", "is_unlimited"]
    ws = get_or_create_worksheet(spreadsheet, "Inventory", headers)

    # 全量覆盖：清空旧数据，保留 header
    ws.clear()
    ws.append_row(headers)

    rows = [[str(item.get(h, "")) for h in headers] for item in inventory]
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
        print(f"写入 {len(rows)} 条库存记录")

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from src.squarespace_client import get_orders, get_inventory
    from src.normalize import normalize_squarespace_orders, normalize_squarespace_inventory

    client = get_client()
    spreadsheet = get_spreadsheet(client)

    orders = get_orders()
    inventory = get_inventory()

    normalized_orders = normalize_squarespace_orders(orders)
    normalized_inventory = normalize_squarespace_inventory(inventory)

    write_orders(spreadsheet, normalized_orders)
    write_inventory(spreadsheet, normalized_inventory)

    print(f"\n完成！查看结果: {spreadsheet.url}")