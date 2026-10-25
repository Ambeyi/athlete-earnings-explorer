import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from analyze import summarize, write_outputs

class EarningsTests(unittest.TestCase):
    def setUp(self):
        self.data=pd.DataFrame({'name':['A','B','A','C'], 'sport':['Sport X','Sport Y','Sport X','Sport X'],
            'year':[2000,2000,2002,2002], 'earnings':[10,20,30,50], 'current_rank':[2,1,2,1]})
    def test_hand_calculated_aggregates(self):
        annual,sport,rank,audit=summarize(self.data)
        self.assertEqual(annual.loc[2000,'mean_earnings'],15)
        self.assertEqual(annual.loc[2002,'total_earnings'],80)
        self.assertEqual(sport.loc['Sport X','appearances'],3)
        self.assertEqual(sport.loc['Sport X','unique_athletes'],2)
        self.assertEqual(rank.loc[1,'mean_earnings'],35)
        self.assertEqual(audit['missing_years'],[2001])
    def test_numeric_rank_order(self):
        self.data['current_rank']=['10','2','1','3']
        self.assertEqual(list(summarize(self.data)[2].index),[1,2,3,10])
    def test_invalid_records(self):
        bad=[pd.concat([self.data,self.data.iloc[:1]]), self.data.assign(earnings=np.inf),
             self.data.assign(earnings=-1), self.data.assign(current_rank=1.5),
             self.data.assign(name=' '),self.data.drop(columns='sport'),self.data.iloc[:0]]
        for data in bad:
            with self.assertRaises(ValueError): summarize(data)
    def test_export(self):
        with tempfile.TemporaryDirectory() as folder:
            write_outputs(self.data,folder)
            self.assertEqual(len(list(Path(folder).iterdir())),5)
            chart=(Path(folder)/'annual_earnings.svg').read_text()
            self.assertIn('<svg',chart)
            self.assertEqual(len(pd.read_csv(Path(folder)/'annual_summary.csv')),2)

if __name__ == '__main__': unittest.main()
