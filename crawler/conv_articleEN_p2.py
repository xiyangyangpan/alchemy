#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from datetime import datetime
import json
import pickle
import zlib
import chardet
from common.utility import logger
from common.DBI import SQLiteManager


def articleEN_p2_check():
    logger.debug('check pickle version...')
    cnt_succ = 0
    cnt_fail = 0

    for a in SQLiteManager.all_article('ArticleEN'):
        try:
            url = a.url
            article = SQLiteManager.get_article("ArticleEN", url)
            if article is None:
                logger.error("failed to load article!! url: %s" % url)
                sys.exit(1)
            decompressed_bytes = zlib.decompress(article.content)
            content = pickle.loads(decompressed_bytes)
            if isinstance(content, str):
                pass
            elif isinstance(content, unicode):
                #print(url)
                #print "unicode string"
                pass
            else:
                logger.error("not a string")
                sys.exit(1)
            # logger.debug("check content ok!")
            cnt_succ += 1
        except ValueError as e:
            print(url)
            print(e)
            cnt_fail += 1
            SQLiteManager.del_article('ArticleEN', url)
    logger.debug('%d success' % cnt_succ)
    logger.debug('%d failed.' % cnt_fail)

if __name__ == "__main__":
    articleEN_p2_check()

