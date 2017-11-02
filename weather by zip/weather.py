#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a data table that shows for every zip 3 in the US, the average temperature each week of the year, averaging over the past 3 years

Table is structured as:

1 record for each zip 3  (roughly 1000 records total)
1 column to record the average temperature for each of 52 weeks, averaged over the last 3 years (52 columns per record)

Temperature values for each record should be in fahrenheit.  Whole numbers are sufficient.
"""

import pandas as pd
import wikitablescrape
from wunderground_scraper import scrape_station
import pickle
from datetime import datetime, timedelta

# get a dictionary mapping zip 3 to its address
wikitablescrape.scrape(
    url="https://en.wikipedia.org/wiki/List_of_ZIP_code_prefixes",
    output_name="zip")

table = pd.read_csv('./zip/zip.csv', header=None)
i = 1
while i < 10:
    tmp = pd.read_csv('./zip/zip_{}.csv'.format(i), header=None)
    table = table.append(tmp)
    i += 1

table = table.replace(['†', '\*'], '', regex=True)

zip_list = []
for j in table.columns:
    zip_list += table[j].tolist()

zip_dict = {}
no_in_use = []
outside_us = []
for i in zip_list:
    item = i.split(' ', maxsplit=1)
    if item[1] == 'Not in use':
        no_in_use.append(item[0])
    elif item[1] == 'Destinations outside U.S.':
        outside_us.append(item[0])
    else:
        zip_dict[item[0]] = item[1]

# Get wunderground station list for each zip code
station_dict = pickle.load(open("stations.p", "rb"))

# Get temperature history data of stations
all_stns = []
for i in station_dict:
    for j in station_dict[i]:
        if j not in all_stns:
            all_stns.append(j)

stns_temp = {}
i = 0
for stn in all_stns:
    i += 1
    print('=======Start scraping {}. {}======'.format(i, stn))
    try:
        tmp2014 = scrape_station(stn, 2014)
        tmp2015 = scrape_station(stn, 2015)
        tmp2016 = scrape_station(stn, 2016)
        tmp = {'2014': tmp2014, '2015': tmp2015, '2016': tmp2016}
        stns_temp[stn] = tmp
    except:
        print('Failure for {}'.format(stn))

pickle.dump(stns_temp, open("stns_temp.p", "wb"))

# Compute weekly avg temperature of stations
stns_avg = {}
for stn in stns_temp.keys():
    temp = stns_temp[stn]
    year_dict = {}
    for year in temp.keys():
#        if int(year) % 4 == 0:
#            yearlen = 366
#        else:
#            yearlen = 365
#        if temp[year] == yearlen:
#            in_df = pd.DataFrame(list(temp[year].values()), columns=['Temp'])
#        else:
#            df = pd.DataFrame(
#                list(temp[year].items()), columns=['Date', 'Temp'])
#            df['Date'] = pd.to_datetime(df['Date'])
#
#            start_date = datetime(int(year), 1, 1)
#            end_date = datetime(int(year), 12, 31)
#            dates_year = [
#                start_date + timedelta(n)
#                for n in range(int((end_date - start_date).days) + 1)
#            ]
#            full_year = pd.DataFrame(dates_year, columns=['Date'])
#            in_df = pd.merge(full_year, df, how='left', on='Date')
        df = pd.DataFrame(
            list(temp[year].items()), columns=['Date', 'Temp'])
        df['Date'] = pd.to_datetime(df['Date'])

        start_date = datetime(int(year), 1, 1)
        end_date = datetime(int(year), 12, 31)
        dates_year = [
            start_date + timedelta(n)
            for n in range(int((end_date - start_date).days) + 1)
        ]
        full_year = pd.DataFrame(dates_year, columns=['Date'])
        in_df = pd.merge(full_year, df, how='left', on='Date')

        out_df = pd.DataFrame(index=[0])
        for i in range(51):
            week = i + 1
            colname = 'Week {}'.format(week)
            out_df[colname] = in_df.iloc[i * 7:week * 7, ].mean()['Temp']
        out_df['Week 52'] = in_df.iloc[357:, ].mean()['Temp']
        year_dict[year] = out_df
    stns_avg[stn] = year_dict

# Compute avg temperature of week
for year in ['2014', '2015', '2016']:
    all_temp = {}
    for zipcode in zip_dict.keys():
        dfs = pd.DataFrame()
        unique_stns = set(station_dict[zipcode])
        for stn in unique_stns:
            try:
                dfs = dfs.append(stns_avg[stn][year], ignore_index=True)
            except KeyError:
                pass
        all_temp[zipcode] = round(dfs.mean(), 2)
    final_df = pd.DataFrame.from_dict(all_temp, orient='index')
    writer = pd.ExcelWriter(
        'zip_temperature_%s.xlsx' % year, engine='xlsxwriter')
    final_df.to_excel(writer, index_label='zip3')
    writer.save()

#%%
year2014 = pd.read_excel('./zip_temperature/zip_temperature_2014.xlsx', index_col='zip3',dtype={'zip3':str})
year2015 = pd.read_excel('./zip_temperature/zip_temperature_2015.xlsx', index_col='zip3',dtype={'zip3':str})   
year2016 = pd.read_excel('./zip_temperature/zip_temperature_2016.xlsx', index_col='zip3',dtype={'zip3':str})   

avg_three_year = round((year2014 + year2015 + year2016)/3, 2)

writer = pd.ExcelWriter(
    './avg_three_years.xlsx', engine='xlsxwriter')
avg_three_year.to_excel(writer, index_label='zip3')


## The above method has problem:
## Since there might be missing values, calculate the avg of stations first may lead to error
## Use method below:

##############################################################
#%% Standard Deviation
# Compute daily temperature of each zip
daily_temp = {}
for year in ['2014', '2015', '2016']:
    all_temp = {}
    for zipcode in zip_dict.keys():
        dfs = pd.DataFrame()
        unique_stns = set(station_dict[zipcode])
        for stn in unique_stns:
            try:
                dfs = dfs.append(stns_temp[stn][year], ignore_index=True)
            except KeyError:
                pass
        all_temp[zipcode] = dfs.mean()
    daily_temp[year] = all_temp
    
pickle.dump(daily_temp, open("daily_temp.p", "wb"))

# Compute std of each week 
std_all = {}
for year in ['2014', '2015', '2016']:
    std_temp = pd.DataFrame()
    for zipcode in zip_dict.keys():
        dailytemp_current = daily_temp[year][zipcode]
        # it is possible that dialytemp_current is empty 
        # since we don't have temperature data for that zipcode, e.g. 090
        if len(dailytemp_current) == 0:
            continue

        df = pd.DataFrame(
            list(dailytemp_current.items()), columns=['Date', 'Temp'])
        df['Date'] = pd.to_datetime(df['Date'])

        start_date = datetime(int(year), 1, 1)
        end_date = datetime(int(year), 12, 31)
        dates_year = [
            start_date + timedelta(n)
            for n in range(int((end_date - start_date).days) + 1)
        ]
        full_year = pd.DataFrame(dates_year, columns=['Date'])
        in_df = pd.merge(full_year, df, how='left', on='Date')

        out_df = pd.DataFrame(index=[zipcode])
        for i in range(51):
            week = i + 1
            colname = 'Week {}'.format(week)
            out_df[colname] = in_df.iloc[i * 7:week * 7, ].std()['Temp']
        out_df['Week 52'] = in_df.iloc[357:, ].std()['Temp']
        std_temp = std_temp.append(out_df)
    std_all[year] = std_temp.sort_index()
    writer = pd.ExcelWriter(
            'std_temperature_%s.xlsx' % year, engine = 'xlsxwriter')
    std_all[year].to_excel(writer, index_label = 'zip3')
    writer.save() 


#%%
# Compute avg of each week (new way)
avg_all = {}
for year in ['2014', '2015', '2016']:
    mean_temp = pd.DataFrame()
    for zipcode in all_temp.keys():
        dailytemp_current = daily_temp[year][zipcode]
        # it is possible that dialytemp_current is empty 
        # since we don't have temperature data for that zipcode, e.g. 090
        if len(dailytemp_current) == 0:
            continue

        df = pd.DataFrame(
            list(dailytemp_current.items()), columns=['Date', 'Temp'])
        df['Date'] = pd.to_datetime(df['Date'])

        start_date = datetime(int(year), 1, 1)
        end_date = datetime(int(year), 12, 31)
        dates_year = [
            start_date + timedelta(n)
            for n in range(int((end_date - start_date).days) + 1)
        ]
        full_year = pd.DataFrame(dates_year, columns=['Date'])
        in_df = pd.merge(full_year, df, how='left', on='Date')

        out_df = pd.DataFrame(index=[zipcode])
        for i in range(51):
            week = i + 1
            colname = 'Week {}'.format(week)
            out_df[colname] = in_df.iloc[i * 7:week * 7, ].mean()['Temp']
        out_df['Week 52'] = in_df.iloc[357:, ].mean()['Temp']
        mean_temp = mean_temp.append(out_df)
    avg_all[year] = mean_temp.sort_index()
    writer = pd.ExcelWriter(
            'avg_temperature_%s.xlsx' % year, engine = 'xlsxwriter')
    avg_all[year].to_excel(writer, index_label = 'zip3')
    writer.save()  
    
pickle.dump(std_all, open("std_all.p", "wb"))
pickle.dump(avg_all, open("avg_all.p", "wb"))

#%%
#year2014 = pd.read_excel('./zip_temperature/zip_temperature_2014.xlsx', index_col='zip3',dtype={'zip3':str})
#year2015 = pd.read_excel('./zip_temperature/zip_temperature_2015.xlsx', index_col='zip3',dtype={'zip3':str})   
#year2016 = pd.read_excel('./zip_temperature/zip_temperature_2016.xlsx', index_col='zip3',dtype={'zip3':str})   

df_concat = pd.concat((avg_all['2014'], avg_all['2015'], avg_all['2016']))
by_row_index = df_concat.groupby(df_concat.index)
std_three_year = by_row_index.std()
avg_three_year = by_row_index.mean()

writer = pd.ExcelWriter(
    './std_three_years.xlsx', engine='xlsxwriter')
std_three_year.to_excel(writer, index_label='zip3')

writer = pd.ExcelWriter(
    './avg_three_years.xlsx', engine='xlsxwriter')
avg_three_year.to_excel(writer, index_label='zip3')

