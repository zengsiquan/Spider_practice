#coding:utf-8

# 爬去豆瓣电影排行前250的电影
import requests
import threading
import time
from lxml import etree
from Queue import Queue
from fake_useragent import UserAgent


class Spider(object):
    # 初始化对象
    def __init__(self):
        self.url = 'https://movie.douban.com/top250?start='
        self.headers = {"User-Agent" : UserAgent().random}
        # self.proxy = {"http" : "http://maozhaojun:ntkn0npx@114.67.224.167:16819"}
        self.counter = 1
        self.data_queue = Queue() # 

    # 发送url请求
    def send_request(self,url):
        print 'it is the %d' %self.counter
        try:
            response = requests.get(url,headers = self.headers)
            print self.headers
            time.sleep(1)
            self.parse_page(response)
        except Exception as e:
            print e


    # 解析页面
    def parse_page(self,response):

        html_obj = etree.HTML(response.content)

        node_list = html_obj.xpath("//div[@class='info']")
        print node_list
        for node in node_list:
            title = node.xpath(".//div[@class='hd']/a/span[1]/text()")[0]
            print title
            score = node.xpath(".//span[@class='rating_num']/text()")[0]
            try:
                info = node.xpath(".//span[@class='inq']/text()")[0]
            except Exception as e:
                info = 'None'
            self.data_queue.put(title + "\t" + score + "\t" + info)

    # 程序执行中心
    def main(self):

        pages = [ i for i in range(0,250,25)]
        thread_list = []
        for page in pages:
            self.counter += 1
            url = self.url + str(page)
            print url
            thread = threading.Thread(target=self.send_request,args=[url])
            thread.start()
            thread_list.append(thread)

        for thread in thread_list:
            thread.join()
        #
        while not self.data_queue.empty():
            print(self.data_queue.get())
        print self.counter

if __name__ == '__main__':
    spider = Spider()
    start_time = time.time()
    spider.main()
    print 'info: 程序执行时间为 %f' %(time.time()-start_time)


#  爬取斗鱼主播信息并存储之mongodb中
from selenium import webdriver
import unittest
import pymongo
import time
from bs4 import BeautifulSoup

class DouyuSpider(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true', '--ssl-protocol=TLSv1'])
        self.count = 0
        self.client = pymongo.MongoClient(host="127.0.0.1", port=27017)
        self.db = self.client["douyu"]
        self.collection = self.db['directory']

    def testDouyu(self):
        self.driver.get("https://www.douyu.com/directory/all")
        while True:
            html = self.driver.page_source
            soup = BeautifulSoup(html,'lxml')
            node = soup.find('div',{'id':'live-list-content'})

            # 房间标题
            room_list = node.find_all("h3", {"class": "ellipsis"})
            # 分类
            sort_list = node.find_all("span", {"class": "tag ellipsis"})
            # 主播名
            name_list = node.find_all("span", {"class": "dy-name ellipsis fl"})
            # 观众人数
            people_list = node.find_all("span", {"class": "dy-num fr"})
            # 相当于进行俩次拆包后再进行遍历
            # room,sort,name,people节点标签
            for room,sort,name,people in zip(room_list,sort_list,name_list,people_list):
                item = {}

                item["_id"] = str(self.count)
                item['room'] = room.get_text().strip()
                item['name'] = name.get_text().strip()
                item['sort'] = sort.get_text().strip()
                item['people'] = people.get_text().strip()
                print item["_id"] + "\t" + item["room"] + "\t" + item["sort"] + "\t" + item["name"] + "\t" + item["people"]
                self.count += 1
                self.collection.insert(item)


            if soup.find('a',{'class':'shark-pager-disable-next'}):
                break
            else:
                self.driver.find_element_by_class_name("shark-pager-next").click()
                time.sleep(0.5)
                print "[INFO] 正在获取下一页"

    # 方法名固定
    def tearDown(self):
        self.driver.quit()
        print "[INFO] 当前主播人数%d" % self.count

if __name__=="__main__":
    unittest.main()
