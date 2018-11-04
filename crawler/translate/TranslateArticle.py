#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import zlib
import pickle
import unicodedata
from datetime import datetime
from scrapy.selector import Selector
from bs4 import BeautifulSoup
from bs4 import NavigableString
from common.DBI import ArticleCN
from common.DBI import SQLiteManager
from common.DBI import AuthorCard
from ArticleElem import ArticleElem
from BaiduApi import BaiduTranslator
from Translator import Translator
from ts_log import logger

depth = 0


term_mapping = {
    'usmf-health-care': '健康医疗',
    'usmf-industrials': '工业',
    'usmf-consumer-goods': '消费品',
    'usmf-other': '其它',
    'usmf-financials': '金融',
    'usmf-technology-and-telecom': '技术通信',
    'usmf-energy-materials-and-utilities': '能源材料公用事业',
    'usmf-investment-planning': '投资规划'
}


def prt_fmt(st, depth_num):
    space_num = 2 * depth_num
    if st:
        if len(st) > 60:
            fmt = '{0:{1}} {2} ...'.format('', space_num, repr(st[:60]))
        else:
            fmt = '{0:{1}} {2}'.format('', space_num, repr(st))
    else:
        fmt = '{0:{1}} {2}'.format('', space_num, '')
    return fmt


def prt_tree(root, depth_num):
    space_num = 2 * depth_num
    if root.string:
        if len(root.string) > 50:
            fmt = '{0:{1}}{2} "{3} ..."'.format('', space_num, root.name, repr(root.string[:50]))
        else:
            fmt = '{0:{1}}{2} "{3}"'.format('', space_num, root.name, repr(root.string))
    else:
        fmt = '{0:{1}}{2} "{3}"'.format('', space_num, root.name, '')
    return fmt


# Description: check if a html tag has specified html tags
# Input: html tag tree
# Output: true/false
def has_sub_tag(root, tag_list):
    for child in root.contents:
        tag_name = child.name
        if tag_name and tag_name.upper() in tag_list:
            return True
    return False


# Description: deep-first-search origin html format article content
# Input: original html byte stream
# Output: tree of ArticleElem, every node contains origin paragraph text
def extract_content(ori_node, new_node, debug=False):
    global depth
    depth += 1
    if debug:
        logger.debug(prt_tree(ori_node, depth))

    rs = ''
    if isinstance(ori_node, NavigableString):
        # NavigableString node is leaf node, no need traverse sub HTML node
        rs = ori_node
        depth -= 1
        return rs
    else:
        # visit self before visiting children
        tag_name = ori_node.name.upper()
        if debug:
            if tag_name in ['DIV', 'TABLE', 'BLOCKQUOTE', 'H2', 'P', 'EM', 'IMG']:
                logger.debug(prt_fmt('+++ BEGIN %s +++' % tag_name, depth))

        if tag_name == 'DIV':
            # if the div node has sub-tag e.g. div, p, img, table, create new Elem;
            # otherwise, ignore the tag
            if has_sub_tag(ori_node, ['DIV', 'P', 'IMG', 'TABLE', 'EM']):
                div_obj = ArticleElem('DIV', '')
                new_node.add(div_obj)
                new_node = div_obj

        # --------------------------------------------------------
        # visit child nodes
        # ignore process child if encountering embed table tag
        # --------------------------------------------------------
        if tag_name not in ['TABLE', 'BLOCKQUOTE']:
            for child in ori_node.contents:
                bq_text = extract_content(child, new_node, debug).strip()
                if isinstance(bq_text, str):
                    bq_text = bq_text.replace(u'\xa0', u' ')
                elif isinstance(bq_text, unicode):
                    pass
                rs += bq_text

        # --------------------------------------------------------
        # visit self node after visiting child html nodes
        # --------------------------------------------------------
        if debug:
            if tag_name in ['DIV', 'H2', 'P']:
                logger.debug(prt_fmt('--- END %s --- %s' % (tag_name, repr(rs)), depth))
            elif tag_name in ['IMG']:
                logger.debug(prt_fmt('--- END %s ---' % ori_node['alt'], depth))
            elif tag_name in ['TABLE', 'BLOCKQUOTE']:
                logger.debug(prt_fmt('--- END %s --- %s' % (tag_name, ori_node.prettify('utf-8', formatter='html')), depth))

        new_sub_node = None
        if tag_name == 'DIV':
            # embed table tag
            if ori_node.has_attr('class') and 'table-responsive' in ori_node['class']:
                pass
            # discard null div tag if the div node don't have sub-tag e.g. div, p
            elif has_sub_tag(ori_node, ['DIV', 'P', 'IMG', 'TABLE', 'BLOCKQUOTE', 'EM']):
                pass
            else:
                # create a new DIV tag in article tree
                if rs != '':
                    new_sub_node = ArticleElem('DIV', unicodedata.normalize("NFKD", rs).encode('ascii', 'ignore'))
        elif tag_name in ['TABLE', 'BLOCKQUOTE']:
            # convert bs4.element.Tag to string
            rs = str(ori_node)
            new_sub_node = ArticleElem(tag_name, rs)
        elif tag_name in ['H2']:
            if rs != '':
                new_sub_node = ArticleElem('HEAD', unicodedata.normalize("NFKD", rs).encode('ascii', 'ignore'))
        elif tag_name in ['P']:
            if has_sub_tag(ori_node, ['EM']):
                if rs != '':
                    new_sub_node = ArticleElem('EM', unicodedata.normalize("NFKD", rs).encode('ascii', 'ignore'))
            else:
                if rs != '':
                    new_sub_node = ArticleElem('PARA', unicodedata.normalize("NFKD", rs).encode('ascii', 'ignore'))
        elif tag_name in ['IMG']:
            new_sub_node = ArticleElem('IMG', '', ori_node)

        # add child node in new generated tree
        if new_sub_node:
            new_node.add(new_sub_node)
        depth -= 1
        return rs

def translate_content(orig_content):
    # translate content
    sel = Selector(text=orig_content)
    for css_div in sel.css('span.article-content').extract():
        try:
            soup_tree = BeautifulSoup(css_div, 'lxml')

            # remove embed advertisement filtering by 'div class="interad"'
            for adv in soup_tree.find_all('div', class_='interad'):
                adv.decompose()

            # extract content from original source HTML
            logger.info('begin extracting content ...')
            article_elem = ArticleElem('BODY', '')
            extract_content(soup_tree, article_elem, debug=False)
            # logger.debug('\n' + article_elem.to_str())
            logger.info('end extracting content!')

            # translate original text into chinese text
            logger.info('begin translating content ...')
            article_elem.translate()
            logger.info('end translating content!')

            # convert tree to HTML tree
            html_tree = article_elem.to_html(article_elem, None, None)
            # logger.debug(html_tree.prettify('utf-8', formatter='html'))

            return str(html_tree)
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(e)
            sys.exit(1)

def translate_orig_article_content(orig_content):
    # translate content
    sel = Selector(text=orig_content)
    for css_div in sel.css('.article-main').extract():
        try:
            soup_tree = BeautifulSoup(css_div, 'lxml')

            # remove embed advertisement filtering by 'div class="interad"'
            for adv in soup_tree.find_all('div', class_='ad-container'):
                adv.decompose()

            # extract content from original source HTML
            logger.info('begin extracting content')
            article_elem = ArticleElem('BODY', '')
            extract_content(soup_tree, article_elem, debug=True)
            logger.info('end extracting content')

            # translate original text into chinese text
            logger.info('begin translating content')
            article_elem.translate()
            logger.info('end translating content')

            # convert tree to HTML tree
            html_tree = article_elem.to_html(article_elem, None, None)
            # logger.debug(html_tree.prettify('utf-8', formatter='html'))

            return str(html_tree)
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(e)
            sys.exit(1)

# ----------------------------------------------------------------------------------
# Description: parse origin html format article content, translate to chinese text
#              and convert html format article
# Input:
#   original html byte stream from MySQL DB
#   bulk size: translation articles per bulk
# Output: chinese html byte stream
# ----------------------------------------------------------------------------------
def translate_articles(bulk_size=1):
    logger.info('Loads articles from DB then translates articles\n')
    success_count, fail_count = 0, 0

    # for article in SQLiteManager.all_article('ArticleEN'):
    for url in SQLiteManager.query_un_translated_article():
        article = SQLiteManager.get_article('ArticleEN', url)
        if article is None:
            logger.error('error get article!! URL: %s\n' % url)
            continue

        # filtering some categories of articles
        if article.articleSection in ['retirement', 'careers', 'taxes', 'credit-cards', 'mortgages']:
            logger.debug('ignore translating article for %s. URL: %s\n' % (article.articleSection, url))
            continue

        # filtering some categories of articles
        if article.articleTag in ['usmf-other']:
            logger.debug('ignore translating article for %s. URL: %s\n' % (article.articleTag, url))
            continue

        logger.info('begin translate article %s' % url)

        # set the translate method for all ArticleElem
        translator_vendor = BaiduTranslator()
        if bulk_size >= 0:
            ArticleElem.translator = translator_vendor
        #else:
        #    ArticleElem.translate_func = ms_translate

        # construct an article object
        article_cn = ArticleCN()
        article_cn.url = article.url

        # translate main title
        main_title = unicodedata.normalize('NFKD', article.mainTitle).encode('ascii', 'ignore')
        article_cn.mainTitle = translator_vendor.translate(main_title)

        # translate sub-title
        sub_title = unicodedata.normalize('NFKD', article.subTitle).encode('ascii', 'ignore')
        article_cn.subTitle = translator_vendor.translate(sub_title)

        if article.articleTag in term_mapping.keys():
            article_cn.articleTag = term_mapping[article.articleTag]
        else:
            article_cn.articleTag = article.articleTag
        article_cn.articleSection = article.articleSection
        article_cn.authorName = article.authorName
        article_cn.publishDate = article.publishDate
        article_cn.publishTime = datetime.strptime(article.publishDate, '%b %d, %Y at %I:%M%p')

        logger.debug('Main Title: %s' % article_cn.mainTitle)
        logger.debug('Sub Title: %s' % article_cn.subTitle)

        # translate content
        content_en = pickle.loads(zlib.decompress(article.content))
        content_cn = translate_content(content_en)

        # pickle object with protocol version 2 compatible with python 2.x
        #article_cn.content = zlib.compress(pickle.dumps(content_cn, protocol=2))
        article_cn.content = zlib.compress(pickle.dumps(content_cn))

        logger.debug('ready to store the translated article.')
        if SQLiteManager.add_article(article_cn):
            logger.debug('successfully store article(%s)\n' % article_cn.mainTitle)
            success_count += 1
            bulk_size -= 1
        else:
            logger.debug('fails to store translated article(%s) into database\n' % article_cn.mainTitle)
            fail_count += 1
        logger.debug('\n')

        # translate a bulk of articles every execution
        if bulk_size == 0:
            break
    logger.info('translating summary:\n\tsuccess = %d\n\tfail = %d' % (success_count, fail_count))

# ----------------------------------------------------------------------------------
# Description: generate html file
#              and convert html format article
# Output: chinese html byte stream
# ----------------------------------------------------------------------------------
def gen_html(file_name, content):
    import bs4

    # load the file
    with open("www/template.html") as inf:
        txt = inf.read()
        soup = bs4.BeautifulSoup(txt, 'lxml')

    # insert it into the document
    content_tag = BeautifulSoup(content, 'lxml')
    soup.body.append(content_tag)

    # save the file again
    with open("www/" + file_name, "w") as outf:
        outf.write(str(soup))

# ----------------------------------------------------------------------------------
# Description: parse origin html format article content, translate to chinese text
#              and convert html format article
# Input:
#   original html byte stream from MySQL DB
#   bulk size: translation articles per bulk
# Output: chinese html byte stream
# ----------------------------------------------------------------------------------
def translate_orig_articles(bulk_size=1):
    logger.info('Loads articles from DB then translates articles\n')
    success_count, fail_count = 0, 0

    un_trans_urls = SQLiteManager.query_un_translated_orig_article()
    if len(un_trans_urls) == 0:
        logger.info('no article to translate!')
        return

    for url in un_trans_urls:
        article = SQLiteManager.get_article('ArticleOrig', url)
        if article is None:
            logger.error('error get article!! URL: %s\n' % url)
            continue

        logger.info('begin translate article %s' % url)

        # set the translate method for all ArticleElem
        translator_vendor = BaiduTranslator()
        #translator_vendor = Translator()
        if bulk_size >= 0:
            ArticleElem.translator = translator_vendor

        # translate main title
        main_title = unicodedata.normalize('NFKD', article.mainTitle).encode('ascii', 'ignore')
        article.mainTitleCN = translator_vendor.translate(main_title)
        logger.debug('Main Title: %s' % article.mainTitleCN)

        # translate content
        content_en = pickle.loads(zlib.decompress(article.content))
        content_cn = translate_orig_article_content(content_en)

        # pickle object with protocol version 2 compatible with python 2.x
        article.contentCN = zlib.compress(pickle.dumps(content_cn))
        gen_html('en_article.html', content_en)
        gen_html('cn_article.html', content_cn)

        logger.debug('ready to store the translated article.')
        if SQLiteManager.upd_article('ArticleOrig', article):
            logger.debug('successfully store article(%s)\n' % article.mainTitle)
            success_count += 1
            bulk_size -= 1
        else:
            logger.debug('fails to store translated article(%s) into database\n' % article.mainTitle)
            fail_count += 1
        logger.debug('\n')
        break

        # translate a bulk of articles every execution
        if bulk_size == 0:
            break
    logger.info('translating summary:\n\tsuccess = %d\n\tfail = %d' % (success_count, fail_count))

# ----------------------------------------------------------------------------------
# Description: translate author info into chinese
#              and convert html format article
# ----------------------------------------------------------------------------------
def translate_author(bulk_size=20):
    logger.debug('Loads articles from DB then translates article tags ...')
    success_count, fail_count = 0, 0

    authors = AuthorCard.get_un_translated_authors()
    if len(authors) == 0:
        logger.info('no author to translate!')

    # set up translator
    translator_vendor = BaiduTranslator()
    for author in authors:
        logger.debug('%s %s' % (author.name, author.contact))
        author_card =  AuthorCard.get(author.contact)
        info = pickle.loads(zlib.decompress(author_card.info))
        info_cn = translator_vendor.translate(info)
        author_card.set_info_cn(info_cn)
        success_count += 1
        bulk_size -= 1
        # translate a bulk of articles every execution
        if bulk_size == 0:
            break

    logger.debug('translating author:\n\tsuccess = %d\n\tfail = %d' % (success_count, fail_count))

# ----------------------------------------------------------------------------------
# Description: translate chinese article tags
#              and convert html format article
# ----------------------------------------------------------------------------------
def tr_article_tags(bulk_size=20):
    logger.debug('Loads articles from DB then translates article tags ...')
    success_count, fail_count = 0, 0
    for article in SQLiteManager.all_article('ArticleCN'):
        logger.debug('%s' % article.url)

        if term_mapping.has_key(article.articleTag):
            tags = term_mapping[article.articleTag]
            SQLiteManager.upd_article_tag('ArticleCN', article.url, tags)
            success_count += 1

            # translate a bulk of articles every execution
            bulk_size -= 1
            if bulk_size == 0:
                break

    logger.debug('translating article tags:\n\tsuccess = %d\n\tfail = %d' % (success_count, fail_count))


if __name__ == "__main__":
    translate_orig_articles(bulk_size=1)
