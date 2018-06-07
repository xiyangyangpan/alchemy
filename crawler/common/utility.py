#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import logging.config
#root_path = os.getenv('USERPROFILE') + '//OneDrive//alchemy//crawler//common//'
#logging.config.fileConfig(root_path+"logging.config")
logging.config.fileConfig("common/logging.config")
logger = logging.getLogger("alchemy")


class Stack:
    def __init__(self):
        self.items = []

    def empty(self):
        return self.size() == 0

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def peek(self):
        return self.items[len(self.items) - 1]

    def size(self):
        return len(self.items)


