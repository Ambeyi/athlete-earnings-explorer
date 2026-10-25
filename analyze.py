"""Validate athlete-year earnings records and export descriptive summaries."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REQUIRED = ['name', 'sport', 'year', 'earnings', 'current_rank']

def summarize(frame):
    missing = set(REQUIRED) - set(frame.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    if frame.empty:
        raise ValueError('Input must contain records')
    d = frame.copy()
    for col in ['name', 'sport']:
        if d[col].isna().any(): raise ValueError(f'Missing {col}')
        d[col] = d[col].astype(str).str.strip()
        if d[col].eq('').any(): raise ValueError(f'Blank {col}')
    for col in ['year', 'earnings', 'current_rank']:
        d[col] = pd.to_numeric(d[col], errors='raise')
        if not np.isfinite(d[col]).all(): raise ValueError(f'Nonfinite {col}')
    for col in ['year', 'current_rank']:
        if (d[col] != np.floor(d[col])).any(): raise ValueError(f'Noninteger {col}')
        d[col] = d[col].astype(int)
    if (d.earnings < 0).any() or (d.current_rank < 1).any():
        raise ValueError('Earnings must be nonnegative and ranks positive')
    if d.duplicated(['name', 'year']).any():
        raise ValueError('Duplicate athlete-year records')
    annual = d.groupby('year').agg(appearances=('name','size'), unique_athletes=('name','nunique'),
        total_earnings=('earnings','sum'), mean_earnings=('earnings','mean'), median_earnings=('earnings','median'))
    sport = d.groupby('sport').agg(appearances=('name','size'), unique_athletes=('name','nunique'),
        mean_earnings=('earnings','mean'), median_earnings=('earnings','median'))
    sport = sport.sort_values(['appearances','sport'], ascending=[False,True])
    rank = d.groupby('current_rank').agg(appearances=('name','size'), mean_earnings=('earnings','mean'), median_earnings=('earnings','median'))
    years = set(d.year)
    audit = {'rows':len(d), 'unique_athlete_names':int(d.name.nunique()), 'year_min':int(d.year.min()),
        'year_max':int(d.year.max()), 'observed_years':len(years),
        'missing_years':[y for y in range(int(d.year.min()),int(d.year.max())+1) if y not in years],
        'sport_labels':int(d.sport.nunique()), 'duplicate_athlete_years':0,
        'previous_year_rank_missing':int(frame.previous_year_rank.isna().sum()) if 'previous_year_rank' in frame else None,
        'years_not_ten_records':{str(y):int(n) for y,n in annual.appearances.items() if n != 10},
        'earnings_unit':'Source code labels values as millions; currency and measurement definitions unverified.',
        'interpretation':'Descriptive summaries of supplied ranking records, not all professional athletes.'}
    return annual, sport, rank, audit

def write_outputs(frame, output):
    annual, sport, rank, audit = summarize(frame)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name, table in [('annual_summary',annual), ('sport_summary',sport), ('rank_summary',rank)]:
        table.to_csv(output/f'{name}.csv')
    (output/'audit.json').write_text(json.dumps(audit, indent=2, allow_nan=False)+'\n')
    years = range(audit['year_min'],audit['year_max']+1)
    chart = annual.reindex(years)
    with plt.rc_context({'svg.fonttype':'none'}):
        fig, ax = plt.subplots(figsize=(9,4.5))
        ax.plot(chart.index,chart.mean_earnings,marker='o',markersize=3,label='Mean',color='#136f63')
        ax.plot(chart.index,chart.median_earnings,marker='s',markersize=3,label='Median',color='#b35528')
        ax.set(title='Earnings among listed athlete-year records',xlabel='Year',ylabel='Earnings (source units, millions)')
        ax.grid(axis='y',alpha=.2); ax.legend(); fig.tight_layout()
        fig.savefig(output/'annual_earnings.svg',metadata={'Description':'Annual mean and median earnings. Missing years appear as gaps.'})
        plt.close(fig)
    return audit

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv',type=Path)
    parser.add_argument('--output',type=Path,default=Path('results'))
    args = parser.parse_args()
    print(json.dumps(write_outputs(pd.read_csv(args.csv),args.output),indent=2))
