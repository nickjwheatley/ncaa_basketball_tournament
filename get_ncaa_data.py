#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import requests
from os.path import exists


# In[2]:


def get_games_won(final_round):
    '''Return number of games won given a team\'s final round. Returns "TBD" if in current tournament as the final rounds have not yet been posted'''
    games_won = {
        'R68':0,'R64':0,'R32':1,'Sweet Sixteen':2,'Elite Eight':3,'Final Four':4,'Finals':5,'CHAMPS':6,'✅':'TBD','❌':'TBD'
    }
    return games_won[final_round]


# In[3]:


def get_ncaa_tournament_data(years = [2017,2018,2019,2021],force_download=False):
    '''Load NCAA tournament data from barttorvik.com and return a cleaned version
    
    Parameters
    ----------
    years : list object [optional]
        Pass the season years desired in %Y format (21-22 season would be 2022)
    force_download : boolean [optional]
        Determines whether pull from website and cache data as "ncaa_tournament_teams.csv"
        
    returns pandas dataframe'''
    if exists('ncaa_tournament_teams.csv') & ~force_download:
        try:
            df = pd.read_csv('ncaa_tournament_teams.csv')
        except:
            raise OSError('No file "ncaa_tournament_teams.csv" found in working directory')
    else:
        df = pd.DataFrame()
        for year in years:
            #iterate through passed years
            res = requests.get('https://barttorvik.com/trank.php?year={}&sort=&top=0&conlimit=All&venue=All&type=All#'.format(year))
            html = pd.read_html(res.content)
            this_df = pd.DataFrame(html[0])
            
            this_df.columns = this_df.columns.droplevel(level=0) #remove top layer of multi-index
            
            #drop header rows and keep desired coluns
            this_df = this_df.loc[this_df['Rk'] != 'Rk'][['Team','Conf','AdjOE','AdjDE']].rename(
                columns={'AdjOE':'Offensive Efficiency','AdjDE':'Defensive Efficiency'})
            
            #convert efficiency columns to numeric values
            for col in ['Offensive Efficiency','Defensive Efficiency']:
                this_df[col] = pd.to_numeric(this_df[col])
                
            #calculate total efficiency metric (Offensive / Defensive)
            this_df['Total Efficiency'] = this_df['Offensive Efficiency'] / this_df['Defensive Efficiency']

            this_df.insert(1,'Seed',this_df['Team'].str.extract('([0-9]+) seed')) #Regex extract Seed from team name
            this_df.insert(2,'Final Round',this_df['Team'].str.extract(', (.*)')) #Regex extract Final Round from team name
            this_df['Team'] = this_df['Team'].str.extract('(.*) [1-9]') #Regex extract team name from comprehensive team name
            this_df.insert(0,'Year',year) #add year column
            this_df = this_df.dropna()
            this_df.insert(4,'Games Won',list(map(get_games_won,this_df['Final Round']))) #map total games won to each team
            df = df.append(this_df).reset_index(drop=True) #append to comprehensive dataframe
        df.set_index('Year').to_csv('ncaa_tournament_teams.csv') #cache data
    return df

