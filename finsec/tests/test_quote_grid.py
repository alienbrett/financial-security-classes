import datetime
import decimal

# import unittest
import zoneinfo

import finsec as fs

from .base_test import BaseTestCase

nyc = zoneinfo.ZoneInfo("US/Eastern")


class TestQuoteGrids(BaseTestCase):
    def setUp(self):
        self.usd = fs.FiatCurrency(
            ticker="USD",
            nation="United States Dollar",
            gsid=fs.GSID(20),
            identifiers=[
                fs.FIGI("abcdefg"),
            ],
        )
        self.spx = fs.DerivedIndex(
            ticker="SPX",
            issuer="Standard & Poor",
            gsid=fs.GSID(100),
            identifiers=[
                fs.FIGI("12345"),
            ],
            currency=self.usd,
        )
        self.hyg = fs.ETP(
            ticker="HYG",
            gsid=fs.GSID(124),
            description="ISHARES IBOXX HIGH YLD CORP",
            primary_exc=fs.Exchange.NYSE,
            issuer="ishares",
        )

        self.spx_call = fs.European(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            callput="call",
            strike=4000,
            expiry_date=datetime.date(2022, 9, 16),
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
        )
        self.spx_put = fs.European(
            gsid=fs.GSID(121),
            underlying_security=self.spx,
            callput="put",
            strike=3000,
            expiry_date=datetime.date(2023, 3, 17),
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234568")],
        )

        exact_expiry_time = datetime.datetime(2023, 3, 17, 9, 30, 0, tzinfo=nyc)
        self.esh23 = fs.NewFuture(
            gsid=fs.GSID("blah"),
            ticker="ESH23",
            underlying_security=self.spx,
            expiry_date=datetime.date(2023, 3, 17),
            primary_exc=fs.Exchange.CME,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            expiry_datetime=exact_expiry_time,
            tick_size=0.25,
            multiplier=50.0,
            identifiers=[fs.FIGI("234467")],
            expiry_series_type=fs.ExpirySeriesType.QUARTERLY,
            currency=self.usd,
        )
        self.esz23 = fs.NewFuture(
            gsid=fs.GSID("blah"),
            ticker="ESH23",
            underlying_security=self.spx,
            expiry_date=datetime.date(2023, 12, 16),
            primary_exc=fs.Exchange.CME,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            expiry_datetime=exact_expiry_time,
            tick_size=0.25,
            multiplier=50.0,
            identifiers=[fs.FIGI("2369")],
            expiry_series_type=fs.ExpirySeriesType.QUARTERLY,
            currency=self.usd,
        )

    def test_sec_cache1(self):
        cache = fs.SecurityCache()
        cache.add(self.spx)
        cache.add(self.usd)

        self.assertEqual(self.usd, cache[self.usd.gsid])
        self.assertEqual(self.spx, cache[self.spx.gsid])

        # either of these lines should work
        # del cache[self.usd.gsid]
        del cache[self.usd]

        self.assertNotIn(self.usd, cache)

    def test_opt_chain1(self):

        chain = fs.OptionChain(underlying=self.spx)
        quotes = [
            fs.LevelOneQuote(bid=1, ask=2, bid_sz=10, ask_sz=20, last=1.5, last_sz=12)
        ] * 2

        for x, y in zip([self.spx_call, self.spx_put], quotes):
            chain.ingest(x, y)

        ys = [self.spx_call, self.spx_put]
        for x in chain.subset():
            self.assertIn(x, ys)

        ys = [self.spx_put]
        for x in chain.subset(strike=3000):
            self.assertIn(x, ys)

        self.assertEqual(
            sorted(chain.get_available_values("strike")),
            [
                decimal.Decimal(3000),
                decimal.Decimal(4000),
            ],
        )
        self.assertEqual(chain[self.spx_call], quotes[0])

    def test_fut_chain1(self):
        chain = fs.FutureChain(underlying=self.spx)
        quotes = [
            fs.LevelOneQuote(bid=1, ask=2, bid_sz=10, ask_sz=20, last=1.5, last_sz=12)
        ] * 2

        for x, y in zip([self.esh23, self.esz23], quotes):
            chain.ingest(x, y)

        ys = [self.esh23, self.esz23]
        for x in chain.subset():
            self.assertIn(x, ys)
        self.assertEqual(chain[self.esh23], quotes[0])

    def test_quote_ops1(self):
        q1 = fs.LevelOneQuote(
            bid=100,
            ask=101,
            bid_sz=10,
            ask_sz=20,
            last=100.5,
            last_sz=12,
            last_time=datetime.datetime(2021, 12, 31, 9, 30, 0, tzinfo=nyc),
            timestamp=datetime.datetime(2022, 1, 1, 0, 0, 1, tzinfo=nyc),
        )
        q2 = fs.LevelOneQuote(
            bid=5,
            ask=6,
            bid_sz=500,
            ask_sz=1,
            last=7.5,
            last_sz=100,
            last_time=datetime.datetime(2021, 12, 31, 9, 30, 0, tzinfo=nyc),
            timestamp=datetime.datetime(2023, 1, 1, 0, 0, 1, tzinfo=nyc),
        )

        q3 = fs.LevelOneQuote(
            bid=105,
            ask=107,
            bid_sz=10,
            ask_sz=1,
            last=108,
            last_sz=12,
            last_time=datetime.datetime(2021, 12, 31, 9, 30, 0, tzinfo=nyc),
            timestamp=datetime.datetime(2023, 1, 1, 0, 0, 1, tzinfo=nyc),
        )

        self.assertEqual(q1 + q2, q3)
        self.assertEqual(q3 - q1, q2)
        self.assertEqual(q1 * 2, q1 + q1)
        self.assertEqual(q3 * 2, q3 + q3)

        # test commutative
        self.assertEqual(q1 + q2, q2 + q1)
        # test associative
        self.assertEqual((q1 + q2) + q3, q1 + (q2 + q3))

    def test_quote_ops2(self):
        q1 = fs.LevelOneQuote(
            bid=100,
            ask=101,
            bid_sz=10,
            ask_sz=20,
            last=100.5,
            last_sz=12,
            last_time=datetime.datetime(2021, 12, 31, 9, 30, 0, tzinfo=nyc),
            timestamp=datetime.datetime(2022, 1, 1, 0, 0, 1, tzinfo=nyc),
        )
        q2 = fs.LevelOneQuote(
            bid=5,
            ask=6,
            bid_sz=500,
            ask_sz=1,
            last=7.5,
            last_sz=100,
            # last time not equal to q1
            last_time=datetime.datetime(2020, 1, 15, 9, 30, 0, tzinfo=nyc),
            timestamp=datetime.datetime(2023, 1, 1, 0, 0, 1, tzinfo=nyc),
        )

        q3 = fs.LevelOneQuote(
            bid=105,
            ask=107,
            bid_sz=10,
            ask_sz=1,
            timestamp=datetime.datetime(2023, 1, 1, 0, 0, 1, tzinfo=nyc),
        )

        self.assertEqual(q1 + q2, q3)
        self.assertEqual(q1 * 2, q1 + q1)
        self.assertEqual(q3 * 2, q3 + q3)

        # test commutative
        self.assertEqual(q1 + q2, q2 + q1)
        # test associative
        self.assertEqual((q1 + q2) + q3, q1 + (q2 + q3))
