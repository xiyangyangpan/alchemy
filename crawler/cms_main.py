#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
from optparse import OptionParser
from cms.RestCommon import *
from cms.RestUser import create_test_user, rest_login, rest_logoff
from cms_log import logger


if __name__ == "__main__":
    usage = "usage: %prog [options] {all|bulk|user}"
    parser = OptionParser(usage)

    parser.add_option("-m", "--mode",
                      default="pub",
                      help="mode: pub, revoke, create",
                      dest="mode")
    (options, args) = parser.parse_args()
    if len(args) != 1 and args[0] not in ['all', 'bulk', 'user']:
        parser.print_help()
        sys.exit(0)
    domain = args[0]

    if options.mode == "pub":
        logger.info("publish translated articles to web site. domain: %s" % domain)
        rest_session_headers = rest_login()
        pub_articles_to_site(rest_session_headers, domain=domain, bulk_size=3)
    elif options.mode == "revoke":
        logger.info("revoke published articles from web site. domain:%s" % domain)
        rest_session_headers = rest_login('george', '123456')
        rest_del_all_nodes(rest_session_headers)
        rest_logoff(rest_session_headers)
    elif options.mode == "create":
        logger.info("create user on web site")
        rest_session_headers = rest_login()
        create_test_user(rest_session_headers)
    else:
        parser.print_help()
        sys.exit(0)

