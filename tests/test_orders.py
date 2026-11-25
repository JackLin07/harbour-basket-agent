import pytest

from shopping_agent.backend.errors import NotFoundError, PermissionError_


def test_get_order(service):
    payload = service.get_order("ORD-5002", customer_id="CUST-1001")
    order = payload["order"]
    assert order["status"] == "in_transit"
    assert order["customer_id"] == "CUST-1001"
    assert "6:00 pm" in order["delivery_window"]


def test_list_orders_is_newest_first(service):
    payload = service.list_orders("CUST-1001")
    ids = [order["id"] for order in payload["orders"]]
    assert ids[0] == "ORD-5002"
    assert "ORD-5001" in ids
    assert "ORD-5003" in ids


def test_order_not_found(service):
    with pytest.raises(NotFoundError):
        service.get_order("ORD-0000", customer_id="CUST-1001")


def test_cannot_read_another_customers_order(service):
    with pytest.raises(PermissionError_):
        service.get_order("ORD-5008", customer_id="CUST-1001")


def test_cancelled_and_ready_statuses(service):
    cancelled = service.get_order("ORD-5004", customer_id="CUST-1002")["order"]
    assert cancelled["status"] == "cancelled"
    pickup = service.get_order("ORD-5016", customer_id="CUST-1002")["order"]
    assert pickup["status"] == "ready_for_pickup"
    assert pickup["delivery_fee_aud"] == 0.0


def test_order_totals_are_consistent(service):
    order = service.get_order("ORD-5001", customer_id="CUST-1001")["order"]
    lines = sum(item["line_total_aud"] for item in order["items"])
    assert order["subtotal_aud"] == pytest.approx(lines)
    assert order["total_aud"] == pytest.approx(order["subtotal_aud"] + order["delivery_fee_aud"])
