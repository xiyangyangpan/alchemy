#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
from translate.TranslateArticle import translate_articles
from translate.TranslateArticle import translate_orig_articles
from ts_log import logger


if __name__ == "__main__":
    # run translator every 30 minutes, max articles shall 
    # not exceed 6 in a bulk. Otherwise, memory overflow
    logger.info("translate articles ...")
    translate_orig_articles(bulk_size=1)
    sys.exit(0)
