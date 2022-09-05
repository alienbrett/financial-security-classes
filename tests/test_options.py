import unittest
import datetime
import finsec as fs


class TestOptionConstructor(unittest.TestCase):

    def setUp(self,):
        self.usd = fs.FiatCurrency(
            ticker = 'USD',
            nation = 'United States Dollar',
            gsid   = fs.GSID(20),
            identifiers = [
                fs.FIGI('abcdefg'),
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



    def test_create_european_call_1(self,):

        option = fs.European(
            gsid                = fs.GSID(120),
            underlying_security = self.spx,

            ## I understand this dates the test, using SPX 4,000 calls!
            ## Or I hope this dates the test...
            callput             = 'call',
            strike              = 4000,

            expiry_date         = datetime.date(2022,9,16),
            primary_exc         = fs.Exchange.CBOE,

            expiry_time_of_day  = fs.ExpiryTimeOfDay.OPEN,

            multiplier          = 100.0,

            identifiers         = [
                fs.FIGI('234567'),
            ],

            #### This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            #### Without this argument, this should be set to UNKNOWN
            # expiry_series_type  = fs.ExpirySeriesType.MONTHLY,

        )

        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.EQUITY_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.CALL)


        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)
        self.assertEqual(option.expiry_date, datetime.date(2022,9,16))
        
        # ## THese should berred without needing to be explicitly set
        self.assertEqual(option.expiry_series_type, fs.ExpirySeriesType.UNKNOWN)
        self.assertEqual(option.settlement_type, fs.SettlementType.CASH)

        self.assertEqual(option.ticker, 'SPX220916C04000000')
        self.assertEqual(option.gsid, fs.GSID(120),)

        self.assertEqual(option.multiplier, 100,)

        self.assertIn(fs.FIGI('234567'), option.identifiers,)

        self.assertEqual(option.denominated_ccy, fs.create_reference_from_security(self.usd))



    def test_create_european_call_2(self,):

        option = fs.European(
            gsid                = fs.GSID(120),
            underlying_security = self.spx,

            ## I understand this dates the test, using SPX 4,000 calls!
            ## Or I hope this dates the test...
            callput             = 'call',
            strike              = 4000,

            expiry_date         = '2022-09-16',
            primary_exc         = fs.Exchange.CBOE,

            expiry_time_of_day  = fs.ExpiryTimeOfDay.OPEN,

            multiplier          = 100.0,

            identifiers         = [
                fs.FIGI('234567'),
            ],

            #### This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            #### Without this argument, this should be set to UNKNOWN
            expiry_series_type  = fs.ExpirySeriesType.MONTHLY,

        )

        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.EQUITY_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.CALL)

        self.assertEqual(option.multiplier, 100,)

        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)
        self.assertEqual(option.expiry_date, datetime.date(2022,9,16))
        
        self.assertEqual(option.expiry_series_type, fs.ExpirySeriesType.MONTHLY)
        # ## THese should berred without needing to be explicitly set
        self.assertEqual(option.settlement_type, fs.SettlementType.CASH)

        self.assertEqual(option.ticker, 'SPX220916C04000000')
        self.assertEqual(option.gsid, fs.GSID(120),)

        self.assertIn(fs.FIGI('234567'), option.identifiers,)

        self.assertEqual(option.denominated_ccy, fs.create_reference_from_security(self.usd))
    



    @unittest.expectedFailure
    def test_create_european_call_3(self,):

        option = fs.European(
            gsid                = fs.GSID(120),
            underlying_security = self.spx,

            ## I understand this dates the test, using SPX 4,000 calls!
            ## Or I hope this dates the test...
            callput             = 'call',
            strike              = 4000,

            expiry_date         = '2022-09-16',
            primary_exc         = fs.Exchange.CBOE,

            expiry_time_of_day  = fs.ExpiryTimeOfDay.OPEN,

            multiplier          = 100.0,

            identifiers         = [
                fs.FIGI('234567'),
            ],

            #### THis line should generate an exception
            settlement_type     = fs.SettlementType.PHYSICAL,

        )
    


    def test_create_european_put_1(self,):

        option = fs.European(
            gsid                = fs.GSID(120),
            underlying_security = self.spx,

            ## I understand this dates the test, using SPX 4,000 calls!
            ## Or I hope this dates the test...
            callput             = 'put',
            strike              = 4000,

            expiry_date         = datetime.date(2022,9,16),
            primary_exc         = fs.Exchange.CBOE,

            expiry_time_of_day  = fs.ExpiryTimeOfDay.OPEN,

            multiplier          = 100.0,

            identifiers         = [
                fs.FIGI('234567'),
            ],
        )

        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.EQUITY_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.PUT)

        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)
        self.assertEqual(option.expiry_date, datetime.date(2022,9,16))
        
        # ## THese should berred without needing to be explicitly set
        self.assertEqual(option.expiry_series_type, fs.ExpirySeriesType.UNKNOWN)
        self.assertEqual(option.settlement_type, fs.SettlementType.CASH)

        self.assertEqual(option.ticker, 'SPX220916P04000000')
        self.assertEqual(option.gsid, fs.GSID(120),)

        self.assertEqual(option.multiplier, 100,)

        self.assertIn(fs.FIGI('234567'), option.identifiers,)

        self.assertEqual(option.denominated_ccy, fs.create_reference_from_security(self.usd))



    def test_create_european_put_2(self,):

        option = fs.European(
            gsid                = fs.GSID(120),
            underlying_security = self.spx,

            ## I understand this dates the test, using SPX 4,000 calls!
            ## Or I hope this dates the test...
            callput             = 'put',
            strike              = 4000,

            expiry_date         = '2022-09-16',
            primary_exc         = fs.Exchange.CBOE,

            expiry_time_of_day  = fs.ExpiryTimeOfDay.OPEN,

            multiplier          = 100.0,

            identifiers         = [
                fs.FIGI('234567'),
            ],

            #### This should be implied, since underlyer doesn't permit physical delivery
            # settlement_type     = fs.SettlementType.CASH,
            #### Without this argument, this should be set to UNKNOWN
            expiry_series_type  = fs.ExpirySeriesType.MONTHLY,
        )

        self.assertEqual(option.security_type, fs.SecurityType.DERIVATIVE)
        self.assertEqual(option.security_subtype, fs.SecuritySubtype.EQUITY_OPTION)
        self.assertEqual(option.option_flavor, fs.OptionFlavor.PUT)

        self.assertEqual(option.multiplier, 100,)

        self.assertEqual(option.primary_exchange, fs.Exchange.CBOE)
        self.assertEqual(option.expiry_date, datetime.date(2022,9,16))
        
        self.assertEqual(option.expiry_series_type, fs.ExpirySeriesType.MONTHLY)
        # ## THese should berred without needing to be explicitly set
        self.assertEqual(option.settlement_type, fs.SettlementType.CASH)

        self.assertEqual(option.ticker, 'SPX220916P04000000')
        self.assertEqual(option.gsid, fs.GSID(120),)

        self.assertIn(fs.FIGI('234567'), option.identifiers,)

        self.assertEqual(option.denominated_ccy, fs.create_reference_from_security(self.usd))
    



    @unittest.expectedFailure
    def test_create_european_put_3(self,):

        option = fs.European(
            gsid                = fs.GSID(120),
            underlying_security = self.spx,

            ## I understand this dates the test, using SPX 4,000 calls!
            ## Or I hope this dates the test...
            callput             = 'put',
            strike              = 4000,

            expiry_date         = '2022-09-16',
            primary_exc         = fs.Exchange.CBOE,

            expiry_time_of_day  = fs.ExpiryTimeOfDay.OPEN,

            multiplier          = 100.0,

            identifiers         = [
                fs.FIGI('234567'),
            ],

            #### THis line should generate an exception
            settlement_type     = fs.SettlementType.PHYSICAL,

        )