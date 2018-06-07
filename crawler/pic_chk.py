#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from datetime import datetime
import json
import pickle
import zlib
import requests
from common.utility import logger
from common.DBI import SQLiteManager

cur_version = sys.version_info
print(cur_version)
if cur_version.major >= 3:
    from urllib.parse import urljoin
    import http.client
else:
    from urlparse import *
    import urllib



def p2_check():
    logger.debug('check pickle version...')
    cnt_succ = 0
    cnt_fail = 0

    url_list = list()
    for article in SQLiteManager.all_article('ArticleCN'):
        try:
            #if article.contentCN : continue
            url = article.url
            print(url)
            decompressed_bytes = zlib.decompress(article.content)
            content = pickle.loads((decompressed_bytes))
            #content = pickle.loads(bytes.decode(decompressed_bytes))
            #zlib_content = zlib.compress(bytes(content, encoding="utf8"))
            #SQLiteManager.upd_article_contentCN('ArticleCN', article.url, zlib_content)
            logger.debug("load content ok!")
            cnt_succ += 1
        except ValueError as e:
            print(e)
            cnt_fail += 1
            url_list.append(url)

    url_file = open("url.txt", "w")
    url_file.writelines(''.join(x+'\n' for x in url_list))
    url_file.close()

    logger.debug('%d new articles are converted.' % cnt_succ)
    logger.debug('%d failed.' % cnt_fail)


if __name__ == "__main__":
    p2_check()

