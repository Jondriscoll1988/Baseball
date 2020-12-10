import pandas as pd
import sqlite3
from baseball_scraper.playerid_lookup import get_lookup_table
import requests
from bs4 import BeautifulSoup
import numpy as np
import io

def dtconv(s):
    s = s.replace(u'\xa0', u' ')
    d = {'Jan': '01',
         'Feb': '02',
         'Mar': '03',
         'Apr': '04',
         'May': '05',
         'Jun': '06',
         'Jul': '07',
         'Aug': '08',
         'Sep': '09',
         'Oct': '10',
         'Nov': '11',
         'Dec': '12'}
    try:
        if '(' in s:
            s = s.split('(')[0]
        month = s.split(' ')[0]
        if int(s.split(' ')[1]) < 10:
            day = '0' + s.split(' ')[1]
        else:
            day = s.split(' ')[1]
        monthreplace = d[month]
        return '{}-{}'.format(monthreplace, day)
    except:
        pass

def sc(date_start, date_end):
    url = "https://baseballsavant.mlb.com/statcast_search/csv?all=true&hfPT=&hfAB=&hfBBT=&hfPR=&hfZ=&stadium=&hfBBL=" \
          "&hfNewZones=&hfGT=R%7CPO%7CS%7C=&hfSea=&hfSit=&player_type=pitcher&hfOuts=&opponent=&pitcher_throws=" \
          "&batter_stands=&hfSA=&game_date_gt={}&game_date_lt={}&team=&position=&hfRO=&home_road=&hfFlag=" \
          "&metric_1=&hfInn=&min_pitches=0&min_results=0&group_by=name&sort_col=pitches&player_event_sort=" \
          "h_launch_speed&sort_order=desc&min_abs=0&type=details&".format(date_start, date_end)
    s = requests.get(url).content
    df = pd.read_csv(io.StringIO(s.decode('utf-8')))
    return df

def get_lookup_table():
    url = "https://raw.githubusercontent.com/chadwickbureau/register/master/data/people.csv"
    s=requests.get(url).content
    table = pd.read_csv(io.StringIO(s.decode('utf-8')), dtype={'key_sr_nfl': object, 'key_sr_nba': object, 'key_sr_nhl': object})
    cols = ['name_last','name_first','key_mlbam', 'key_retro', 'key_bbref', 'key_fangraphs', 'mlb_played_first','mlb_played_last']
    table = table[cols]
    table['name_last'] = table['name_last'].str.lower()
    table['name_first'] = table['name_first'].str.lower()
    table[['key_mlbam', 'key_fangraphs','mlb_played_first','mlb_played_last']]\
        = table[['key_mlbam', 'key_fangraphs','mlb_played_first','mlb_played_last']].fillna(-1)
    table[['key_mlbam', 'key_fangraphs','mlb_played_first','mlb_played_last']]\
        = table[['key_mlbam', 'key_fangraphs','mlb_played_first','mlb_played_last']].astype(int)
    return table

def table(playerid, year):
    pitch_url = 'https://www.baseball-reference.com/players/gl.fcgi?id={}&t=p&year={}'.format(playerid, year)
    bat_url = 'https://www.baseball-reference.com/players/gl.fcgi?id={}&t=b&year={}'.format(playerid, year)
    ps, bs = requests.get(pitch_url).content, requests.get(bat_url).content
    psoup, bsoup = BeautifulSoup(ps, 'html.parser'), BeautifulSoup(bs, 'html.parser')
    ptable, btable = psoup.find_all('table'), bsoup.find_all('table')
    if len(ptable) == 1 and len(btable) == 0:
        return 'pitcher', dfFromTable(ptable[0], playerid, year)
    elif len(ptable) == 1 and len(btable) == 5:
        return 'both', dfFromTable(ptable[0], playerid, year), dfFromTable(btable[4], playerid, year)
    elif len(ptable) == 0 and len(btable) == 5:
        return 'batter', dfFromTable(btable[4], playerid, year)
    else:
        return None

def dfFromTable(table, playerid, year):
    if table is not None:
        headings = [th.get_text() for th in table.find("tr").find_all("th")]
        headings = headings[1:]
        df = pd.DataFrame(data=[], columns=headings)
        data = []
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        for row in rows:
            dlist = []
            for i in row.find_all('td'):
                dlist.append(i.text)
            if len(dlist) > 0:
                zipped = zip(headings, dlist)
                d = dict(zipped)
                data.append(d)
        df = df.append(data)
        df['Date'] = str(year) + '-' + df['Date'].apply(dtconv)
        df['Year'] = year
        df = df.rename(columns={'': 'home_or_away'})
        df['BREFID'] = playerid
        if 'DFS(DK)' not in df.columns:
            df['DFS(DK)'] = np.nan
        if 'DFS(FD)' not in df.columns:
            df['DFS(FD)'] = np.nan
        return df

def careerGameLogs(playerid, year_start, year_end):
    years = [i for i in range(year_start, year_end + 1)]
    big_pitch = []
    big_bat = []
    for year in years:
        log = table(playerid, year)
        if log is not None:
            if log[0] == 'pitcher':
                big_pitch.append(log[1])
            elif log[0] == 'both':
                big_pitch.append(log[1])
                big_bat.append(log[2])
            elif log[0] == 'batter':
                big_bat.append(log[1])
            else:
                print("Something's gone horribly wrong...")
    state = 0
    if len(big_pitch) > 0:
        pitchfinal = pd.concat(big_pitch)
        state += 2
    if len(big_bat) > 0:
        batfinal = pd.concat(big_bat)
        state += 3
    if state == 2:
        return 1, pitchfinal
    elif state == 3:
        return 2, batfinal
    elif state == 5:
        return 3, pitchfinal, batfinal
    else:
        print('something went horribly wrong at the very end!')

def gameLogDB(df, engine):
    file_name = 'error_log.txt'
    f = open(file_name, 'a+')
    ids = df.key_bbref.to_list()
    first_year = df.mlb_played_first.to_list()
    last_year = df.mlb_played_last.to_list()
    name_last = df.name_last.to_list()
    name_first = df.name_first.to_list()
    for i in zip(ids, first_year,last_year, name_last, name_first):
        print(f'adding {i[0]} to database...')
        try:
            logs = careerGameLogs(i[0],i[1],i[2])
            if logs[0] == 1:
                logs[1]['name_last'] = i[3]
                logs[1]['name_first'] = i[4]
                logs[1].to_sql('game_log_pitching', con = engine, if_exists = 'append', index = False)
            elif logs[0] == 2:
                logs[1]['name_last'] = i[3]
                logs[1]['name_first'] = i[4]
                logs[1].to_sql('game_log_batting', con = engine, if_exists = 'append', index = False)
            elif logs[0] == 3:
                logs[1]['name_last'] = i[3]
                logs[1]['name_first'] = i[4]
                logs[1].to_sql('game_log_pitching', con = engine, if_exists = 'append', index = False)
                logs[2]['name_last'] = i[3]
                logs[2]['name_first'] = i[4]
                logs[2].to_sql('game_log_batting', con = engine, if_exists = 'append', index = False)
            print(f'{i[4]} {i[3]} added to database')
        except:
            print(f'{i[4]} {i[3]} not added to database')
            f.write(f'{i[4]} {i[3]}')
    print('Done')
    f.close()

def statCastDB(start_dt, end_dt, dbpath):
    engine = sqlite3.connect(dbpath)
    data = allStatcast(start_dt = start_dt, end_dt = end_dt)
    data.to_sql('statcast', con = engine, if_exists = 'append', index = False)

if __name__ == '__main__':
    update = input('Choose either Statcast or Baseball Reference')
    if update == 'statcast'.lower():
        startdate = input('select a starting date in yyyy-mm-dd format')
        enddate = input('select an end date in yyyy-mm-dd format')
        engine = sqlite3.connect('/Users/jonathandriscoll/db/sqlite3/Baseball.db')
        statcastDB(startdate, enddate, dbpath)
        print('finished updating')
    elif update == 'baseball reference'.lower():
        y = input('select a most recent active year to update:')
        lookup = getLookup()
        active = lookup[lookup['mlb_played_last'] == int(y)].reset_index()
        active.loc[:,'mlb_played_last'] = active.loc[:,'mlb_played_last'].apply(int)
        active.loc[:,'mlb_played_first'] = active.loc[:,'mlb_played_first'].apply(int)
        engine = sqlite3.connect(dbpath)
        gameLogDB(active, engine)
    else:
        print('not a valid selection')