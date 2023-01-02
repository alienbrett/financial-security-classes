import datetime
import zoneinfo

import finsec as fs

from .base_test import BaseTestCase

nyc = zoneinfo.ZoneInfo("US/Eastern")


class TestSerializers(BaseTestCase):
    def setUp(
        self,
    ):
        self.usd = fs.FiatCurrency(
            ticker="USD",
            nation="United States",
            gsid=fs.GSID(100),
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

        self.option = fs.European(
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
            identifiers=[
                fs.FIGI("234567"),
            ],
            # This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            # Without this argument, this should be set to UNKNOWN
            # expiry_series_type  = fs.ExpirySeriesType.MONTHLY,
        )

        exact_expiry_time = datetime.datetime(2023, 3, 17, 9, 30, 0, tzinfo=nyc)

        self.esh23 = fs.NewFuture(
            gsid=fs.GSID("blah"),
            ticker="ESH23",
            underlying_security=self.spx,
            expiry_date=exact_expiry_time,
            primary_exc=fs.Exchange.CME,
            expiry_time_of_day=fs.ExpiryTimeOfDay.OPEN,
            tick_size=0.25,
            multiplier=50.0,
            identifiers=[
                fs.FIGI("234567"),
            ],
            # This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            expiry_series_type=fs.ExpirySeriesType.QUARTERLY,
            currency=self.usd,
        )

    def test_serializers_1(self):
        for obj in [self.usd, self.spx, self.esh23, self.option]:

            obj_dict = fs.dict_encode(obj)
            recovered_obj = fs.dict_decode(obj_dict)

            self.assertEqual(obj, recovered_obj)

    def test_serializers_2(self):
        for obj in [self.usd, self.spx, self.esh23, self.option]:

            obj_dict = fs.json_encode(obj)
            recovered_obj = fs.json_decode(obj_dict)

            self.assertEqual(obj, recovered_obj)
