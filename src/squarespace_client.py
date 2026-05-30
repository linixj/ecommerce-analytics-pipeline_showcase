import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SQUARESPACE_API_KEY")
BASE_URL = "https://api.squarespace.com/1.0/commerce"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "User-Agent": "ecommerce-analytics-pipeline",
    "Content-Type": "application/json"
}

def get_orders(since=None):
    orders = []
    url = f"{BASE_URL}/orders"
    
    params = {}
    if since:
        params["modifiedAfter"] = since
        params["modifiedBefore"] = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    while True:
        response = requests.get(url, headers=HEADERS, params=params)
        if not response.ok:
            print(f"错误状态码: {response.status_code}")
            print(f"错误详情: {response.text}")
            break
        data = response.json()
        orders.extend(data.get("result", []))
        cursor = data.get("pagination", {}).get("nextPageCursor")
        if not cursor:
            break
        params["cursor"] = cursor

    print(f"Squarespace: 拿到 {len(orders)} 个订单")
    return orders
# def get_orders(cursor=None):
    # orders = []
    # url = f"{BASE_URL}/orders"
    
    # params = {}  # 先不加任何过滤参数，拉全量
    # if cursor:
    #     params["cursor"] = cursor

    # while True:
    #     response = requests.get(url, headers=HEADERS, params=params)
        
    #     # 先打印详细错误信息
    #     if not response.ok:
    #         print(f"错误状态码: {response.status_code}")
    #         print(f"错误详情: {response.text}")
    #         break
            
    #     data = response.json()
    #     orders.extend(data.get("result", []))
        
    #     cursor = data.get("pagination", {}).get("nextPageCursor")
    #     if not cursor:
    #         break
    #     params["cursor"] = cursor

    # print(f"Squarespace: 拿到 {len(orders)} 个订单")
    # return orders

def get_inventory():
    """拉取库存数据"""
    url = f"{BASE_URL}/inventory"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    
    inventory = data.get("inventory", [])
    print(f"Squarespace: 拿到 {len(inventory)} 个库存条目")
    return inventory

if __name__ == "__main__":
    print("测试 Squarespace 连接...")
    orders = get_orders()
    inventory = get_inventory()
    
    if orders:
        print(f"\n最新一个订单样本：")
        print(orders[0])