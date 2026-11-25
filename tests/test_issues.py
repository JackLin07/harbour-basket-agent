from shopping_agent.backend.errors import NotFoundError, PermissionError_, ValidationError


def test_seeded_issue_is_visible(service):
    payload = service.list_issues("CUST-1001")
    ids = [issue["id"] for issue in payload["issues"]]
    assert "ISS-7001" in ids
    assert payload["issues"][0]["order_id"] == "ORD-5003" or any(
        issue["order_id"] == "ORD-5003" for issue in payload["issues"]
    )


def test_report_issue(service):
    payload = service.report_issue(
        "CUST-1001",
        "The butter was missing from my delivery.",
        order_id="ORD-5003",
        issue_type="missing_item",
        product_ids=["HB-3008"],
    )
    issue = payload["issue"]
    assert issue["id"].startswith("ISS-")
    assert issue["status"] == "open"
    assert issue["issue_type"] == "missing_item"
    listed = service.list_issues("CUST-1001")
    assert any(row["id"] == issue["id"] for row in listed["issues"])


def test_report_issue_rejects_empty_description(service):
    try:
        service.report_issue("CUST-1001", "   ")
    except ValidationError:
        pass
    else:
        raise AssertionError("expected ValidationError")


def test_report_issue_rejects_foreign_order(service):
    try:
        service.report_issue(
            "CUST-1001",
            "Please refund this.",
            order_id="ORD-5008",
            issue_type="refund_request",
        )
    except PermissionError_:
        pass
    else:
        raise AssertionError("expected PermissionError_")


def test_unknown_issue_type(service):
    try:
        service.report_issue("CUST-1001", "Something happened", issue_type="explode")  # type: ignore[arg-type]
    except ValidationError as exc:
        assert "issue_type" in str(exc).lower() or "unknown" in str(exc).lower()
    else:
        raise AssertionError("expected ValidationError")


def test_unknown_customer_on_list(service):
    try:
        service.list_issues("CUST-0000")
    except NotFoundError:
        pass
    else:
        raise AssertionError("expected NotFoundError")
