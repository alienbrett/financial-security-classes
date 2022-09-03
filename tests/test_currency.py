import unittest
import finsec as fs


class TestCurrencyConstructor(unittest.TestCase):

    def test_create_currency_1(self,):
        usd = fs.FiatCurrency(
            ticker = 'USD',
            nation = 'United States',
            gsid   = fs.GSID(100),
        )

        self.assertEqual(usd.security_type, fs.SecurityType.CURRENCY)
        self.assertEqual(usd.security_subtype, fs.SecuritySubtype.NATIONAL_FIAT)

        self.assertEqual(usd.ticker, 'USD')
        self.assertEqual(usd.issuer, 'United States')
        self.assertEqual(usd.identifiers, [])




    def test_create_currency_2(self,):
        usd = fs.FiatCurrency(
            ticker = 'USD',
            nation = 'United States',
            gsid   = fs.GSID(100),
            identifiers = [
                fs.FIGI('12345'),
            ],
        )

        self.assertIn(fs.FIGI('12345'), usd.identifiers,)





    @unittest.expectedFailure
    def test_create_usd_fail_1(self,):
        usd = fs.FiatCurrency(
            ticker = 'USD',
            nation = 'United States',
            gsid   = fs.GSID(100),
            identifiers = [
                fs.FIGI('12345'),
            ],
        )

        self.assertEqual(usd.settlement_type, fs.SettlementType.UNKNOWN)


    @unittest.expectedFailure
    def test_create_usd_fail_2(self,):
        usd = fs.FiatCurrency(
            ticker = 'USD',
            nation = 'United States',
            gsid   = fs.GSID(100),
            identifiers = [
                fs.FIGI('12345'),
            ],
        )

        self.assertEqual(usd.primary_exchange, fs.Exchange.NYSE)
        # self.assertEqual(usd.settlement_type, fs.SettlementType.UNKNOWN)
    

    ################## Crypto

    def test_create_crypto_currency_1(self,):
        btc = fs.CryptoCurrency(
            ticker = ' btc ',
            gsid   = fs.GSID(100),
            identifiers = [fs.FIGI('test')],
        )

        self.assertIn(fs.FIGI('test'), btc.identifiers,)
        self.assertEqual(btc.security_type, fs.SecurityType.CURRENCY)
        self.assertEqual(btc.security_subtype, fs.SecuritySubtype.CRYPTOCURRENCY)

        self.assertEqual(btc.ticker, 'BTC')
        self.assertIsNone(btc.issuer,)