# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re
from scrapy import Request
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
import pymysql

from ScrapStar import settings

HEIGHT_WEIGHT_REGEX = re.compile(r'\d{1,3}(\.\d+)?')


def getNumber(item, tag):
    if tag not in item:
        return
    try:
        item[tag] = HEIGHT_WEIGHT_REGEX.search(item[tag]).group()
        if re.compile(r'[^\u4e00-\u9fa5]+').search(item[tag]).group() == "磅":
            item[tag] = item[tag] * 0.4535924
    except:
        return


def getBirth(item):
    try:
        year = re.search(r'(\d){4}', item["birthday"]).group()
        month = re.findall(r'\d+', item["birthday"])[1]
        day = re.findall(r'\d+', item["birthday"])[2]
        # if year == '' or month == "" or day == '':
        #     raise DropItem()
        dot = "."
        item["birthday"] = dot.join([year, month, day])
    except:
        return


def getNation(item):
    char = "族"
    if 'nation' not in item or item['nation'] is None:
        return
    if item["nation"].find(char) != -1:
        find = item["nation"].find(char)
        item["nation"] = item["nation"][:find]


def deleteh(item, tags):
    pass
    # for tag in tags:
    #     if '<' in item[tag]:
    #         item[tag] = re.sub(r'<.*>', "", item[tag])
    #     if '(' in item[tag]:
    #         item[tag] = re.sub(r'(.*)', "", item[tag])


def changeName(item):
    try:
        if item["nationality"] == "中华人民共和国":
            item["nationality"] = "中国"
    except:
        return


class FormatDataPipeline(object):
    def process_item(self, item, spider):
        # deleteh(item, ['chineseName', 'nationality', 'foreignName', 'nation', 'constellation',
        #                'height', 'weight', 'birthday', 'birthPlace', 'profession',
        #                'university'])  # delete html tags in data
        changeName(item)
        getNumber(item, 'height')
        getNumber(item, 'weight')
        getNation(item)
        getBirth(item)
        if settings.ENABLE_DEBUG:
            print(item)
        else:
            print(item['name'] + ": " + item['url'])
        return item


PREFIX_LENGTH = len('https://baike.baidu.com/item/')


class SaveImagePipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        # 下载图片，如果传过来的是集合需要循环下载
        # meta里面的数据是从spider获取，然后通过meta传递给下面方法：file_path
        itemId = item['url'][PREFIX_LENGTH:]
        for (link, title) in item['imageLinks']:
            yield Request(url=link, meta={'itemId': itemId, 'name': item['name'], 'imageTitle': title})

    def item_completed(self, results, item, info):
        # 是一个元组，第一个元素是布尔值表示是否成功
        # image_paths = [x['path'] for ok, x in results if ok]
        # if not image_paths:
        #     raise DropItem("Item contains no images")
        # item['image_paths'] = image_paths
        # return item
        # if not results[0][0]:
        #     raise DropItem('下载失败')
        # return item
        return item

    # 重命名，若不重写这函数，图片名为哈希，就是一串乱七八糟的名字
    def file_path(self, request, response=None, info=None):
        # 接收上面meta传递过来的图片名称
        itemId = request.meta['itemId']
        name = request.meta['name']
        # 提取url前面名称作为图片名
        typeSuffix = request.url.split('.')[-1]
        image_name = request.meta['imageTitle'] + "." + typeSuffix
        # 清洗Windows系统的文件夹非法字符，避免无法创建目录
        folder_strip = re.sub(r'[?\\*|"<>:/]', '-', str(itemId + "_" + name))
        image_name = re.sub(r'[?\\*|"<>:/]', '', str(image_name))
        # 分文件夹存储的关键：{0}对应着name；{1}对应着image_guid
        filename = u'{0}/{1}'.format(folder_strip, image_name)
        return filename


def makeStr(s):
    if s is None:
        return ""
    else:
        return str(s)
    pass


CREATE_TABLE_SQL = """
CREATE DATABASE stars;
use stars;
CREATE TABLE IF NOT EXISTS stars (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR (255),
  url VARCHAR (255),
  chineseName VARCHAR (255),
  foreignName VARCHAR (255),
  nationality VARCHAR (255),
  nation VARCHAR (255),
  constellation VARCHAR (255),
  height VARCHAR (255),
  weight VARCHAR (255),
  birthday VARCHAR (255),
  birthPlace VARCHAR (255),
  profession VARCHAR (255),
  university VARCHAR (255),
  works VARCHAR (500),
  imageLinks VARCHAR(2000)
);
"""


class SaveToDatabasePipeline(object):

    def prepareDatabase(self):
        try:
            self.cursor.execute(CREATE_TABLE_SQL)
        except:
            pass
        pass

    def __init__(self) -> None:
        self.handle = pymysql.connect(
            host=settings.DATABASE_HOST,
            user=settings.DATABASE_USER_NAME,
            passwd=settings.DATABASE_PASSWORD,
            charset="utf8",
            use_unicode=True
        )
        self.cursor = self.handle.cursor()
        self.prepareDatabase()

    def saveItemToDatabase(self, item):
        sql = """INSERT INTO stars(name,url,chineseName,foreignName,
                      nationality,nation,constellation,height,weight,birthday,
                      birthPlace,profession,university,works,imageLinks) 
                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        try:
            self.cursor.execute(sql,
                                (makeStr(item['name']), makeStr(item['url']),
                                 makeStr(item['chineseName']), makeStr(item['foreignName']),
                                 makeStr(item['nationality']), makeStr(item['nation']), makeStr(item['constellation']),
                                 makeStr(item['height']), makeStr(item['weight']), makeStr(item['birthday']),
                                 makeStr(item['birthPlace']), makeStr(item['profession']), makeStr(item['university']),
                                 makeStr(item['works']),
                                 makeStr(item['imageLinks'])))
            self.cursor.connection.commit()
        except BaseException as e:
            if settings.ENABLE_DEBUG:
                raise e
            print("Error: ", e)
            self.handle.rollback()

    def process_item(self, item, spider):
        cursor = self.handle.cursor()
        cursor.execute("USE stars;")
        result = cursor.execute(f"SELECT id FROM stars WHERE url = '{item['url']}';")
        if result != 0:
            print("Ignore: " + item['name'])
            return item
        self.saveItemToDatabase(item)
        return item

    def close_spider(self, spider):
        if self.handle is not None:
            self.handle.close()
