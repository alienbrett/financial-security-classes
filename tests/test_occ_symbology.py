
import unittest
import datetime
import finsec as fs


class TestOCCSymbology(unittest.TestCase):

    def setUp(self,):
        pass


    def test_constructor_1(self,):
        occ = fs.option_format(
            symbol      = 'SPY',
            exp_date    = datetime.date(2012,11,17),
            flavor      = 'call',
            strike      = 140.,
        )

        self.assertEqual(occ, 'SPY121117C00140000')
        self.assertEqual(140, fs.option_strike(occ))
        self.assertEqual('call', fs.option_flavor(occ))
        self.assertEqual('SPY', fs.option_symbol(occ))


    def test_constructor_2(self,):
        occ = fs.option_format(
            symbol      = 'lamr ',
            exp_date    = datetime.datetime(2015,1,17),
            flavor      = 'call',
            strike      = 52.50,
        )

        self.assertEqual(occ, 'LAMR150117C00052500')
        self.assertEqual(52.50, fs.option_strike(occ))
        self.assertEqual('call', fs.option_flavor(occ))
        self.assertEqual('LAMR', fs.option_symbol(occ))


    def test_constructor_3(self,):
        occ = fs.option_format(
            symbol      = 'SPx',
            exp_date    = '2014-11-22',
            flavor      = 'put',
            strike      = 19.5,
        )

        self.assertEqual(occ, 'SPX141122P00019500')
        self.assertEqual(19.5, fs.option_strike(occ))
        self.assertEqual('put', fs.option_flavor(occ))
        self.assertEqual('SPX', fs.option_symbol(occ))