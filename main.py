"""Command-line MVP: seed data, run payroll sequentially and in parallel, compare."""
import argparse
import time

from db import connect, seed_employees, load_payroll_inputs
from payroll import payroll_sequential, payroll_parallel, PARALLEL_THRESHOLD


def fmt(paise):
    return f"Rs {paise / 100:,.2f}"


def main():
    p = argparse.ArgumentParser(description="Enterprise payroll MVP")
    p.add_argument("--employees", type=int, default=500_000)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--show", type=int, default=3, help="sample rows to print")
    args = p.parse_args()

    conn = connect()
    seed_employees(conn, args.employees)
    records = load_payroll_inputs(conn)
    print(f"Loaded {len(records):,} employees")

    t0 = time.perf_counter()
    seq = payroll_sequential(records)
    t_seq = time.perf_counter() - t0

    t0 = time.perf_counter()
    par = payroll_parallel(records, args.workers)
    t_par = time.perf_counter() - t0

    print(f"Sequential : {t_seq:.2f} s")
    print(f"Parallel   : {t_par:.2f} s ({args.workers} workers)")
    print(f"Speedup    : {t_seq / t_par:.2f}x")
    print(f"Outputs identical: {seq == par}")
    if len(records) < PARALLEL_THRESHOLD:
        print(f"Note: below {PARALLEL_THRESHOLD:,} records the app would run sequentially.")

    for i in range(min(args.show, len(seq))):
        print(f"  employee {i + 1}: net pay {fmt(seq[i])}")
    conn.close()


if __name__ == "__main__":
    main()
