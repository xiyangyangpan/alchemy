# -*- coding:utf-8 -*-
import os
import codecs
from utility import logger, root_path
from DBI import ArticleEN, SQLiteManager
from scrapy.selector import Selector
from items import FoolItem


def extract_ori_html(response):
    if response:
        main_title = response.css('div#article-1.full_article > section.usmf-new.article-header > header > h1::text').extract_first()
        if main_title is None: main_title = ''

        sub_title = response.css('div#article-1.full_article > section.usmf-new.article-header > header > h2::text').extract_first()
        if sub_title is None: sub_title = ''

        content = response.css('span.article-content').extract_first()
        if content is None: content = ''

        # extract author name
        author_name = response.css('div.author-name::text').extract_first()
        if author_name is None: author_name = ''

        # extract publish date
        publish_date = response.css('div.publication-date::text').extract_first()
        if publish_date is None: publish_date = ''

        article_tag = response.xpath('//meta[contains(@property,"article:tag")]/@content').extract_first()
        if article_tag is None: article_tag = ''

        article_section = response.xpath('//meta[contains(@property,"article:section")]/@content').extract_first()
        if article_section is None: article_section = ''

        article_url = response.xpath('//meta[contains(@property,"og:url")]/@content').extract_first()
        if article_url is None: article_url = ''

        item = FoolItem()
        item['url'] = article_url
        item['mainTitle'] = main_title
        item['subTitle'] = sub_title
        item['content'] = content
        item['articleTag'] = article_tag
        item['articleSection'] = article_section
        item['authorName'] = author_name.strip()
        item['publishDate'] = publish_date.strip()
        return item


def read_html_from_repository():
    for root, dirs, files in os.walk(root_path + '..//temp'):
        logger.debug(root)
        file_list = '\nrepository dir: ' + root
        for f in files:
            file_list += '\n\t' + f
        logger.debug(file_list)

        for f in files:
            article_file = root + '//' + f
            html_bytes = codecs.open(article_file, 'r', 'utf-8').read()
            html_selector = Selector(text=html_bytes)
            item = extract_ori_html(html_selector)
            logger.debug(item)

            if not SQLiteManager.has_article('ArticleEN', item['url']):
                logger.debug('store new article in database. title: %s, url: %s'
                             % (item['mainTitle'], item['url']))
                SQLiteManager.add_article(ArticleEN(item))
            else:
                logger.info('article already exists URL: %s' % item['url'])


if __name__ == "__main__":
    #translate_from_db()
    read_html_from_repository()
