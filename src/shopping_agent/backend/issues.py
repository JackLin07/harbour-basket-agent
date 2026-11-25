"""Issue / complaint log, seeded from issues.json and append-only in memory."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from itertools import count

from shopping_agent.backend.errors import ValidationError
from shopping_agent.models import Issue, IssueStatus, IssueType
from shopping_agent.paths import issues_path

_MELBOURNE = timezone(timedelta(hours=11))
VALID_TYPES: set[str] = {
    "missing_item",
    "damaged",
    "wrong_item",
    "quality",
    "late_delivery",
    "refund_request",
    "other",
}


class IssueStore:
    def __init__(self, issues: list[Issue] | None = None) -> None:
        self._issues: list[Issue] = list(issues or [])
        self._seq = count(start=len(self._issues) + 1)

    @classmethod
    def from_json(cls, path=None) -> IssueStore:
        path = path or issues_path()
        if not path.exists():
            return cls([])
        payload = json.loads(path.read_text(encoding="utf-8"))
        issues = [Issue.model_validate(row) for row in payload.get("issues", [])]
        return cls(issues)

    def report(
        self,
        customer_id: str,
        description: str,
        *,
        order_id: str | None = None,
        issue_type: IssueType = "other",
        product_ids: list[str] | None = None,
    ) -> Issue:
        if not description.strip():
            raise ValidationError("An issue description is required.")
        if issue_type not in VALID_TYPES:
            raise ValidationError(f"Unknown issue_type {issue_type!r}. Use one of: {sorted(VALID_TYPES)}.")
        issue = Issue(
            id=f"ISS-{8000 + next(self._seq)}",
            customer_id=customer_id,
            order_id=order_id,
            issue_type=issue_type,  # type: ignore[arg-type]
            product_ids=product_ids or [],
            description=description.strip(),
            status="open",
            created_at=datetime.now(_MELBOURNE),
            resolution=None,
        )
        self._issues.append(issue)
        return issue

    def list_for_customer(self, customer_id: str) -> list[Issue]:
        return [issue for issue in self._issues if issue.customer_id == customer_id]

    def update_status(self, issue_id: str, status: IssueStatus, resolution: str | None = None) -> Issue:
        for issue in self._issues:
            if issue.id == issue_id:
                issue.status = status
                if resolution is not None:
                    issue.resolution = resolution
                return issue
        from shopping_agent.backend.errors import NotFoundError

        raise NotFoundError(f"No issue with id {issue_id!r}.")
