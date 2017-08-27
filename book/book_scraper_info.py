#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
这个项目主要目的是下载纵横中文网上小说的信息。 我提供一个excel 文件， 有3430本书的书名和作者笔名。

对每一本书 ， 程序将去zongheng网搜索这本书， 需要书名和作者都对应， 找到后对每本书搜集以下信息。
以http://book.zongheng.com/book/625089.html 为例：
1.	名字：墨历天下
2.	作者：萧夜月
3.	分类：奇幻玄幻
4.	总字数：9729字
5.	关键词：古典仙侠，穿越，天下3
6.	作品简介：本来要放弃游戏的墨韵，莫名其妙下居然来到了一个跟游戏背景相同的世界，面对陌生却又熟悉的环境，墨韵又该何去何从？
7.	进入目录　（http://book.zongheng.com/showchapter/625089.html）对每一章搜集以下信息：比如http://book.zongheng.com/chapter/625089/34913203.html 里
a.	标题：略显玻璃心的序章
b.	更新时间：2016-11-14 20:14:08
c.	字数：3371
d.	前两百字：夜，一男子坐在电脑旁不断地敲击着电脑似乎在打着什么，但是不一会却又把刚刚打出的东西全部删掉，之后双手按着太阳**躺在了椅子上。“唉，还是不知道该怎么说。”看着屏幕上那个身着一袭白色时装的男性角色游戏角色男子喃喃自语道，“本来说好要一起玩下去的，结果现在却是我先要离开……”说着男子一声轻叹拿起桌上的一听啤酒就灌倒了嘴里。只听“叮”的一声，游戏的聊天界面上闪出了一行紫色的密语，“墨韵，要去56吗？”正当男
（要是少于200字， 就都拿下来。 VＩＰ 章节系统显示前200字。 要去掉html代码）

** update **
搜索时只用作品名字搜，有时候同一个书名可能会对应几本书， 把这几本书都拿下来，文件名还是用书名_作者名。 （换句话说， 就是不用作者名， 希望能提高成功率）

"""

from bs4 import BeautifulSoup, SoupStrainer
import requests
import pandas as pd
import time
from requests.exceptions import ConnectionError
from itertools import repeat
from multiprocessing import Pool

s = requests.session()
s.keep_alive = False


#%%
def read_url(url):
    page = ''
    sec = 0
    while page == '':
        try:
            page = requests.get(url)
        except (ConnectionError, ConnectionResetError):
            sec += 3
            time.sleep(sec)
            continue

    return(page.text)


#%%
# 只搜索书名，如果存在相符合的书籍，返回作者和书籍网址
def get_author_dict(bookname):
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
# 根据书籍网址，搜集每章信息: 纵横中文网
def get_chapter_info(book_url):  # For zongheng.com
    chapterPage = book_url.replace('/book/', '/showchapter/')
    strainer = SoupStrainer('div', id='chapterListPanel')
    target2 = BeautifulSoup(read_url(chapterPage), "lxml", parse_only=strainer)
    chaps = target2.select('td[class=chapterBean]')

    chapters = pd.DataFrame()
    for chap in chaps:
        chapter_name = chap.attrs['chaptername']
        chapter_word = int(chap.attrs['wordnum'])

        chap_ref = chap.select_one('a[href]').get('href')
        strainer2 = SoupStrainer('div', class_='content')
        target3 = BeautifulSoup(
            read_url(chap_ref), "lxml", parse_only=strainer2)
        update_time = target3.select_one('span[datetime]').get_text(strip=True)
        chapter_content = target3.select_one(
            'div[id=chapterContent]').get_text(strip=True)
        chapter_content = chapter_content[:200]  # first 200 characters

        chapters = chapters.append({'7-a.chapter_name': chapter_name,
                                    '7-b.update_time': update_time,
                                    '7-c.chaper_word': chapter_word,
                                    '7-d.chapter_content': chapter_content}, ignore_index=True)
    return chapters


#%% 花语女生网
def get_chapter_info2(book_url):    # For huayu.baidu.com
    chapterPage = book_url.replace('/book/', '/showchapter/')
    strainer = SoupStrainer('div', class_='bookchaplist clearmar')
    target2 = BeautifulSoup(read_url(chapterPage), "lxml", parse_only=strainer)
    chaps = target2.select('li')

    chapters = pd.DataFrame()
    for chap in chaps:
        chapter_name = chap.select_one('a[href]')
        chapter_name = chapter_name.get_text(strip=True)
        chapter_word = int(chap.select_one(
            'span[class=chapcount]').get_text(strip=True))
        update_time = chap.select_one(
            'span[class=chaptime]').get_text(strip=True)

        # check if the chapter is VIP needed
        try:
            chap.select_one('em').get_text()
        except:
            # no vip
            chap_ref = 'http://huayu.baidu.com%s' % chap.select_one(
                'a[href]').get('href')
            strainer2 = SoupStrainer('div', class_='wrap book_reader')
            target3 = BeautifulSoup(
                read_url(chap_ref), "lxml", parse_only=strainer2)

            chapter_content = ''
            content_list = target3.select('p')  # list of content
            while len(chapter_content) <= 200:
                for i in content_list:
                    span = i.span
                    chapter_content += i.get_text().replace(span.get_text(), '')

            chapter_content = chapter_content[:200]
        else:
            # vip
            chapter_content = '非收费用户不能订阅VIP章节，请充值'

        chapters = chapters.append({'7-a.chapter_name': chapter_name,
                                    '7-b.update_time': update_time,
                                    '7-c.chaper_word': chapter_word,
                                    '7-d.chapter_content': chapter_content}, ignore_index=True)

    return chapters


#%% 抓取数据
def parl_scraper(bookname, output_path):
    print('===开始提取 %s===' % bookname)
    # 作者
    author_dict = get_author_dict(bookname)

    if author_dict is None:  # No search match
        return(bookname)
    else:
        for author, bookPage in author_dict.items():
            strainer = SoupStrainer('body')
            main_target = BeautifulSoup(
                read_url(bookPage), "lxml", parse_only=strainer)

            target = main_target.select_one('div[class=status\ fl]')
            if target is None:  # huayu.baidu.com
                target = main_target.select_one('div[class=marr10]')
                # 分类
                category = main_target.select_one(
                    'a[href*=category]').get_text(strip=True)
                # 字数
                total_words = target.select_one(
                    'div[class=booknumber]').get_text().split('\r\n')[1].split('：')[1]
                total_words = int(total_words)
                # 关键词
                keywords = target.select('a[href*=keyword]')
                key_words = ','.join([i.get_text(strip=True)
                                      for i in keywords])
                # 作品简介
                abstract = target.select_one(
                    'p[class=jj]').get_text(strip=True)
                # 每章信息
                chapters = get_chapter_info2(bookPage)

                output = pd.DataFrame({'1.author_name': author,
                                       '2.book_name': bookname,
                                       '3.category': category,
                                       '4.total_words': total_words,
                                       '5.key_words': key_words,
                                       '6.abstract': abstract}, index=[0])

                output = pd.concat([output, chapters], axis=1)

                output.to_excel('%s/%s_%s.xls' %
                                (output_path, bookname, author), 'Sheet1')
                print('提取成功：%s_%s' % (bookname, author))
            else:   # zongheng.com
                # 分类
                category = target.select_one(
                    'a[href*=store]').get_text(strip=True)
                # 字数
                total_words = target.select_one(
                    'span[title]').get_text(strip=True)
                total_words = int(total_words)
                # 关键词
                keywords = target.select_one('div[class=keyword]').select('a')
                key_words = ','.join([i.get_text(strip=True)
                                      for i in keywords])
                # 作品简介
                abstract = target.select_one(
                    'div[class=info_con]').get_text(strip=True)
                # 每章信息
                chapters = get_chapter_info(bookPage)

                output = pd.DataFrame({'1.author_name': author,
                                       '2.book_name': bookname,
                                       '3.category': category,
                                       '4.total_words': total_words,
                                       '5.key_words': key_words,
                                       '6.abstract': abstract}, index=[0])

                output = pd.concat([output, chapters], axis=1)

                output.to_excel('%s/%s_%s.xls' %
                                (output_path, bookname, author), 'Sheet1')
                print('提取成功：%s_%s' % (bookname, author))


#%%
if __name__ == '__main__':
    # get file path & output path from user input
    file = input('请输入目录文件路径: ')
    output_path = input('请输入输出路径: ')

    # Load spreadsheet
    xl = pd.ExcelFile(file)
    df = xl.parse('Sheet1')
    book_list = df['book_name'].drop_duplicates().str.strip().tolist()

    pool = Pool()
    failure_list = pool.starmap(
        parl_scraper, zip(book_list, repeat(output_path)))
    pool.close()
    pool.join()

    # keep track of books which have no matching search results
    with open("%s/失败目录.txt" % output_path, "w") as failure_file:
        failure_file.write("没有符合以下书名的查询结果：\n")
        failure_file.write("\n".join(filter(None, failure_list)))
