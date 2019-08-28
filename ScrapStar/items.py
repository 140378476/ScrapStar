# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Item, Field


class ScrapstarItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class StarItem(Item):
    name = Field()
    url = Field()
    chineseName = Field()
    foreignName = Field()
    nationality = Field()
    nation = Field()
    constellation = Field()
    height = Field()
    weight = Field()
    birthday = Field()
    birthPlace = Field()
    profession = Field()
    university = Field()
    works = Field()
    imageLinks = Field()  # pairs of (imageUrl, title)
