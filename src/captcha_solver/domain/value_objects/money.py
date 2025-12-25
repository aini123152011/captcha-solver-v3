"""值对象 - Money"""

from decimal import Decimal
from typing import Self


class Money:
    """金额值对象 - 不可变"""

    __slots__ = ("_amount", "_currency")

    def __init__(self, amount: Decimal | float | str, currency: str = "USD") -> None:
        if isinstance(amount, float):
            amount = Decimal(str(amount))
        elif isinstance(amount, str):
            amount = Decimal(amount)
        self._amount = amount
        self._currency = currency.upper()

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency(self) -> str:
        return self._currency

    def __add__(self, other: Self) -> Self:
        if self._currency != other._currency:
            raise ValueError(f"Cannot add {self._currency} and {other._currency}")
        return Money(self._amount + other._amount, self._currency)

    def __sub__(self, other: Self) -> Self:
        if self._currency != other._currency:
            raise ValueError(f"Cannot subtract {self._currency} and {other._currency}")
        return Money(self._amount - other._amount, self._currency)

    def __mul__(self, factor: int | float | Decimal) -> Self:
        return Money(self._amount * Decimal(str(factor)), self._currency)

    def __neg__(self) -> Self:
        return Money(-self._amount, self._currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return False
        return self._amount == other._amount and self._currency == other._currency

    def __lt__(self, other: Self) -> bool:
        if self._currency != other._currency:
            raise ValueError(f"Cannot compare {self._currency} and {other._currency}")
        return self._amount < other._amount

    def __le__(self, other: Self) -> bool:
        return self == other or self < other

    def __gt__(self, other: Self) -> bool:
        return not self <= other

    def __ge__(self, other: Self) -> bool:
        return not self < other

    def __hash__(self) -> int:
        return hash((self._amount, self._currency))

    def __repr__(self) -> str:
        return f"Money({self._amount}, '{self._currency}')"

    def __str__(self) -> str:
        return f"{self._currency} {self._amount:.4f}"

    def is_positive(self) -> bool:
        return self._amount > 0

    def is_negative(self) -> bool:
        return self._amount < 0

    def is_zero(self) -> bool:
        return self._amount == 0

    @classmethod
    def zero(cls, currency: str = "USD") -> Self:
        return cls(Decimal("0"), currency)
