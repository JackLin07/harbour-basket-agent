"""Domain errors the service layer raises. Tools should catch and return these as JSON."""


class ShoppingError(Exception):
    """Base class for expected, user-facing backend errors."""

    code = "shopping_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code

    def to_dict(self) -> dict[str, str]:
        return {"ok": False, "error": self.code, "message": str(self)}


class NotFoundError(ShoppingError):
    code = "not_found"


class OutOfStockError(ShoppingError):
    code = "out_of_stock"


class ValidationError(ShoppingError):
    code = "validation_error"


class PermissionError_(ShoppingError):
    """Raised when a customer tries to access someone else's order."""

    code = "forbidden"
