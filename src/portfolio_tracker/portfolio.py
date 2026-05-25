from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

DEFAULT_FILE = Path("portfolio.json")

@dataclass
class Holding:
    symbol: str
    shares: float
    price: float

    def value(self) -> float:
        return self.shares * self.price

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Holding":
        return cls(symbol=data["symbol"], shares=data["shares"], price=data["price"])

class Portfolio:
    def __init__(self, holdings: List[Holding] | None = None) -> None:
        self.holdings = holdings or []

    def add_holding(self, holding: Holding) -> None:
        existing = next((h for h in self.holdings if h.symbol == holding.symbol), None)
        if existing:
            existing.shares += holding.shares
            existing.price = holding.price
        else:
            self.holdings.append(holding)

    def remove_holding(self, symbol: str) -> bool:
        symbols = [h.symbol for h in self.holdings]
        if symbol in symbols:
            self.holdings = [h for h in self.holdings if h.symbol != symbol]
            return True
        return False

    def total_value(self) -> float:
        return sum(h.value() for h in self.holdings)

    def list_holdings(self) -> List[Holding]:
        return list(self.holdings)

    def save(self, path: Path = DEFAULT_FILE) -> None:
        data = [holding.to_dict() for holding in self.holdings]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = DEFAULT_FILE) -> "Portfolio":
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text(encoding="utf-8"))
        holdings = [Holding.from_dict(item) for item in raw]
        return cls(holdings)
