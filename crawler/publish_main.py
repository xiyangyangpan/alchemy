#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from optparse import OptionParser
from cms.PubArticleToSite import *


if __name__ == "__main__":
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)

    parser.add_option("-m", "--mode",
                      default="pub",
                      help="mode: pub, revoke",
                      dest="mode")
    (options, args) = parser.parse_args()

    if options.mode == "pub":
        print("publish a translated article to web site")
        rest_session_headers = rest_login()
        pub_articles_to_site(rest_session_headers, bulk_size=3)
    elif options.mode == "revoke":
        print("revoke all published article from web site")
        rest_session_headers = rest_login()
        rest_del_all_nodes(rest_session_headers)
    else:
        parser.print_help()
        sys.exit(0)

