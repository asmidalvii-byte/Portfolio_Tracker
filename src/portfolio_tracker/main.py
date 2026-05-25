from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from portfolio_tracker.portfolio import Holding, Portfolio, DEFAULT_FILE


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Portfolio Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add or update a holding")
    add_parser.add_argument("--symbol", required=True, help="Ticker symbol")
    add_parser.add_argument("--shares", type=float, required=True, help="Number of shares")
    add_parser.add_argument("--price", type=float, required=True, help="Price per share")
    add_parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help="Portfolio JSON file")

    remove_parser = subparsers.add_parser("remove", help="Remove a holding")
    remove_parser.add_argument("--symbol", required=True, help="Ticker symbol to remove")
    remove_parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help="Portfolio JSON file")

    subparsers.add_parser("list", help="List current holdings")
    value_parser = subparsers.add_parser("value", help="Show portfolio value")
    value_parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help="Portfolio JSON file")

    return parser.parse_args(argv)


def show_holdings(portfolio: Portfolio) -> None:
    if not portfolio.holdings:
        print("No holdings found.")
        return

    print("Symbol  Shares   Price   Value")
    print("------  ------   -----   -----")
    for holding in portfolio.list_holdings():
        print(f"{holding.symbol:6}  {holding.shares:6.2f}  {holding.price:7.2f}  {holding.value():7.2f}")
    print(f"\nTotal portfolio value: {portfolio.total_value():.2f}")


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    file_path = getattr(args, "file", DEFAULT_FILE)
    portfolio = Portfolio.load(file_path)

    if args.command == "add":
        portfolio.add_holding(Holding(symbol=args.symbol.upper(), shares=args.shares, price=args.price))
        portfolio.save(file_path)
        print(f"Added/updated holding: {args.symbol.upper()}")
        return 0

    if args.command == "remove":
        removed = portfolio.remove_holding(args.symbol.upper())
        if removed:
            portfolio.save(file_path)
            print(f"Removed holding: {args.symbol.upper()}")
            return 0
        print(f"Holding not found: {args.symbol.upper()}")
        return 1

    if args.command == "list":
        show_holdings(portfolio)
        return 0

    if args.command == "value":
        print(f"Portfolio value: {portfolio.total_value():.2f}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
