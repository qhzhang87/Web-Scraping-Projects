#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
我提供大约5200 本书名 （见附件），根据每本书名去zongheng.com搜到书， 下载所有读者的书评 （在评论区中），
对每个评论 （比如在http://book.zongheng.com/book/555035.html 的第一个评论）， 
搜集 发表时间 （2017-06-19 11:56）， 
    评论人的ID （左手边的思念），
    评论的标题 （【捧场】 左手边的思念给《大逆之门》捧场了 1000000 纵横币！且为本书投了4400…）， 
    评论的内容（捧场《大逆之门》 1000000 纵横币,投了4400张月票。这本书太棒了！这本书太棒了！犒劳一下，希望后续更加精彩！）， 
    点击（10）， 
    回复（0）， 
    赞（0）。 
不需要搜集回复。 

所有结果可保存在一个csv 文件中。 

同时保留一个书名对应URL的文件。 
"""

from bs4 import BeautifulSoup, SoupStrainer
import requests
import pandas as pd
import time
from requests.exceptions import ConnectionError
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

s = requests.session()
s.keep_alive = False


#%% Load book names
xl = pd.ExcelFile('book_list.xls')
book_df = xl.parse('Sheet1')
book_list = book_df['book_name'].drop_duplicates().str.strip().tolist()


#%%
def read_url(url):
    page = ''
    while page == '':
        try:
            page = requests.get(url)
        except (ConnectionError, ConnectionResetError):
            time.sleep(2)
            continue

    return(page.text)


#%%
def get_author_dict(bookname):
    '''
    搜索书名，如果存在相符合的书籍，返回作者和书籍网址
    '''
    url = "http://search.zongheng.com/search/bookName/%s/1.html" % bookname
    strainer = SoupStrainer('div', class_='search_res box')
    target = BeautifulSoup(read_url(url), "lxml", parse_only=strainer)
    targetElements = target.select('div[class=search_text]')

    if targetElements == []:   # 搜索结果为空
        print('提取失败: 没有符合"%s"的查询结果' % bookname)
        return
    else:
        author_dict = {}
        for elem in targetElements:
            title = elem.select_one('a[href*=/book/]')
            if title.get_text(strip=True) != bookname:
                continue

            search_author = elem.select_one(
                'a[href*=userInfo]').get_text(strip=True)
            author_dict[search_author] = title.get('href')

        if author_dict == {}:   # 搜索结果与书名不完全吻合
            print('提取失败: 没有符合"%s"的查询结果' % bookname)
            return
        else:
            return(author_dict)

        
#%%
def scrape_comment_page(driver):
    '''
    scrape comment sections for www.zongheng.com
    @return: list of dictionaries, in which dictionary keys are:
        发表时间, 评论人的ID, 评论的标题, 评论的内容, 点击, 回复, 赞
    '''
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, "lxml")
    titles = soup.select('h4.thread')
    commenters = soup.select('p.wz_fb')
    comments_text = soup.select('div.wz p[id*=fullThreadContent]')
    like = soup.select('span.support')
    others = soup.select('span.fl')
    comment_time = others[::3]
    click = others[1::3]
    reply = others[2::3]
                    
    comments = []
    for i in range(len(titles)):
        comments.append({
                'comment_time': comment_time[i].get_text(strip=True).replace('发表时间：', ''),
                'commenter_id': commenters[i].get_text(strip=True).replace('说：', ''),
                'comment_title': titles[i].get_text(strip=True),
                'comment_text': comments_text[i].get_text(strip=True).replace('[收起]', ''),
                'click': click[i].get_text(strip=True).replace('点击[', '').replace(']', ''),
                'reply': reply[i].get_text(strip=True).replace('回复[', '').replace(']', ''),
                'like': like[i].get_text(strip=True).replace('[', '').replace(']', '')
                })
    
    return comments


#%%
def scrape_comment_page2(driver):
    '''
    scrape comment sections for huayu.baidu.com
    @returns: list of dictionaries, in which dictionary keys are:
        发表时间, 评论人的ID, 评论的标题, 评论的内容, 点击, 回复, 支持, 反对  #多了‘反对’！
    '''
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, "lxml")
    titles = soup.select('div.head')
    comments_text = soup.select('div.wz_box')
    others = soup.select('div.support')
    
    comments = []
    for i in range(len(titles)):
        tmp = comments_text[i].select_one('a')
        if tmp is None:  # 评论已经显示完全，没有‘查看全文’
            full_comment = comments_text[i].get_text(strip=True)
        else:  # 评论部分省略，去到评论页面抓取
            comment_url = 'http://huayu.baidu.com' + tmp.get('href')
            csoup = BeautifulSoup(read_url(comment_url), 'lxml')
            full_comment = csoup.select_one('div.wz_box p').get_text(strip=True)
            
        commenter = others[i].find('span', recursive=False).get_text(strip=True).replace('发表人:', '')
        spans = others[i].select('div.fr span')
        comments.append({
                'comment_time': spans[0].get_text(strip=True).replace('日期: ', ''),
                'commenter_id': commenter,
                'comment_title': titles[i].get_text(strip=True),
                'comment_text': full_comment,
                'click': spans[2].get_text(strip=True).replace('点击数:', ''),
                'reply': spans[1].get_text(strip=True).replace('回复数:', ''),
                'like': spans[3].get_text(strip=True).replace('支持[','').replace(']', ''),
                'unlike': spans[4].get_text(strip=True).replace('反对[','').replace(']','')
                })
    
    return comments


#%%
def get_comments(driver, bookname, no_comment, error_list):
    author_dict = get_author_dict(bookname)
    if author_dict is None:  # No search match
        return
    else:
        output = []
        for author, book_url in author_dict.items():
            comment_url = book_url.replace('/book/', '/threadList/')
            page1 = comment_url + '#page_1'
            driver.get(page1)
            if driver.title == '访问页面不存在':
                error_list.append('访问页面不存在: %s %s' % (bookname, page1))
                continue
            if 'huayu.baidu.com' in driver.current_url:  # 花语女生网
                while True:
                    try: ##有可能系统错误
                        WebDriverWait(driver, 5).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.page_info')))
                        break
                    except:
                        driver.get(page1)
                        continue
                comments = scrape_comment_page2(driver)
                if comments == []: # No comment
                    print('No comment yet for book %s by author %s' % (bookname, author))
                    # return(['No comment', author])
                    # !!! we cannot use this, since other books from other authors inside the for loop
                    #     may do have comments, and we shouldn't break the loop
                    no_comment.append('书名：%s 作者：%s' % (bookname, author))
                    continue
                # Here we cannot use while loop
                # since at the last page, when we click '下一页', we will go to page 1
                page_number = driver.find_element_by_css_selector('div.page').text
                last_page = int(page_number.split('>')[0].split(' ')[-1])
                for i in range(1, last_page):  # i is current page
                    try:
                        driver.find_element_by_css_selector('input.page_text').clear()
                        time.sleep(.5)
                        driver.find_element_by_css_selector('input.page_text').send_keys(i+1)
                        time.sleep(.5)
                        WebDriverWait(driver, 20).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input.page_button'))).click()
                        time.sleep(.5)
                        WebDriverWait(driver, 20).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.page_info')))
                        comments += scrape_comment_page2(driver)
                    except:
                        print('Error for book %s: %s' % (bookname, page1))
                        error_list.append('Error for book %s: %s' % (bookname, page1))
                        comments = []
                        break
            else:  # 纵横小说网
                while True:
                    try: ##有可能系统错误
                        WebDriverWait(driver, 5).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.pagenumber')))
                        break
                    except:
                        driver.get(page1)
                        continue
                comments = scrape_comment_page(driver)
                if comments == []: # No comment
                    print('No comment yet for book %s by author %s' % (bookname, author))
                    # return(['No comment', author])
                    # !!! we cannot use this, since other books from other authors inside the for loop
                    #     may do have comments, and we shouldn't break the loop
                    no_comment.append('书名：%s 作者：%s' % (bookname, author))
                    continue
                while True:
                    try:
                        next_button = driver.find_element_by_css_selector('a.scrollpage.next')
                    except NoSuchElementException:
                        break
                    next_button.click()
                    time.sleep(.1)
                    while True:
                        try: ##有可能系统错误
                            WebDriverWait(driver, 5).until(
                                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.pagenumber')))
                            break
                        except:
                            driver.get(page1)
                            continue
                    comments += scrape_comment_page(driver)
            
            for c in comments:
                c.update({"bookname":bookname, 'author': author, 'book_url': book_url})
            output += comments
            
        return (output, no_comment, error_list)
    

#%%
chrome_options = webdriver.ChromeOptions()
# disable image and flash
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs",prefs)
chrome_options.add_argument("--disable-internal-flash")
chrome_options.add_argument("--disable-plugins-discovery")


#%%
failure_list = []
no_comment = []
output = []
error_list = []

driver = webdriver.Chrome(chrome_options=chrome_options)

for bookname in book_list[1073:]:
    comment_info = get_comments(driver, bookname, no_comment, error_list)
    if comment_info is None:  # No search match
        failure_list.append(bookname)
    else:
        comments = comment_info[0]
        no_comment = comment_info[1]
        error_list = comment_info[2]
        output += comments
        
driver.quit()


#%%
with open("failure.txt", "w") as f:
    f.write("没有符合以下书名的查询结果：\n")
    f.write("\n".join(failure_list))
    
with open("no_comment.txt", "w") as f:
    f.write("以下书籍暂时还没有评论: \n")
    f.write("\n".join(no_comment))
    
df = pd.DataFrame(output)
#df.drop_duplicates(inplace=True)
df2 = df.drop_duplicates()
#df['comment_text'] = df['comment_text'].replace(['&hellip;', '&middot;', '\[cat_\d*\]', '\[cat_\d*'], '', regex=True)

## df.comment_text contains urls
#writer = pd.ExcelWriter('comments.xlsx', 
#                        engine='xlsxwriter', 
#                        options={'strings_to_urls': False})
#df2.to_excel(writer, index=False)
df2.to_csv('comments.csv', index=False)

