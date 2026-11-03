"""PySide6 desktop GUI for the enterprise payroll MVP.

Tabs:
  Employees - seed synthetic data and browse it 100 rows at a time
  Payroll   - run payroll sequentially and in parallel, show timing and speedup
"""
import sys
import time

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QHeaderView, QLabel, QMainWindow, QMessageBox,
    QPushButton, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from db import connect, count_employees, fetch_page, load_payroll_inputs, seed_employees
from payroll import PARALLEL_THRESHOLD, payroll_parallel, payroll_sequential

PAGE_SIZE = 100


def fmt(paise):
    return f"Rs {paise / 100:,.2f}"


def make_table(headers):
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    return table


class PayrollWorker(QThread):
    """Runs the benchmark off the UI thread so the window stays responsive."""
    done = Signal(dict)

    def __init__(self, records, workers):
        super().__init__()
        self.records = records
        self.workers = workers

    def run(self):
        t0 = time.perf_counter()
        seq = payroll_sequential(self.records)
        t_seq = time.perf_counter() - t0

        t0 = time.perf_counter()
        par = payroll_parallel(self.records, self.workers)
        t_par = time.perf_counter() - t0

        self.done.emit({
            "seq": seq, "t_seq": t_seq, "t_par": t_par,
            "identical": seq == par, "workers": self.workers,
        })


class EmployeeTab(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.page = 0

        self.seed_count = QSpinBox()
        self.seed_count.setRange(1, 1_000_000)
        self.seed_count.setValue(50_000)
        self.seed_btn = QPushButton("Generate employees")
        self.seed_btn.clicked.connect(self.on_seed)

        self.prev_btn = QPushButton("< Prev")
        self.next_btn = QPushButton("Next >")
        self.prev_btn.clicked.connect(lambda: self.go(self.page - 1))
        self.next_btn.clicked.connect(lambda: self.go(self.page + 1))
        self.page_label = QLabel()

        self.table = make_table(["ID", "Name", "Hours", "Rate (Rs/h)", "Deductions (Rs)"])

        top = QHBoxLayout()
        top.addWidget(QLabel("Employees:"))
        top.addWidget(self.seed_count)
        top.addWidget(self.seed_btn)
        top.addStretch()

        nav = QHBoxLayout()
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.page_label, 1)
        nav.addWidget(self.next_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.table)
        layout.addLayout(nav)
        self.refresh()

    def on_seed(self):
        seed_employees(self.conn, self.seed_count.value())
        self.page = 0
        self.refresh()

    def go(self, page):
        if 0 <= page <= self.last_page():
            self.page = page
            self.refresh()

    def last_page(self):
        return max(0, (count_employees(self.conn) - 1) // PAGE_SIZE)

    def refresh(self):
        rows = fetch_page(self.conn, self.page, PAGE_SIZE)
        self.table.setRowCount(len(rows))
        for r, (eid, name, hours, rate, ded) in enumerate(rows):
            values = [eid, name, hours, f"{rate / 100:,.2f}", f"{ded / 100:,.2f}"]
            for c, v in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
        total = count_employees(self.conn)
        self.page_label.setText(
            f"Page {self.page + 1} of {self.last_page() + 1}  ({total:,} employees)")
        self.prev_btn.setEnabled(self.page > 0)
        self.next_btn.setEnabled(self.page < self.last_page())


class PayrollTab(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.worker = None

        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 16)
        self.workers_spin.setValue(4)
        self.run_btn = QPushButton("Run payroll")
        self.run_btn.clicked.connect(self.on_run)

        self.status = QLabel("Generate employees first, then run payroll.")
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("font-size: 14px;")

        self.table = make_table(["#", "Net pay"])

        top = QHBoxLayout()
        top.addWidget(QLabel("Worker processes:"))
        top.addWidget(self.workers_spin)
        top.addWidget(self.run_btn)
        top.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.status)
        layout.addWidget(self.result_label)
        layout.addWidget(QLabel(f"First {PAGE_SIZE} net pay results:"))
        layout.addWidget(self.table)

    def on_run(self):
        records = load_payroll_inputs(self.conn)
        if not records:
            QMessageBox.information(self, "No data", "Generate employees first.")
            return
        self.run_btn.setEnabled(False)
        mode = "parallel" if len(records) >= PARALLEL_THRESHOLD else "sequential"
        self.status.setText(f"Running {len(records):,} records (app would use {mode} mode)...")
        self.worker = PayrollWorker(records, self.workers_spin.value())
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def on_done(self, res):
        self.run_btn.setEnabled(True)
        speedup = res["t_seq"] / res["t_par"] if res["t_par"] else 0
        self.result_label.setText(
            f"Sequential: {res['t_seq']:.2f} s    "
            f"Parallel ({res['workers']} workers): {res['t_par']:.2f} s    "
            f"Speedup: {speedup:.2f}x    "
            f"Outputs identical: {'Yes' if res['identical'] else 'NO'}")
        self.status.setText("Done.")

        seq = res["seq"][:PAGE_SIZE]
        self.table.setRowCount(len(seq))
        for i, paise in enumerate(seq):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(fmt(paise)))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Integrated Enterprise Computing Framework - MVP")
        self.resize(900, 600)
        self.conn = connect()

        tabs = QTabWidget()
        tabs.addTab(EmployeeTab(self.conn), "Employees")
        tabs.addTab(PayrollTab(self.conn), "Payroll")
        self.setCentralWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
