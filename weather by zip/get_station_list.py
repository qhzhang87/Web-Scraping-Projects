#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import pickle


def get_page(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    return soup


# def get_stations(url):  # url: page of a zip code
#     soup = get_page(url)
#     pagelinks = soup.select('td a')
#     station_list = []
#     for j in pagelinks:
#         pageurl = 'https://www.wunderground.com/' + j.get('href')
#         page_soup = get_page(pageurl)
#         try:
#             history_url = page_soup.select_one('a#city-nav-history').get(
#                 'href')
#             station_id = history_url.split('/')[3]
#             station_list.append(station_id)
#         except:
#             print(url, pageurl)
#             next
#     return station_list

url = 'https://www.wunderground.com/weather-by-zip-code.asp?MR=1'
soup = get_page(url)
zipcodes = soup.select_one('section.inner-content ul').select('a')

station_dict = {}
for i in zipcodes:
    code = i.get_text()
    print('=======Starting scraping zip code {}======='.format(code))
    station_list = []    
    url = 'https://www.wunderground.com' + i.get('href')
    soup = get_page(url)
    if 'Weather by U.S. Zip Code' in soup.text:
        pagelinks = soup.select('td a')
        
        for j in pagelinks:
            if 'tablesaw-cell-persist' in str(j.parent):
                pageurl = 'https://www.wunderground.com' + j.get('href')
                page_soup = get_page(pageurl)
                try:
                    history_url = page_soup.select_one('a#city-nav-history').get(
                        'href')
                    station_id = history_url.split('/')[3]
                    station_list.append(station_id)
                except:
                    print('{}: {}'.format(code, pageurl))
                    next
    else:  # for zip code 399, https://www.wunderground.com/cgi-bin/findweather/getForecast?query=pz:399&zip=1&MR=1
        try:
            history_url = soup.select_one('a#city-nav-history').get(
                'href')
            station_id = history_url.split('/')[3]
            station_list.append(station_id)
        except:
            print('{}: {}'.format(code, pageurl))
            next

    station_dict[code] = station_list


pickle.dump(station_dict, open("stations.p", "wb"))  # save it into a file named save.p
