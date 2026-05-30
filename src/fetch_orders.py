import os
import sys
import argparse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv


load_dotenv()

# 自动刷新 Etsy token
from src.refresh_etsy_token import refresh_access_token
refresh_access_token()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.squarespace_client import get_orders as ss_get_orders, get_inventory as ss_get_inventory
from src.etsy_client import get_orders as etsy_get_orders, get_listings as etsy_get_listings
from src.normalize import (
    normalize_squarespace_orders,
    normalize_squarespace_inventory,
    normalize_etsy_orders,
)
from src.sheets_writer import get_client, get_spreadsheet, write_orders, write_inventory


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch ecommerce orders and sync to Google Sheets")
    
    parser.add_argument(
        "--mode",
        choices=["incremental", "full"],
        default="incremental",
        help="incremental: 只拉指定天数内的新订单（默认）; full: 全量拉取"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="incremental 模式下拉取最近几天的数据（默认7天）"
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="自定义起始日期，格式 YYYY-MM-DD，例如 --since 2025-01-01"
    )
    parser.add_argument(
        "--platform",
        choices=["all", "squarespace", "etsy"],
        default="all",
        help="指定拉取哪个平台（默认all）"
    )
    
    return parser.parse_args()


def get_since_timestamp(args):
    """根据参数计算起始时间"""
    if args.mode == "full":
        return None, None
    
    if args.since:
        dt = datetime.strptime(args.since, "%Y-%m-%d")
    else:
        dt = datetime.now(tz=timezone.utc) - timedelta(days=args.days)

    
    iso_format = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    unix_format = int(dt.timestamp())
    
    return iso_format, unix_format


def fetch_squarespace(since_iso):
    """拉取 Squarespace 数据"""
    print(f"\n--- Squarespace {'全量' if not since_iso else f'自 {since_iso}'} ---")
    orders = ss_get_orders(since=since_iso)
    inventory = ss_get_inventory()
    return orders, inventory


def fetch_etsy(since_unix):
    """拉取 Etsy 数据"""
    if since_unix:
        since_str = datetime.fromtimestamp(since_unix).strftime("%Y-%m-%d")
        print(f"\n--- Etsy 自 {since_str} ---")
    else:
        print("\n--- Etsy 全量 ---")
    
    shop_id = os.getenv("ETSY_SHOP_ID")
    orders = etsy_get_orders(shop_id, since=since_unix)
    return orders


def run():
    args = parse_args()
    since_iso, since_unix = get_since_timestamp(args)
    
    print(f"\n=== Ecommerce Analytics Pipeline ===")
    print(f"模式: {args.mode}")
    print(f"平台: {args.platform}")
    if since_iso:
        print(f"起始时间: {since_iso}")
    
    all_orders = []
    all_inventory = []
    
    # 拉取数据
    if args.platform in ["all", "squarespace"]:
        ss_orders, ss_inventory = fetch_squarespace(since_iso)
        all_orders.extend(normalize_squarespace_orders(ss_orders))
        all_inventory.extend(normalize_squarespace_inventory(ss_inventory))
    
    if args.platform in ["all", "etsy"]:
        etsy_orders = fetch_etsy(since_unix)
        all_orders.extend(normalize_etsy_orders(etsy_orders))
    
    print(f"\n--- 汇总 ---")
    print(f"总订单条目: {len(all_orders)}")
    print(f"总库存条目: {len(all_inventory)}")
    
    # 写入 Sheets
    print(f"\n--- 写入 Google Sheets ---")
    client = get_client()
    spreadsheet = get_spreadsheet(client)
    write_orders(spreadsheet, all_orders)
    if all_inventory:
        write_inventory(spreadsheet, all_inventory)
    
    print(f"\n完成！{spreadsheet.url}")


if __name__ == "__main__":
    run()