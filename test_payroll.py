import unittest
from payroll import net_pay_paise, payroll_sequential, payroll_parallel


class PayrollTests(unittest.TestCase):
    def test_no_overtime(self):
        # 40 h * Rs 100/h (10000 paise), no deductions
        self.assertEqual(net_pay_paise((40, 10_000, 0)), 400_000)

    def test_overtime_at_1_5x(self):
        # 40 h regular + 10 h overtime at 1.5x = 400000 + 150000
        self.assertEqual(net_pay_paise((50, 10_000, 0)), 550_000)

    def test_deductions_subtracted(self):
        self.assertEqual(net_pay_paise((40, 10_000, 50_000)), 350_000)

    def test_parallel_matches_sequential(self):
        records = [(30 + i % 30, 20_000 + i, i * 7) for i in range(5_000)]
        self.assertEqual(payroll_sequential(records),
                         payroll_parallel(records, workers=2))


if __name__ == "__main__":
    unittest.main()
