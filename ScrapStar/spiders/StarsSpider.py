from scrapy import Selector, Request
from scrapy.spiders import CrawlSpider

from ScrapStar.items import StarItem

ENABLE_DEBUG = False


class StarsSpider(CrawlSpider):
    name = "StarsSpider"
    allowed_domains = ["baike.baidu.com"]
    start_urls = ['https://baike.baidu.com/item/%E5%90%B4%E4%BA%AC',
                  'https://baike.baidu.com/item/%E8%B0%A2%E6%A5%A0/2844135',]
    url = 'https://baike.baidu.com/item/%E5%90%B4%E4%BA%AC'

    def getTextOrHrefText(self, block: Selector):
        #
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
                return self.getTextOrHrefText(sl[0])
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
        pass

    def parse(self, response):
        item = StarItem()
        sel = Selector(response)
        self.getTitle(item, sel)
        basicInfos = sel.xpath('//dl[@class="basicInfo-block basicInfo-left" or '
                               '@class="basicInfo-block basicInfo-right"]')
        for basicInfo in basicInfos:
            # print(basicInfo.xpath('dt[@class="basicInfo-item name"]/text()').extract())
            self.findBasicInfo(item, basicInfo)
        if 'name' in item:
            name = item['name']
            if ENABLE_DEBUG:
                print(item)
            else:
                print(item['name'])
            yield item

        if ENABLE_DEBUG:
            return
        related = sel.xpath('//div[@id="slider_relations"]/ul')
        for r in related:
            links = r.xpath("li/a/@href").extract()
            for link in links:
                # print(link)
                nextUrl = "https://baike.baidu.com" + link
                yield Request(nextUrl, callback=self.parse)
