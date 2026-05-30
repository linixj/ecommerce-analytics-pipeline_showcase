import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.squarespace_client import get_orders as ss_get_orders, get_inventory as ss_get_inventory
from src.etsy_client import get_orders as etsy_get_orders, get_listings as etsy_get_listings
from src.normalize import (
    normalize_squarespace_orders,
    normalize_squarespace_inventory,
    normalize_etsy_orders,
)
from src.sheets_writer import get_client, get_spreadsheet, write_orders, write_inventory

def run():
    print("=== Ecommerce Analytics Pipeline ===\n")

    # 1. 拉取数据
    print("--- 拉取 Squarespace 数据 ---")
    ss_orders = ss_get_orders()
    ss_inventory = ss_get_inventory()

    print("\n--- 拉取 Etsy 数据 ---")
    etsy_shop_id = os.getenv("ETSY_SHOP_ID")
    etsy_orders = etsy_get_orders(etsy_shop_id)

    # 2. Normalize
    print("\n--- Normalizing 数据 ---")
    normalized_orders = []
    normalized_orders.extend(normalize_squarespace_orders(ss_orders))
    normalized_orders.extend(normalize_etsy_orders(etsy_orders))
    normalized_inventory = normalize_squarespace_inventory(ss_inventory)

    print(f"总订单条目: {len(normalized_orders)}")
    print(f"总库存条目: {len(normalized_inventory)}")

    # 3. 写入 Sheets
    print("\n--- 写入 Google Sheets ---")
    client = get_client()
    spreadsheet = get_spreadsheet(client)
    write_orders(spreadsheet, normalized_orders)
    write_inventory(spreadsheet, normalized_inventory)

    print(f"\n完成！查看结果: {spreadsheet.url}")

if __name__ == "__main__":
    run()