import unittest

import finsec as fs

from .base_test import BaseTestCase


class TestStockConstructor(BaseTestCase):
    def test_create_stock_1(
        self,
    ):
        tsla = fs.Stock(
            ticker="TSLA",
            gsid=fs.GSID(123),
            description="its tesla man",
            primary_exc=fs.Exchange.NYSE,
        )

        self.assertEqual(tsla.security_type, fs.SecurityType.EQUITY)
        self.assertEqual(tsla.security_subtype, fs.SecuritySubtype.COMMON_STOCK)

        self.assertEqual(tsla.primary_exchange, fs.Exchange.NYSE)
        self.assertEqual(tsla.ticker, "TSLA")
        self.assertEqual(tsla.identifiers, [])

    def test_create_stock_2(
        self,
    ):
        tsla = fs.Stock(
            ticker="\ttSLa  ",
            # gsid = fs.GSID(123),
            # description = 'IBOXX high yield smthg',
            # primary_exc = fs.Exchange.NYSE,
        )

        self.assertEqual(tsla.ticker, "TSLA")

        self.assertIsNone(tsla.gsid)
        self.assertIsNone(tsla.primary_exchange)
        self.assertIsNone(tsla.description)

        self.assertEqual(tsla.identifiers, [])

    def test_create_stock_3(
        self,
    ):
        tsla = fs.Stock(
            ticker="tsla",
            identifiers=[
                fs.CUSIP("testing123"),
                fs.FIGI("12345"),
                fs.ISIN("memeer"),
            ],
            # gsid = fs.GSID(123),
            # description = 'IBOXX high yield smthg',
            # primary_exc = fs.Exchange.NYSE,
        )

        self.assertEqual(tsla.ticker, "TSLA")

        self.assertIsNone(tsla.gsid)
        self.assertIsNone(tsla.primary_exchange)
        self.assertIsNone(tsla.description)

        self.assertIn(
            fs.CUSIP("testing123"),
            tsla.identifiers,
        )
        self.assertIn(
            fs.FIGI("12345"),
            tsla.identifiers,
        )
        self.assertIn(
            fs.ISIN("memeer"),
            tsla.identifiers,
        )

    @unittest.expectedFailure
    def test_create_stock_fail_1(
        self,
    ):
        tsla = fs.Stock(
            ticker="TSLA",
        )

        self.assertEqual(tsla.settlement_type, fs.SettlementType.UNKNOWN)

    @unittest.expectedFailure
    def test_create_stock_fail_2(
        self,
    ):
        tsla = fs.Stock(
            ticker="TSLA",
        )

        self.assertEqual(tsla.option_flavor, fs.OptionFlavor.CALL)


# Test ETP #


class TestETPConstructor(BaseTestCase):
    def test_create_etp_1(
        self,
    ):
        hyg = fs.ETP(
            ticker="HYG",
            gsid=fs.GSID(124),
            description="ISHARES IBOXX HIGH YLD CORP",
            primary_exc=fs.Exchange.NYSE,
            issuer="ishares",
        )

        self.assertEqual(hyg.security_type, fs.SecurityType.EQUITY)
        self.assertEqual(hyg.security_subtype, fs.SecuritySubtype.ETP)

        self.assertEqual(hyg.primary_exchange, fs.Exchange.NYSE)
        self.assertEqual(hyg.ticker, "HYG")
        self.assertEqual(hyg.identifiers, [])

    def test_create_etp_2(
        self,
    ):
        hyg = fs.ETP(
            ticker=" hyg ",
            gsid=fs.GSID(124),
            # description = 'ISHARES IBOXX HIGH YLD CORP',
            # primary_exc = fs.Exchange.NYSE,
            # issuer      = 'ishares',
        )

        self.assertEqual(hyg.security_type, fs.SecurityType.EQUITY)
        self.assertEqual(hyg.security_subtype, fs.SecuritySubtype.ETP)

        # self.assertEqual(hyg.primary_exchange, fs.Exchange.NYSE)
        self.assertEqual(hyg.ticker, "HYG")
        self.assertEqual(hyg.identifiers, [])
