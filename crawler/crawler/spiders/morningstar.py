# -*- coding: utf-8 -*-
import logging
import json
import calendar
import unicodedata
from datetime import datetime, timedelta
import dateutil.parser as dp
from collections import OrderedDict
import sys
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request
from crawler.items import FoolItem
from crawler.items import AlchemyItem
from crawler.items import ArticleItem
from common.DBI import SQLiteManager
import ConfigParser

cp = ConfigParser.SafeConfigParser()
cp.read('alchemy.conf')
allowed_domain = cp.get('crawler2', 'allowed_domain')
start_url = cp.get('crawler2', 'start_url')


class MorningstarSpider(CrawlSpider):
    name = 'morningstar'
    allowed_domains = [allowed_domain]
    cls_db_mgr = None
    fetched_cnt = 0
    crawl_days = 1
    max_fetched_article_per_day = 20

    def start_requests(self):
        start_urls = [
            start_url + '/articles/archive/articles-archive.html'
        ]
        for url in start_urls:
            startRequest = Request(url=url, callback=self.parse_start_url)
            #startRequest.meta['dont_cache'] = True
            yield startRequest

    def parse_start_url(self, response):
        logging.log(logging.INFO, 'parse_start_url(): %s' % response.url)

        cnt = 0
        tr_list = response.css('#archive-table > tbody > tr')
        for tr in tr_list:
            td_list = tr.css('td')
            td_title = td_list[0]
            td_collection = td_list[1]
            td_author = td_list[2]
            td_date = td_list[3]

            article_title = td_title.css('a::text').extract_first()
            article_link = td_title.css('a::attr("href")').extract_first()
            logging.log(logging.DEBUG, 'title: %s' % article_title)
            logging.log(logging.DEBUG, 'link: %s' % article_link)

            article_collection = td_collection.css('a::text').extract_first()
            logging.log(logging.DEBUG, 'collection: %s' % article_collection)

            article_author = td_author.css('a::text').extract_first()
            logging.log(logging.DEBUG, 'author: %s' % article_author)

            article_date = td_date.css('td::text').extract_first().strip()
            logging.log(logging.DEBUG, 'date: %s\n' % article_date)

            # generate request to download and parse an article
            full_url = start_url + '/' + article_link
            yield Request(full_url, callback=self.parse_article)

            cnt += 1
            if cnt > 2: break

        # 用今天日期减掉时间差，参数为1天，获得昨天的日期
        #last_day = datetime.now() - timedelta(days=MorningstarSpider.crawl_days)
        #logging.log(logging.INFO, 'parse_start_url(): current year-month %s' % last_day.strftime('%Y-%m'))
        
        #sitemap_loc_url = start_url + '/sitemap/%s' % last_day.strftime('%Y/%m')
        #logging.log(logging.DEBUG, 'sitemap url: %s' % sitemap_loc_url)
        #sitemap_request = Request(sitemap_loc_url, callback=self.parse_child_sitemap)
        #sitemap_request.meta['dont_cache'] = True
        # yield sitemap_request


    def parse_child_sitemap(self, response):
        logging.log(logging.INFO, 'parse_child_sitemap(): %s' % response.url)

        response.selector.remove_namespaces()

        article_url_list = response.css('loc::text').extract()
        logging.log(logging.INFO, 'parse_child_sitemap(): %d url extracted' % len(article_url_list))

        investing_url_list = []
        for article_url in article_url_list:
            # 忽略下载URL含有关键字的文章
            exclusive_words = ['motley', 'foolish', 'solar', 'student']
            skip_down_flag = False
            for w in exclusive_words:
                if w in article_url:
                    skip_down_flag = True
                    break
            if skip_down_flag:
                continue

            # 只下载投资类文章
            if article_url.startswith(start_url + '/investing'):
                investing_url_list.append(article_url)

        logging.log(logging.DEBUG, 'parse_child_sitemap(): %d url to filter' % len(investing_url_list))

        max_traceback_days = 30
        day_counter = OrderedDict()
        for d in range(max_traceback_days):
            last_day = datetime.now() - timedelta(days=d)
            last_day_key = last_day.strftime('%Y/%m/%d')
            day_counter[last_day_key] = list()

        download_url_list = list()
        max_download_per_day = MorningstarSpider.max_fetched_article_per_day
        for url in investing_url_list:
            key = ''
            for k in day_counter.keys():
                if k in url:
                    key = k
                    break
            if key == '':
                continue
            if SQLiteManager.has_article('ArticleEN', url):
                day_counter[key].append(url)
        logging.log(logging.DEBUG, 'parse_child_sitemap(): articles in database\n%s' % json.dumps(day_counter, indent=4))

        for url in investing_url_list:
            key = ''
            for k in day_counter.keys():
                if k in url:
                    key = k
                    break
            if key == '':
                continue
            if len(day_counter[key]) < max_download_per_day and url not in day_counter[key]:
                day_counter[key].append(url)
                download_url_list.append(url)

        logging.log(logging.INFO, 'parse_child_sitemap(): %d url to be downloaded' % len(download_url_list))

        # send URL download request
        for url in download_url_list:
            logging.log(logging.INFO, 'request %s' % url)
            yield Request(url, callback=self.parse_article)

    def parse_article(self, response):
        logging.log(logging.DEBUG, '---------------------------------------------')
        logging.log(logging.DEBUG, type(response))
        MorningstarSpider.fetched_cnt += 1
 
        #------------------------------------------------------------------
        # extract article info
        #------------------------------------------------------------------
        # main title
        mainTitle = response.css('.article-header .article-title::text').extract_first()
        logging.log(logging.DEBUG, 'title: %s' % mainTitle)

        # article tag
        articleTag = response.css('.article-header .article-eyebrow a::text').extract_first()
        logging.log(logging.DEBUG, 'articleTag: %s' % articleTag)

        # article content
        content = response.css('.article-main').extract_first()
        if isinstance(content, str):
            logging.log(logging.DEBUG, "content ordinary string")
        elif isinstance(content, unicode):
            logging.log(logging.DEBUG, "content unicode string, convert to UTF-8")
            content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore').encode("UTF-8")
        else:
            logging.error("content not a string")
            sys.exit(1)

        # publish timestamp
        iso_time = response.css('head meta[name=buildTimestamp]::attr("content")').extract_first()
        publishTime = dp.parse(iso_time).strftime("%Y%m%d%H%M%S")
        logging.log(logging.DEBUG, 'publishTime: %s' % publishTime)

        #------------------------------------------------------------------
        # extract author signature and sub-info
        #------------------------------------------------------------------
        article_signature = response.css('.article-signature')
        # author name
        authorName = article_signature.css('b[data-authoremail]::text').extract_first()
        logging.log(logging.DEBUG, 'authorName: %s' % authorName)
        # author email
        authorEmail = article_signature.css('b[data-authoremail]::attr("data-authoremail")').extract_first()
        logging.log(logging.DEBUG, 'authorEmail: %s' % authorEmail)
        # author info
        authorInfo = article_signature.css('div .popover-content ul.menu li::text').extract_first().strip()
        if isinstance(authorInfo, str):
            logging.log(logging.DEBUG, "authorInfo ordinary string")
        elif isinstance(authorInfo, unicode):
            logging.log(logging.DEBUG, "authorInfo unicode string, convert to UTF-8")
            authorInfo = unicodedata.normalize('NFKD', authorInfo).encode('ascii', 'ignore').encode("UTF-8")
        else:
            logging.error("authorInfo not a string")
            sys.exit(1)
        logging.log(logging.DEBUG, 'authorInfo: %s' % repr(authorInfo))
        # author link
        authorLink = article_signature.css('div .popover-content ul.menu li a::attr("href")').extract_first().strip()
        logging.log(logging.DEBUG, 'authorLink: %s' % authorLink)
        #logging.log(logging.DEBUG, '---------------------------------------------')

        #------------------------------------------------------------------
        # populate item
        #------------------------------------------------------------------
        item = ArticleItem()
        item['url'] = response.url
        item['mainTitle'] = mainTitle
        item['content'] = content
        item['articleTag'] = articleTag
        item['articleSection'] = None
        item['publishTime'] = publishTime
        item['authorName'] = authorName
        item['authorContact'] = authorEmail
        item['authorInfo'] = authorInfo
        item['authorLink'] = start_url + authorLink

        # debug
        logging.log(logging.INFO, 'url=%s mainTitle=%s publishTime=%s' % (item['url'], item['mainTitle'], item['publishTime']))
        logging.log(logging.INFO, 'extract article from HTML response ok!')
        logging.log(logging.INFO, '--------------------------------------')
        return item
