import unittest
import datetime
import json
import finsec as fs
import zoneinfo

from base_test import BaseTestCase

nyc = zoneinfo.ZoneInfo('US/Eastern')

class TestFutureConstructor(BaseTestCase):

    def setUp(self,):
        self.usd = fs.FiatCurrency(
            ticker = 'USD',
            nation = 'United States Dollar',
            gsid   = fs.GSID(20),
            identifiers = [
                fs.FIGI('abcdefg'),
            ],
        )
        self.jpy = fs.FiatCurrency(
            ticker = 'JPY',
            nation = 'Japanese Yen',
            gsid   = fs.GSID(30),
            identifiers = [
                fs.FIGI('ecdfg'),
            ],
        )

        self.spx = fs.DerivedIndex(
            ticker = 'SPX',
            issuer = 'Standard & Poor',
            gsid   = fs.GSID(100),
            identifiers = [
                fs.FIGI('12345'),
            ],
            currency = self.usd,
        )

        self.esu22 = fs.NewFuture(
            gsid                = fs.GSID(120),
            ticker              = 'ESU22',
            underlying_security = self.spx,

            expiry_date         = datetime.date(2022,9,16),
            primary_exc         = fs.Exchange.CME,

            expiry_time_of_day  = fs.ExpiryTimeOfDay.OPEN,

            tick_size           = 0.25,
            multiplier          = 50.0,

            identifiers         = [
                fs.FIGI('234567'),
            ],

            #### This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            #### Without this argument, this should be set to UNKNOWN
            # expiry_series_type  = fs.ExpirySeriesType.MONTHLY,

        )

        exact_expiry_time = datetime.datetime( 2023,3,17, 9, 30,0, tzinfo = nyc)

        self.esh23 = fs.NewFuture(
            gsid                = fs.GSID('blah'),
            ticker              = 'ESH23',
            underlying_security = self.spx,

            expiry_date         = datetime.date(2023,3,17),
            primary_exc         = fs.Exchange.CME,

            expiry_time_of_day  = fs.ExpiryTimeOfDay.OPEN,
            expiry_datetime     = exact_expiry_time,

            tick_size           = 0.25,
            multiplier          = 50.0,

            identifiers         = [
                fs.FIGI('234567'),
            ],

            #### This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            expiry_series_type  = fs.ExpirySeriesType.QUARTERLY,

            currency = self.jpy,
        )


    def test_create_future_1(self,):

        self.assertEqual(self.esu22.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(self.esu22.security_subtype, fs.SecuritySubtype.FUTURE)

        self.assertEqual(self.esu22.primary_exchange, fs.Exchange.CME)
        self.assertEqual(self.esu22.expiry_date, datetime.date(2022,9,16))
        
        ## THese should be inferred without needing to be explicitly set
        self.assertEqual(self.esu22.expiry_series_type, fs.ExpirySeriesType.UNKNOWN)
        self.assertEqual(self.esu22.settlement_type, fs.SettlementType.CASH)

        self.assertEqual(self.esu22.ticker, 'ESU22')
        self.assertEqual(self.esu22.gsid, fs.GSID(120),)

        self.assertIn(fs.FIGI('234567'), self.esu22.identifiers,)

        self.assertEqual(self.esu22.denominated_ccy, fs.create_reference_from_security(self.usd))

    


    def test_create_future_2(self,):
    

        self.assertEqual(self.esh23.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(self.esh23.security_subtype, fs.SecuritySubtype.FUTURE)

        self.assertEqual(self.esh23.ticker, 'ESH23')

        self.assertEqual(self.esh23.primary_exchange, fs.Exchange.CME)
        self.assertEqual(self.esh23.expiry_date, datetime.date(2023,3,17))
        
        ## These should be inferred without needing to be explicitly set
        self.assertEqual(self.esh23.expiry_series_type, fs.ExpirySeriesType.QUARTERLY)
        self.assertEqual(self.esh23.settlement_type, fs.SettlementType.CASH)

        self.assertEqual(self.esh23.denominated_ccy, fs.create_reference_from_security(self.jpy))




    def test_serialize_future_1(self,):
        obj = self.esh23

        # obj_dict = obj.dict()
        # obj_json = json.dumps(obj_dict)
        obj_json = obj.json()

        obj_recovered = fs.Future.parse_raw(obj_json)

        self.assertEqual(obj_recovered, obj)


    def test_serialize_future_2(self,):
        obj = self.esu22

        # obj_dict = obj.dict()
        # obj_json = json.dumps(obj_dict)
        obj_json = obj.json()

        obj_recovered = fs.Future.parse_raw(obj_json)

        self.assertEqual(obj_recovered, obj)




    def test_serialize_usd_1(self,):
        obj = self.usd

        # obj_dict = obj.dict()
        # obj_json = json.dumps(obj_dict)
        obj_json = obj.json()

        obj_recovered = fs.Security.parse_raw(obj_json)

        self.assertEqual(obj_recovered, obj)


    def test_serialize_jpy_1(self,):
        obj = self.jpy

        # obj_dict = obj.dict()
        # obj_json = json.dumps(obj_dict)
        obj_json = obj.json()

        obj_recovered = fs.Security.parse_raw(obj_json)
        # obj_recovered = fs.Security.parse_raw(obj_json)

        self.assertEqual(obj_recovered, obj)