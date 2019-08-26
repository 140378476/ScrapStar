from scrapy import Selector, Request
from scrapy.spiders import CrawlSpider

from ScrapStar.items import StarItem
import re

ENABLE_DEBUG = False

MAX_IMAGE_COUNT = 5

DD_REGEX = re.compile('(<dd.*?>)|(</dd>)')
HREF_REGEX = re.compile('<a[^>]*>(.*?)</a>')


class StarsSpider(CrawlSpider):
    name = "StarsSpider"
    baseUrl = "https://baike.baidu.com"
    allowed_domains = ["baike.baidu.com"]
    start_urls = ['https://baike.baidu.com/item/%E5%90%B4%E4%BA%AC',
                  'https://baike.baidu.com/item/%E8%B0%A2%E6%A5%A0/2844135', ]
    url = 'https://baike.baidu.com/item/%E5%90%B4%E4%BA%AC'

    def extractMixture(self, block: Selector):
        text = block.extract()
        text = text.replace('\n', '')
        text = DD_REGEX.sub("", text)
        text = HREF_REGEX.sub("\\1", text)
        return text.strip()

    def getTextOrHrefText(self, block: Selector):
        #
        # return
        # print(block.extract())
        t = block.xpath("text()").extract_first()
        if t is not None:
            t = t.strip()
            if len(t) > 0:
                return t
        t = block.xpath("a/text()").extract_first()
        if t is not None:
            return t.strip()
        return None

    def getTitle(self, item: StarItem, sel: Selector):
        t = sel.xpath('//dd[@class="lemmaWgt-lemmaTitle-title"]/h1/text()').extract_first()
        item['name'] = t
        pass

    def findBasicInfo(self, item: StarItem, basicInfo: Selector):
        def getItem(key: str):
            sl = basicInfo.xpath(f'dt[@class="basicInfo-item name" and text()="{key}"]/following-sibling::dd[1]')
            if len(sl) != 0:
                return self.extractMixture(sl[0])
            return None

        def fillItem(variableName: str, key: str):
            t = getItem(key)
            if t is None:
                return
            item[variableName] = t

        fillItem('chineseName', "中文名")
        fillItem('foreignName', "外文名")
        fillItem('nationality', '国\xa0\xa0\xa0\xa0籍')
        fillItem('nation', '民\xa0\xa0\xa0\xa0族')
        fillItem('constellation', '星\xa0\xa0\xa0\xa0座')
        fillItem('height', '身\xa0\xa0\xa0\xa0高')
        fillItem('weight', '体\xa0\xa0\xa0\xa0重')
        fillItem('birthday', '出生日期')
        fillItem('birthPlace', '出生地')
        fillItem('university', '毕业院校')
        fillItem('profession', '职\xa0\xa0\xa0\xa0业')
        fillItem('works', '代表作品')
        pass

    def parse(self, response):
        item = StarItem()
        # print(response.url)
        sel = Selector(response)
        self.getTitle(item, sel)
        basicInfos = sel.xpath('//dl[@class="basicInfo-block basicInfo-left" or '
                               '@class="basicInfo-block basicInfo-right"]')
        for basicInfo in basicInfos:
            # print(basicInfo.xpath('dt[@class="basicInfo-item name"]/text()').extract())
            self.findBasicInfo(item, basicInfo)
        if 'name' in item:
            # name = item['name']
            if ENABLE_DEBUG:
                print(item)
            else:
                print(item['name'] + ": "+response.url)
        imageFolder = response.url.replace("/item/", "/pic/")
        yield Request(imageFolder, callback=lambda x: self.parseImageFolder(item, x))

        if ENABLE_DEBUG:
            return
        related = sel.xpath('//div[@id="slider_relations"]/ul')
        for r in related:
            links = r.xpath("li/a/@href").extract()
            for link in links:
                # print(link)
                nextUrl = StarsSpider.baseUrl + link
                yield Request(nextUrl, callback=self.parse)

    def extractImage(self, block: Selector):
        link = block.xpath("img/@src").extract_first()
        title = block.xpath("@title").extract_first()
        if link is None or title is None:
            return None
        return link, title

    def parseImageFolder(self, item, response):
        sel = Selector(response)
        blocks = sel.xpath('//div[@class="pic-list"]/a')
        imageLinks = []
        for block in blocks:
            link = self.extractImage(block)
            if link is not None:
                imageLinks.append(link)
                if len(imageLinks) >= MAX_IMAGE_COUNT:
                    break
            # imageLinks = map(lambda x: StarsSpider.baseUrl + x, imageLinks)
        if ENABLE_DEBUG:
            print(imageLinks[0])
        item['imageLinks'] = [imageLinks[0], ]

        yield item
