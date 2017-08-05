# -*- coding:utf-8 -*-
#
#
#   用于爬取每日TOP50
#
#

import requests
import sys
import datetime
import time
import os
import re
import random
from bs4 import BeautifulSoup

non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd) 

###########################################爬虫部分########################################

res = requests.Session()

class PixivSpider():

    #初始化部分
    def __init__(self, username, password):
        self.base_url = 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
        self.login_url = 'https://accounts.pixiv.net/api/login?lang=zh'
        self.main_url = 'http://www.pixiv.net'
        #daily top 50的地址
        self.target_url = 'https://www.pixiv.net/ranking.php?mode=daily&content=illust'
        #referer需要使用
        self.original_url = "http://www.pixiv.net/member_illust.php?mode=medium&illust_id="
        self.headers = {
            'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) ''AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        }
        self.pixiv_id = username
        self.password = password
        self.post_key = []
        self.return_to = 'http://www.pixiv.net'
        self.load_path = 'E:\DailyTop50'

    #登陆部分
    def login(self):
        #下面获取postkey
        post_key_html = res.get(self.base_url, headers = self.headers).text
        post_key_soup = BeautifulSoup(post_key_html, 'html.parser')
        self.post_key = post_key_soup.find('input')['value']
        data = {
            'pixiv_id': self.pixiv_id,
            'password': self.password,
            'return_to': self.return_to,
            'post_key': self.post_key
        }
        res.post(self.login_url, data=data, headers=self.headers)

    #从top50页面获取图片详情页面
    def getInfoUrl(self):
        html = res.get(self.target_url, headers=self.headers).text
        soup = BeautifulSoup(html, 'html.parser')
        rank = 1
        #下面的列表保存TOP50页面的图片详细页面链接
        url_list=[]
        section = soup.find_all('div', class_='ranking-image-item')
        while(rank <= 50):
            url = 'http://www.pixiv.net'+ section[rank - 1].find('a').get('href')
            url_list.append(url)
            rank = rank + 1
        return url_list

    #图片详情界面获取详细信息
    def getInfo(self):
        rank = 1
        url_list = self.getInfoUrl()
        info_list = []

        while(rank <= 50):
            html = res.get(url_list[rank - 1], headers=self.headers).text
            soup = BeautifulSoup(html, 'html.parser')
            #获取详情
            author_id = str(str(soup.find('title').text).split('/')[1])[1:-1]
            author_url = self.main_url + soup.find('a', class_='user-link').get('href')
            img_title = str(soup.find('title').text).split('/')[0]
            img_caption = soup.find_all('p', class_='caption')[-1].text
            img_rank = rank
            try:
                img_url = soup.find('img',class_='original-image').get('data-src')
            except:
                result_pic_more = re.search(re.compile('</li><li>.*?\s(.*?)P</li>', re.S),
                                            str(soup.find_all("ul", class_="meta")))
                img_url = "有多张图片，总共有 " + result_pic_more.group(1) + " 张"
            Info = {
                'author_id': author_id,
                'author_url': author_url,
                'img_title': img_title.translate(non_bmp_map),
                'img_caption': img_caption.translate(non_bmp_map),
                'img_url': img_url,
                'img_rank': img_rank
                }
            info_list.append(Info)
            rank = rank + 1
        return info_list

    def getYesterday(self):
        today = datetime.date.today()
        one_day = datetime.timedelta(days=1)
        yesterday = today - one_day
        return yesterday

    #下载图片部分
    def downloadImg(self):
        headers = self.headers
        counts = 0
        subdir = str(self.getYesterday())
        #当前目录下创建img文件夹
        if(os.path.exists('img')):
            os.chdir('img')
            if(os.path.exists(subdir)):
                os.chdir(subdir)
            else:
                path = str(os.mkdir(subdir))
                os.chdir(path)
        else:
            os.mkdir('img')
            os.chdir('img')
            if (os.path.exists(subdir)):
                os.chdir(subdir)
            else:
                path = str(os.mkdir(subdir))
                os.chdir(path)
        url_list = self.getInfoUrl()
        info_list = self.getInfo()
        referer_list = []
        for urls in url_list:
            referer_list.append(self.original_url+url_list[counts].split('=')[-1])
            counts = counts + 1
        counts = 0
        while(counts < 50):
            headers['Referer'] = referer_list[counts]
            try:
                if('Error' == info_list[counts]['img_url']):
                    counts = counts + 1
                    continue
                html = requests.get(info_list[counts]['img_url'], headers=headers)
                img = html.content
            except:
                print('获取图片失败！'+str(counts+1))
                counts = counts + 1
                continue
            title = str(counts + 1)
            print('正在保存排名#'+str(counts+1)+'的图片')
            with open(title + '.jpg', 'ab') as f:
                f.write(img)
            print(str(counts+1)+'图片保存完成')
            counts = counts + 1
    def work(self):
        self.login()
        self.downloadImg()



        #测试部分
username = input('输入你的Pixiv帐号：')
password = input('输入你的Pixiv密码：')
pixiv = PixivSpider(username, password)
pixiv.work()
