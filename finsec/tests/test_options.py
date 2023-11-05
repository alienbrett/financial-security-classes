import datetime
import unittest

import finsec as fs

from .base_test import BaseTestCase

try:
    import zoneinfo

    nyc = zoneinfo.ZoneInfo("US/Eastern")
except ModuleNotFoundError:
    import pytz

    nyc = pytz.timezone("US/Eastern")


class TestOptionConstructor(BaseTestCase):
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

    def test_create_european_call_1(self):

        option = fs.European(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            # I understand this dates the test, using SPX 4,000 calls!
            # Or I hope this dates the test...
            callput="call",
            strike=4000,
            expiry_date=datetime.date(2022, 9, 16),
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
            # This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            # Without this argument, this should be set to UNKNOWN
            # expiry_series_type  = fs.ExpirySeriesType.MONTHLY,
        )

        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.INDEX_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.CALL)
        # self.assertEqual(option.option_exercise, fs.OptionExerciseStyle.EUROPEAN)
        self.assertEqual(option.exercise.style, fs.OptionExerciseStyle.EUROPEAN)
        self.assertEqual(
            option.exercise.exercise.expiry_date, datetime.date(2022, 9, 16)
        )
        self.assertEqual(
            option.exercise.exercise.expiry_series_type, fs.ExpirySeriesType.UNKNOWN
        )
        self.assertEqual(
            option.exercise.exercise.settlement_type, fs.SettlementType.CASH
        )

        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)

        self.assertEqual(option.ticker, "SPX220916C04000000")
        self.assertEqual(option.gsid, fs.GSID(120))

        self.assertEqual(option.multiplier, 100)

        self.assertIn(fs.FIGI("234567"), option.identifiers)

        self.assertEqual(
            option.denominated_ccy, fs.create_reference_from_security(self.usd)
        )

    def test_create_european_call_2(self):
        option = fs.European(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            callput="call",
            strike=4000,
            expiry_date="2022-09-16",
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
            # This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            # Without this argument, this should be set to UNKNOWN
            expiry_series_type=fs.ExpirySeriesType.MONTHLY,
        )

        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.INDEX_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.CALL)

        self.assertEqual(option.exercise.style, fs.OptionExerciseStyle.EUROPEAN)
        self.assertEqual(
            option.exercise.exercise.expiry_date, datetime.date(2022, 9, 16)
        )
        self.assertEqual(
            option.exercise.exercise.settlement_type, fs.SettlementType.CASH
        )
        self.assertEqual(
            option.exercise.exercise.expiry_series_type, fs.ExpirySeriesType.MONTHLY
        )

        self.assertEqual(option.multiplier, 100)

        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)

        self.assertEqual(option.ticker, "SPX220916C04000000")
        self.assertEqual(
            option.gsid,
            fs.GSID(120),
        )

        self.assertIn(fs.FIGI("234567"), option.identifiers)

        self.assertEqual(
            option.denominated_ccy, fs.create_reference_from_security(self.usd)
        )

    @unittest.expectedFailure
    def test_create_european_call_3(self):
        option = fs.European(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            # I understand this dates the test, using SPX 4,000 calls!
            # Or I hope this dates the test...
            callput="call",
            strike=4000,
            expiry_date="2022-09-16",
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
            # THis line should generate an exception
            settlement_type=fs.SettlementType.PHYSICAL,
        )
        if option:
            self.assertTrue(True)

    def test_create_european_put_1(self):
        option = fs.European(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            callput=fs.OptionFlavor.PUT,
            strike=4000,
            expiry_date=datetime.datetime(2022, 9, 16, 9, 30, tzinfo=nyc),
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
        )
        self.assertEqual(option.exercise.style, fs.OptionExerciseStyle.EUROPEAN)
        self.assertEqual(
            option.exercise.exercise.expiry_date, datetime.date(2022, 9, 16)
        )
        self.assertEqual(
            option.exercise.exercise.expiry_datetime,
            datetime.datetime(2022, 9, 16, 9, 30, tzinfo=nyc),
        )
        self.assertEqual(
            option.exercise.exercise.expiry_series_type, fs.ExpirySeriesType.UNKNOWN
        )
        self.assertEqual(
            option.exercise.exercise.settlement_type, fs.SettlementType.CASH
        )
        self.assertEqual(
            option.exercise.exercise.expiry_time_of_day, fs.ExpiryTimeOfDay.OPEN
        )
        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.INDEX_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.PUT)
        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)
        self.assertEqual(option.ticker, "SPX220916P04000000")
        self.assertEqual(option.gsid, fs.GSID(120))
        self.assertEqual(option.multiplier, 100)
        self.assertIn(fs.FIGI("234567"), option.identifiers)

        self.assertEqual(
            option.denominated_ccy, fs.create_reference_from_security(self.usd)
        )

    def test_create_european_put_2(self):

        option = fs.European(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            # I understand this dates the test, using SPX 4,000 calls!
            # Or I hope this dates the test...
            callput="put",
            strike=4000,
            expiry_date="2022-09-16",
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
            # This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            # Without this argument, this should be set to UNKNOWN
            expiry_series_type=fs.ExpirySeriesType.MONTHLY,
        )

        self.assertEqual(option.exercise.style, fs.OptionExerciseStyle.EUROPEAN)
        self.assertEqual(
            option.exercise.exercise.expiry_date, datetime.date(2022, 9, 16)
        )
        self.assertEqual(
            option.exercise.exercise.expiry_series_type, fs.ExpirySeriesType.MONTHLY
        )
        self.assertEqual(
            option.exercise.exercise.settlement_type, fs.SettlementType.CASH
        )
        self.assertEqual(
            option.exercise.exercise.expiry_time_of_day, fs.ExpiryTimeOfDay.OPEN
        )

        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.INDEX_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.PUT)

        self.assertEqual(option.multiplier, 100)

        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)
        self.assertEqual(option.ticker, "SPX220916P04000000")
        self.assertEqual(
            option.gsid,
            fs.GSID(120),
        )

        self.assertIn(
            fs.FIGI("234567"),
            option.identifiers,
        )

        self.assertEqual(
            option.denominated_ccy, fs.create_reference_from_security(self.usd)
        )

    @unittest.expectedFailure
    def test_create_european_put_3(self):
        option = fs.European(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            # I understand this dates the test, using SPX 4,000 calls!
            # Or I hope this dates the test...
            callput="put",
            strike=4000,
            expiry_date="2022-09-16",
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
            # THis line should generate an exception
            settlement_type=fs.SettlementType.PHYSICAL,
        )
        if option:
            self.assertTrue(True)

    def test_create_american_call_1(self):
        option = fs.American(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            # I understand this dates the test, using SPX 4,000 calls!
            # Or I hope this dates the test...
            callput="call",
            strike=4000,
            expiry_date=datetime.date(2022, 9, 16),
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
            # This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            # Without this argument, this should be set to UNKNOWN
            # expiry_series_type  = fs.ExpirySeriesType.MONTHLY,
        )
        self.assertEqual(option.exercise.style, fs.OptionExerciseStyle.AMERICAN)
        self.assertEqual(
            option.exercise.exercise.expiry_date, datetime.date(2022, 9, 16)
        )
        self.assertEqual(
            option.exercise.exercise.expiry_series_type, fs.ExpirySeriesType.UNKNOWN
        )
        self.assertEqual(
            option.exercise.exercise.settlement_type, fs.SettlementType.CASH
        )
        self.assertEqual(
            option.exercise.exercise.expiry_time_of_day, fs.ExpiryTimeOfDay.OPEN
        )

        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.INDEX_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.CALL)
        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)

        # # THese should berred without needing to be explicitly set
        self.assertEqual(option.ticker, "SPX220916C04000000")
        self.assertEqual(
            option.gsid,
            fs.GSID(120),
        )
        self.assertEqual(option.multiplier, 100)
        self.assertIn(fs.FIGI("234567"), option.identifiers)
        self.assertEqual(
            option.denominated_ccy, fs.create_reference_from_security(self.usd)
        )

    def test_create_american_call_2(self):

        option = fs.American(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            # I understand this dates the test, using SPX 4,000 calls!
            # Or I hope this dates the test...
            callput="call",
            strike=4000,
            expiry_date="2022-09-16",
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
            # This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            # Without this argument, this should be set to UNKNOWN
            expiry_series_type=fs.ExpirySeriesType.MONTHLY,
        )
        self.assertEqual(option.exercise.style, fs.OptionExerciseStyle.AMERICAN)
        self.assertEqual(
            option.exercise.exercise.expiry_date, datetime.date(2022, 9, 16)
        )
        self.assertEqual(
            option.exercise.exercise.expiry_series_type, fs.ExpirySeriesType.MONTHLY
        )
        self.assertEqual(
            option.exercise.exercise.settlement_type, fs.SettlementType.CASH
        )
        self.assertEqual(
            option.exercise.exercise.expiry_time_of_day, fs.ExpiryTimeOfDay.OPEN
        )

        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.INDEX_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.CALL)
        self.assertEqual(option.multiplier, 100)
        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)
        self.assertEqual(option.ticker, "SPX220916C04000000")
        self.assertEqual(option.gsid, fs.GSID(120))
        self.assertIn(fs.FIGI("234567"), option.identifiers)
        self.assertEqual(
            option.denominated_ccy, fs.create_reference_from_security(self.usd)
        )

    @unittest.expectedFailure
    def test_create_american_call_3(self):

        option = fs.American(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            # I understand this dates the test, using SPX 4,000 calls!
            # Or I hope this dates the test...
            callput="call",
            strike=4000,
            expiry_date="2022-09-16",
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
            # THis line should generate an exception
            settlement_type=fs.SettlementType.PHYSICAL,
        )
        if option:
            self.assertTrue(True)

    def test_create_american_put_1(self):

        option = fs.American(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            # I understand this dates the test, using SPX 4,000 calls!
            # Or I hope this dates the test...
            callput="put",
            strike=4000,
            expiry_date=datetime.date(2022, 9, 16),
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
        )
        self.assertEqual(option.exercise.style, fs.OptionExerciseStyle.AMERICAN)
        self.assertEqual(
            option.exercise.exercise.expiry_date, datetime.date(2022, 9, 16)
        )
        self.assertEqual(
            option.exercise.exercise.expiry_series_type, fs.ExpirySeriesType.UNKNOWN
        )
        self.assertEqual(
            option.exercise.exercise.settlement_type, fs.SettlementType.CASH
        )
        self.assertEqual(
            option.exercise.exercise.expiry_time_of_day, fs.ExpiryTimeOfDay.OPEN
        )

        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.INDEX_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.PUT)
        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)
        self.assertEqual(option.ticker, "SPX220916P04000000")
        self.assertEqual(
            option.gsid,
            fs.GSID(120),
        )
        self.assertEqual(option.multiplier, 100)
        self.assertIn(fs.FIGI("234567"), option.identifiers)
        self.assertEqual(
            option.denominated_ccy, fs.create_reference_from_security(self.usd)
        )

    def test_create_american_put_2(self):

        option = fs.American(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            # I understand this dates the test, using SPX 4,000 calls!
            # Or I hope this dates the test...
            callput="put",
            strike=4000,
            expiry_date="2022-09-16",
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
            # This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            # Without this argument, this should be set to UNKNOWN
            expiry_series_type=fs.ExpirySeriesType.MONTHLY,
        )
        self.assertEqual(option.exercise.style, fs.OptionExerciseStyle.AMERICAN)
        self.assertEqual(
            option.exercise.exercise.expiry_date, datetime.date(2022, 9, 16)
        )
        self.assertEqual(
            option.exercise.exercise.expiry_series_type, fs.ExpirySeriesType.MONTHLY
        )
        self.assertEqual(
            option.exercise.exercise.settlement_type, fs.SettlementType.CASH
        )
        self.assertEqual(
            option.exercise.exercise.expiry_time_of_day, fs.ExpiryTimeOfDay.OPEN
        )

        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.INDEX_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.PUT)
        self.assertEqual(option.multiplier, 100)
        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)
        self.assertEqual(option.ticker, "SPX220916P04000000")
        self.assertEqual(option.gsid, fs.GSID(120))
        self.assertIn(fs.FIGI("234567"), option.identifiers)

        self.assertEqual(
            option.denominated_ccy, fs.create_reference_from_security(self.usd)
        )

    @unittest.expectedFailure
    def test_create_american_put_3(self):
        option = fs.American(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            # I understand this dates the test, using SPX 4,000 calls!
            # Or I hope this dates the test...
            callput="put",
            strike=4000,
            expiry_date="2022-09-16",
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
            # THis line should generate an exception
            settlement_type=fs.SettlementType.PHYSICAL,
        )
        if option:
            self.assertTrue(True)

    def test_serialize_option_1(self):
        obj = fs.American(
            gsid=fs.GSID(120),
            underlying_security=self.spx,
            # I understand this dates the test, using SPX 4,000 calls!
            # Or I hope this dates the test...
            callput="put",
            strike=4000,
            expiry_date="2022-09-16",
            primary_exc=fs.Exchange.CBOE,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            multiplier=100.0,
            identifiers=[fs.FIGI("234567")],
            # This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            # Without this argument, this should be set to UNKNOWN
            expiry_series_type=fs.ExpirySeriesType.MONTHLY,
        )

        obj_json = obj.model_dump_json()
        obj_recovered = fs.Option.model_validate_json(obj_json)

        self.assertEqual(obj_recovered, obj)
        self.assertEqual(
            obj_recovered.exercise.exercise.expiry_date, datetime.date(2022, 9, 16)
        )
        self.assertEqual(
            obj_recovered.exercise.exercise.expiry_series_type,
            fs.ExpirySeriesType.MONTHLY,
        )
        self.assertEqual(
            obj_recovered.exercise.exercise.settlement_type, fs.SettlementType.CASH
        )
        self.assertEqual(
            obj_recovered.exercise.exercise.expiry_time_of_day, fs.ExpiryTimeOfDay.OPEN
        )

    def test_american_unknown_settlement_failure(self):
        try:
            option = fs.American(
                gsid=fs.GSID(120),
                underlying_security=self.hyg,
                callput="call",
                strike=85,
                expiry_date="2022-09-16",
                primary_exc=fs.Exchange.CBOE,
                expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
                multiplier=100.0,
                identifiers=[fs.FIGI("234567")],
                # THis line should generate an exception
                # settlement_type=fs.SettlementType.PHYSICAL,
                currency=self.usd,
            )
            option = option

        except fs.InvalidSettlementType:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_american_unknown_currency_failure(self):
        try:
            option = fs.American(
                gsid=fs.GSID(120),
                underlying_security=self.hyg,
                callput="call",
                strike=85,
                expiry_date="2022-09-16",
                primary_exc=fs.Exchange.CBOE,
                expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
                multiplier=100.0,
                identifiers=[fs.FIGI("234567")],
                settlement_type=fs.SettlementType.PHYSICAL,
            )
            option = option

        except fs.UnknownDenominatedCurrency:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_european_unknown_settlement_failure(self):
        try:
            option = fs.European(
                gsid=fs.GSID(120),
                underlying_security=self.hyg,
                callput="call",
                strike=85,
                expiry_date="2022-09-16",
                primary_exc=fs.Exchange.CBOE,
                expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
                multiplier=100.0,
                identifiers=[fs.FIGI("234567")],
                # THis line should generate an exception
                # settlement_type=fs.SettlementType.PHYSICAL,
                currency=self.usd,
            )
            option = option

        except fs.InvalidSettlementType:
            self.assertTrue(True)
        else:
            self.assertTrue(False)
