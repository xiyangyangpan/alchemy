#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from datetime import datetime
import json
import pickle
import zlib
import requests
import ConfigParser
from common.utility import logger
from common.DBI import SQLiteManager
from urlparse import *
import httplib
# httplib.HTTPConnection.debuglevel = 5

# 注意：drupal service -> REST -》 server
# Request/Response parsing必须配置为json格式
# logging.basicConfig(level=logging.DEBUG)

# --------------------------------------------------------------------
# 配置区域
# --------------------------------------------------------------------
cp = ConfigParser.SafeConfigParser()
cp.read('alchemy.conf')
auth_info = {'username': cp.get('site', 'user'), 'password': cp.get('site', 'pass')}
site_base_URL = cp.get('site', 'site_url')
logger.info('current user: %s' % cp.get('site', 'user'))
logger.info('site URL: %s' % repr(site_base_URL))

login_URL = 'rest/user/login'
session_token_URL = 'services/session/token'
term_URL = 'rest/taxonomy_term'
node_URL = 'rest/node'
CSRF = None
# --------------------------------------------------------------------


# --------------------------------------------------------------------
# login web site via REST API
# output: login response (JSON format)
# --------------------------------------------------------------------
def rest_login():
    login_headers = {
        'Content-Type': 'application/json',
        "Connection": "keep-alive"
    }
    rest_response_login = requests.post(urljoin(site_base_URL, login_URL), headers=login_headers, json=auth_info)
    # logger.debug('response_login.text = %s' % rest_response_login.text)
    if rest_response_login.status_code != requests.codes.ok:
        logger.error( rest_response_login)
        sys.exit(1)
    logger.debug('login success!')

    login_response = json.loads(rest_response_login.text)
    rest_session_headers = {
        'Cookie': login_response['session_name'] + '=' + login_response['sessid'],
        'X-CSRF-Token': login_response['token'],
        'Content-type': 'application/json'
    }
    return rest_session_headers


# --------------------------------------------------------------------
# list all nodes (JSON list)
#   input:
#     rest_session_headers: headers for connected session (json format)
# --------------------------------------------------------------------
def rest_list_nodes(rest_session_headers):
    response_list = requests.get(urljoin(site_base_URL, node_URL), headers=rest_session_headers, json={})
    print ('response_list = ', response_list.text)
    print ('-----------------------------------------\n')


# --------------------------------------------------------------------
# list all nodes (JSON list)
#   input:
#     rest_session_headers: headers for connected session (json format)
# --------------------------------------------------------------------
# httplib.HTTPConnection.debuglevel = 5
def rest_del_nodes(rest_session_headers):
    response = requests.get(urljoin(site_base_URL, node_URL), headers=rest_session_headers, json={})
    node_list = json.loads(response.text)
    for node in node_list:
        if node['type'] == 'paid_article':
            response_del = requests.delete(
                urljoin(site_base_URL, node_URL+'/'+node['nid']),
                headers=rest_session_headers,
                json={})
            print( 'response_list = ', response_del)
    print( '-----------------------------------------\n')


def rest_del_all_nodes(rest_session_headers):
    while True:
        response = requests.get(urljoin(site_base_URL, node_URL), headers=rest_session_headers, json={})
        node_list = json.loads(response.text)
        logger.debug('fetch node list. status = %s' % response.status_code)
        if response.status_code != 200:
            break

        cnt = 0
        for node in node_list:
            if node['type'] == 'article':
                cnt += 1
                url_del = urljoin(site_base_URL, node_URL+'/'+node['nid'])
                response_del = requests.delete(
                    url_del,
                    headers=rest_session_headers,
                    json={})
                print(response_del)
        if cnt == 0:
            logger.debug('no article node, exit!!')
            break
        else:
            logger.debug('delete %d nodes from remote site' % cnt)


# --------------------------------------------------------------------
# list all taxonomy term (JSON list)
#   input:
#     rest_session_headers: headers for connected session (json format)
# --------------------------------------------------------------------
def rest_list_taxonomy_term(rest_session_headers):
    logger.debug('list taxonomy term')

    response = requests.get(urljoin(site_base_URL, term_URL), headers=rest_session_headers, json={})
    logger.debug( 'response_list = ', response.text)
    parsed = json.loads(response.text)
    # print json.dumps(parsed, indent=4, sort_keys=True)
    return parsed


def get_taxonomy_term_tid(taxonomy_term, term_name):
    term_tid = ''
    for t in taxonomy_term:
        print( 't = ', t)
        print( 'articleTag = ', term_name)
        if t['name'] == term_name:
            term_tid = t['tid']
            break
    if term_tid == '':
        sys.exit(1)
    return term_tid


# --------------------------------------------------------------------
# Post an article to Web site
#   input:
#     article_type: "paid_article", "article"
#     rest_session_headers: headers for connected session (json format)
#     article
# --------------------------------------------------------------------
# httplib.HTTPConnection.debuglevel = 5
def pub_cn_article(article_type, url, rest_session_headers):
    logger.info('article URL: %s' % url)
    article_cn = SQLiteManager.get_article('ArticleCN', url)
    if article_cn is None:
        logger.error("failed to get article!! url: %s" % url)
        return False

    main_title = article_cn.mainTitle
    term_name = article_cn.articleTag
    content = pickle.loads(zlib.decompress(article_cn.content))
    logger.info('article content size: %d' % len(content))

    # 设置订阅类型
    if len(content) >= 2500:
        subscription_type = '付费'
    else:
        subscription_type = '免费'

    orig_article_source = "<a href=\"%s\">The Motley Fool</a>" % url
    pub_date_format = "%m/%d/%Y - %H:%M"
    orig_article_ts = datetime.strptime(article_cn.publishDate, '%b %d, %Y at %I:%M%p').strftime(pub_date_format)
    logger.info('article publish time: %s' % orig_article_ts)

    article = {
        "title": main_title,
        "field_publish_date": {
            'und': [{
                'value': {
                    'date': orig_article_ts
                }
            }]
        },
        "status": "1",
        "comment": "2",
        "promote": "1",
        "type": article_type,
        "language": "zh-hans",
        "body": {
            "und": [{
                "value": content,
                "format": "full_html"
            }]
        },
        "field_tags": {"und": term_name},
        "field_subscription": {"und": subscription_type},
        "field_author": {
            "und": [{
                "value": article_cn.authorName
            }]
        },
        "field_source": {
            "und": [{
                "value": orig_article_source,
                "format": "filtered_html"
            }]
        }
    }

    logger.debug('post an article to site')
    res = requests.post(urljoin(site_base_URL, node_URL), headers=rest_session_headers, json=article)
    logger.debug('response text: %s\n' % res.text)
    if res.status_code == 200:
        logger.info('post article successfully! status code: 200\n')
        return True
    else:
        logger.error(res.text)
        return False


# --------------------------------------------------------------------
# Post Chinese Articles to Web site
#   input:
#     rest_session_headers: headers for connected session (json format)
#     SQL DB: articles in MySQL DB
# --------------------------------------------------------------------
def pub_articles_to_site(rest_session_headers, domain, bulk_size=1):
    logger.debug('ready to publish articles ... domain: %s' % domain)
    cnt_succ = 0
    cnt_fail = 0

    for article in SQLiteManager.all_article('ArticleCN'):
        # if domain is 'all', publish all articles
        if (not article.publishedFlag) or (domain is 'all'):
            if not pub_cn_article('article', article.url, rest_session_headers):
                # error occurs when posting article to web site
                cnt_fail += 1
                if cnt_fail == bulk_size:
                    break
                continue
            else:
                SQLiteManager.upd_article_published_flag('ArticleCN', article.url, True)
                cnt_succ += 1
                if cnt_succ == bulk_size:
                    break
    logger.debug('%d new articles are published.' % cnt_succ)

