# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
from common.DBI import ArticleEN, ArticleOrig
from common.DBI import SQLiteManager
from common.DBI import AuthorCard


class CrawlerPipeline(object):
    def process_item(self, item, spider):
        url = item['url']
        logging.log(logging.DEBUG, 'CrawlerPipeline::process_item(): %s' % url)

        if 'morningstar.com' in url:
            if SQLiteManager.has_article('ArticleOrig', url):
                logging.log(logging.DEBUG, 'CrawlerPipeline::process_item(): article already exists')
                return
            else:
                authorId = AuthorCard.has_author(item)
                if authorId is None:
                    authorId = AuthorCard.add_author(item)
                    logging.log(logging.DEBUG, 'CrawlerPipeline::process_item(): store author in database')
                item['authorId'] = authorId
                logging.log(logging.DEBUG, 'CrawlerPipeline::process_item(): store article in database')
                SQLiteManager.add_article(ArticleOrig(item))
                return item
        elif 'fool.com' in url:
            if SQLiteManager.has_article('ArticleEN', url):
                logging.log(logging.DEBUG, 'CrawlerPipeline::process_item(): article already exists')
                return
            else:
                logging.log(logging.DEBUG, 'CrawlerPipeline::process_item(): store article in database')
                SQLiteManager.add_article(ArticleEN(item))
                return item
        else:
            logging.error('%s not supported!')
            return
