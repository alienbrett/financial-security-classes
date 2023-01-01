import unittest
import finsec as fs

from base_test import BaseTestCase

class TestIndexConstructor(BaseTestCase):

    def setUp(self,):
        self.usd = fs.FiatCurrency(
            ticker = 'USD',
            nation = 'United States',
            gsid   = fs.GSID(20),
            identifiers = [
                fs.FIGI('abcdefg'),
            ],
        )

    def test_create_index_1(self,):
        spx = fs.DerivedIndex(
            ticker = 'spx',
            issuer = 'Standard & Poor',
            gsid   = fs.GSID(100),
            identifiers = [
                fs.FIGI('12345'),
            ],
        )

        self.assertEqual(spx.security_type, fs.SecurityType.INDEX)
        self.assertEqual(spx.security_subtype, fs.SecuritySubtype.DERIVED_INDEX)

        self.assertEqual(spx.ticker, 'SPX')
        self.assertEqual(spx.issuer, 'Standard & Poor')
        self.assertIn(fs.FIGI('12345'), spx.identifiers,)


    def test_create_index_2(self,):
        spx = fs.DerivedIndex(
            ticker = 'SPX',
            issuer = 'Standard & Poor',
            gsid   = fs.GSID(100),
            identifiers = [
                fs.FIGI('12345'),
            ],
            currency = self.usd,
        )

        usd_ref = fs.create_reference_from_security(self.usd)
        self.assertEqual(spx.denominated_ccy, usd_ref)



    # def test_serialize_1(self,):
    #     spx = fs.DerivedIndex(
    #         ticker = 'spx',
    #         issuer = 'Standard & Poor',
    #         gsid   = fs.GSID(100),
    #         identifiers = [
    #             fs.FIGI('12345'),
    #         ],
    #     )