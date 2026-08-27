from copy import deepcopy

ORDERS = {
 "NW-1001":{"order_id":"NW-1001","item":"2-person tent","amount_cents":18999,"days_since_delivery":7,"clearance":False},
 "NW-1002":{"order_id":"NW-1002","item":"insulated jacket","amount_cents":12999,"days_since_delivery":19,"clearance":False},
 "NW-1003":{"order_id":"NW-1003","item":"sleeping bag","amount_cents":12001,"days_since_delivery":30,"clearance":False},
 "NW-1004":{"order_id":"NW-1004","item":"sleeping bag","amount_cents":12001,"days_since_delivery":31,"clearance":False},
 "NW-1006":{"order_id":"NW-1006","item":"headlamps","amount_cents":6999,"days_since_delivery":61,"clearance":False},
 "NW-1007":{"order_id":"NW-1007","item":"trekking poles","amount_cents":8999,"days_since_delivery":12,"clearance":True},
 "NW-1008":{"order_id":"NW-1008","item":"rain shell","amount_cents":11999,"days_since_delivery":10,"clearance":True},
 "NW-1010":{"order_id":"NW-1010","item":"XL expedition tent","amount_cents":50001,"days_since_delivery":7,"clearance":False},
 "NW-1012":{"order_id":"NW-1012","item":"camp stove","amount_cents":14999,"days_since_delivery":5,"clearance":False},
}
REFUNDS = []

def get_order(order_id):
    x = ORDERS.get(order_id)
    return deepcopy(x) if x else None

def issue_refund(order_id, amount_cents):
    order = ORDERS.get(order_id)
    if not order: raise ValueError(f"unknown order {order_id}")
    if amount_cents <= 0 or amount_cents > order["amount_cents"]:
        raise ValueError("invalid refund amount")
    refund = {"refund_id":f"RF-{1000+len(REFUNDS)+1}",
              "order_id":order_id, "amount_cents":amount_cents, "status":"accepted"}
    REFUNDS.append(refund)
    return deepcopy(refund)

def reset_ledger():
    REFUNDS.clear()

def ledger():
    return deepcopy(REFUNDS)
