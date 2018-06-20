# -*- coding: utf-8 -*-
import logging
import datetime
import calendar
import unicodedata
from datetime import datetime, timedelta
from collections import OrderedDict
import sys
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request
from crawler.items import FoolItem
from crawler.items import AlchemyItem
from common.DBI import SQLiteManager
import ConfigParser

cp = ConfigParser.SafeConfigParser()
cp.read('alchemy.conf')
allowed_domain = cp.get('crawler', 'allowed_domain')
start_url = cp.get('crawler', 'start_url')


class FoolSpider(CrawlSpider):
    name = 'fool'
    allowed_domains = [allowed_domain]
    start_urls = [start_url+'/sitemap']
    cls_db_mgr = None
    fetched_cnt = 0
    crawl_days = 1

    def parse_start_url(self, response):
        logging.log(logging.INFO, 'parse_start_url(): %s' % response.url)

        # 用今天日期减掉时间差，参数为1天，获得昨天的日期
        last_day = datetime.now() - timedelta(days=FoolSpider.crawl_days)
        logging.log(logging.INFO, 'parse_start_url(): current year-month %s' % last_day.strftime('%Y-%m'))
        sitemap_loc_url = start_url + '/sitemap/%s' % last_day.strftime('%Y/%m')
        logging.log(logging.DEBUG, 'sitemap url: %s' % sitemap_loc_url)
        sitemap_request = Request(sitemap_loc_url, callback=self.parse_child_sitemap)
        sitemap_request.meta['dont_cache'] = True
        yield sitemap_request

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

        logging.log(logging.INFO, 'parse_child_sitemap(): %d url to filter' % len(investing_url_list))

        max_crawler_days = 20
        day_counter = OrderedDict()
        for d in range(max_crawler_days):
            last_day = datetime.now() - timedelta(days=d)
            last_day_key = last_day.strftime('%Y/%m/%d')
            day_counter[last_day_key] = list()

        download_url_list = list()
        max_download_per_day = 15
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
        logging.log(logging.INFO, 'parse_child_sitemap():\n%s' % str(day_counter))

        for url in investing_url_list:
            key = ''
            for k in day_counter.keys():
                if k in url:
                    key = k
                    break
            if key == '':
                continue
            if len(day_counter[key]) < max_download_per_day:
                day_counter[key].append(url)
                download_url_list.append(url)

        logging.log(logging.INFO, 'parse_child_sitemap(): %d url to be downloaded' % len(download_url_list))

        # send URL download request
        for url in download_url_list:
            logging.log(logging.INFO, 'request %s' % url)
            #yield Request(url, callback=self.parse_article)

    def parse_article(self, response):
        logging.log(logging.DEBUG, type(response))
        FoolSpider.fetched_cnt += 1
 
        mainTitle = response.css('div#article-1.full_article > section.usmf-new.article-header > header > h1::text').extract_first()
        if mainTitle is None: mainTitle = ''
        
        subTitle = response.css('div#article-1.full_article > section.usmf-new.article-header > header > h2::text').extract_first()
        if subTitle is None: subTitle = ''
        
        content = response.css('span.article-content').extract_first()
        if content is None: content = ''

        # extract author name
        authorName = response.css('div.author-name::text').extract_first()
        if authorName is None: authorName = ''
        
        # extract publish date
        publishDate = response.css('div.publication-date::text').extract_first()
        if publishDate is None:
            logging.log(logging.ERROR, 'fail to extract div.publication-date::text')
            sys.exit(1)
        
        articleTag = response.xpath('//meta[contains(@property,"article:tag")]/@content').extract_first()
        if articleTag is None: articleTag = ''
        
        articleSection = response.xpath('//meta[contains(@property,"article:section")]/@content').extract_first()
        if articleSection is None: articleSection = ''
        
        item = FoolItem()
        item['url'] = response.url
        item['mainTitle'] = mainTitle
        item['subTitle'] = subTitle
        item['articleTag'] = articleTag
        item['articleSection'] = articleSection
        item['authorName'] = authorName.strip()
        item['publishDate'] = publishDate.strip()
        item['publishTime'] = None

        if isinstance(content, str):
            item['content'] = content
            logging.log(logging.DEBUG, "parse_article(): content is ordinary string")
        elif isinstance(content, unicode):
            logging.log(logging.DEBUG, "parse_article(): content is unicode string, convert to UTF-8 string.")
            content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore')
            item['content'] = content.encode("UTF-8")
        else:
            logging.error("not a string")
            sys.exit(1)

        # debug
        logging.log(logging.INFO, 'url=%s mainTitle=%s publishDate=%s' % (item['url'], item['mainTitle'], item['publishDate']))
        logging.log(logging.INFO, 'extract article from HTML response ok!')
        logging.log(logging.INFO, '--------------------------------------')
        return item
