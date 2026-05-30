import requests
import os
from dotenv import load_dotenv

load_dotenv()

USER_TOKEN = os.getenv("EBAY_USER_TOKEN")
BASE_URL = "https://api.ebay.com"

HEADERS = {
    "Authorization": f"Bearer {USER_TOKEN}",
    "Content-Type": "application/json",
    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
}

def get_orders(limit=50):
    """拉取所有订单"""
    orders = []
    url = f"{BASE_URL}/sell/fulfillment/v1/order"
    params = {
        "limit": limit,
        "filter": "orderfulfillmentstatus:{NOT_STARTED|IN_PROGRESS|FULFILLED}"
    }

    while True:
        response = requests.get(url, headers=HEADERS, params=params)
        if not response.ok:
            print(f"eBay 错误: {response.status_code}")
            print(response.text)
            break

        data = response.json()
        results = data.get("orders", [])
        orders.extend(results)

        next_url = data.get("next")
        if not next_url:
            break
        url = next_url
        params = {}

    print(f"eBay: 拿到 {len(orders)} 个订单")
    return orders

def get_inventory(limit=100):
    """拉取库存"""
    inventory = []
    url = f"{BASE_URL}/sell/inventory/v1/inventory_item"
    params = {"limit": limit}

    while True:
        response = requests.get(url, headers=HEADERS, params=params)
        if not response.ok:
            print(f"eBay inventory 错误: {response.status_code}")
            print(response.text)
            break

        data = response.json()
        results = data.get("inventoryItems", [])
        inventory.extend(results)

        next_url = data.get("next")
        if not next_url:
            break
        url = next_url
        params = {}

    print(f"eBay: 拿到 {len(inventory)} 个库存条目")
    return inventory

if __name__ == "__main__":
    print("测试 eBay 连接...")
    orders = get_orders()
    inventory = get_inventory()
    if orders:
        print("\n订单样本:")
        print(orders[0])
    if inventory:
        print("\n库存样本:")
        print(inventory[0])