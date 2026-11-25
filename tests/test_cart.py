import pytest

from shopping_agent.backend.errors import NotFoundError, OutOfStockError, ValidationError

CUSTOMER = "CUST-1001"


def test_empty_cart(service):
    cart = service.view_cart(CUSTOMER)["cart"]
    assert cart["items"] == []
    assert cart["subtotal_aud"] == 0
    assert cart["delivery_fee_aud"] == 0
    assert cart["total_aud"] == 0


def test_add_and_view_cart(service):
    added = service.add_to_cart(CUSTOMER, "HB-1001", 2)
    assert added["ok"] is True
    cart = added["cart"]
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2
    assert cart["items"][0]["line_total_aud"] == pytest.approx(6.4)
    # Under $50, delivery fee applies
    assert cart["delivery_fee_aud"] == 9.0
    assert cart["total_aud"] == pytest.approx(15.4)


def test_add_is_cumulative(service):
    service.add_to_cart(CUSTOMER, "HB-1002", 1)
    service.add_to_cart(CUSTOMER, "HB-1002", 1)
    cart = service.view_cart(CUSTOMER)["cart"]
    assert cart["items"][0]["quantity"] == 2


def test_free_delivery_threshold(service):
    # Olive oil is $12; 5 of them is $60.
    service.add_to_cart(CUSTOMER, "HB-5007", 5)
    cart = service.view_cart(CUSTOMER)["cart"]
    assert cart["subtotal_aud"] == pytest.approx(60.0)
    assert cart["delivery_fee_aud"] == 0.0
    assert cart["total_aud"] == pytest.approx(60.0)


def test_cannot_add_out_of_stock(service):
    with pytest.raises(OutOfStockError):
        service.add_to_cart(CUSTOMER, "HB-1017", 1)


def test_cannot_add_more_than_stock(service):
    # Eye fillet has stock 6
    with pytest.raises(OutOfStockError):
        service.add_to_cart(CUSTOMER, "HB-2013", 99)


def test_update_and_remove(service):
    service.add_to_cart(CUSTOMER, "HB-3001", 1)
    service.update_cart_item(CUSTOMER, "HB-3001", 3)
    cart = service.view_cart(CUSTOMER)["cart"]
    assert cart["items"][0]["quantity"] == 3
    service.remove_from_cart(CUSTOMER, "HB-3001")
    assert service.view_cart(CUSTOMER)["cart"]["items"] == []


def test_update_zero_removes(service):
    service.add_to_cart(CUSTOMER, "HB-3001", 2)
    service.update_cart_item(CUSTOMER, "HB-3001", 0)
    assert service.view_cart(CUSTOMER)["cart"]["items"] == []


def test_clear_cart(service):
    service.add_to_cart(CUSTOMER, "HB-3001", 1)
    service.add_to_cart(CUSTOMER, "HB-1002", 1)
    service.clear_cart(CUSTOMER)
    assert service.view_cart(CUSTOMER)["cart"]["items"] == []


def test_add_unknown_product(service):
    with pytest.raises(NotFoundError):
        service.add_to_cart(CUSTOMER, "HB-0000", 1)


def test_invalid_quantity(service):
    with pytest.raises(ValidationError):
        service.add_to_cart(CUSTOMER, "HB-1001", 0)


def test_carts_are_per_customer(service):
    service.add_to_cart("CUST-1001", "HB-1001", 1)
    service.add_to_cart("CUST-1002", "HB-1002", 1)
    c1 = service.view_cart("CUST-1001")["cart"]
    c2 = service.view_cart("CUST-1002")["cart"]
    assert c1["items"][0]["product_id"] == "HB-1001"
    assert c2["items"][0]["product_id"] == "HB-1002"


def test_unknown_customer_rejected(service):
    with pytest.raises(NotFoundError):
        service.view_cart("CUST-9999")
