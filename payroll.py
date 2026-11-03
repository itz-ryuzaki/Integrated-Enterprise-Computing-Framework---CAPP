"""Payroll calculation. All money is in integer paise (1 rupee = 100 paise)."""
from multiprocessing import Pool

STANDARD_HOURS = 40
PARALLEL_THRESHOLD = 40_000  # below this size, run sequentially (per the report)


def net_pay_paise(record):
    """record = (hours, rate_paise_per_hour, deductions_paise)."""
    hours, rate, deductions = record
    regular = min(hours, STANDARD_HOURS)
    overtime = max(hours - STANDARD_HOURS, 0)
    gross = regular * rate + overtime * rate * 3 // 2  # overtime at 1.5x
    return gross - deductions


def payroll_sequential(records):
    return [net_pay_paise(r) for r in records]


def payroll_parallel(records, workers=4):
    chunk = max(1, len(records) // (4 * workers))
    with Pool(processes=workers) as pool:
        return pool.map(net_pay_paise, records, chunksize=chunk)


def run_payroll(records, workers=4):
    """Use the parallel engine only for large jobs, as the report describes."""
    if len(records) >= PARALLEL_THRESHOLD:
        return payroll_parallel(records, workers)
    return payroll_sequential(records)
