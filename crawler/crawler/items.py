# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy

class AlchemyItem(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    mainTitle = scrapy.Field()
    subTitle = scrapy.Field()
    content = scrapy.Field()
    articleTag = scrapy.Field()
    articleSection = scrapy.Field()
    authorName = scrapy.Field()
    publishDate = scrapy.Field()   
    publishTime = scrapy.Field()   

class FoolItem(AlchemyItem):
    def __init__(self):
        AlchemyItem.__init__(self)

    def __str__(self):
        return 'FoolItem: %s %s' % (self['url'], self['mainTitle'])

class ArticleItem(scrapy.Item):
    # define the fields for your item here like:
    # article full URL, index key
    url = scrapy.Field()

    # id to author item, forign index
    authorId = scrapy.Field()

    # article title
    mainTitle = scrapy.Field()
    # article content
    content = scrapy.Field()
    # article tag
    articleTag = scrapy.Field()
    # article time
    publishTime = scrapy.Field()   

class AuthorItem(scrapy.Item):
    # define the fields for your item here like:
    # id to author item, index key
    authorId = scrapy.Field()

    # article title
    mainTitle = scrapy.Field()
    # article content
    content = scrapy.Field()
    # article tag
    articleTag = scrapy.Field()
    # article time
    publishTime = scrapy.Field()   


