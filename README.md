# Enterprise Payroll MVP (GUI)

A small slice of the PBL project "Integrated Enterprise Computing Framework":
payroll in integer paise, a SQLite store, a PySide6 desktop GUI, and a
sequential vs multiprocessing benchmark.

## Files
- `gui.py` - PySide6 window with two tabs: Employees and Payroll
- `payroll.py` - payroll arithmetic, sequential and parallel engines
- `db.py` - SQLite employee table, synthetic data, paged reads
- `main.py` - command-line version (no GUI), kept for benchmarking
- `test_payroll.py` - unit tests

## Setup and run
    pip install PySide6
    python gui.py
    python -m unittest -v test_payroll.py

## Using the app
1. Employees tab: choose a count and click "Generate employees". Browse 100 rows per page.
2. Payroll tab: choose the number of worker processes and click "Run payroll".
   The app shows sequential time, parallel time, speedup, and whether outputs match.
   The benchmark runs in a background thread, so the window stays responsive.

## Scope
Not included yet: orders and the order pipeline, inventory, the LRU cache,
reports and CSV export, and the Module 5 demonstrations.
