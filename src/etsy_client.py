import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ETSY_API_KEY")
SHARED_SECRET = os.getenv("ETSY_SHARED_SECRET")
ACCESS_TOKEN = os.getenv("ETSY_ACCESS_TOKEN")
SHOP_ID = os.getenv("ETSY_SHOP_ID")
BASE_URL = "https://openapi.etsy.com/v3/application"

HEADERS = {
    "x-api-key": f"{API_KEY}:{SHARED_SECRET}",
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}


def get_shop_id():
    """通过 access token 拿到自己的 shop ID"""
    url = f"{BASE_URL}/users/me"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    shop_id = data.get("shop_id")
    print(f"Etsy Shop ID: {shop_id}")
    return shop_id

def get_orders(shop_id, limit=100, since=None):
    orders = []
    offset = 0

    while True:
        url = f"{BASE_URL}/shops/{shop_id}/receipts"
        params = {
            "limit": limit,
            "offset": offset,
            "was_paid": "true"
        }
        if since:
            params["min_created"] = since
            
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        orders.extend(results)
        if len(results) < limit:
            break
        offset += limit

    print(f"Etsy: 拿到 {len(orders)} 个订单")
    return orders

# def get_orders(shop_id, limit=100):
    # """拉取所有订单"""
    # orders = []
    # offset = 0

    # while True:
    #     url = f"{BASE_URL}/shops/{shop_id}/receipts"
    #     params = {
    #         "limit": limit,
    #         "offset": offset,
    #         "was_paid": "true"
    #     }
    #     response = requests.get(url, headers=HEADERS, params=params)
    #     response.raise_for_status()
    #     data = response.json()

    #     results = data.get("results", [])
    #     orders.extend(results)

    #     if len(results) < limit:
    #         break
    #     offset += limit

    # print(f"Etsy: 拿到 {len(orders)} 个订单")
    # return orders

def get_listings(shop_id, limit=100):
    """拉取所有 active listings"""
    listings = []
    offset = 0

    while True:
        url = f"{BASE_URL}/shops/{shop_id}/listings/active"
        params = {
            "limit": limit,
            "offset": offset,
        }
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        listings.extend(results)

        if len(results) < limit:
            break
        offset += limit

    print(f"Etsy: 拿到 {len(listings)} 个 listings")
    return listings

if __name__ == "__main__":
    print("测试 Etsy 连接...")
    shop_id = os.getenv("ETSY_SHOP_ID")
    print(f"使用 shop ID: {shop_id}")
    orders = get_orders(shop_id)
    listings = get_listings(shop_id)
    if orders:
        print("\n订单样本:")
        print(orders[0])
    if listings:
        print("\nListing 样本:")
        print(listings[0])