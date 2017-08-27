#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import re
import requests
import time
from requests.exceptions import ConnectionError
from selenium import webdriver

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
def scrape_page(path):
    '''
    extract book information from downloaded web page file
    @path: pathlib.PosixPath of page file
    @returns: lists that store the information: category, book_title, book_id
    '''
    category = []
    book_title = []
    book_id = []

    with path.open() as f:
        page = f.read()
    soup = BeautifulSoup(page, 'lxml')

    info_list = []
    # 首页焦点图
    flashbox = soup.select('div.flash h2 a')
    category.extend(['首页焦点图'] * len(flashbox))
    info_list.extend(flashbox)
    # 小封推
    block = soup.select('div.i_block h2 a')
    category.extend(['小封推'] * len(block))
    info_list.extend(block)
    # 品书试读榜
    pssd = soup.select('div.pssd li a')
    category.extend(['品书试读榜'] * len(pssd))
    info_list.extend(pssd)
    # 重磅 会员 女生 全本
    bookbox = soup.select('div.bookbox h2 a')
    category.extend(['重磅推荐'] * 2)
    category.extend(['会员推荐'] * 2)
    category.extend(['女生推荐'] * 2)
    category.extend(['全本推荐'] * 2)
    info_list.extend(bookbox)
    # 潜力大作榜
    ql = soup.select('div.ql_jp li a')
    category.extend(['潜力大作榜'] * len(ql))
    info_list.extend(ql)
    # 纵横风云榜
    fy = soup.select('div.fy h2 a')
    category.extend(['纵横风云榜'] * len(fy))
    info_list.extend(fy)

    target = soup.select('div.list.box')
    # 纵横新书榜
    newbook = target[0].select('li a')
    category.extend(['纵横新书榜'] * len(newbook))
    info_list.extend(newbook)
    # 月票榜
    month_piao = target[1].select('li a')
    category.extend(['月票榜'] * len(month_piao))
    info_list.extend(month_piao)
    # 月度冠军点击榜
    month_top = target[2].select('h2 a')
    category.extend(['月度冠军点击榜'] * len(month_top))
    info_list.extend(month_top)
    # 百万字精品排行榜
    million = target[3].select('li a')
    category.extend(['百万字精品排行榜'] * len(million))
    info_list.extend(million)
    # VIP作品榜
    vip = target[4].select('li a')
    category.extend(['VIP作品榜'] * len(vip))
    info_list.extend(vip)
    # 红票（周）
    red = target[5].select("div[tabid='2'] li a")
    category.extend(['红票（周）'] * len(red))
    info_list.extend(red)
    # 黑票（周）
    black = target[5].select("div[tabid='5'] li a")
    category.extend(['黑票（周）'] * len(black))
    info_list.extend(black)
    # 用户点击榜（周）
    user_click = target[6].select("div[tabid='2'] li a")
    category.extend(['用户点击榜（周）'] * len(user_click))
    info_list.extend(user_click)
    # 动漫评价榜
    comic_list = target[7].select('li a')
    category.extend(['动漫评价榜'] * len(comic_list))
    info_list.extend(comic_list)
    # 动漫点击榜(周)
    comic_click = target[8].select("div[tabid='2'] li a")
    category.extend(['动漫点击榜（周）'] * len(comic_click))
    info_list.extend(comic_click)

    # 会员主打
    huiyuan = soup.select('div.tui h3 a')
    category.extend(['会员主打'] * len(huiyuan))
    info_list.extend(huiyuan)
    # 精品推荐 图推
    boutique_box = soup.select('div.boutique.box div.bookbox h3 a')
    category.extend(['精品推荐 图推'] * len(boutique_box))
    info_list.extend(boutique_box)
    # 精品推荐
    boutique_other = soup.select('div.boutique div.wz_link ul li a')
    boutique_other = boutique_other[::2]
    category.extend(['精品推荐'] * len(boutique_other))
    info_list.extend(boutique_other)
    # 纵横女生推荐
    girl = soup.select('div[class=recommend] a[title]')
    girl = girl[::2]
    category.extend(['纵横女生推荐'] * len(girl))
    info_list.extend(girl)
    # 闪亮女主笔
    girl2 = soup.select('div.recommend.quan a[title]')
    girl2 = girl2[::3]
    category.extend(['闪亮女主笔'] * len(girl2))
    info_list.extend(girl2)
    # 女主笔红人榜
    girl_red = soup.select('div.mmtj_r div[class=list] li a')
    category.extend(['女主笔红人榜'] * len(girl_red))
    info_list.extend(girl_red)
    # 女主笔点击榜
    girl_click = soup.select('div.woman_click.list div[tabid="2"] ul li a')
    category.extend(['女主笔点击榜'] * len(girl_click))
    info_list.extend(girl_click)
    # 动漫精选
    comic_box = soup.select('div.comic.box h4 a[href*=series]')
    category.extend(['动漫精选'] * len(comic_box))
    info_list.extend(comic_box)

    for i in info_list:
        # 首页焦点图可能不是书, then we cannot get the book id
        # e.g. 20130522181827.htm
        i_id = re.findall('\d+.html', i.get('href'))
        if i_id == []:  # i is not a book
            i_title = None
            i_id = None
        else:  # i is indeed a book
            i_id = i_id[0].replace('.html', '')
            # book title may have been left out, such as '绝世高手都市横...'
            # or i.get_text(strip=True) may result '血神笑：'
            # thus if <a> has title attribute, we will extract book title from
            # <a> title attribute
            if i.get('title') is None:
                i_title = i.get_text(strip=True)
            else:
                i_title = i.get('title').strip()
                i_title = re.sub('((都市言情|古代言情|幻想时空|耽美同人|科幻游戏|历史军事|都市娱乐|武侠仙侠|奇幻玄幻): |：.*)',
                                 '', i_title)

        book_title.extend([i_title])
        book_id.extend([i_id])

    # 动漫精选
    # the header is not comic book name, so go to the comic page to extract
    # the book name
    c_url = soup.select_one('div.comic.box h3 a[href*=series]').get('href')
    try:
        c_title = BeautifulSoup(read_url(c_url), "lxml").select_one(
            'h1').get_text(strip=True)
        category.extend(['动漫精选'])
        book_title.extend([c_title])
        book_id.extend(re.findall('\d+', c_url))
    except:
        print('Error in comic title: %s %s' % (path, c_url))

    return (category, book_title, book_id)


#%%
def scrape_page_2(path, driver):
    '''
    extract book information from downloaded web page file
    @path: pathlib.PosixPath of page file
    @driver: created selenium webdriver
    @returns: lists that store the information: category, book_title, book_id
    '''
    category = []
    book_title = []
    book_id = []

    with path.open() as f:
        page = f.read()
    soup = BeautifulSoup(page, 'lxml')

    info_list = []

    # 纵横热书
    redbook = soup.select('div.kind_recom div[tabid="1"] h3 a')
    category += ['纵横热书'] * len(redbook)
    info_list += redbook
    # 女生精品
    girl_bouti = soup.select("div.kind_recom div[tabid='2'] h3 a")
    category += ['女生精品'] * len(girl_bouti)
    info_list += girl_bouti
    # 出版热推
    publish = soup.select('div.kind_recom div[tabid="3"] h3 a')
    category += ['出版热推'] * len(publish)
    info_list += publish
    # 纵横风云榜
    fy = soup.select("div.fy div[tabid='1'] h3 a")
    category += ['纵横风云榜'] * len(fy)
    info_list += fy
    # 上周风云
    fy_before = soup.select("div.fy div[tabid='2'] h3 a")
    category += ['上周风云'] * len(fy_before)
    info_list += fy_before

    # 品书试读榜
    pssd = soup.select("div#clk_rco_pinshu [tabid='1'] ul li a[title]")
    category += ['品书试读榜'] * len(pssd)
    info_list += pssd
    # 上周品书
    ps_bf = soup.select("div#clk_rco_pinshu div[tabid='2'] li a[title]")
    category += ['上周品书'] * len(ps_bf)
    info_list += ps_bf

    # 小说新书榜
    xinshu = soup.select('div#clk_rco_xinshu ul li a[title]')
    category += ['小说新书榜'] * len(xinshu)
    info_list += xinshu
    # 潜力大作榜
    qianli = soup.select('div#clk_rco_qianli ul li a[title]')
    category += ['潜力大作榜'] * len(qianli)
    info_list += qianli
    # 精品小说推荐图推
    bouti_pic = soup.select('div.boutique h3 a')
    category += ['精品小说推荐图推'] * len(bouti_pic)
    info_list += bouti_pic
    # 精品小说推荐文字推
    bouti_wz = soup.select('div.boutique div.wz_link ul li span a')
    category += ['精品小说推荐文字推'] * len(bouti_wz)
    info_list += bouti_wz
    # 重磅小说推荐
    zhongbang = soup.select('div#clk_rco_zhongbang h3 a.book')
    category += ['重磅小说推荐'] * len(zhongbang)
    info_list += zhongbang

    # 小说月票榜
    # <li> not included in the page source code, thus use selenium webdriver
    driver.get(path.resolve().as_uri())
    html_source = driver.page_source
    soup2 = BeautifulSoup(html_source, 'lxml')
    yuepiao = soup2.select('div#clk_rco_yuepiaorank div.book_list ul li a')
    category += ['小说月票榜'] * len(yuepiao)
    info_list += yuepiao

    # 用户点击榜（周）
    user_click = soup.select("div#clk_rco_clickrank div[tabid='2'] ul li a")
    category += ['用户点击榜（周）'] * len(user_click)
    info_list += user_click
    # 红票榜（周）
    hongpiao = soup.select("div#clk_rco_hongheirank div[tabid='2'] li a")
    category += ['红票榜（周）'] * len(hongpiao)
    info_list += hongpiao
    # 黑票榜（周）
    heipiao = soup.select("div#clk_rco_hongheirank div[tabid='5'] li a")
    category += ['黑票榜（周）'] * len(heipiao)
    info_list += heipiao
    # 言情小说推荐图推
    yq_pic = soup.select('div#clk_rco_femalyangqing h3 a')
    category += ['言情小说推荐图推'] * len(yq_pic)
    info_list += yq_pic
    # 言情小说推荐文字推
    yq_wz = soup.select('div#clk_rco_femalyangqing div.wz_link li span a')
    category += ['言情小说推荐文字推'] * len(yq_wz)
    info_list += yq_wz
    # 言情小说／女主笔 红人榜
    yq_hot = soup.select('div#clk_rco_femalhot ul li a[title]')
    category += ['言情小说红人榜'] * len(yq_hot)
    info_list += yq_hot
    # 言情小说／女主笔 点击榜（周）
    yq_click = soup.select("div#clk_rco_femalclick div[tabid='2'] li a")
    category += ['言情小说点击榜（周）'] * len(yq_click)
    info_list += yq_click
    # 动漫评价榜
    comic_pj = soup.select('div#clk_rco_comicpingjia li a')
    category += ['动漫评价榜'] * len(comic_pj)
    info_list += comic_pj
    # 动漫精品推荐
    comicbest = soup.select('div#clk_rco_comicbest div.wz a[title]')
    category += ['动漫精品推荐'] * len(comicbest)
    info_list += comicbest

    # 动漫点击榜（周）
    comic_click = soup.select("div#clk_rco_comicclick div[tabid='2'] li a")
    category += ['动漫点击榜（周）'] * len(comic_click)
    info_list += comic_click
    # 新书订阅榜
    newbook = soup.select('div#clk_rco_newbookorder li a[title]')
    category += ['新书订阅榜'] * len(newbook)
    info_list += newbook
    # 热门作品更新榜
    hot_update = soup.select(
        "div#clk_rco_hotupdaterank div[tabid='2'] li a[title]")
    category += ['热门作品更新榜'] * len(hot_update)
    info_list += hot_update
    # 今日畅销榜
    today_pop = soup.select('div#clk_rco_popularrank li a[title]')
    category += ['今日畅销榜'] * len(today_pop)
    info_list += today_pop

    # 从开始2014年7月开始增加：无线风向标，无线潜力新书榜
    three_side = soup.select('div.three_side')
    if len(three_side) == 12:  # check if include new charts
        wuxian = three_side[11].select('div.book_list')
        # 无线风向标
        fxb = wuxian[0].select('a[title]')
        category += ['无线风向标'] * len(fxb)
        info_list += fxb
        # 无线潜力新书榜
        qlxs = wuxian[1].select('a[title]')
        category += ['无线潜力新书榜'] * len(qlxs)
        info_list += qlxs

    for i in info_list:
        i_title = i.get('title').strip().replace('[new]', '')
        i_title = re.sub('((都市言情|古代言情|幻想时空|耽美同人): |：.*)', '', i_title)
        book_title.extend([i_title])

        # href possible formats:
        # 1: http://book.zongheng.com/book/65189.html
        # 2: http://book.zongheng.com/book/348955.html?rec=1
        # 3:
        # http://www.zongheng.com/redirect.do?url=aHR0cDovL21lcnJ5Ym9vay50YW9iYW8uY29tL3NlYXJjaC5odG0%2Fc2VhcmNoPXkma2V5d29yZD0lQzIlRkUlQ0QlRjUmbG93UHJpY2U9JmhpZ2hQcmljZT0%3D
        i_id = re.findall('\d+.html', i.get('href'))
        if i_id == []:  # format3
            i_id = None
        else:
            i_id = i_id[0].replace('.html', '')
        book_id.extend([i_id])

    return (category, book_title, book_id)


#%%
def scrape_page_3(path):
    category = []
    book_title = []
    book_id = []

    with path.open() as f:
        page = f.read()
    soup = BeautifulSoup(page, 'lxml')

    # 大封推
    dft = soup.select('div#index_tpic_big a')
    for i in dft:
        i_id = re.findall('book/\d+.html', i.get('href'))
        if i_id != []:  # make sure that i is a book
            i_id = re.sub('book/|.html', '', i_id[0])
            i_title = i.find('img')['alt'].strip().split('：')[0]
            category += ['大封推']
            book_id += [i_id]
            book_title += [i_title]

    # 首页推荐
    shouye = soup.select("div[alog-group*='newsWord'] a")
    for i in shouye:
        i_id = re.findall('book/\d+.html', i.get('href'))
        if i_id != []:  # make sure that i is a book
            i_id = re.sub('book/|.html', '', i_id[0])
            try:
                url = i.get('href')
                newsoup = BeautifulSoup(read_url(url), 'lxml')
                i_title = newsoup.select_one('h1 a').get_text(strip=True)
            except:
                i_title = i.get('title').strip()
            category += ['首页推荐']
            book_title += [i_title]
            book_id += [i_id]
    # charts
    charts = soup.select('div.toplist')
    for c in charts:
        chart_name = c.select('h2')
        if len(chart_name) == 2:
            info = c.select('li a[title]')
            for i in range(len(info) // 2):
                category += [chart_name[0].get_text(strip=True)]
                book_title += [info[i].get('title').strip()]
                book_id += re.findall('\d+', info[i].get('href'))
            for i in range(len(info) // 2, len(info)):
                category += [chart_name[1].get_text(strip=True)]
                book_title += [info[i].get('title').strip()]
                book_id += re.findall('\d+', info[i].get('href'))
        else:
            tabs = c.select('div[class*=tab]')
            if tabs == []:  # no tab
                info = c.select('li a[title]')
                for i in info:
                    category += [chart_name[0].get_text(strip=True)]
                    book_title += [i.get('title').strip()]
                    book_id += re.findall('\d+', i.get('href'))
            else:  # 取周榜
                info = tabs[3].select('li a[title]')
                for i in info:
                    category += [chart_name[0].get_text(strip=True) + '（周）']
                    book_title += [i.get('title').strip()]
                    book_id += re.findall('\d+', i.get('href'))
    # 品书试读 小编推荐 免费精品 经典全本
    mindbox = soup.select('div.mind_showbox')
    pssd = mindbox[0].select('h3 a')
    for i in pssd:
        category += ['品书试读']
        book_title += [i.get('title').strip()]
        book_id += re.findall('\d+', i.get('href'))
    xbtj = mindbox[1].select('h3 a')
    for i in xbtj:
        category += ['小编推荐']
        book_title += [i.get('title').strip()]
        book_id += re.findall('\d+', i.get('href'))
    mfjp = mindbox[2].select('h3 a')
    for i in mfjp:
        category += ['免费精品']
        book_title += [i.get('title').strip()]
        book_id += re.findall('\d+', i.get('href'))
    jdqb = mindbox[3].select('h3 a')
    for i in jdqb:
        category += ['经典全本']
        book_title += [i.get('title').strip()]
        book_id += re.findall('\d+', i.get('href'))
    # 分类热门推荐
    catbox = soup.select('div.cat_book')
    for box in catbox:
        cat = box.select_one('h2.catname').get_text()
        tu = box.select_one('h3 a')
        category += [cat]
        book_title += [tu.get('title').strip()]
        book_id += re.findall('\d+', tu.get('href'))
        wz = box.select('ul.wz a')
        for i in wz:
            category += [cat]
            try:
                url = i.get('href')
                newsoup = BeautifulSoup(read_url(url), 'lxml')
                i_title = newsoup.select_one('h1 a').get_text(strip=True)
            except:
                i_title = i.get('title').strip()
            book_title += [i_title]
            book_id += re.findall('\d+', i.get('href'))
    # 言情动漫图推
    pic = soup.select('div.index_l_piclnk')
    category += ['言情小说大图推']
    if len(pic) == 2:  # it's possible that there is no 动漫推荐版块
        category += ['动漫精品大图推']
    for i in pic:
        book_title += [i('p')[0].get_text(strip=True)]
        book_id += re.findall('\d+', i.select_one('a').get('href'))
    # 言情小说推荐
    girl = soup.select_one('div#girl_show').select('a[title]')
    girl = girl[::2]
    category += ['言情小说推荐小图推'] * 2
    category += ['言情小说推荐文字推'] * (len(girl) - 2)
    for i in girl:
        i_title = i.get('title').strip()
        i_title = re.sub('(都市言情|古代言情|幻想时空|耽美同人): ', '', i_title)
        book_title += [i_title]
        book_id += re.findall('\d+', i.get('href'))
    # 动漫精品推荐
    comic = soup.select('div#comic_show ul.wz a[class]')
    for i in comic:
        category += ['动漫精品推荐文字推']
        i_title = i.get('title').strip()
        i_title = re.findall('\[.*\]', i_title)[0]
        i_title = i_title.replace('[', '').replace(']', '')
        book_title += [i_title]
        book_id += re.findall('\d+', i.get('href'))
    comic_pic = soup.select('div#comic_show div.bookbox a')
    comic_pic = comic_pic[1::2]
    for i in comic_pic:
        category += ['动漫精品推荐小图推']
        i_title = i.get('title').strip()
        book_title += [i_title]
        book_id += re.findall('\d+', i.get('href'))

    return (category, book_title, book_id)


#%%
def task1(dir_path):
    # create empty lists to store book infos
    page_id = []
    category = []
    book_title = []
    book_id = []
    # For books: http://book.zongheng.com/book/book_id.html
    # For comics: http://comic.zongheng.com/series/book_id.html

    driver = webdriver.Chrome()
    pathlist = Path(dir_path).iterdir()
    for path in pathlist:
        if path.suffix == '.htm':
            if bool(re.match('(2013|201401|201402)', path.stem)):
                info = scrape_page(path)
            elif path.stem >= '20141120104110':
                info = scrape_page_3(path)
            else:
                info = scrape_page_2(path, driver)

            page_id.extend([path.stem] * len(info[0]))
            category.extend(info[0])
            book_title.extend(info[1])
            book_id.extend(info[2])

    driver.quit()
    df = pd.DataFrame(list(map(list, zip(page_id, category, book_title, book_id))),
                      columns=['ID', 'Category', 'BookTitle', 'BookId'])
    # drop rows with book_title is None
    df = df.dropna(subset='BookTitle')
    df['BookTitle'] = df['BookTitle'].replace(
        ['(奇幻修真|都市生活|虚拟网游|异世大陆|东方玄幻|竞技同人|悬疑灵异|宦海仕途|都市异能|穿梭时空|异术超能|都市重生|古典仙侠|奇幻玄幻|历史军事|都市娱乐): ',
         '(【更新】|【推荐】|【新作】|【周更】|【更】|【新】|\[new\]|\[荐\])'], '', regex=True)
    ## comic may have this format: [过早去！] 超萌武汉地区的早点拟人化 [猎神] 戴上眼镜去狩猎吧少年
    idxs = (df['Category'] == '动漫精品推荐') & (df['BookTitle'].str.contains('\['))
    df.ix[idxs, 'BookTitle'] = df.ix[idxs, 'BookTitle'].str.split(']').str[0].str.replace('[', '')

    return df


#%%
df = task1('snapshots')
df.to_excel('task1.xlsx', index=False)
