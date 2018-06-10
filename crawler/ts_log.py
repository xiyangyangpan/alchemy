#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger("TS")
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)-8s %(message)s', '%d %b %Y %H:%M:%S',)
file_handler = RotatingFileHandler("ts.log", maxBytes=2*1024*1024, backupCount=1)
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)
