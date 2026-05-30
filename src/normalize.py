from datetime import datetime

def normalize_squarespace_orders(raw_orders):
    """把 Squarespace 原始订单数据转成统一格式"""
    normalized = []
    
    for order in raw_orders:
        order_id = order.get("orderNumber", "")
        created_at = order.get("createdOn", "")
        platform = "squarespace"
        fulfillment_status = order.get("fulfillmentStatus", "")
        
        # 一个订单可能有多个商品，每个 lineItem 单独一行
        for item in order.get("lineItems", []):
            sku = item.get("sku", "")
            product_name = item.get("productName", "")
            quantity = item.get("quantity", 0)
            
            unit_price = item.get("unitPricePaid", {}).get("value", "0")
            currency = item.get("unitPricePaid", {}).get("currency", "USD")
            
            # 提取规格
            variant_options = item.get("variantOptions", [])
            variant = ", ".join([f"{v['optionName']}: {v['value']}" for v in variant_options]) if variant_options else ""
            
            # 订单级别的金额
            subtotal = order.get("subtotal", {}).get("value", "0")
            discount = order.get("discountTotal", {}).get("value", "0")
            grand_total = order.get("grandTotal", {}).get("value", "0")
            
            normalized.append({
                "order_id": order_id,
                "platform": platform,
                "created_at": created_at,
                "sku": sku,
                "product_name": product_name,
                "variant": variant,
                "quantity": quantity,
                "unit_price": float(unit_price),
                "subtotal": float(subtotal),
                "discount": float(discount),
                "grand_total": float(grand_total),
                "fulfillment_status": fulfillment_status,
                "currency": currency,
            })
    
    return normalized


def normalize_squarespace_inventory(raw_inventory):
    """把 Squarespace 库存数据转成统一格式"""
    normalized = []
    
    for item in raw_inventory:
        sku = item.get("sku", "")
        product_name = item.get("descriptor", "")
        quantity_available = item.get("quantity", 0)
        is_unlimited = item.get("isUnlimited", False)
        
        normalized.append({
            "sku": sku,
            "product_name": product_name,
            "platform": "squarespace",
            "quantity_available": 999 if is_unlimited else quantity_available,
            "is_unlimited": is_unlimited,
        })
    
    return normalized


def normalize_etsy_orders(raw_orders):
    """Etsy 订单 normalize（key 到了之后填充）"""
    normalized = []
    for order in raw_orders:
        for item in order.get("transactions", []):
            normalized.append({
                "order_id": str(order.get("receipt_id", "")),
                "platform": "etsy",
                "created_at": datetime.fromtimestamp(order.get("create_timestamp", 0)).isoformat(),
                "sku": item.get("sku", ""),
                "product_name": item.get("title", ""),
                "variant": ", ".join([v.get("formatted_value", "") for v in item.get("variations", [])]),
                "quantity": item.get("quantity", 0),
                "unit_price": float(item.get("price", {}).get("amount", 0)) / float(item.get("price", {}).get("divisor", 1)),
                "subtotal": float(order.get("subtotal", {}).get("amount", 0)) / float(order.get("subtotal", {}).get("divisor", 1)),
                "discount": float(order.get("discount_amt", {}).get("amount", 0)) / float(order.get("discount_amt", {}).get("divisor", 1)),
                "grand_total": float(order.get("grandtotal", {}).get("amount", 0)) / float(order.get("grandtotal", {}).get("divisor", 1)),
                "fulfillment_status": "FULFILLED" if order.get("is_shipped") else "PENDING",
                "currency": order.get("subtotal", {}).get("currency_code", "USD"),
            })
    return normalized


def normalize_ebay_orders(raw_orders):
    """eBay 订单 normalize（key 到了之后填充）"""
    normalized = []
    for order in raw_orders:
        for item in order.get("lineItems", []):
            normalized.append({
                "order_id": order.get("orderId", ""),
                "platform": "ebay",
                "created_at": order.get("creationDate", ""),
                "sku": item.get("sku", ""),
                "product_name": item.get("title", ""),
                "variant": "",
                "quantity": item.get("quantity", 0),
                "unit_price": float(item.get("lineItemCost", {}).get("value", 0)),
                "subtotal": float(order.get("pricingSummary", {}).get("priceSubtotal", {}).get("value", 0)),
                "discount": float(order.get("pricingSummary", {}).get("priceDiscount", {}).get("value", 0)) if order.get("pricingSummary", {}).get("priceDiscount") else 0.0,
                "grand_total": float(order.get("pricingSummary", {}).get("total", {}).get("value", 0)),
                "fulfillment_status": order.get("orderFulfillmentStatus", ""),
                "currency": item.get("lineItemCost", {}).get("currency", "USD"),
            })
    return normalized