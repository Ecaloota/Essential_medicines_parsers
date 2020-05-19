import unittest
from orange_book_parser import Drug as obp

class TestOrangeBookParser(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_ingredient_name(self):
        self.assertEqual(['budesonide'],obp.parse_ingredient_name(self,"BUDESONIDE"))
        self.assertEqual(['betamethasone valerate'],obp.parse_ingredient_name(self,"BETAMETHASONE VALERATE"))
        self.assertEqual(['budesonide','formoterol fumarate dihydrate'],obp.parse_ingredient_name(self,"BUDESONIDE; FORMOTEROL FUMARATE DIHYDRATE"))
        self.assertEqual(['amoxicillin','omeprazole magnesium','rifabutin'],\
            obp.parse_ingredient_name(self,"AMOXICILLIN; OMEPRAZOLE MAGNESIUM; RIFABUTIN"))

    def test_parse_approve_date(self):
        pass

if __name__=="__main__":
    unittest.main()