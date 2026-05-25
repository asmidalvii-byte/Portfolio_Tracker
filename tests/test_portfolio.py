from pathlib import Path

from portfolio_tracker.portfolio import Holding, Portfolio


def test_add_and_total_value(tmp_path: Path) -> None:
    portfolio = Portfolio()
    portfolio.add_holding(Holding(symbol="AAPL", shares=5, price=150.0))
    portfolio.add_holding(Holding(symbol="GOOG", shares=2, price=120.0))

    assert portfolio.total_value() == 5 * 150.0 + 2 * 120.0

    file_path = tmp_path / "portfolio.json"
    portfolio.save(file_path)

    loaded = Portfolio.load(file_path)
    assert len(loaded.holdings) == 2
    assert loaded.total_value() == portfolio.total_value()
