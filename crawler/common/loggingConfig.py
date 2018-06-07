#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import logging.config


if __name__ == "__main__":
    logging.config.fileConfig("logging.config")
    logger = logging.getLogger("diamsql")
    
    logger.debug('This is debug message')
    logger.info('This is info message')
    logger.warning('This is warning message')