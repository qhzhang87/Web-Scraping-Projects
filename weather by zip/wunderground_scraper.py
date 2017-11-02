# coding: utf-8
'''
scrape history temperature data of a station from www.wunderground.com/history
'''

from datetime import timedelta
import requests
from bs4 import BeautifulSoup
import re


# def scrape_station(station, start_date, end_date):
#     '''
#     This function scrapes the weather data web pages from wunderground.com
#     for the station you provide it.

#     You can look up your city's weather station by performing a search for
#     it on wunderground.com then clicking on the "History" section.
#     The 4-letter name of the station will appear on that page.

#     Args:
#         start_date (str): datetime object, e.g.datetime(year=2014, month=7, day=1)
#         end_date (str): datetime object.

#     '''
#     temp_dict = {}
#     # Use .format(station, YYYY, M, D)
#     lookup_URL = 'http://www.wunderground.com/history/airport/{}/{}/{}/{}/DailyHistory.html'

#     while start_date != end_date:
#         formatted_lookup_URL = lookup_URL.format(
#             station, start_date.year, start_date.month, start_date.day)
#         page = requests.get(formatted_lookup_URL)
#         soup = BeautifulSoup(page.text, 'lxml')
#         try:
#             meanrow = soup.find(text='Mean Temperature').parent.parent.parent
#             try:
#                 avgtemp = int(meanrow.select_one('span.wx-value').get_text())
#             except:
#                 maxrow = soup.find(text='Max Temperature').parent.parent.parent
#                 maxtemp = int(maxrow.select_one('span.wx-value').get_text())
#                 minrow = soup.find(text='Min Temperature').parent.parent.parent
#                 mintemp = int(minrow.select_one('span.wx-value').get_text())
#                 avgtemp = (maxtemp + mintemp)/2
#         except:
#             avgtemp = None
#         temp_dict[start_date] = avgtemp
#         start_date += timedelta(days=1)
#     return temp_dict


def scrape_station(station, year):
    '''
    This function scrapes the weather data web pages from wunderground.com
    for the station you provide it.

    You can look up your city's weather station by performing a search for
    it on wunderground.com then clicking on the "History" section.
    The 4-letter name of the station will appear on that page.

    Args:
        start_date (str): datetime object, e.g.datetime(year=2014, month=7, day=1)
        end_date (str): datetime object.

    '''
    temp_dict = {}
    # Use .format(station, YYYY, M, D)
    url = 'https://www.wunderground.com/history/airport/{}/{}/1/1/CustomHistory.html?dayend=31&monthend=12&yearend={}'.format(station, year,year)

    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    
    table = soup.find_all('table')[1]
    rows = table.findAll('tr')
    for tr in rows[1:]:
        try:
            firstcol = tr.find('td').a
            if firstcol is not None:
                cols = tr.findAll('td')
                date = re.match('.*/(\d+/\d+/\d+)/.*', cols[0].a.get('href')).group(1)
                try:
                    avgtemp = int(cols[2].get_text(strip=True))
                except ValueError:
                    try:
                        maxtemp = int(cols[1].get_text(strip=True))
                        mintemp = int(cols[3].get_text(strip=True))
                        avgtemp = (maxtemp + mintemp) / 2
                    except ValueError:
                        avgtemp = None
                temp_dict[date] = avgtemp
        except:
            pass
        
    return temp_dict
            
                
