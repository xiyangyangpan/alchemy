# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
from common.DBI import ArticleEN
from common.DBI import SQLiteManager


class CrawlerPipeline(object):
    def process_item(self, item, spider):
        logging.log(logging.DEBUG, 'CrawlerPipeline::process_item(): %s' % item['url'])

        if SQLiteManager.has_article('ArticleEN', item['url']):
            logging.log(logging.DEBUG, 'CrawlerPipeline::process_item(): article already exists')
            return
        else:
            logging.log(logging.DEBUG, 'CrawlerPipeline::process_item(): store article in database')
            SQLiteManager.add_article(ArticleEN(item))
            return item
