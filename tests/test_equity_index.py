import unittest
import finsec as fs


class TestIndexConstructor(unittest.TestCase):

    def test_create_index_1(self,):
        usd = fs.DerivedIndex(
            ticker = 'SPX',
            issuer = 'Standard & Poor',
            gsid   = fs.GSID(100),
            identifiers = [
                fs.FIGI('12345'),
            ],
        )

        self.assertEqual(usd.security_type, fs.SecurityType.INDEX)
        self.assertEqual(usd.security_subtype, fs.SecuritySubtype.DERIVED_INDEX)

        self.assertEqual(usd.ticker, 'SPX')
        self.assertEqual(usd.issuer, 'Standard & Poor')
        self.assertIn(fs.FIGI('12345'), usd.identifiers,)
