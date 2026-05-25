# Portfolio Tracker

A lightweight Python portfolio tracker for managing holdings, showing current value, and saving the portfolio to disk.

## Features

- Add, remove, and list holdings
- Compute total portfolio value
- Persist portfolio data in a JSON file
- CLI interface for quick usage

## Requirements

- Python 3.10+

## Installation

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install the package:

```bash
python -m pip install -e .
```

## Usage

Run the CLI command:

```bash
portfolio-tracker --help
```

Example commands:

```bash
portfolio-tracker add --symbol AAPL --shares 5 --price 170.00
portfolio-tracker list
portfolio-tracker value
```

## Development

Run tests with `pytest`:

```bash
python -m pip install pytest
pytest
```
