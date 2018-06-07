#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
from translate.TranslateArticle import translate_articles


if __name__ == "__main__":
    # run translator every 30 minutes, max articles shall 
    # not exceed 6 in a bulk. Otherwise, memory overflow
    translate_articles(bulk_size=6)
    sys.exit(0)
