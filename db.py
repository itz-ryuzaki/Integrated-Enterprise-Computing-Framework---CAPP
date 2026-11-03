"""SQLite storage for employees (single writer)."""
import random
import sqlite3


def connect(path="enterprise.db"):
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        hours INTEGER NOT NULL,
        rate_paise INTEGER NOT NULL,
        deductions_paise INTEGER NOT NULL)""")
    return conn


def seed_employees(conn, n, seed=42):
    rng = random.Random(seed)
    rows = [(f"Employee {i}", rng.randint(30, 60),
             rng.randint(20_000, 90_000), rng.randint(0, 5_000_00))
            for i in range(n)]
    conn.execute("DELETE FROM employees")
    conn.executemany(
        "INSERT INTO employees (name, hours, rate_paise, deductions_paise) "
        "VALUES (?, ?, ?, ?)", rows)
    conn.commit()


def load_payroll_inputs(conn):
    """Returns (hours, rate, deductions) tuples in the order of employee id."""
    return conn.execute(
        "SELECT hours, rate_paise, deductions_paise FROM employees ORDER BY id"
    ).fetchall()


def count_employees(conn):
    return conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]


def fetch_page(conn, page, size=100):
    """Paged read, as the Employee screen does (100 rows per page)."""
    return conn.execute(
        "SELECT id, name, hours, rate_paise, deductions_paise FROM employees "
        "ORDER BY id LIMIT ? OFFSET ?", (size, page * size)).fetchall()
