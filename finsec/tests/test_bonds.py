import datetime
import decimal
import unittest

import finsec as fs
import finsec.fixed_income_objs as fio

from .base_test import BaseTestCase


class TestLegs(BaseTestCase):
    def test_fixed_bond1(self):
        ntnl = 1_000_000
        fixleg1 = fio.Leg(
            notional=ntnl,
            # cpn=fio.FixedRate(rate=decimal.Decimal('0.01')),
            cpn=fio.FixedRate(rate=0.01),
            acc=fio.AccrualInfo(
                start=datetime.date(2025, 1, 1),
                end=datetime.date(2026, 1, 1),
                dc=fio.DayCount.Thirty360,
                freq=12,
                bdc=fio.BusinessDayConvention.unadjusted,
            ),
        )
        bnd1 = fio.Bond(
            notional=ntnl,
            leg=fixleg1,
            # settle: datetime.date
            settle_days=1,
        )
        # print(bnd1)
        bnd1.as_quantlib()
        # print(bnd1.cashflows_df())

    def test_accrual1(
        self,
    ):
        acc1 = fio.AccrualInfo(
            start=datetime.date(2025, 1, 1),
            # end=datetime.date(2025,11,5),
            end="3m",
            period="1m",
            dc=fio.DayCount.Thirty360,
            front_stub_not_back=False,
        )
        dts = acc1.nodes()
        self.assert_array_equal(
            dts,
            [
                datetime.date(2025, 1, 1),
                datetime.date(2025, 2, 1),
                datetime.date(2025, 3, 1),
                datetime.date(2025, 4, 1),
            ],
        )
        self.assertAlmostEqual(1 / 12, acc1.fraction(dts[0], dts[1]))

        sched = acc1.schedule()
        self.assertEqual(
            sched,
            fio.AccrualSchedule(
                start=[
                    datetime.date(2025, 1, 1),
                    datetime.date(2025, 2, 1),
                    datetime.date(2025, 3, 1),
                ],
                end=[
                    datetime.date(2025, 2, 1),
                    datetime.date(2025, 3, 1),
                    datetime.date(2025, 4, 1),
                ],
                frac=[1 / 12] * 3,
            ),
        )
