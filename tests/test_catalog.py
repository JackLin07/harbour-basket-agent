from shopping_agent.backend.errors import NotFoundError


def test_catalogue_has_expected_size(service):
    products = service.catalog.all()
    assert 150 <= len(products) <= 200


def test_get_product(service):
    product = service.catalog.get("HB-1001")
    assert product.name == "Hass Avocados"
    assert product.price_aud == 3.2
    assert product.currency == "AUD"
    assert "vegan" in product.dietary_tags


def test_get_missing_product(service):
    try:
        service.catalog.get("HB-9999")
    except NotFoundError as exc:
        assert "HB-9999" in str(exc)
    else:
        raise AssertionError("expected NotFoundError")


def test_search_by_keyword(service):
    payload = service.search_products("avocado")
    ids = [row["id"] for row in payload["products"]]
    assert "HB-1001" in ids


def test_search_synonym_avo(service):
    payload = service.search_products("ripe avo")
    ids = [row["id"] for row in payload["products"]]
    assert "HB-1001" in ids


def test_search_gluten_free_pasta(service):
    payload = service.search_products(
        "pasta",
        dietary_tags=["gluten-free"],
    )
    ids = [row["id"] for row in payload["products"]]
    assert "HB-5038" in ids
    assert "HB-5001" not in ids  # regular spaghetti contains gluten


def test_search_allergen_free_nuts(service):
    payload = service.search_products(
        "snack",
        allergen_free=["peanuts", "tree-nuts"],
        limit=20,
    )
    for row in payload["products"]:
        assert "peanuts" not in row["allergens"]
        assert "tree-nuts" not in row["allergens"]
    ids = [row["id"] for row in payload["products"]]
    assert "HB-7010" not in ids  # roasted mixed nuts
    assert "HB-5019" not in ids  # peanut butter


def test_search_max_price(service):
    payload = service.search_products("milk", max_price=4.0, dietary_tags=["vegan"])
    for row in payload["products"]:
        assert row["price_aud"] <= 4.0
        assert "vegan" in row["dietary_tags"]


def test_search_category_filter(service):
    payload = service.search_products(category="baby", limit=20)
    assert payload["count"] >= 1
    assert all(row["category"] == "baby" for row in payload["products"])


def test_out_of_stock_excluded_by_default(service):
    payload = service.search_products("raspberries", in_stock_only=True)
    ids = [row["id"] for row in payload["products"]]
    assert "HB-1017" not in ids
    payload_all = service.search_products("raspberries", in_stock_only=False)
    ids_all = [row["id"] for row in payload_all["products"]]
    assert "HB-1017" in ids_all
    rasp = next(row for row in payload_all["products"] if row["id"] == "HB-1017")
    assert rasp["stock"] == 0


def test_search_by_product_id(service):
    payload = service.search_products("HB-2009")
    assert payload["products"][0]["id"] == "HB-2009"
    assert "Salmon" in payload["products"][0]["name"]
