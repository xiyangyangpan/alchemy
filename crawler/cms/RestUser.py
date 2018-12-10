#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from datetime import datetime
import json
import requests
import ConfigParser
from common.DBI import SQLiteManager
from cms_log import logger
from urlparse import *
from RestCommon import site_base_URL
from RestCommon import user_URL, login_URL, logout_URL
import httplib
#httplib.HTTPConnection.debuglevel = 5


# --------------------------------------------------------------------
# login web site via REST API
# output: login response (JSON format)
# --------------------------------------------------------------------
def rest_login(user_id, pass_wd):
    rest_headers = {
        'Content-Type': 'application/json',
        "Connection": "keep-alive"
    }

    auth_info = {
        'username': user_id,
        'password': pass_wd
    }

    rest_response_login = requests.post(
        urljoin(site_base_URL, login_URL),
        headers=rest_headers,
        json=auth_info)
    # logger.debug('response_login.text = %s' % rest_response_login.text)
    if rest_response_login.status_code != requests.codes.ok:
        logger.error( rest_response_login)
        sys.exit(1)
    logger.debug('login success!')

    login_response = json.loads(rest_response_login.text)
    rest_session_headers = {
        'Cookie': login_response['session_name'] + '=' + login_response['sessid'],
        'X-CSRF-Token': login_response['token'],
        'Content-type': 'application/json'
    }
    return rest_session_headers

# --------------------------------------------------------------------
# logoff web site via REST API
# output: logoff response (JSON format)
# --------------------------------------------------------------------
def rest_logoff(rest_session_headers):
    rest_response_login = requests.post(
        urljoin(site_base_URL, logout_URL),
        headers=rest_session_headers
    )
    # logger.debug('response_login.text = %s' % rest_response_login.text)
    print rest_response_login
    if rest_response_login.status_code != requests.codes.ok:
        logger.error(rest_response_login)
        sys.exit(1)
    logger.debug('logout success!')


# --------------------------------------------------------------------
# Create an User on Web site
#   input:
#     User
#     rest_session_headers: headers for connected session (json format)
# --------------------------------------------------------------------
def rest_create_user(rest_session_headers, uname, umail, upasswd, uinfo, ucontact):
    user = {
        "name": uname,
        "mail": umail,
        "pass": upasswd,
        "field_user_information": {
            "und": {
                "0": {
                    "value": uinfo
                }
            }
        },
        "field_contact_address": {
            "und": {
                "0": {
                    "value": ucontact
                }
            }
        }
    }

    logger.info('create an user on site')
    res = requests.post(
        urljoin(site_base_URL, user_URL),
        headers=rest_session_headers,
        json=user)
    print(res.text)
    logger.debug('response text: %s\n' % res.text)
    if res.status_code == 200:
        logger.info('create user successfully! status code: 200\n')
        return True
    else:
        logger.error(res.text)
        return False

# --------------------------------------------------------------------
# Create an User on Web site
#   input:
#     User
#     rest_session_headers: headers for connected session (json format)
# --------------------------------------------------------------------
def create_test_user(rest_session_headers):
    for i in range(1, 30):
        uname = 'user' + str(i)
        umail = uname + '@alchemy.net'
        upasswd = 'password'
        uinfo = 'user info for ' + uname
        ucontact = 'user contact address for ' + uname
        rest_create_user(rest_session_headers,
                         uname, umail, upasswd,
                         uinfo, ucontact)


