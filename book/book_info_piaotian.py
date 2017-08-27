#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
from datetime import datetime
from selenium import webdriver

s = requests.session()
s.keep_alive = False

#%%
# Load spreadsheet
xl = pd.ExcelFile('book_name_list.xls')
book_df = xl.parse('Sheet1')
book_list = book_df['book_name'].drop_duplicates().str.strip().tolist()


#%%
def book_search(driver, bookname):
    driver.find_element_by_css_selector(
        'div#content input').send_keys(bookname)
    driver.find_elements_by_tag_name('form')[1].submit()
    html_source = driver.page_source

    soup = BeautifulSoup(html_source, 'lxml')

    tbl = soup.select('div#content table tbody')
    if len(tbl) == 1:  # no search result, or multiple search result
        rows = tbl[0].select('tr')
        if len(rows) == 1:  # no search result
            print('No search resulf for %s' % bookname)
            return
        else:  # multiple match
            book_info = []
            for i in rows[1:]:
                searchname = i.select_one('td')
                if searchname.get_text(strip=True) == bookname:
                    b_url = searchname.find('a').get('href')
                    soup2 = BeautifulSoup(requests.get(b_url).text, 'lxml')
                    tbl_info = soup2.select_one(
                        'div#content table tr td').select('td')

                    book_dict = {}
                    book_dict['bookname'] = bookname
                    book_dict['time'] = datetime.utcnow(
                    ).strftime('%Y%m%d%H%M%S')
                    book_dict['url'] = b_url
                    book_dict['作者'] = tbl_info[3].get_text(
                        strip=True).split('：')[1]
                    for i in [10, 11, 12, 13]:  # range(2, 14)
                        cell = tbl_info[i].get_text(strip=True)
                        pair = cell.split('：')
                        book_dict[pair[0]] = pair[1]

                    book_info.append(book_dict)
            if book_info == []:
                print('No search resulf for %s' % bookname)
                return

    else:  # directly go to the bookpage
        tbl_info = tbl[1].select('td')
        if tbl_info[1].get_text(strip=True) != bookname:  # name not match
            print('No search resulf for %s' % bookname)
            return
        else:
            book_dict = {}
            book_dict['bookname'] = bookname
            book_dict['time'] = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            book_dict['url'] = driver.current_url
            book_dict['作者'] = tbl_info[3].get_text(strip=True).split('：')[1]
            for i in [10, 11, 12, 13]:
                cell = tbl_info[i].get_text(strip=True)
                pair = cell.split('：')
                book_dict[pair[0]] = pair[1]

            book_info = [book_dict]

    return book_info


#%%
def get_snapshots(url):
    '''
    search web archieve for history infos
    use Wayback CDX Server API:
        https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server
    @return: list of web archieve timestamps
    '''
    u = 'http://web.archive.org/cdx/search/cdx?url=%s&fl=timestamp,original&output=json' % url
    r = requests.get(u)
    timestamp_list = r.json()[1:]

    #  replace .com with .net
    url = url.replace('com', 'net')
    u = 'http://web.archive.org/cdx/search/cdx?url=%s&fl=timestamp,original&output=json' % url
    r = requests.get(u)
    timestamp_list += r.json()[1:]

    return timestamp_list


#%%
def snapshot_info(url, book_dict):
    soup = BeautifulSoup(requests.get(url).text, "lxml")
    try:
        # For http://web.archive.org/web/20161012164125/http://www.piaotian.com:80/bookinfo/1/1674.html,
        # Got an HTTP 301 response at crawl time and redirect to piaotian.net,
        # so we skip this one
        tbl_rows = soup.select('div#content table')[1].select('tr')[2:]
        tbl_info = []
        for row in tbl_rows:
            tbl_info += row.select('td')
    except:
        return

    book_dict['作者'] = tbl_info[1].get_text(strip=True).split('：')[1]
    for i in tbl_info[2:]:  # [6, 10, 11, 12, 13]:
        # for all three rows of table, scrape cells that contain numbers
        cell = i.get_text(strip=True)
        if any(str.isdigit(s) for s in cell):
            pair = cell.split('：')
            book_dict[pair[0]] = pair[1]

    return book_dict


#%%
def task2(book_list):
    driver = webdriver.Chrome()
    failure_list = []
    scrape_info = []
    for bookname in book_list:
        driver.get('http://www.piaotian.com/modules/article/search.php')
        time.sleep(10)
        info = book_search(driver, bookname)
        if info is None:  # no search result
            failure_list += [bookname]
        else:
            for i in info:
                for t in get_snapshots(i['url']):
                    url = 'http://web.archive.org/web/%s/%s' % (t[0], t[1])
                    book_dict = {}
                    book_dict['bookname'] = bookname
                    book_dict['time'] = t[0]
                    book_dict = snapshot_info(url, book_dict)
                    if book_dict is not None:
                        scrape_info.append(book_dict)
                scrape_info.append(i)

    driver.quit()

    return (failure_list, scrape_info)


#%%
output = task2(book_list)

with open("Task2_failure.txt", "w") as f:
    f.write("没有符合以下书名的查询结果：\n")
    f.write("\n".join(output[0]))

df = pd.DataFrame.from_records(output[1])
df.drop(['url', '全文长度', '最后更新'], axis=1, inplace=True)
df.rename(columns={'收 藏 数': '收藏数'}, inplace=True)
df.to_excel('task2.xlsx', index=False)
