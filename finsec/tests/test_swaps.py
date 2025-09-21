import datetime
import decimal
import unittest
import QuantLib as ql

import finsec as fs

from .base_test import BaseTestCase

usd_ccy = fs.FiatCurrency( ticker='USD', gsid='USD')
usd = fs.create_reference_from_security(usd_ccy)

class TestSwaps(BaseTestCase):

    def test_basic_ois(self):
        swp_ntnl = 1_000_000
        swp_start = datetime.date(2025,1,1)
        swp_end = '5y'
        swp_index = 'SOFR'
        swp = fs.Swap.make_ois(
            ccy=usd,
            start=datetime.date(2025, 1, 1),
            end='5y',
            rate=3.5 / 100,
            dc_fix=fs.DayCount.Actual360,
            dc_float=fs.DayCount.Actual360,
            freq_fix=1,
            freq_float=1,
            index='SOFR',
            cal_pay=fs.Calendar.US_SOFR,
            notional=1_000_000,
            pay_delay=fs.Period(period='2d'),
        )
        # display(swp.model_dump())

        ql.Settings.instance().evaluationDate = ql.Date(1, 1, 2025)

        ql_curve_raw = ql.FlatForward(
            0,
            fs.Calendar.US_SOFR.as_ql(),
            ql.QuoteHandle(ql.SimpleQuote(
                0.05,
            )),
            ql.Actual360(),
        )

        ql_curve = ql.YieldTermStructureHandle(ql_curve_raw)

        swp_engine = ql.DiscountingSwapEngine(ql_curve)

        ql_swp = swp.as_quantlib(
            index_lookup={
                'SOFR': ql.Sofr(ql_curve),
            }
        )

        ql_swp.setPricingEngine(swp_engine)

        self.assertAlmostEqual(
            ql_swp.fairRate(),
            0.05,
            2
        )