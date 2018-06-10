#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
from optparse import OptionParser
from cms.PubArticleToSite import *
from cms_log import logger


if __name__ == "__main__":
    usage = "usage: %prog [options] {all|bulk}"
    parser = OptionParser(usage)

    parser.add_option("-m", "--mode",
                      default="pub",
                      help="mode: pub, revoke",
                      dest="mode")
    (options, args) = parser.parse_args()
    print(args)

    if len(args) != 1 and args[0] not in ['all', 'bulk']:
        parser.print_help()
        sys.exit(0)
    domain = args[0]

    if options.mode == "pub":
        logger.info("publish translated articles to web site")
        logger.info("domain: %s" % domain)
        rest_session_headers = rest_login()
        pub_articles_to_site(rest_session_headers, domain=domain, bulk_size=3)
    elif options.mode == "revoke":
        logger.info("revoke published articles from web site")
        logger.info("domain: %s" % domain)
        rest_session_headers = rest_login()
        rest_del_all_nodes(rest_session_headers)
    else:
        parser.print_help()
        sys.exit(0)

